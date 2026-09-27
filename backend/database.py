"""SQLite database: vehicles, violations, system_events.

Beginner note: SQLite needs no server - it is just one file
(data/rto.db). sqlite3 is part of Python itself.
"""
import os
import sqlite3
from datetime import datetime

from backend.config import DATABASE_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_number TEXT UNIQUE NOT NULL,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    total_violations INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL REFERENCES vehicles(id),
    violation_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    location TEXT NOT NULL DEFAULT '',
    evidence_image TEXT NOT NULL DEFAULT '',
    evidence_video TEXT NOT NULL DEFAULT '',
    confidence REAL NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'Potential Violation'
);
CREATE TABLE IF NOT EXISTS system_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    message TEXT NOT NULL DEFAULT ''
);
"""


def get_connection(path=DATABASE_PATH):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(path=DATABASE_PATH):
    conn = get_connection(path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def get_or_create_vehicle(conn, vehicle_number):
    """One row per vehicle number - never duplicates (UNIQUE column)."""
    row = conn.execute(
        "SELECT * FROM vehicles WHERE vehicle_number = ?", (vehicle_number,)
    ).fetchone()
    ts = now_iso()
    if row:
        conn.execute(
            "UPDATE vehicles SET last_seen = ?, total_violations = total_violations + 1 "
            "WHERE id = ?",
            (ts, row["id"]),
        )
        return row["id"]
    cur = conn.execute(
        "INSERT INTO vehicles (vehicle_number, first_seen, last_seen, total_violations)"
        " VALUES (?, ?, ?, 1)",
        (vehicle_number, ts, ts),
    )
    return cur.lastrowid


def save_violation(vehicle_number, violation_type, location="",
                   evidence_image="", evidence_video="",
                   confidence=0.0, status="Potential Violation",
                   path=DATABASE_PATH):
    """Save one violation + bump the vehicle's counter. Returns violation id."""
    conn = get_connection(path)
    vehicle_id = get_or_create_vehicle(conn, vehicle_number)
    cur = conn.execute(
        "INSERT INTO violations (vehicle_id, violation_type, timestamp, location,"
        " evidence_image, evidence_video, confidence, status)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (vehicle_id, violation_type, now_iso(), location,
         evidence_image, evidence_video, confidence, status),
    )
    vid = cur.lastrowid
    conn.commit()
    conn.close()
    return vid


def log_event(event_type, message="", path=DATABASE_PATH):
    conn = get_connection(path)
    conn.execute(
        "INSERT INTO system_events (event_type, timestamp, message) VALUES (?, ?, ?)",
        (event_type, now_iso(), message),
    )
    conn.commit()
    conn.close()
