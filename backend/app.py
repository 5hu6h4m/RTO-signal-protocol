"""Flask app: pages + API + background camera/AI worker.

Beginner map:
  create_app()  -> builds everything, safe to import for tests
  _camera_worker -> background thread: reads camera, keeps latest frame,
                   runs AI analyse every ~30 frames (helmet/triple)
  serial on_violation -> engine.handle_red_light_trigger(latest frame)
  /api/demo/*   -> clearly-labelled demo buttons (no fake AI claims)
"""
import os
import threading
import time

from flask import Flask, jsonify, render_template, request, send_from_directory

from backend import config
from backend.database import init_db, log_event, save_violation
from backend.routes import system as system_routes
from backend.routes import vehicles as vehicle_routes
from backend.routes import violations as violation_routes

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

    def on_violation():
        engine.handle_red_light_trigger(state["latest"])

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
            ok, frame = camera.read()
            if not ok:
                time.sleep(1)
                continue
            state["latest"] = frame
            n += 1
            if n % 30 == 0:  # analyse ~1 fps of a 30 fps stream
                try:
                    engine.analyze_frame(frame)
                except Exception:
                    pass

    threading.Thread(target=worker, daemon=True).start()

    # ---- API blueprints ----
    app.register_blueprint(violation_routes.bp, url_prefix="/api/violations")
    app.register_blueprint(vehicle_routes.bp, url_prefix="/api/vehicles")
    app.register_blueprint(system_routes.bp, url_prefix="/api")

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
            return send_from_directory(app.static_folder, "placeholder.svg")
        return send_from_directory(directory, name)

    # ---- live MJPEG feed (placeholder when no camera/cv2) ----
    @app.get("/api/camera/feed")
    def feed():
        if not (camera.available and _CV2):
            return send_from_directory(app.static_folder, "placeholder.svg")

        def gen():
            idle = 0
            while True:
                frame = state["latest"]
                if frame is None:
                    idle += 1
                    time.sleep(0.2)
                    # if camera died mid-stream, break so <img> fires
                    # onerror and the frontend shows Retry
                    if idle > 50:
                        break
                    continue
                idle = 0
                try:
                    ok, jpg = cv2.imencode(".jpg", frame)
                except Exception:
                    time.sleep(0.2)
                    continue
                if not ok:
                    continue
                yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
                       + jpg.tobytes() + b"\r\n")
                time.sleep(0.08)
        resp = app.response_class(
            gen(), mimetype="multipart/x-mixed-replace; boundary=frame")
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        return resp

    @app.get("/api/camera/status")
    def camera_status():
        """Lightweight probe used by Live page badge + Retry button."""
        st = camera.status() if hasattr(camera, "status") else {
            "available": bool(camera.available), "source": str(config.VIDEO_SOURCE)}
        st["has_frame"] = state["latest"] is not None
        return jsonify(st)

    @app.get("/api/camera/snapshot")
    def camera_snapshot():
        """Single JPEG of the latest frame — 'Camera test' button."""
        frame = state["latest"]
        if frame is None or not _CV2:
            return send_from_directory(app.static_folder, "placeholder.svg")
        ok, jpg = cv2.imencode(".jpg", frame)
        if not ok:
            return send_from_directory(app.static_folder, "placeholder.svg")
        return app.response_class(jpg.tobytes(), mimetype="image/jpeg")

    # ---- clearly-labelled demo endpoints ----
    @app.post("/api/demo/trigger")
    def demo_trigger():
        """Insert a sample violation for presentation (never claims AI did it)."""
        data = request.get_json(force=True, silent=True) or {}
        vtype = data.get("violation_type", "Red Light Violation")
        number = data.get("vehicle_number", "MH15AB1234")
        vid = save_violation(number, vtype, location=config.LOCATION,
                             confidence=0.0, status="Demo entry (simulated)")
        log_event("demo", f"{vtype} | {number} | id={vid}")
        return jsonify({"id": vid, "demo": True})

    @app.post("/api/demo/simulate-red-light")
    def demo_red_light():
        """Run the REAL red-light pipeline on the current camera frame."""
        vid = engine.handle_red_light_trigger(state["latest"])
        return jsonify({"id": vid, "pipeline": "real",
                        "note": "Real AI pipeline on live frame; plate may be unclear."})

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=config.FLASK_PORT)
