"""Camera input: webcam index | video file | phone IP stream.

VIDEO_SOURCE examples:
  "0"                       -> laptop webcam
  "traffic.mp4"             -> recorded video (test without hardware!)
  "http://192.168.x.x:8080/video" -> phone camera (IP Webcam app)

Reliability notes (laptop webcam focus):
  - open() retries with V4L2 backend on Linux, sets 640x480 for speed
  - read() auto-reopens on failure (USB busy / suspend / unplug)
  - status() exposes state for dashboard badge + /api/camera/status
"""

import time

try:
    import cv2
    _CV2 = True
except Exception:
    cv2 = None
    _CV2 = False


def parse_source(value):
    value = str(value).strip()
    return int(value) if value.isdigit() else value


class VideoSource:
    def __init__(self, source="0", width=640, height=480):
        self.source = parse_source(source)
        self.width = width
        self.height = height
        self.cap = None
        self.available = False
        self.last_error = ""
        self.frames_read = 0
        self.last_frame_time = 0.0
        self._last_open_attempt = 0.0
        if _CV2:
            self._open()

    def _open(self):
        """Try to open the capture device/file. Never raises."""
        now = time.time()
        # throttle re-open attempts to 1 per 3 seconds
        if now - self._last_open_attempt < 3:
            return False
        self._last_open_attempt = now
        try:
            self._release_locked()
            # On Linux prefer V4L2 for webcams (integer sources only)
            if isinstance(self.source, int):
                try:
                    self.cap = cv2.VideoCapture(
                        self.source, cv2.CAP_V4L2)
                except Exception:
                    self.cap = cv2.VideoCapture(self.source)
            else:
                self.cap = cv2.VideoCapture(self.source)
            if self.cap is not None and self.cap.isOpened():
                # modest resolution = faster AI + MJPEG
                try:
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                    # smaller buffer = lower latency live view
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                except Exception:
                    pass
                self.available = True
                self.last_error = ""
                return True
            self.available = False
            self.last_error = (
                f"Cannot open VIDEO_SOURCE={self.source!r}. "
                "Check: webcam plugged? `ls /dev/video*`? "
                "Or set VIDEO_SOURCE=traffic.mp4 in .env")
            return False
        except Exception as e:
            self.available = False
            self.last_error = f"Camera open failed: {e}"
            return False

    def _release_locked(self):
        try:
            if self.cap is not None:
                self.cap.release()
        except Exception:
            pass
        self.cap = None

    def read(self):
        """Returns (ok, frame). Auto-reopens on failure. Never raises."""
        if not _CV2:
            self.last_error = "opencv not installed (pip install opencv-python)"
            return False, None
        if not self.available or self.cap is None:
            self._open()
            if not self.available:
                return False, None
        try:
            ok, frame = self.cap.read()
        except Exception as e:
            self.last_error = f"Camera read error: {e}"
            self.available = False
            return False, None
        if not ok or frame is None:
            # video file ended -> loop it; webcam dropped -> reopen
            if isinstance(self.source, str):
                try:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ok, frame = self.cap.read()
                    if ok and frame is not None:
                        self.frames_read += 1
                        self.last_frame_time = time.time()
                        return True, frame
                except Exception:
                    pass
            self.available = False
            self.last_error = (
                "Camera frame grab failed — retrying. "
                "If webcam: close other apps using it (Meet/Zoom).")
            # try reopen immediately (throttled inside _open)
            self._open()
            return False, None
        self.frames_read += 1
        self.last_frame_time = time.time()
        self.last_error = ""
        return True, frame

    def status(self):
        """JSON-friendly state for /api/camera/status + dashboard badge."""
        return {
            "available": self.available,
            "source": str(self.source),
            "frames_read": self.frames_read,
            "last_error": self.last_error,
            "opencv": _CV2,
        }

    def release(self):
        self._release_locked()
        self.available = False
