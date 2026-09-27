"""Evidence capture: save a frame ONLY when a violation occurs.

We never record continuously - one JPEG per violation keeps the
college laptop's disk happy and makes the viva explanation trivial.
"""
import os
from datetime import datetime

try:
    import cv2
    _CV2 = True
except Exception:
    cv2 = None
    _CV2 = False

from backend.config import EVIDENCE_DIR


def save_evidence(frame, violation_type, out_dir=EVIDENCE_DIR):
    """Draw nothing, just stamp filename. Returns saved path (or '')."""
    if not _CV2 or frame is None:
        return ""
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = "".join(c if c.isalnum() else "_" for c in violation_type)
    path = os.path.join(out_dir, f"{safe}_{stamp}.jpg")
    cv2.imwrite(path, frame)
    return path
