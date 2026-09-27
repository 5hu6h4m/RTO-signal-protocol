"""Vehicle/person detector using pre-trained YOLO (Ultralytics).

Beginner note: we do NOT train anything. YOLOv8n already knows
person/car/motorcycle/bus/truck (COCO classes). First run downloads
the ~6 MB yolov8n.pt weights automatically.

If ultralytics/OpenCV is not installed, detection degrades to an
explicitly-labelled empty result - never fake boxes.
"""
try:
    from ultralytics import YOLO
    _YOLO_AVAILABLE = True
except Exception:
    YOLO = None
    _YOLO_AVAILABLE = False

WANTED = {"person", "car", "motorcycle", "bus", "truck"}


class VehicleDetector:
    def __init__(self, model_name="yolov8n.pt"):
        self.model_name = model_name
        self.model = None
        self.demo_fallback = False
        if _YOLO_AVAILABLE:
            try:
                self.model = YOLO(model_name)  # downloads on first run
            except Exception:
                self.model = None
                self.demo_fallback = True
        else:
            self.demo_fallback = True

    def detect(self, frame):
        """Return list of {label, bbox[x1,y1,x2,y2], conf} for wanted classes."""
        if self.model is None:
            return []  # honest empty: no model, no claims
        results = self.model(frame, verbose=False)[0]
        out = []
        for box in results.boxes:
            label = results.names[int(box.cls[0])]
            if label not in WANTED:
                continue
            x1, y1, x2, y2 = (int(v) for v in box.xyxy[0].tolist())
            out.append({"label": label,
                        "bbox": [x1, y1, x2, y2],
                        "conf": float(box.conf[0])})
        return out
