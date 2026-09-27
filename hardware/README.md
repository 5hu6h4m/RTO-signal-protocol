# Hardware guide (prototype, 5V Arduino Uno only)

## Parts
Arduino Uno, breadboard, jumper wires, red/yellow/green LEDs,
3x 220 ohm resistors, IR obstacle sensor, 5V active buzzer, USB cable.

## Connections
| Arduino | Component | Detail |
|---|---|---|
| Pin 8 | Red LED anode | via 220 ohm; cathode to GND |
| Pin 9 | Yellow LED anode | via 220 ohm; cathode to GND |
| Pin 10 | Green LED anode | via 220 ohm; cathode to GND |
| Pin 2 | IR sensor OUT | sensor VCC to 5V, GND to GND (LOW = obstacle) |
| Pin 3 | Buzzer + | buzzer - to GND |
| USB | Laptop | serial @ 9600 baud |

## Behaviour
GREEN 8 s -> YELLOW 2 s -> RED 8 s, repeating. During RED, an IR
trip sounds the buzzer 2 s and prints `VIOLATION_TRIGGERED`.
Every signal change prints `SIGNAL:<COLOR>`.

## Find your port (Fedora)
1. Unplug Arduino, run `ls /dev/ttyACM* /dev/ttyUSB*`.
2. Plug it in, run again - the new entry is your board.
3. Put it in `.env` as `ARDUINO_PORT=/dev/ttyACM0`.
4. Add yourself to dialout if permission denied:
   `sudo usermod -aG dialout $USER` then log out/in.

## Upload
`arduino-cli board list` to confirm, then compile+upload
`traffic_signal.ino` from the Arduino IDE or arduino-cli.

## Safety
5V USB-powered prototype only. No mains, no relays, no motors.
LEDs always through 220 ohm resistors.
