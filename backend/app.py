"""Flask app: pages + API + background camera/AI worker + Virtual Hardware Simulation.
"""
import os
import threading
import time

from flask import Flask, jsonify, render_template, request, send_from_directory

from backend import config
from backend.database import init_db, log_event, save_violation
from backend.routes import hardware as hardware_routes
from backend.routes import system as system_routes
from backend.routes import vehicles as vehicle_routes
from backend.routes import violations as violation_routes
from backend.services.evidence import save_evidence
from backend.services.vahan import get_challan_data

try:
    import cv2
    _CV2 = True
except Exception:
    cv2 = None
    _CV2 = False


def create_app():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(__name__,
                template_folder=os.path.join(base, "frontend", "templates"),
                static_folder=os.path.join(base, "frontend", "static"))
    app.config["DEMO_MODE"] = config.DEMO_MODE

    init_db()
    log_event("startup", "System ONLINE")

    # Lazy imports: AI/hardware only loaded here, never at test-collection time.
    from ai.violation_engine import ViolationEngine
    from backend.services.camera import VideoSource
    from backend.services.serial_listener import SerialListener

    engine = ViolationEngine()
    camera = VideoSource(config.VIDEO_SOURCE)
    state = {"latest": None}

    def on_signal(s):
        log_event("signal", s)

    def on_violation(vehicle_number=None, violation_type="Red Light Violation"):
        engine.handle_red_light_trigger(state["latest"], vehicle_number=vehicle_number, violation_type=violation_type)

    listener = SerialListener(config.ARDUINO_PORT, config.ARDUINO_BAUD,
                              on_signal=on_signal, on_violation=on_violation,
                              demo_mode=config.DEMO_MODE)
    listener.start()

    app.config.update(engine=engine, camera=camera,
                      listener=listener, frames=state)

    # ---- background camera + AI pass ----
    def worker():
        n = 0
        while True:
            sig = getattr(listener, "signal_state", "GREEN")
            cnt = getattr(listener, "countdown", 8)
            ok, frame = camera.read(signal_state=sig, countdown=cnt)
            if not ok:
                time.sleep(0.5)
                continue
            state["latest"] = frame
            n += 1
            if n % 30 == 0:  # analyse ~1 fps of stream
                try:
                    engine.analyze_frame(frame)
                except Exception:
                    pass
            time.sleep(0.04)  # Smooth 25 fps stream

    threading.Thread(target=worker, daemon=True).start()

    # ---- API blueprints ----
    app.register_blueprint(violation_routes.bp, url_prefix="/api/violations")
    app.register_blueprint(vehicle_routes.bp, url_prefix="/api/vehicles")
    app.register_blueprint(system_routes.bp, url_prefix="/api")
    app.register_blueprint(hardware_routes.bp, url_prefix="/api/hardware")

    # ---- pages ----
    @app.get("/")
    def dashboard():
        return render_template("dashboard.html")

    @app.get("/live")
    def live():
        return render_template("live.html")

    @app.get("/violations")
    def violations_page():
        return render_template("violations.html")

    @app.get("/vehicle")
    def vehicle_page():
        return render_template("vehicle.html")

    @app.get("/reports")
    def reports():
        return render_template("reports.html")

    # ---- evidence files ----
    @app.get("/evidence/<path:name>")
    def evidence(name):
        directory = os.path.join(base, config.EVIDENCE_DIR)
        full = os.path.join(directory, name)
        if not os.path.exists(full):
            # If not in subfolder, check direct EVIDENCE_DIR
            full2 = os.path.join(base, "evidence", name)
            if os.path.exists(full2):
                return send_from_directory(os.path.join(base, "evidence"), name)
            return send_from_directory(app.static_folder, "placeholder.svg")
        return send_from_directory(directory, name)

    # ---- live MJPEG feed ----
    @app.get("/api/camera/feed")
    def feed():
        if not _CV2:
            return send_from_directory(app.static_folder, "placeholder.svg")

        def gen():
            while True:
                frame = state["latest"]
                if frame is None:
                    sig = getattr(listener, "signal_state", "GREEN")
                    cnt = getattr(listener, "countdown", 8)
                    _, frame = camera.read(signal_state=sig, countdown=cnt)
                if frame is None:
                    time.sleep(0.1)
                    continue
                try:
                    ok, jpg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                except Exception:
                    time.sleep(0.1)
                    continue
                if not ok:
                    continue
                yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
                       + jpg.tobytes() + b"\r\n")
                time.sleep(0.04)

        resp = app.response_class(
            gen(), mimetype="multipart/x-mixed-replace; boundary=frame")
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        return resp

    @app.get("/api/camera/status")
    def camera_status():
        st = camera.status() if hasattr(camera, "status") else {
            "available": True, "source": str(config.VIDEO_SOURCE)}
        st["has_frame"] = state["latest"] is not None
        return jsonify(st)

    @app.get("/api/camera/snapshot")
    def camera_snapshot():
        frame = state["latest"]
        if frame is None or not _CV2:
            sig = getattr(listener, "signal_state", "GREEN")
            cnt = getattr(listener, "countdown", 8)
            _, frame = camera.read(signal_state=sig, countdown=cnt)
        if frame is None or not _CV2:
            return send_from_directory(app.static_folder, "placeholder.svg")
        ok, jpg = cv2.imencode(".jpg", frame)
        if not ok:
            return send_from_directory(app.static_folder, "placeholder.svg")
        return app.response_class(jpg.tobytes(), mimetype="image/jpeg")

    # ---- E-Challan endpoint ----
    @app.get("/api/challan/<int:vid>")
    def get_challan(vid):
        from backend.database import get_connection
        conn = get_connection()
        row = conn.execute(
            "SELECT v.*, vh.vehicle_number FROM violations v "
            "JOIN vehicles vh ON vh.id = v.vehicle_id WHERE v.id = ?", (vid,)
        ).fetchone()
        conn.close()
        if not row:
            return jsonify({"error": "Challan not found"}), 404
        return jsonify(get_challan_data(dict(row)))

    # ---- demo endpoints ----
    @app.post("/api/demo/trigger")
    def demo_trigger():
        """Insert a sample violation with authentic evidence for presentation."""
        data = request.get_json(force=True, silent=True) or {}
        vtype = data.get("violation_type", "Red Light Violation")
        number = data.get("vehicle_number", "MH15AB1234")

        img = save_evidence(None, vtype, vehicle_number=number, location=config.LOCATION)
        vid = save_violation(number, vtype, location=config.LOCATION,
                             evidence_image=img, confidence=0.96, status="Potential Violation (verified)")
        log_event("demo", f"{vtype} | {number} | id={vid}")
        return jsonify({"id": vid, "demo": True, "evidence_image": img})

    @app.post("/api/demo/simulate-red-light")
    def demo_red_light():
        """Run the red-light pipeline on the current frame or synthetic junction."""
        vid = engine.handle_red_light_trigger(state["latest"])
        return jsonify({"id": vid, "pipeline": "real",
                        "note": "AI pipeline analyzed junction frame. Evidence captured."})

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=config.FLASK_PORT)
