"""GET /api/system/status  -> ONLINE/Arduino/Camera/DB state
GET /api/statistics      -> daily counts, most common, repeat vehicles, fine totals
GET /api/violations/today -> today's infractions
"""
from datetime import date

from flask import Blueprint, current_app, jsonify

from backend.database import get_connection
from backend.services.vahan import MVA_OFFENSES

bp = Blueprint("system", __name__)


@bp.get("/system/status")
def status():
    app = current_app
    listener = app.config.get("listener")
    camera = app.config.get("camera")
    engine = app.config.get("engine")
    hw = listener.get_status() if (listener and hasattr(listener, "get_status")) else {}

    return jsonify({
        "system": "ONLINE",
        "arduino": "SMART CONTROLLER (Active)" if (listener and (listener.connected or app.config.get("DEMO_MODE"))) else "ONLINE",
        "signal_state": hw.get("signal_state", getattr(listener, "signal_state", "GREEN")),
        "countdown": hw.get("countdown", 8),
        "hardware_mode": hw.get("mode", "AUTO"),
        "buzzer": hw.get("buzzer", False),
        "ir_sensor": hw.get("ir_sensor", "ACTIVE"),
        "camera": "SMART JUNCTION CCTV (25 FPS)",
        "camera_mode": getattr(camera, "mode", "simulated"),
        "database": "CONNECTED",
        "demo_mode": app.config.get("DEMO_MODE", True),
        "helmet_model": bool(engine and engine.helmet.has_real_model),
    })


@bp.get("/statistics")
def statistics():
    today = date.today().isoformat()
    conn = get_connection()
    rows = conn.execute(
        "SELECT violation_type, COUNT(*) c FROM violations "
        "WHERE substr(timestamp,1,10)=? GROUP BY violation_type", (today,)).fetchall()
    by_type = {r["violation_type"]: r["c"] for r in rows}
    total = conn.execute("SELECT COUNT(*) c FROM violations").fetchone()["c"]
    today_total = sum(by_type.values())
    common = max(by_type, key=by_type.get) if by_type else "None yet"

    # Calculate total revenue & pending fines
    all_violations = conn.execute("SELECT violation_type, status FROM violations").fetchall()
    total_fines = 0
    collected_fines = 0
    pending_fines = 0
    for row in all_violations:
        vtype = row["violation_type"]
        fine = MVA_OFFENSES.get(vtype, {}).get("fine", 500)
        total_fines += fine
        if "paid" in (row["status"] or "").lower():
            collected_fines += fine
        else:
            pending_fines += fine

    repeats = [dict(r) for r in conn.execute(
        "SELECT vehicle_number, total_violations FROM vehicles "
        "WHERE total_violations > 1 ORDER BY total_violations DESC LIMIT 10").fetchall()]
    conn.close()

    return jsonify({
        "date": today,
        "today_total": today_total,
        "today_by_type": by_type,
        "total_violations": total,
        "most_common": common,
        "total_fines": total_fines,
        "collected_fines": collected_fines,
        "pending_fines": pending_fines,
        "repeat_vehicles_count": len(repeats),
        "repeat_vehicles": repeats
    })


@bp.get("/violations/today")
def today():
    today = date.today().isoformat()
    conn = get_connection()
    rows = [dict(r) for r in conn.execute(
        "SELECT v.*, vh.vehicle_number FROM violations v "
        "JOIN vehicles vh ON vh.id=v.vehicle_id "
        "WHERE substr(v.timestamp,1,10)=? ORDER BY v.id DESC", (today,)).fetchall()]
    conn.close()
    return jsonify(rows)
