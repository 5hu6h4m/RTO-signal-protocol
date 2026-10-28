"""Arduino serial link & Virtual Traffic Signal Controller.

Supports dual operation:
1. Physical Arduino Uno via USB serial (when hardware is connected).
2. Complete Virtual Hardware & Junction Controller (for presentation / simulation):
   - Real-time signal cycle (GREEN -> YELLOW -> RED) with live countdown.
   - Manual Signal Override (Force RED, Force GREEN, Emergency Clear).
   - Virtual IR Beam sensor trigger with buzzer indicator.
   - Thread-safe state query for the web dashboard.
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
        self.on_violation = on_violation or (lambda *args, **kwargs: None)
        self.demo_mode = demo_mode or not _SERIAL
        self.signal_state = "GREEN"
        self.mode = "AUTO"  # "AUTO" or "MANUAL"
        self.countdown = 8
        self.buzzer_active = False
        self.ir_state = "ACTIVE"  # "ACTIVE" or "TRIPPED"
        self.connected = False
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._thread = None
        self._ser = None
        self._buzzer_timer = None

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

    def set_signal(self, state):
        """Manually override signal state (RED, YELLOW, GREEN). Sets mode to MANUAL."""
        state = state.upper()
        if state not in ("RED", "YELLOW", "GREEN"):
            return False
        with self._lock:
            self.signal_state = state
            self.mode = "MANUAL"
            self.countdown = 0
        self.on_signal(state)
        return True

    def set_mode(self, mode):
        """Set mode to 'AUTO' or 'MANUAL'."""
        mode = mode.upper()
        if mode not in ("AUTO", "MANUAL"):
            return False
        with self._lock:
            self.mode = mode
            if mode == "AUTO":
                self.countdown = 8 if self.signal_state != "YELLOW" else 3
        return True

    def trigger_ir(self, vehicle_number=None, violation_type="Red Light Violation"):
        """Simulates IR sensor beam break when vehicle crosses stop line."""
        with self._lock:
            self.ir_state = "TRIPPED"
            is_red = (self.signal_state == "RED")

        def _reset_ir():
            time.sleep(2.5)
            with self._lock:
                self.ir_state = "ACTIVE"
                self.buzzer_active = False

        threading.Thread(target=_reset_ir, daemon=True).start()

        if is_red:
            with self._lock:
                self.buzzer_active = True
            # Fire violation callback
            try:
                self.on_violation(vehicle_number=vehicle_number, violation_type=violation_type)
            except TypeError:
                self.on_violation()
            return {"violation": True, "message": "VIOLATION TRIGGERED! Stop-line crossed during RED signal."}
        else:
            return {"violation": False, "message": f"Stop-line crossed safely during {self.signal_state} signal."}

    def get_status(self):
        """Returns snapshot of virtual/real hardware state for web UI."""
        with self._lock:
            return {
                "connected": self.connected,
                "demo_mode": self.demo_mode,
                "signal_state": self.signal_state,
                "countdown": max(0, self.countdown),
                "mode": self.mode,
                "buzzer": self.buzzer_active,
                "ir_sensor": self.ir_state,
            }

    def _handle_line(self, line):
        line = line.strip()
        if line.startswith("SIGNAL:"):
            self.signal_state = line.split(":", 1)[1]
            self.on_signal(self.signal_state)
        elif line == "VIOLATION_TRIGGERED":
            self.buzzer_active = True
            self.ir_state = "TRIPPED"
            try:
                self.on_violation()
            except Exception:
                pass
            time.sleep(2)
            self.buzzer_active = False
            self.ir_state = "ACTIVE"

    def _loop(self):
        cycle_phases = [("GREEN", 8), ("YELLOW", 3), ("RED", 8)]
        phase_idx = 0

        while not self._stop.is_set():
            if self.demo_mode:
                if self.mode == "MANUAL":
                    # Held in manual override; tick lightly
                    time.sleep(0.5)
                    continue

                state, duration = cycle_phases[phase_idx]
                with self._lock:
                    self.signal_state = state
                    self.countdown = duration
                self.on_signal(state)

                # Count down 1s per tick so UI sees active timer
                for sec in range(duration, 0, -1):
                    if self._stop.is_set():
                        return
                    if self.mode == "MANUAL":
                        break
                    with self._lock:
                        self.countdown = sec
                    time.sleep(1)

                if self.mode == "AUTO":
                    phase_idx = (phase_idx + 1) % len(cycle_phases)
            else:
                try:
                    raw = self._ser.readline().decode(errors="ignore")
                    if raw:
                        self._handle_line(raw)
                except Exception:
                    time.sleep(0.5)
