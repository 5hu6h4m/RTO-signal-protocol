"""Number-plate pipeline: vehicle box -> plate candidate -> OCR text.

College-simple approach (no LP-detector model required):
1. Take the lower half of the vehicle box (plates live there).
2. Find rectangular contours; keep the most plate-like one.
3. OCR it via ai/ocr.py. If anything fails -> UNKNOWN_PLATE.

If you later get a dedicated LP model (models/lp.pt), drop it in and
set USE_LP_MODEL=1 behaviour by editing _find_plate_contour() - the
function signature stays the same.
"""
try:
    import cv2
    _CV2 = True
except Exception:
    cv2 = None
    _CV2 = False

from ai.ocr import read_plate_text
from backend.config import UNKNOWN_PLATE


def _find_plate_contour(region):
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    best, best_score = None, 0
    area = region.shape[0] * region.shape[1]
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if h == 0:
            continue
        aspect = w / h
        fill = (w * h) / max(area, 1)
        # Plates are wide rectangles covering a small part of the region
        if 2.0 < aspect < 6.0 and 0.01 < fill < 0.5:
            if w * h > best_score:
                best, best_score = (x, y, w, h), w * h
    return best


def recognize_from_vehicle(frame, vehicle_bbox):
    """Returns (plate_text, confidence, plate_crop_or_None)."""
    if not _CV2:
        return UNKNOWN_PLATE, 0.0, None
    x1, y1, x2, y2 = vehicle_bbox
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
    vehicle = frame[y1:y2, x1:x2]
    if vehicle.size == 0:
        return UNKNOWN_PLATE, 0.0, None
    lower = vehicle[vehicle.shape[0] // 2:, :]  # plates live low
    found = _find_plate_contour(lower)
    crop = lower[found[1]:found[1] + found[3], found[0]:found[0] + found[2]] \
        if found else lower
    text, conf = read_plate_text(crop)
    return text, conf, crop
