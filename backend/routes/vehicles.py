"""GET /api/vehicles/<number> -> vehicle + full violation history + Vahan 4.0 registry.
"""
from flask import Blueprint, jsonify

from backend.database import get_connection
from backend.services.vahan import lookup_vahan, MVA_OFFENSES

bp = Blueprint("vehicles", __name__)


@bp.get("/<vehicle_number>")
def vehicle_history(vehicle_number):
    clean = vehicle_number.strip().upper().replace(" ", "").replace("-", "")
    conn = get_connection()
    vehicle = conn.execute(
        "SELECT * FROM vehicles WHERE vehicle_number = ?", (clean,)
    ).fetchone()

    vahan = lookup_vahan(clean)

    if not vehicle:
        conn.close()
        return jsonify({
            "vehicle_number": clean,
            "total_violations": 0,
            "total_fine_amount": 0,
            "unpaid_fines": 0,
            "vahan": vahan,
            "violations": []
        })

    violations = [dict(r) for r in conn.execute(
        "SELECT * FROM violations WHERE vehicle_id = ? ORDER BY id DESC",
        (vehicle["id"],)).fetchall()]
    conn.close()

    total_fines = 0
    unpaid_fines = 0
    for v in violations:
        vtype = v.get("violation_type", "Other")
        cost = MVA_OFFENSES.get(vtype, {}).get("fine", 500)
        v["fine_amount"] = cost
        total_fines += cost
        if "paid" not in (v.get("status") or "").lower():
            unpaid_fines += cost

    return jsonify({
        "vehicle_number": vehicle["vehicle_number"],
        "total_violations": vehicle["total_violations"],
        "total_fine_amount": total_fines,
        "unpaid_fines": unpaid_fines,
        "first_seen": vehicle["first_seen"],
        "last_seen": vehicle["last_seen"],
        "vahan": vahan,
        "violations": violations
    })
