"""Admin utility to clean up unwanted test violations and reaction images.

Usage:
  python3 cleanup_records.py --list             # List all current violation records
  python3 cleanup_records.py --delete 20 21 22   # Delete specific IDs and their photos
  python3 cleanup_records.py --clean-orphans    # Delete unreferenced test images in evidence/images/
"""
import argparse
import os
import sqlite3

DB_PATH = "data/rto.db"
EVIDENCE_DIR = "evidence/images"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def list_records():
    conn = get_conn()
    rows = conn.execute(
        "SELECT v.id, vh.vehicle_number, v.violation_type, v.timestamp, v.evidence_image "
        "FROM violations v JOIN vehicles vh ON vh.id = v.vehicle_id ORDER BY v.id DESC"
    ).fetchall()
    conn.close()

    if not rows:
        print("No violation records found in database.")
        return

    print("\n=== Current Violation Records ===")
    print(f"{'ID':<6} | {'Vehicle':<15} | {'Violation':<22} | {'Timestamp':<20} | {'Evidence Path'}")
    print("-" * 90)
    for r in rows:
        img_exists = "[Found]" if os.path.exists(r["evidence_image"]) else "[Missing]"
        print(f"{r['id']:<6} | {r['vehicle_number']:<15} | {r['violation_type']:<22} | {r['timestamp']:<20} | {r['evidence_image']} {img_exists}")
    print("-" * 90)


def delete_records(ids):
    conn = get_conn()
    for vid in ids:
        row = conn.execute("SELECT * FROM violations WHERE id = ?", (vid,)).fetchone()
        if not row:
            print(f"Record #{vid} not found.")
            continue

        vehicle_id = row["vehicle_id"]
        img_path = row["evidence_image"]

        # Delete image file
        if img_path and os.path.exists(img_path):
            try:
                os.remove(img_path)
                print(f"[Deleted File] {img_path}")
            except Exception as e:
                print(f"[Warning] Could not remove {img_path}: {e}")

        # Delete row
        conn.execute("DELETE FROM violations WHERE id = ?", (vid,))
        print(f"[Deleted Record] Violation #{vid} removed from database.")

        # Update vehicle count
        c = conn.execute("SELECT COUNT(*) c FROM violations WHERE vehicle_id = ?", (vehicle_id,)).fetchone()["c"]
        if c == 0:
            conn.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
            print(f"[Cleaned Vehicle] Vehicle ID #{vehicle_id} removed (no violations left).")
        else:
            conn.execute("UPDATE vehicles SET total_violations = ? WHERE id = ?", (c, vehicle_id))

    conn.commit()
    conn.close()
    print("Cleanup completed successfully.")


def clean_orphans():
    conn = get_conn()
    rows = conn.execute("SELECT evidence_image FROM violations WHERE evidence_image != ''").fetchall()
    conn.close()

    active_paths = {os.path.normpath(r["evidence_image"]) for r in rows}
    if not os.path.exists(EVIDENCE_DIR):
        print(f"Directory {EVIDENCE_DIR} does not exist.")
        return

    removed = 0
    for fname in os.listdir(EVIDENCE_DIR):
        full_path = os.path.normpath(os.path.join(EVIDENCE_DIR, fname))
        if full_path not in active_paths:
            try:
                os.remove(full_path)
                print(f"[Removed Orphan Image] {full_path}")
                removed += 1
            except Exception as e:
                print(f"[Error removing] {full_path}: {e}")

    print(f"Cleaned {removed} unreferenced image(s).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean up test evidence images and database records.")
    parser.add_argument("--list", action="store_true", help="List all current violation records")
    parser.add_argument("--delete", nargs="+", type=int, help="Delete one or more violation IDs")
    parser.add_argument("--clean-orphans", action="store_true", help="Delete unreferenced image files in evidence/images")
    args = parser.parse_args()

    if args.delete:
        delete_records(args.delete)
    elif args.clean_orphans:
        clean_orphans()
    else:
        list_records()
