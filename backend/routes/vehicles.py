"""GET /api/vehicles/<number> -> vehicle + full violation history.

Demo: /api/vehicles/MH15AB1234 shows Total + list (No Helmet,
Red Light Violation, Triple Riding) once demo data exists.
"""
from flask import Blueprint, jsonify

from backend.database import get_connection

bp = Blueprint("vehicles", __name__)


@bp.get("/<vehicle_number>")
def vehicle_history(vehicle_number):
    conn = get_connection()
    vehicle = conn.execute(
        "SELECT * FROM vehicles WHERE vehicle_number = ?", (vehicle_number,)
    ).fetchone()
    if not vehicle:
        conn.close()
        return jsonify({"vehicle_number": vehicle_number,
                        "total_violations": 0, "violations": []})
    violations = [dict(r) for r in conn.execute(
        "SELECT * FROM violations WHERE vehicle_id = ? ORDER BY id DESC",
        (vehicle["id"],)).fetchall()]
    conn.close()
    return jsonify({"vehicle_number": vehicle["vehicle_number"],
                    "total_violations": vehicle["total_violations"],
                    "first_seen": vehicle["first_seen"],
                    "last_seen": vehicle["last_seen"],
                    "violations": violations})
