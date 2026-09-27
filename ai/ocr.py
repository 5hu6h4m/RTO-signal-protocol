"""OCR for number plates: preprocess -> pytesseract -> cleaned text.

Beginner note: OCR often fails on blurry/angled plates. That is EXPECTED.
On failure we return ("Number Plate Not Clearly Detected", 0.0) - never
a guessed number. A plate is accepted only if it looks like a real
Indian plate (letters+digits, reasonable length).
"""
import re

try:
    import cv2
    _CV2 = True
except Exception:
    cv2 = None
    _CV2 = False

try:
    import pytesseract
    _TESS = True
except Exception:
    _TESS = False

from backend.config import UNKNOWN_PLATE

PLATE_RE = re.compile(r"[A-Z]{2}\d{1,2}[A-Z]{0,3}\d{3,4}")


def preprocess(plate_img):
    """Grayscale -> upscale 2x -> contrast stretch -> adaptive threshold."""
    gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray = cv2.equalizeHist(gray)
    return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY, 31, 10)


def read_plate_text(plate_img):
    """Returns (text, confidence). text is UNKNOWN_PLATE on any failure."""
    if not (_CV2 and _TESS):
        return UNKNOWN_PLATE, 0.0
    try:
        clean = preprocess(plate_img)
        data = pytesseract.image_to_data(
            clean, config="--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
            output_type=pytesseract.Output.DATAFRAME)
        data = data.dropna(subset=["text"])
        raw = "".join(data["text"].astype(str)).upper()
        raw = re.sub(r"[^A-Z0-9]", "", raw)
        match = PLATE_RE.search(raw)
        if not match:
            return UNKNOWN_PLATE, 0.0
        conf = float(data["conf"].replace(-1, 0).mean()) / 100.0
        return match.group(0), round(min(max(conf, 0.0), 1.0), 2)
    except Exception:
        return UNKNOWN_PLATE, 0.0
