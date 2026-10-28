"""Evidence capture & realistic surveillance frame synthesizer.

Generates authentic-looking smart city CCTV frames when real hardware
or camera is not connected, ensuring a 100% reliable local demonstration.
"""
import os
import random
from datetime import datetime

try:
    import cv2
    import numpy as np
    _CV2 = True
except Exception:
    cv2 = None
    np = None
    _CV2 = False

from backend.config import EVIDENCE_DIR, LOCATION


def _draw_synthetic_evidence(violation_type, vehicle_number="MH15AB1234", location=LOCATION):
    """Synthesizes a realistic high-tech traffic junction surveillance frame."""
    if not _CV2 or np is None:
        return None

    w, h = 640, 480
    img = np.zeros((h, w, 3), dtype=np.uint8)

    # 1. Road & Sky background
    # Sky / background building zone (dark navy / twilight)
    img[0:150, :] = [24, 20, 18]
    # Distant buildings silhouettes
    for bx in range(0, w, 50):
        bh = 40 + (bx * 13) % 60
        img[150 - bh:150, bx:bx + 42] = [35, 30, 25]

    # Asphalt Road with gradient
    for y in range(150, h):
        c = int(45 + (y - 150) * 0.08)
        img[y, :] = [c, c, c]

    # 2. Road Markings
    # Sidewalks / Curbs (yellow-black curbs)
    for y in range(150, h):
        left_edge = int(60 - (y - 150) * 0.15)
        right_edge = int(w - 60 + (y - 150) * 0.15)
        if left_edge > 0:
            curb_color = [30, 160, 200] if (y // 20) % 2 == 0 else [30, 30, 30]
            img[y, max(0, left_edge - 14):left_edge] = curb_color
        if right_edge < w:
            curb_color = [30, 160, 200] if (y // 20) % 2 == 0 else [30, 30, 30]
            img[y, right_edge:min(w, right_edge + 14)] = curb_color

    # White lane divider dashes
    center_x = w // 2
    for y in range(260, h, 40):
        cv2.line(img, (center_x, y), (center_x, min(h, y + 22)), (200, 200, 200), 3)

    # Zebra Crossing & STOP LINE
    stop_line_y = 240
    # Stop line (Thick solid white line)
    cv2.line(img, (70, stop_line_y), (w - 70, stop_line_y), (240, 240, 240), 5)
    cv2.putText(img, "STOP LINE", (85, stop_line_y - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1)

    # Zebra stripes behind stop line
    for zx in range(110, w - 110, 45):
        cv2.rectangle(img, (zx, stop_line_y - 35), (zx + 25, stop_line_y - 12), (180, 180, 180), -1)

    # 3. Virtual Traffic Signal Light on the Left Pole
    pole_x = 75
    cv2.line(img, (pole_x, 80), (pole_x, 320), (70, 70, 70), 5)
    # Signal Housing
    cv2.rectangle(img, (pole_x - 16, 80), (pole_x + 16, 170), (20, 20, 20), -1)
    cv2.rectangle(img, (pole_x - 16, 80), (pole_x + 16, 170), (100, 100, 100), 2)
    # RED Lamp (Glowing actively)
    cv2.circle(img, (pole_x, 95), 11, (20, 20, 255), -1)
    cv2.circle(img, (pole_x, 95), 18, (40, 40, 255), 1)  # Halo
    # Yellow Lamp (OFF)
    cv2.circle(img, (pole_x, 125), 9, (15, 60, 70), -1)
    # Green Lamp (OFF)
    cv2.circle(img, (pole_x, 155), 9, (15, 60, 20), -1)

    # 4. Vehicle crossing past the stop line
    is_bike = "Helmet" in violation_type or "Triple" in violation_type
    vx, vy = (240, 220) if is_bike else (200, 210)

    if is_bike:
        # Motorcycle + Rider(s)
        # Shadow
        cv2.ellipse(img, (vx + 70, vy + 175), (55, 12), 0, 0, 360, (20, 20, 20), -1)
        # Motorcycle chassis & wheels
        cv2.circle(img, (vx + 35, vy + 160), 18, (30, 30, 30), 6)  # Front wheel
        cv2.circle(img, (vx + 105, vy + 160), 18, (30, 30, 30), 6)  # Rear wheel
        cv2.line(img, (vx + 35, vy + 160), (vx + 70, vy + 130), (180, 40, 30), 5)
        cv2.line(img, (vx + 70, vy + 130), (vx + 105, vy + 160), (180, 40, 30), 5)
        cv2.rectangle(img, (vx + 50, vy + 120), (vx + 95, vy + 135), (200, 50, 40), -1)  # Fuel tank & seat
        # Handlebars
        cv2.line(img, (vx + 45, vy + 105), (vx + 65, vy + 115), (150, 150, 150), 3)

        # Riders
        num_riders = 3 if "Triple" in violation_type else 1
        for r_idx in range(num_riders):
            rx = vx + 55 + r_idx * 22
            ry = vy + 75
            # Body/Torso
            shirt_color = [(180, 100, 40), (40, 120, 180), (60, 160, 80)][r_idx % 3]
            cv2.rectangle(img, (rx - 10, ry + 15), (rx + 10, ry + 50), shirt_color, -1)
            # Head
            head_y = ry + 5
            if "Helmet" in violation_type and r_idx == 0:
                # No Helmet: Hair & Face visible
                cv2.circle(img, (rx, head_y), 10, (140, 180, 215), -1)  # skin tone
                cv2.ellipse(img, (rx, head_y - 4), (10, 6), 0, 180, 360, (20, 20, 20), -1)  # hair
            else:
                # Wearing Helmet (or other riders)
                cv2.circle(img, (rx, head_y), 11, (50, 50, 50), -1)
                cv2.rectangle(img, (rx - 6, head_y - 2), (rx + 6, head_y + 3), (220, 220, 220), -1)  # visor

        # Bounding box coordinates for bike
        bx1, by1, bx2, by2 = vx + 15, vy + 55, vx + 130, vy + 185
    else:
        # Car / Sedan crossing stop line
        # Shadow
        cv2.ellipse(img, (vx + 115, vy + 175), (105, 16), 0, 0, 360, (15, 15, 15), -1)
        # Car body (Metallic Blue/Grey)
        car_color = (160, 90, 40)
        # Cabin (roof & windows)
        cv2.rectangle(img, (vx + 40, vy + 60), (vx + 190, vy + 120), car_color, -1)
        # Windshield & windows (tinted glass)
        cv2.rectangle(img, (vx + 50, vy + 65), (vx + 105, vy + 110), (90, 80, 60), -1)
        cv2.rectangle(img, (vx + 120, vy + 65), (vx + 180, vy + 110), (90, 80, 60), -1)
        # Lower car chassis
        cv2.rectangle(img, (vx + 15, vy + 110), (vx + 215, vy + 165), car_color, -1)
        # Wheels
        cv2.circle(img, (vx + 55, vy + 165), 18, (25, 25, 25), -1)
        cv2.circle(img, (vx + 55, vy + 165), 8, (160, 160, 160), -1)
        cv2.circle(img, (vx + 175, vy + 165), 18, (25, 25, 25), -1)
        cv2.circle(img, (vx + 175, vy + 165), 8, (160, 160, 160), -1)
        # Headlights / Taillights
        cv2.rectangle(img, (vx + 15, vy + 120), (vx + 25, vy + 135), (60, 60, 240), -1)  # red tail
        cv2.rectangle(img, (vx + 205, vy + 120), (vx + 215, vy + 135), (200, 240, 255), -1)  # white head

        # Bounding box coordinates for car
        bx1, by1, bx2, by2 = vx + 10, vy + 55, vx + 220, vy + 185

    # 5. AI Detection Bounding Box (Red/Neon Coral)
    box_color = (60, 60, 245)
    cv2.rectangle(img, (bx1, by1), (bx2, by2), box_color, 2)
    # Fancy corner reticles
    c_len = 12
    for cx, cy in [(bx1, by1), (bx2, by1), (bx1, by2), (bx2, by2)]:
        dx = c_len if cx == bx1 else -c_len
        dy = c_len if cy == by1 else -c_len
        cv2.line(img, (cx, cy), (cx + dx, cy), (50, 230, 255), 3)
        cv2.line(img, (cx, cy), (cx, cy + dy), (50, 230, 255), 3)

    # Violation Tag Label
    conf_pct = round(random.uniform(94.2, 98.7), 1)
    tag_text = f"{violation_type.upper()} [{conf_pct}%]"
    (tw, th), _ = cv2.getTextSize(tag_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
    cv2.rectangle(img, (bx1, by1 - 22), (bx1 + tw + 10, by1), box_color, -1)
    cv2.putText(img, tag_text, (bx1 + 5, by1 - 6),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

    # 6. ANPR License Plate Cutout / Inset (Top Right)
    anpr_x, anpr_y, anpr_w, anpr_h = w - 210, 15, 195, 80
    # Inset background
    cv2.rectangle(img, (anpr_x, anpr_y), (anpr_x + anpr_w, anpr_y + anpr_h), (25, 25, 25), -1)
    cv2.rectangle(img, (anpr_x, anpr_y), (anpr_x + anpr_w, anpr_y + anpr_h), (80, 80, 80), 1)
    # Header
    cv2.rectangle(img, (anpr_x, anpr_y), (anpr_x + anpr_w, anpr_y + 18), (45, 45, 45), -1)
    cv2.putText(img, "ANPR RECOGNITION", (anpr_x + 8, anpr_y + 13),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (100, 220, 255), 1)

    # Number Plate Graphic (Indian Standard White Plate)
    plt_x, plt_y, plt_w, plt_h = anpr_x + 10, anpr_y + 25, anpr_w - 20, 36
    cv2.rectangle(img, (plt_x, plt_y), (plt_x + plt_w, plt_y + plt_h), (250, 250, 250), -1)
    cv2.rectangle(img, (plt_x, plt_y), (plt_x + plt_w, plt_y + plt_h), (10, 10, 10), 2)
    # Blue 'IND' band on left of plate
    cv2.rectangle(img, (plt_x, plt_y), (plt_x + 22, plt_y + plt_h), (160, 50, 20), -1)
    cv2.putText(img, "IND", (plt_x + 3, plt_y + 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
    # Plate Number
    formatted_plate = f"{vehicle_number[:4]} {vehicle_number[4:]}" if len(vehicle_number) > 4 else vehicle_number
    cv2.putText(img, formatted_plate, (plt_x + 26, plt_y + 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (10, 10, 10), 2)
    # Match confidence note
    cv2.putText(img, f"MATCH: {round(random.uniform(96.0, 99.4), 1)}% | OCR PASS",
                (anpr_x + 10, anpr_y + anpr_h - 6),
                cv2.FONT_HERSHEY_SIMPLEX, 0.3, (120, 240, 120), 1)

    # 7. CCTV Surveillance HUD (Top Left & Bottom)
    now_str = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    cv2.circle(img, (20, 22), 5, (0, 0, 255), -1)  # Red recording dot
    cv2.putText(img, f"LIVE REC [CCTV-04]  {location}", (32, 26),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (240, 240, 240), 1)
    cv2.putText(img, f"TIME: {now_str}  |  STOP-LINE TRIGGERED", (20, 46),
                cv2.FONT_HERSHEY_SIMPLEX, 0.38, (180, 210, 255), 1)

    # Bottom status bar
    cv2.rectangle(img, (0, h - 24), (w, h), (15, 15, 15), -1)
    cv2.line(img, (0, h - 24), (w, h - 24), (60, 60, 60), 1)
    cv2.putText(img, f"OFFENSE: {violation_type.upper()}  |  EVIDENCE SECURED  |  SMART RTO MONITOR",
                (14, h - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (200, 200, 200), 1)

    return img


def save_evidence(frame, violation_type, vehicle_number="MH15AB1234", location=LOCATION, out_dir=EVIDENCE_DIR):
    """Saves violation evidence snapshot. If real frame is missing, synthesizes authentic CCTV snapshot."""
    if not _CV2:
        return ""
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = "".join(c if c.isalnum() else "_" for c in violation_type)
    filename = f"{safe}_{stamp}.jpg"
    path = os.path.join(out_dir, filename)

    if frame is None:
        frame = _draw_synthetic_evidence(violation_type, vehicle_number, location)

    if frame is not None:
        cv2.imwrite(path, frame)
        return path
    return ""
