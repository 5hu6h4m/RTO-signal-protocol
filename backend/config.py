"""Central configuration. Reads .env (if present) + environment variables.

Beginner note: this file uses ONLY the standard library so the
environment self-test can run even before `pip install`.
"""
import os


def _load_dotenv(path=".env"):
    """Tiny .env loader (avoids needing python-dotenv just for config)."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()


def _as_int(name, default):
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


ARDUINO_PORT = os.getenv("ARDUINO_PORT", "/dev/ttyACM0")
ARDUINO_BAUD = _as_int("ARDUINO_BAUD", 9600)
VIDEO_SOURCE = os.getenv("VIDEO_SOURCE", "0")  # "0" -> webcam 0
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/rto.db")
EVIDENCE_DIR = os.getenv("EVIDENCE_DIR", "evidence/images")
FLASK_PORT = _as_int("FLASK_PORT", 5000)
LOCATION = os.getenv("LOCATION", "College Demo Junction")
DEMO_MODE = os.getenv("DEMO_MODE", "1") == "1"

UNKNOWN_PLATE = "Number Plate Not Clearly Detected"
