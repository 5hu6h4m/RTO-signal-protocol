# Smart RTO Traffic Rule Violation Detection and Monitoring System
College-level mini project prototype. Red-light violation demo with
Arduino + IR sensor + buzzer, plus AI detection (YOLO) for no-helmet /
triple-riding, plate OCR, SQLite history and a Flask dashboard.

## Features (core MVP)
- Red Light Violation (Arduino IR trigger -> buzzer -> capture -> AI -> DB -> dashboard)
- No Helmet detection (**potential** violations; needs optional `models/helmet.pt`, honestly labelled without it)
- Triple Riding detection (person-motorcycle association, >2 riders)
- Number Plate Recognition (contour crop + Tesseract; `Number Plate Not Clearly Detected` on failure - never guessed)
- Multiple violations grouped per vehicle (`/api/vehicles/MH15AB1234`)
- Violation history, daily statistics, web dashboard (Dashboard/Live/Violations/Vehicle/Reports)
- Demo Mode with clearly-labelled simulated buttons (no fake AI claims)

## Architecture
```
Toy vehicle crosses stop line during RED
  -> [Arduino Uno: LEDs + IR + buzzer] --USB serial--> [serial_listener]
       SIGNAL:RED / VIOLATION_TRIGGERED
  -> [VideoSource: webcam 0 | traffic.mp4 | phone IP URL]
  -> [YOLOv8n: person/car/motorcycle/bus/truck] -> [plate crop -> OCR]
  -> [ViolationEngine + evidence/*.jpg] -> [SQLite data/rto.db]
  -> [Flask API + Bootstrap dashboard :5000]
```

## Hardware requirements
Arduino Uno, breadboard, wires, red/yellow/green LEDs + 3x 220 ohm,
IR obstacle sensor, 5V buzzer, USB cable, laptop + webcam/phone.
See `hardware/README.md` for the exact connection table.

## Software requirements
Fedora Linux, Python 3.10+, Arduino IDE or arduino-cli,
Tesseract OCR (`sudo dnf install -y tesseract-ocr`).

## Installation
```bash
sudo dnf install -y python3-pip tesseract-ocr v4l-utils
cp .env.example .env   # then set ARDUINO_PORT, VIDEO_SOURCE
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## YOLO setup
Nothing to train. First run of the detector auto-downloads `yolov8n.pt`
(~6 MB). Optional: drop a helmet-capable model at `models/helmet.pt`
(class names containing `helmet`/`no_helmet`) to enable verified
helmet decisions; without it the UI says "unverified".

## OCR setup
Install Tesseract (above) + `pytesseract` (in requirements).
Plates are accepted only if they match an Indian-plate pattern;
otherwise the record stores `Number Plate Not Clearly Detected`.

## Arduino setup
Open `hardware/arduino/traffic_signal.ino`, upload to the Uno,
find your port (`ls /dev/ttyACM*`), set `ARDUINO_PORT` in `.env`.

## Database setup
Automatic: `backend/database.py::init_db()` creates
`vehicles / violations / system_events` on first start.

## How to run
```bash
source .venv/bin/activate
python3 run.py   # -> http://localhost:5000
```
No Arduino? Keep `DEMO_MODE=1` and use Live-page demo buttons.
Have a video? Set `VIDEO_SOURCE=traffic.mp4` in `.env`.

## How to test
```bash
python3 tests/test_phase1.py   # stdlib only, always works
```
Then: RED on -> break IR beam -> buzzer -> dashboard shows
RED LIGHT VIOLATION with evidence; search MH15AB1234 for history.

## Troubleshooting
| Symptom | Fix |
|---|---|
| `No module named pip` | `sudo dnf install -y python3-pip` |
| Permission denied `/dev/ttyACM0` | `sudo usermod -aG dialout $USER`, log out/in |
| No camera | `VIDEO_SOURCE=traffic.mp4`; check `ls /dev/video*` |
| torch/ultralytics fails on Python 3.14 | use Python 3.11 venv |
| OCR always unclear | brighter, head-on, close-up plate photos |

## Limitations (say in viva)
Prototype accuracy only; "Potential Violation, requires verification".
Standard YOLO cannot see helmets - needs the optional model.
No legal/enforcement validity.

## Future scope
Wrong-side driving, pure-vision stop-line, parking, seat-belt,
phone-use, ANPR camera, cloud/GPS tracking.
