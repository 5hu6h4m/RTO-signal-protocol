/* Smart RTO - Traffic signal + stop-line violation trigger.
 * Board: Arduino Uno. Protocol over USB serial @ 9600 baud:
 *   SIGNAL:RED | SIGNAL:YELLOW | SIGNAL:GREEN   (on every change)
 *   VIOLATION_TRIGGERED                         (IR tripped while RED)
 *
 * Wiring (all 5V-safe prototype levels):
 *   RED LED    : pin 8  -> 220 ohm -> LED anode, LED cathode -> GND
 *   YELLOW LED : pin 9  -> 220 ohm -> LED anode, LED cathode -> GND
 *   GREEN LED  : pin 10 -> 220 ohm -> LED anode, LED cathode -> GND
 *   IR sensor  : VCC -> 5V, GND -> GND, OUT -> pin 2 (LOW = obstacle)
 *   Buzzer (+) : pin 3, Buzzer (-) -> GND (active buzzer, 5V, <30 mA)
 */
const int RED_PIN = 8, YEL_PIN = 9, GRN_PIN = 10;
const int IR_PIN = 2, BUZZER_PIN = 3;
const unsigned long GREEN_MS = 8000, YELLOW_MS = 2000, RED_MS = 8000;

void setSignal(bool r, bool y, bool g) {
  digitalWrite(RED_PIN, r); digitalWrite(YEL_PIN, y); digitalWrite(GRN_PIN, g);
}
void announce(const char* s) { Serial.print("SIGNAL:"); Serial.println(s); }

void setup() {
  pinMode(RED_PIN, OUTPUT); pinMode(YEL_PIN, OUTPUT); pinMode(GRN_PIN, OUTPUT);
  pinMode(IR_PIN, INPUT); pinMode(BUZZER_PIN, OUTPUT);
  Serial.begin(9600);
}

void violationAlarm() {
  digitalWrite(BUZZER_PIN, HIGH);
  Serial.println("VIOLATION_TRIGGERED");
  delay(2000);                    // buzzer + debounce window
  digitalWrite(BUZZER_PIN, LOW);
}

void runPhase(bool r, bool y, bool g, const char* name, unsigned long ms) {
  setSignal(r, y, g); announce(name);
  unsigned long t0 = millis();
  bool alarmedThisPhase = false;
  while (millis() - t0 < ms) {
    // Only the RED phase is enforced: crossing the stop line now = violation.
    if (r && digitalRead(IR_PIN) == LOW && !alarmedThisPhase) {
      violationAlarm();
      alarmedThisPhase = true;
    }
    if (digitalRead(IR_PIN) == HIGH) alarmedThisPhase = false;  // re-arm
    delay(50);
  }
}

void loop() {
  runPhase(false, false, true, "GREEN", GREEN_MS);
  runPhase(false, true, false, "YELLOW", YELLOW_MS);
  runPhase(true, false, false, "RED", RED_MS);
}
