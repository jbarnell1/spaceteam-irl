# Spaceteam IRL — Breadboard Prototype Guide

## What You'll Need
- 2× ESP32 DevKit V1 boards (one Hub, one Tablet)
- 2× 0.91" OLED displays (SSD1306, 128×32, I2C)
- 1× Joystick module (for the Tablet board)
- 2× Tactile pushbuttons (Submit + Crisis on Tablet)
- 1× Tactile pushbutton (Start on Hub)
- 1× LED + 220Ω resistor (for the Tablet board)
- 2× USB cables (one per board)
- Breadboard + jumper wires

## Arduino IDE Setup (one-time)

### 1. Install ESP32 Board Support
1. **File → Preferences**
2. In "Additional Board Manager URLs", add:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
3. **Tools → Board → Board Manager** → search `esp32` → install **"ESP32 by Espressif Systems"**

### 2. Install Libraries
Open **Sketch → Include Library → Manage Libraries** and install:

| Library | Author | Version |
|---|---|---|
| **ArduinoJson** | Benoit Blanchon | 6.x (NOT 7.x) |
| **Adafruit SSD1306** | Adafruit | latest |
| **Adafruit GFX Library** | Adafruit | (auto-installed with SSD1306) |

### 3. Board Settings
For both boards, set:
- **Board:** `ESP32 Dev Module`
- **Upload Speed:** `115200`
- **Flash Frequency:** `80MHz`
- **Partition Scheme:** `Default 4MB with spiffs`

## Flashing

### Flash the Hub
1. Plug in the **Hub** ESP32 via USB
2. **Tools → Port** → select its COM port
3. Open `firmware/prototype/hub_prototype/hub_prototype.ino`
4. Click **Upload** (→ arrow button)
5. Wait for "Done uploading"

### Flash the Tablet
1. Plug in the **Tablet** ESP32 via USB (can use same PC, different port)
2. **Tools → Port** → select the OTHER COM port
3. Open `firmware/prototype/tablet_prototype/tablet_prototype.ino`
4. Click **Upload**

> **Tip:** If upload fails, hold the **BOOT** button on the ESP32 while it says "Connecting..." then release after upload starts.

## Wiring Reference

### Hub ESP32
| GPIO | Component |
|------|-----------|
| 27 | Start button (other leg → GND) |
| 22 | OLED SCL |
| 21 | OLED SDA |
| 2 | Onboard blue LED (no wire needed) |
| 3.3V | OLED VCC |
| GND | OLED GND, button GND |

### Tablet ESP32
| GPIO | Component |
|------|-----------|
| 34 | Joystick VRx |
| 35 | Joystick VRy |
| 27 | Joystick SW (other leg → GND) |
| 26 | Submit button (other leg → GND) |
| 25 | Crisis button (other leg → GND) |
| 33 | LED anode (→ 220Ω → GND) |
| 22 | OLED SCL |
| 21 | OLED SDA |
| 3.3V | OLED VCC, Joystick VCC |
| GND | OLED GND, Joystick GND, all button GNDs, LED cathode |

## Playing the Game

1. **Power both boards** (USB or external 5V)
2. **Hub** boots → OLED shows `PAIRING MODE` → blue LED blinks
3. **Tablet** boots → OLED shows `SEEKING HUB...` → external LED blinks
4. After ~1-2 seconds they find each other automatically
5. Hub OLED: `TABLET JOINED! Press btn to start`
6. **Press the Hub's start button**
7. Countdown: `3... 2... 1... GO!`
8. Hub sends **10 random commands** to the tablet:

| Command | What to Do | Timeout |
|---------|-----------|---------|
| **JOYSTICK** | Move joystick to target position (watch OLED — it shows live X,Y and "IN RANGE" when close). Press **SUBMIT** when in range. | 10 sec |
| **BUTTON** | Press the **SUBMIT** button | 6 sec |
| **CRISIS** | Press the **CRISIS** button (LED alarm blinks!) | 4 sec |

9. After each command: LED blinks for success/fail, Hub shows score
10. After 10 commands: **GAME OVER** screen with accuracy %
11. Press the Hub button to play again!

## Debugging

Open **Tools → Serial Monitor** (set baud to `115200`) to see log messages from whichever board is plugged in. You'll see all ESP-NOW messages logged as `[HUB TX]`, `[HUB RX]`, `[TAB TX]`, `[TAB RX]`.

### Common Issues

| Problem | Fix |
|---------|-----|
| OLED blank | Check SDA/SCL wiring. Try swapping SDA↔SCL. Check 3.3V power. |
| "ESP-NOW FAILED" | Make sure no other WiFi code is running. Reset the board. |
| Boards don't find each other | Both must be on default WiFi channel (auto). Reset both and wait 5 seconds. |
| Joystick values seem wrong | Open Serial Monitor on tablet — check "Joystick center" values at boot. If axes are swapped/inverted, swap GPIO 34↔35 pin assignment in the sketch. |
| Upload fails | Hold the **BOOT** button on the ESP32 during upload. |
| Compile error about `esp_now_recv_info_t` | You have Arduino-ESP32 Core v3.x. See the note at the top of the tablet sketch for the fix. |

## What This Proves

This prototype validates the core game loop:
- ✅ ESP-NOW pairing (Hub broadcasts, tablet discovers)
- ✅ Sub-10ms wireless command delivery
- ✅ Joystick analog input → position matching
- ✅ Button input → event response
- ✅ Crisis urgency mechanic
- ✅ Score tracking & game flow
- ✅ OLED real-time feedback
- ✅ Two-device state synchronization

Once this works, you've proven the fundamental Spaceteam IRL concept on a breadboard — the hardest engineering risk is retired.
