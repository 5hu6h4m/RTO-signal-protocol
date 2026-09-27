"""Triple-riding check: >2 people on one motorcycle = potential violation.

College-simple method: a person belongs to a motorcycle if the
person box overlaps it (bottom-center of person inside expanded bike box).
"""
from ai.detector import VehicleDetector  # noqa: F401  (keeps ai package coherent)


def _center_in(box, outer):
    x1, y1, x2, y2 = box
    ox1, oy1, ox2, oy2 = outer
    cx, cy = (x1 + x2) / 2, y2  # bottom-center of person
    return ox1 <= cx <= ox2 and oy1 <= cy <= oy2


def check_triple_riding(detections):
    """detections: list from VehicleDetector.detect().

    Returns list of {motorcycle_bbox, rider_count, is_triple}.
    """
    bikes = [d for d in detections if d["label"] == "motorcycle"]
    people = [d for d in detections if d["label"] == "person"]
    out = []
    for bike in detections:
        if bike["label"] != "motorcycle":
            continue
        x1, y1, x2, y2 = bike["bbox"]
        pad = 20  # small tolerance so near-touching riders count
        expanded = [x1 - pad, y1 - pad, x2 + pad, y2 + pad]
        riders = sum(1 for p in people if _center_in(p["bbox"], expanded))
        out.append({"motorcycle_bbox": bike["bbox"],
                    "rider_count": riders,
                    "is_triple": riders > 2})
    return out
