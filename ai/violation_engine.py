"""Violation engine: glues signal state + AI + database.

Flow for red-light (the MAIN demo):
  Arduino VIOLATION_TRIGGERED -> grab frame -> detect vehicle ->
  read plate (or UNKNOWN) -> save_evidence -> save_violation()

Flow for AI pass (runs on live frames / video file):
  detect -> triple-riding? -> helmet? -> save each potential violation
  (deduplicated: same type + same vehicle within 60 s is skipped)
"""
import time

from ai.detector import VehicleDetector
from ai.helmet_detector import HelmetDetector
from ai.number_plate import recognize_from_vehicle
from ai.triple_riding import check_triple_riding
from backend import config
from backend.database import log_event, save_violation
from backend.services.evidence import save_evidence

DEDUP_SECONDS = 60


class ViolationEngine:
    def __init__(self):
        self.detector = VehicleDetector()
        self.helmet = HelmetDetector()
        self._recent = {}  # (vehicle, type) -> timestamp, dedup helper

    # ---------- helpers ----------
    def _is_duplicate(self, vehicle, vtype):
        key = (vehicle, vtype)
        now = time.time()
        if key in self._recent and now - self._recent[key] < DEDUP_SECONDS:
            return True
        self._recent[key] = now
        return False

    def _store(self, vehicle, vtype, frame, conf, status="Potential Violation"):
        if self._is_duplicate(vehicle, vtype):
            return None
        img = save_evidence(frame, vtype)
        vid = save_violation(vehicle, vtype, location=config.LOCATION,
                             evidence_image=img, confidence=conf, status=status)
        log_event("violation", f"{vtype} | {vehicle} | id={vid}")
        return vid

    # ---------- MAIN: red-light trigger from Arduino ----------
    def handle_red_light_trigger(self, frame):
        """Called the moment VIOLATION_TRIGGERED arrives."""
        vehicle, conf = config.UNKNOWN_PLATE, 0.0
        if frame is not None:
            dets = self.detector.detect(frame)
            vehicles = [d for d in dets
                        if d["label"] in ("car", "motorcycle", "bus", "truck")]
            if vehicles:
                best = max(vehicles, key=lambda d: d["conf"])
                vehicle, conf, _ = recognize_from_vehicle(frame, best["bbox"])
        status = ("AI-detected event (plate read)" if vehicle != config.UNKNOWN_PLATE
                  else "AI-detected event (plate unclear - requires verification)")
        return self._store(vehicle, "Red Light Violation", frame, conf, status)

    # ---------- AI pass over any frame (video file / live) ----------
    def analyze_frame(self, frame):
        """Detect helmet/triple-riding potentials. Returns list of saved ids."""
        if frame is None:
            return []
        saved = []
        dets = self.detector.detect(frame)
        for item in check_triple_riding(dets):
            if item["is_triple"]:
                vehicle, conf, _ = recognize_from_vehicle(
                    frame, item["motorcycle_bbox"])
                vid = self._store(vehicle, "Triple Riding", frame, conf)
                if vid:
                    saved.append(vid)
        for det in dets:
            if det["label"] != "person":
                continue
            res = self.helmet.check(frame, det["bbox"])
            if res["status"] == "no_helmet" and res.get("verified"):
                vehicle, conf, _ = self._plate_near(frame, dets, det)
                vid = self._store(vehicle, "No Helmet", frame,
                                  round((conf + res["confidence"]) / 2, 2))
                if vid:
                    saved.append(vid)
        return saved

    def _plate_near(self, frame, dets, person):
        bikes = [d for d in dets if d["label"] == "motorcycle"]
        if bikes:
            best = min(bikes, key=lambda b: abs(b["bbox"][0] - person["bbox"][0]))
            return recognize_from_vehicle(frame, best["bbox"])
        return config.UNKNOWN_PLATE, 0.0, None
