"""Virtual Hardware & Traffic Simulation Control Routes.

Allows the web dashboard to control the signal lights, trip the virtual IR sensor,
switch camera feed modes, and run realistic presentation scenarios.
"""
from flask import Blueprint, current_app, jsonify, request
from backend.services.vahan import lookup_vahan

bp = Blueprint("hardware", __name__)


@bp.get("/status")
def hardware_status():
    app = current_app
    listener = app.config.get("listener")
    camera = app.config.get("camera")
    hw = listener.get_status() if hasattr(listener, "get_status") else {}
    hw["camera_mode"] = getattr(camera, "mode", "auto")
    hw["camera_available"] = bool(camera and camera.available)
    return jsonify(hw)


@bp.post("/signal")
def set_signal():
    """Sets signal state ('RED', 'YELLOW', 'GREEN') or mode ('AUTO')."""
    data = request.get_json(force=True, silent=True) or {}
    state = data.get("state", "").upper()
    mode = data.get("mode", "").upper()
    listener = current_app.config.get("listener")

    if not listener:
        return jsonify({"error": "Hardware listener not running"}), 500

    if state == "AUTO" or mode == "AUTO":
        listener.set_mode("AUTO")
        return jsonify({"success": True, "mode": "AUTO", "signal": listener.signal_state})

    if state in ("RED", "YELLOW", "GREEN"):
        listener.set_signal(state)
        return jsonify({"success": True, "mode": "MANUAL", "signal": state})

    return jsonify({"error": "Invalid state. Use RED, YELLOW, GREEN, or AUTO."}), 400


@bp.post("/trigger-ir")
def trigger_ir():
    """Simulates a vehicle breaking the IR obstacle beam at the stop line."""
    data = request.get_json(force=True, silent=True) or {}
    vehicle_number = data.get("vehicle_number")
    violation_type = data.get("violation_type", "Red Light Violation")

    listener = current_app.config.get("listener")
    camera = current_app.config.get("camera")

    if camera and hasattr(camera, "trigger_sim_violation"):
        camera.trigger_sim_violation(vehicle_number or "MH15AB1234")

    if not listener:
        return jsonify({"error": "Hardware listener not running"}), 500

    result = listener.trigger_ir(vehicle_number=vehicle_number, violation_type=violation_type)
    return jsonify(result)


@bp.post("/camera-mode")
def set_camera_mode():
    """Toggles camera feed between 'webcam' and 'simulated'."""
    data = request.get_json(force=True, silent=True) or {}
    mode = data.get("mode", "simulated").lower()
    camera = current_app.config.get("camera")

    if not camera:
        return jsonify({"error": "Camera service not running"}), 500

    camera.set_mode(mode)
    return jsonify({"success": True, "camera_mode": camera.mode, "status": camera.status()})


@bp.post("/scenario")
def run_scenario():
    """Runs pre-packaged, viva-ready presentation scenarios."""
    data = request.get_json(force=True, silent=True) or {}
    scenario_id = str(data.get("scenario", "1"))
    listener = current_app.config.get("listener")
    engine = current_app.config.get("engine")
    frames = current_app.config.get("frames", {})

    scenarios = {
        "1": {"type": "Red Light Violation", "vehicle": "MH12DE1432", "desc": "Car jumped signal during active RED"},
        "2": {"type": "No Helmet", "vehicle": "MH14AB9821", "desc": "Two-wheeler rider detected without helmet"},
        "3": {"type": "Triple Riding", "vehicle": "MH15BT4554", "desc": "Motorcycle carrying 3 occupants detected"},
        "4": {"type": "Over Speeding", "vehicle": "DL08CA7721", "desc": "Vehicle speeding at 78 km/h in 50 km/h zone"},
    }

    sc = scenarios.get(scenario_id, scenarios["1"])

    if sc["type"] == "Red Light Violation" and listener:
        listener.set_signal("RED")
        res = listener.trigger_ir(vehicle_number=sc["vehicle"], violation_type=sc["type"])
    else:
        frame = frames.get("latest")
        vid = engine.handle_red_light_trigger(frame, vehicle_number=sc["vehicle"], violation_type=sc["type"])
        res = {"violation": True, "message": f"{sc['type']} recorded for {sc['vehicle']}", "id": vid}

    return jsonify({"success": True, "scenario": sc, "result": res})
