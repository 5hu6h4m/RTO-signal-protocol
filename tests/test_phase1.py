"""Phase-1 self-test: stdlib only (runs BEFORE pip install).

Checks: folders exist, config loads, DB tables create + dedup works,
triple-riding logic is correct, no third-party imports required.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend import config  # noqa: E402
from backend.database import (get_connection, init_db,  # noqa: E402
                              save_violation)

PASS, FAIL = "PASS", "FAIL"
results = []


def check(name, cond):
    results.append((name, PASS if cond else FAIL))


def main():
    for d in ["backend", "ai", "hardware/arduino", "frontend/templates",
              "frontend/static", "evidence/images", "tests"]:
        check(f"dir {d}", os.path.isdir(os.path.join(ROOT, d)))
    for f in ["requirements.txt", ".env.example", "run.py",
              "backend/config.py", "backend/database.py", "backend/app.py",
              "ai/detector.py", "ai/violation_engine.py",
              "hardware/arduino/traffic_signal.ino"]:
        check(f"file {f}", os.path.isfile(os.path.join(ROOT, f)))

    check("config VIDEO_SOURCE present", hasattr(config, "VIDEO_SOURCE"))
    check("config UNKNOWN_PLATE honest",
          config.UNKNOWN_PLATE == "Number Plate Not Clearly Detected")

    # Triple-riding pure logic (no cv2 needed)
    sys.path.insert(0, ROOT)
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "tr", os.path.join(ROOT, "ai", "triple_riding.py"))
    # triple_riding imports ai.detector at module level (ultralytics optional
    # inside detector, so this stays import-safe); skip if it fails.
    try:
        tr = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tr)
        dets = [{"label": "motorcycle", "bbox": [100, 100, 300, 300], "conf": 0.9},
                {"label": "person", "bbox": [120, 120, 160, 300], "conf": 0.9},
                {"label": "person", "bbox": [180, 120, 220, 300], "conf": 0.9},
                {"label": "person", "bbox": [240, 120, 280, 300], "conf": 0.9}]
        r = tr.check_triple_riding(dets)
        check("triple riding detected (3 riders)",
              len(r) == 1 and r[0]["is_triple"] and r[0]["rider_count"] == 3)
    except Exception as e:
        check(f"triple riding logic ({e})", False)

    # DB round-trip in /tmp (never touches real data/rto.db)
    db = "/tmp/rto_phase1_test.db"
    if os.path.exists(db):
        os.remove(db)
    init_db(db)
    v1 = save_violation("MH15AB1234", "No Helmet", path=db)
    v2 = save_violation("MH15AB1234", "Red Light Violation", path=db)
    conn = get_connection(db)
    n = conn.execute("SELECT total_violations FROM vehicles WHERE vehicle_number='MH15AB1234'").fetchone()["total_violations"]
    conn.close()
    check("vehicle dedup (1 row, count=2)", v1 != v2 and n == 2)

    print("\nPhase-1 self-test:")
    failed = 0
    for name, res in results:
        print(f"  [{res}] {name}")
        failed += res == FAIL
    print("ALL PASS" if not failed else f"{failed} FAILURES")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
