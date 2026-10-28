"""Camera input: webcam index | video file | smart simulated CCTV feed.

Supports dual modes:
1. Physical Webcam / Video file / IP stream when available.
2. High-Tech Simulated Traffic Junction CCTV Feed (for presentations):
   - Smoothly animated vehicles approaching and crossing the stop line.
   - Synchronized with traffic signal (stops on RED, proceeds on GREEN).
   - Real-time AI bounding box detection overlays with confidence metrics.
   - Realistic CCTV telemetry overlay with live clock and frame counter.
"""
import math
import time
from datetime import datetime

try:
    import cv2
    import numpy as np
    _CV2 = True
except Exception:
    cv2 = None
    np = None
    _CV2 = False


def parse_source(value):
    value = str(value).strip()
    return int(value) if value.isdigit() else value


class VideoSource:
    def __init__(self, source="0", width=640, height=480):
        self.raw_source = source
        self.source = parse_source(source)
        self.width = width
        self.height = height
        self.cap = None
        self.available = False
        self.mode = "auto"  # "auto", "webcam", "simulated"
        self.last_error = ""
        self.frames_read = 0
        self.last_frame_time = 0.0
        self._last_open_attempt = 0.0

        # Simulation state
        self._sim_tick = 0
        self._vehicles = [
            {"id": "V1", "type": "car", "color": (210, 210, 215), "plate": "MH12DE1432",
             "lane": 0, "y": 80.0, "speed": 2.2, "target_y": 80.0, "violator": False},
            {"id": "V2", "type": "bike", "color": (40, 50, 190), "plate": "MH14AB9821",
             "lane": 1, "y": -40.0, "speed": 2.8, "target_y": -40.0, "violator": False},
            {"id": "V3", "type": "car", "color": (180, 110, 40), "plate": "MH15AB1234",
             "lane": 0, "y": -180.0, "speed": 2.0, "target_y": -180.0, "violator": False},
        ]
        self._force_violation_vehicle = None

        if _CV2:
            self._open()

    def _open(self):
        """Try to open the capture device/file. Never raises."""
        if str(self.raw_source).lower() == "simulated":
            self.mode = "simulated"
            self.available = True
            self.last_error = ""
            return True

        now = time.time()
        if now - self._last_open_attempt < 3:
            return False
        self._last_open_attempt = now
        try:
            self._release_locked()
            if isinstance(self.source, int):
                try:
                    self.cap = cv2.VideoCapture(self.source, cv2.CAP_V4L2)
                except Exception:
                    self.cap = cv2.VideoCapture(self.source)
            else:
                self.cap = cv2.VideoCapture(self.source)

            if self.cap is not None and self.cap.isOpened():
                try:
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                except Exception:
                    pass
                self.available = True
                self.last_error = ""
                return True
            self.available = False
            self.last_error = f"Cannot open VIDEO_SOURCE={self.source!r}."
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

    def set_mode(self, mode):
        """Switch between 'auto', 'webcam', and 'simulated'."""
        self.mode = mode.lower()
        if self.mode == "webcam" and not self.available:
            self._open()

    def trigger_sim_violation(self, vehicle_number="MH15AB1234"):
        """Orders a simulated vehicle to cross the stop line during RED."""
        for v in self._vehicles:
            if v["y"] < 250:
                v["violator"] = True
                v["plate"] = vehicle_number
                return True
        return False

    def read(self, signal_state="GREEN", countdown=8):
        """Returns (ok, frame). Falls back to simulated CCTV if webcam is off or mode is simulated."""
        if not _CV2 or np is None:
            return False, None

        # 1. Try real webcam if requested and available
        if self.mode == "webcam" or (self.mode == "auto" and self.available):
            if self.cap is None or not self.available:
                self._open()
            if self.available and self.cap is not None:
                try:
                    ok, frame = self.cap.read()
                    if ok and frame is not None:
                        self.frames_read += 1
                        self.last_frame_time = time.time()
                        return True, frame
                except Exception:
                    pass

        # 2. Simulated CCTV frame generator
        frame = self._render_simulated_frame(signal_state, countdown)
        self.frames_read += 1
        self.last_frame_time = time.time()
        return True, frame

    def _render_simulated_frame(self, signal_state="GREEN", countdown=8):
        """Draws a live animated smart junction surveillance frame."""
        w, h = self.width, self.height
        img = np.zeros((h, w, 3), dtype=np.uint8)
        self._sim_tick += 1

        # Asphalt roadway
        img[0:130, :] = [30, 26, 22]  # Distant background
        img[130:h, :] = [48, 48, 48]  # Road surface

        # Curbs with diagonal safety stripes
        for y in range(130, h):
            curb_col = [25, 175, 225] if ((y + self._sim_tick // 4) // 18) % 2 == 0 else [30, 30, 30]
            img[y, 40:52] = curb_col
            img[y, w - 52:w - 40] = curb_col

        # Lane markings
        lane_x1 = 60 + (w - 120) // 3
        lane_x2 = 60 + 2 * (w - 120) // 3
        for y in range(230, h, 35):
            cv2.line(img, (lane_x1, y), (lane_x1, min(h, y + 20)), (210, 210, 210), 2)
            cv2.line(img, (lane_x2, y), (lane_x2, min(h, y + 20)), (210, 210, 210), 2)

        # Stop Line & Pedestrian Crosswalk
        stop_line_y = 220
        # Zebra stripes
        for zx in range(65, w - 65, 38):
            cv2.rectangle(img, (zx, stop_line_y - 28), (zx + 22, stop_line_y - 8), (170, 170, 170), -1)
        # Solid white stop line
        cv2.line(img, (52, stop_line_y), (w - 52, stop_line_y), (250, 250, 250), 5)
        cv2.putText(img, "STOP LINE", (65, stop_line_y - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

        # Virtual Signal Head graphic
        sig_x, sig_y = 70, 70
        cv2.rectangle(img, (sig_x - 14, sig_y), (sig_x + 14, sig_y + 80), (15, 15, 15), -1)
        cv2.rectangle(img, (sig_x - 14, sig_y), (sig_x + 14, sig_y + 80), (90, 90, 90), 1)

        # Red Lamp
        if signal_state == "RED":
            cv2.circle(img, (sig_x, sig_y + 16), 9, (20, 20, 255), -1)
            cv2.circle(img, (sig_x, sig_y + 16), 16, (40, 40, 255), 1)
        else:
            cv2.circle(img, (sig_x, sig_y + 16), 7, (20, 20, 70), -1)

        # Yellow Lamp
        if signal_state == "YELLOW":
            cv2.circle(img, (sig_x, sig_y + 40), 9, (10, 200, 240), -1)
            cv2.circle(img, (sig_x, sig_y + 40), 16, (30, 160, 220), 1)
        else:
            cv2.circle(img, (sig_x, sig_y + 40), 7, (15, 60, 70), -1)

        # Green Lamp
        if signal_state == "GREEN":
            cv2.circle(img, (sig_x, sig_y + 64), 9, (40, 240, 60), -1)
            cv2.circle(img, (sig_x, sig_y + 64), 16, (40, 200, 60), 1)
        else:
            cv2.circle(img, (sig_x, sig_y + 64), 7, (15, 60, 20), -1)

        # Update and render simulated vehicles
        lane_centers = [120, 260, 400]
        stop_threshold = stop_line_y - 65

        for v in self._vehicles:
            is_red = (signal_state == "RED")
            # Movement logic
            if is_red and not v["violator"]:
                # Decelerate before stop line
                if v["y"] < stop_threshold:
                    dist = stop_threshold - v["y"]
                    v["y"] += min(v["speed"], max(0.2, dist * 0.08))
            else:
                # Accelerate forward
                v["y"] += v["speed"]

            # Loop back when exiting bottom
            if v["y"] > h + 40:
                v["y"] = -120.0
                v["violator"] = False
                v["speed"] = 2.0 + (self._sim_tick % 3) * 0.4

            vx = lane_centers[v["lane"]]
            vy = int(v["y"])

            # Render vehicle
            if v["type"] == "car":
                # Shadow
                cv2.ellipse(img, (vx + 45, vy + 55), (42, 10), 0, 0, 360, (20, 20, 20), -1)
                # Car chassis
                cv2.rectangle(img, (vx, vy), (vx + 90, vy + 55), v["color"], -1)
                cv2.rectangle(img, (vx + 15, vy + 12), (vx + 75, vy + 42), (50, 45, 40), -1)
                # Headlights
                cv2.rectangle(img, (vx + 4, vy + 50), (vx + 18, vy + 54), (200, 240, 255), -1)
                cv2.rectangle(img, (vx + 72, vy + 50), (vx + 86, vy + 54), (200, 240, 255), -1)

                bx1, by1, bx2, by2 = vx - 4, vy - 4, vx + 94, vy + 58
                label = f"CAR 95% | {v['plate']}"
            else:
                # Motorcycle
                cv2.ellipse(img, (vx + 18, vy + 45), (18, 6), 0, 0, 360, (20, 20, 20), -1)
                cv2.line(img, (vx + 18, vy), (vx + 18, vy + 42), v["color"], 6)
                # Rider
                cv2.circle(img, (vx + 18, vy + 14), 8, (60, 60, 60), -1)
                cv2.rectangle(img, (vx + 10, vy + 20), (vx + 26, vy + 36), (40, 110, 180), -1)

                bx1, by1, bx2, by2 = vx - 2, vy - 2, vx + 38, vy + 46
                label = f"BIKE 92% | {v['plate']}"

            # If vehicle is violating stop line during RED, highlight in Red Bounding Box!
            is_violating = (is_red and vy > stop_threshold)
            box_col = (40, 40, 255) if is_violating else (40, 220, 70)

            # Draw AI bounding box
            cv2.rectangle(img, (bx1, by1), (bx2, by2), box_col, 2)
            cv2.rectangle(img, (bx1, by1 - 18), (bx1 + 160, by1), box_col, -1)
            tag = "[VIOLATION]" if is_violating else label
            cv2.putText(img, tag, (bx1 + 4, by1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)

        # 4. CCTV HUD Overlay
        now_str = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        # Top banner
        cv2.rectangle(img, (0, 0), (w, 32), (12, 12, 12), -1)
        cv2.line(img, (0, 32), (w, 32), (60, 60, 60), 1)

        # REC Dot & Camera name
        dot_color = (0, 0, 255) if (self._sim_tick // 15) % 2 == 0 else (0, 180, 0)
        cv2.circle(img, (18, 16), 5, dot_color, -1)
        cv2.putText(img, "SMART RTO AI SURVEILLANCE  [CAM-04 JUNCTION]", (30, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (240, 240, 240), 1)

        # Clock & Telemetry
        cv2.putText(img, now_str, (w - 180, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 230, 255), 1)

        # Signal state badge on bottom right
        badge_col = (30, 30, 220) if signal_state == "RED" else (
            (10, 180, 220) if signal_state == "YELLOW" else (30, 190, 50))
        cv2.rectangle(img, (w - 170, h - 30), (w - 10, h - 8), (20, 20, 20), -1)
        cv2.rectangle(img, (w - 170, h - 30), (w - 10, h - 8), badge_col, 1)
        cv2.putText(img, f"SIGNAL: {signal_state} ({countdown:02d}s)", (w - 162, h - 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, badge_col, 1)

        # IR Sensor Status badge on bottom left
        cv2.putText(img, "IR BEAM: ARMED [READY]", (16, h - 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.36, (140, 220, 140), 1)

        return img

    def status(self):
        """JSON-friendly state for /api/camera/status + dashboard badge."""
        return {
            "available": True,
            "mode": self.mode,
            "hardware_webcam": self.available,
            "source": "Simulated Smart Junction" if self.mode == "simulated" or not self.available else str(self.source),
            "frames_read": self.frames_read,
            "last_error": "",
            "opencv": _CV2,
        }

    def release(self):
        self._release_locked()
        self.available = False
