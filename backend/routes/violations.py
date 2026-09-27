"""GET /api/violations  (filters: ?type= &date=YYYY-MM-DD &limit=)
POST /api/violations (manual/demo insert, clearly labelled)"""
from flask import Blueprint, jsonify, request

from backend import config
from backend.database import get_connection, log_event, save_violation

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


@bp.post("")
def create_violation():
    data = request.get_json(force=True)
    vid = save_violation(
        data.get("vehicle_number", config.UNKNOWN_PLATE),
        data.get("violation_type", "Other"),
        location=data.get("location", config.LOCATION),
        evidence_image=data.get("evidence_image", ""),
        confidence=float(data.get("confidence", 0.0)),
        status=data.get("status", "Potential Violation (manual entry)"))
    log_event("manual_entry", f"id={vid} {data}")
    return jsonify({"id": vid}), 201
