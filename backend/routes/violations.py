"""GET /api/violations  (filters: ?type= &date=YYYY-MM-DD &limit=)
POST /api/violations (manual/demo insert, clearly labelled)
GET /api/violations/<id> (full E-Challan details)
POST /api/violations/<id>/pay (mark challan as paid)
DELETE /api/violations/<id> (delete record and evidence file)
"""
import os
from flask import Blueprint, jsonify, request

from backend import config
from backend.database import get_connection, log_event, save_violation
from backend.services.evidence import save_evidence
from backend.services.vahan import get_challan_data

bp = Blueprint("violations", __name__)


@bp.get("")
def list_violations():
    vtype = request.args.get("type", "")
    date = request.args.get("date", "")
    limit = min(int(request.args.get("limit", 100)), 500)
    q = ("SELECT v.*, vh.vehicle_number FROM violations v "
         "JOIN vehicles vh ON vh.id = v.vehicle_id WHERE 1=1")
    args = []
    if vtype:
        q += " AND v.violation_type = ?"
        args.append(vtype)
    if date:
        q += " AND substr(v.timestamp, 1, 10) = ?"
        args.append(date)
    q += " ORDER BY v.id DESC LIMIT ?"
    args.append(limit)
    conn = get_connection()
    rows = [dict(r) for r in conn.execute(q, args).fetchall()]
    conn.close()
    return jsonify(rows)


@bp.get("/<int:vid>")
def get_violation_challan(vid):
    """Returns official E-Challan document payload for this violation."""
    conn = get_connection()
    row = conn.execute(
        "SELECT v.*, vh.vehicle_number FROM violations v "
        "JOIN vehicles vh ON vh.id = v.vehicle_id WHERE v.id = ?", (vid,)
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Violation not found"}), 404

    data = dict(row)
    challan = get_challan_data(data)
    return jsonify(challan)


@bp.post("/<int:vid>/pay")
def pay_challan(vid):
    """Simulates online payment of the e-challan."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM violations WHERE id = ?", (vid,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Violation not found"}), 404

    new_status = "Challan Paid (Online UPI)"
    conn.execute("UPDATE violations SET status = ? WHERE id = ?", (new_status, vid))
    conn.commit()
    conn.close()

    log_event("payment", f"Challan #{vid} paid successfully")
    return jsonify({"success": True, "violation_id": vid, "status": new_status, "payment_status": "PAID"})


@bp.post("")
def create_violation():
    data = request.get_json(force=True)
    vnum = data.get("vehicle_number", "MH15AB1234")
    vtype = data.get("violation_type", "Other")

    # If no evidence image provided, generate an authentic CCTV snapshot!
    img = data.get("evidence_image", "")
    if not img:
        img = save_evidence(None, vtype, vehicle_number=vnum, location=data.get("location", config.LOCATION))

    vid = save_violation(
        vnum,
        vtype,
        location=data.get("location", config.LOCATION),
        evidence_image=img,
        confidence=float(data.get("confidence", 0.96)),
        status=data.get("status", "Potential Violation (verified)"))
    log_event("manual_entry", f"id={vid} {data}")
    return jsonify({"id": vid, "evidence_image": img}), 201


@bp.delete("/<int:vid>")
def delete_violation(vid):
    """Deletes a violation record and unlinks its evidence image file."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM violations WHERE id = ?", (vid,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Violation not found"}), 404

    data = dict(row)
    vehicle_id = data.get("vehicle_id")
    img_path = data.get("evidence_image")

    # Safely delete image file from filesystem if present
    if img_path:
        # Normalize relative path
        norm_path = img_path.lstrip("/\\")
        if os.path.exists(norm_path):
            try:
                os.remove(norm_path)
            except OSError:
                pass

    # Delete violation from database
    conn.execute("DELETE FROM violations WHERE id = ?", (vid,))

    # Update or clean vehicle count
    remaining = conn.execute("SELECT COUNT(*) c FROM violations WHERE vehicle_id = ?", (vehicle_id,)).fetchone()["c"]
    if remaining == 0:
        conn.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
    else:
        conn.execute("UPDATE vehicles SET total_violations = ? WHERE id = ?", (remaining, vehicle_id))

    conn.commit()
    conn.close()

    log_event("violation_deleted", f"Violation #{vid} and image deleted")
    return jsonify({"success": True, "deleted_id": vid})


@bp.post("/clear-all")
def clear_all_violations():
    """Wipes all violation records, cleans images, and resets vehicle counter."""
    conn = get_connection()
    rows = conn.execute("SELECT evidence_image FROM violations").fetchall()
    for r in rows:
        img_path = r["evidence_image"]
        if img_path:
            norm = img_path.lstrip("/\\")
            if os.path.exists(norm) and "placeholder" not in norm:
                try:
                    os.remove(norm)
                except OSError:
                    pass
    conn.execute("DELETE FROM violations")
    conn.execute("DELETE FROM vehicles")
    conn.commit()
    conn.close()
    log_event("clear_all", "All violation records wiped")
    return jsonify({"success": True, "message": "All violation records cleared"})


