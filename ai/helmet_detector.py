"""No-helmet detection interface (honest college version).

IMPORTANT (say this in viva): standard COCO YOLO has NO 'helmet'
class, so plain yolov8n cannot detect helmets. This module therefore:

1. Accepts an optional helmet-capable model at models/helmet.pt
   (any Ultralytics model trained with helmet/no-helmet classes).
   If present, it is used for real.
2. Otherwise returns status 'uncertain' - the UI shows
   "Potential No Helmet Violation (unverified)".
3. DEMO_MODE simulation is explicitly labelled as simulated.

Plug-in contract: helmet.pt must output class names containing
'helmet' and/or 'no_helmet' (case-insensitive).
"""
import os

try:
    from ultralytics import YOLO
    _YOLO_AVAILABLE = True
except Exception:
    YOLO = None
    _YOLO_AVAILABLE = False

HELMET_MODEL_PATH = "models/helmet.pt"


class HelmetDetector:
    def __init__(self, model_path=HELMET_MODEL_PATH):
        self.model = None
        if _YOLO_AVAILABLE and os.path.exists(model_path):
            try:
                self.model = YOLO(model_path)
            except Exception:
                self.model = None

    @property
    def has_real_model(self):
        return self.model is not None

    def check(self, frame, person_bbox):
        """Return dict(status, confidence, verified).

        status: 'helmet' | 'no_helmet' | 'uncertain'
        verified is True only when a real helmet model decided.
        """
        if self.model is not None:
            x1, y1, x2, y2 = person_bbox
            h, w = frame.shape[:2]
            # Head region = top third of the person box (simple, explainable)
            head = frame[max(0, y1):min(h, y1 + (y2 - y1) // 3),
                         max(0, x1):min(w, x2)]
            if head.size == 0:
                return {"status": "uncertain", "confidence": 0.0, "verified": False}
            res = self.model(head, verbose=False)[0]
            best, best_conf = "uncertain", 0.0
            for box in res.boxes:
                name = res.names[int(box.cls[0])].lower()
                conf = float(box.conf[0])
                if "no_helmet" in name or ("no" in name and "helmet" in name):
                    if conf > best_conf:
                        best, best_conf = "no_helmet", conf
                elif "helmet" in name:
                    if conf > best_conf:
                        best, best_conf = "helmet", conf
            return {"status": best, "confidence": best_conf, "verified": True}
        return {"status": "uncertain", "confidence": 0.0, "verified": False,
                "note": "No helmet model installed; standard YOLO cannot detect helmets."}
