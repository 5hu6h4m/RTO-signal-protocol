"""Arduino serial link. Protocol (documented, simple):

  Arduino -> Python:
    SIGNAL:RED | SIGNAL:YELLOW | SIGNAL:GREEN   (on every signal change)
    VIOLATION_TRIGGERED                          (IR tripped while RED)

  No Python -> Arduino commands in the MVP (keep it one-way & robust).

Usage:
  listener = SerialListener(port, baud, on_signal=fn, on_violation=fn)
  listener.start()   # background thread, never blocks the web server

If the board/pyserial is missing we run in DEMO_MODE: the listener
replays a fake signal cycle and logs that clearly - the dashboard
shows "Arduino: DEMO (simulated)".
"""
import threading
import time

try:
    import serial
    _SERIAL = True
except Exception:
    serial = None
    _SERIAL = False


class SerialListener:
    def __init__(self, port="/dev/ttyACM0", baud=9600,
                 on_signal=None, on_violation=None, demo_mode=True):
        self.port = port
        self.baud = baud
        self.on_signal = on_signal or (lambda s: None)
        self.on_violation = on_violation or (lambda: None)
        self.demo_mode = demo_mode or not _SERIAL
        self.signal_state = "UNKNOWN"
        self.connected = False
        self._stop = threading.Event()
        self._thread = None
        self._ser = None

    def start(self):
        if not self.demo_mode:
            try:
                self._ser = serial.Serial(self.port, self.baud, timeout=1)
                time.sleep(2)  # Arduino resets on serial open; wait
                self.connected = True
            except Exception:
                self.demo_mode = True  # fall back, stay working
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        try:
            if self._ser:
                self._ser.close()
        except Exception:
            pass

    def _handle_line(self, line):
        line = line.strip()
        if line.startswith("SIGNAL:"):
            self.signal_state = line.split(":", 1)[1]
            self.on_signal(self.signal_state)
        elif line == "VIOLATION_TRIGGERED":
            self.on_violation()

    def _loop(self):
        if self.demo_mode:
            # Fake cycle: GREEN 8s -> YELLOW 2s -> RED 8s, repeat.
            for state, duration in self._cycle():
                if self._stop.is_set():
                    return
                self.signal_state = state
                self.on_signal(state)
                time.sleep(duration)
            return
        while not self._stop.is_set():
            try:
                raw = self._ser.readline().decode(errors="ignore")
                if raw:
                    self._handle_line(raw)
            except Exception:
                time.sleep(0.5)

    @staticmethod
    def _cycle():
        while True:
            for state, duration in (("GREEN", 8), ("YELLOW", 2), ("RED", 8)):
                yield state, duration
