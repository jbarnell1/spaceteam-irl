# PCB Design Brief — Spaceteam IRL Tablets

> **Purpose:** This document gives a PCB designer everything they need to lay out the tablet boards for the Spaceteam IRL project. The goal is JLCPCB-assembled PCBAs dropped into 3D-printed enclosures.
>
> **Key references (read these first):**
> - [docs/tablet-archetypes.md](../../docs/tablet-archetypes.md) — Full control loadouts, GPIO assignments, pin budgets, and archetype definitions for all 8 tablet types
> - [hardware/bom/tablet-bom.md](../bom/tablet-bom.md) — Complete bill of materials with component costs
> - [README.md](../../README.md) — Full project overview

---

## Table of Contents

- [Project Context](#project-context)
- [Board Strategy](#board-strategy)
- [MCU & Power Circuit](#mcu--power-circuit)
- [Shared Peripherals](#shared-peripherals)
- [Archetype Control Connections](#archetype-control-connections)
- [I2C Bus Architecture](#i2c-bus-architecture)
- [SPI Bus Architecture](#spi-bus-architecture)
- [GPIO Pin Allocation](#gpio-pin-allocation)
- [Physical Constraints](#physical-constraints)
- [Design-for-Manufacturing Notes](#design-for-manufacturing-notes)
- [Deliverables](#deliverables)

---

## Project Context

This is a cooperative tabletop game where up to 8 players each hold a physical tablet with knobs, switches, and buttons. A central Hub sends commands via ESP-NOW wireless; players scramble to flip the right controls under time pressure.

There are **8 archetype variants** of the tablet (Navigator, Engineer, Operator, Sentinel, Medic, Analyst, Scout, Commander). Each shares an identical base circuit but has a different set of 5 physical controls. See [tablet-archetypes.md](../../docs/tablet-archetypes.md) for the complete definition of every archetype.

**Target:** ~$20 COGS/tablet at 1,000+ units, assembled by JLCPCB.

---

## Board Strategy

### Option A: Single Universal PCB (Recommended for Prototype)

One PCB design with **footprints for all possible controls** across all 8 archetypes. Each archetype only populates its specific slots; unused footprints are left empty (DNP — Do Not Populate).

**Pros:** One board design to maintain. JLCPCB only needs one PCB order. Assembly variants handled by BOM selection.
**Cons:** Board is larger than needed for any single archetype. Some wasted space. Higher per-unit PCB cost due to size.

### Option B: Base + Daughterboard (Recommended for Production)

- **Base board** (~60×50mm est.): MCU, power, I2C mux, SPI bus, connectors for displays, feedback components. Identical for all 8 archetypes.
- **Control daughterboard** (per archetype): Mounted on top or side. Carries the 5 archetype-specific control connectors/footprints. 8 different daughterboard designs.

**Pros:** Base board is small and cheap. Only the daughterboard varies. Easier to manage 8 control layouts independently.
**Cons:** More board designs. Needs inter-board connector (pin headers or FPC).

### Recommendation

Start with **Option A** for the first prototype run (1–10 units). Move to **Option B** for production (100+ units) once layouts are validated.

---

## MCU & Power Circuit

### ESP32-S3-WROOM-1-N16R8

Standard reference design per Espressif's hardware design guide:
- Decoupling: 10µF + 100nF on 3V3 pin
- EN pin: RC circuit (10kΩ pull-up + 1µF to GND) for clean power-on reset
- GPIO0: 10kΩ pull-up (boot mode select)
- USB D+/D−: Route to USB-C pad for firmware flashing (development only — no USB in gameplay)
- Antenna keepout: Follow module datasheet — no copper pour or traces under antenna area

### Power Supply

```
2× AA (3.0V nom, 1.8V min) → TPS61200 Boost → 3.3V rail
```

- **TPS61200DRCR** (SOT-23-6 / SON-6): Fixed 3.3V output variant preferred (TPS61200DRCR or TPS61202DSCR)
- Input range: 0.3V–5.5V (handles dead-battery graceful shutdown)
- Output: 3.3V @ up to 600mA (sufficient for ESP32-S3 peak ~500mA during WiFi/BLE TX)
- Layout: Place inductor (4.7µH shielded, e.g., Wurth 744043004R7) close to IC. Short, wide traces on power path. Follow TI datasheet layout example exactly.
- Battery connector: JST-PH 2-pin, keyed. Polarity protection via series Schottky diode (optional, adds ~0.2V drop).

### Power Switch

SPST slide switch inline with battery positive. Place at board edge for enclosure access.

---

## Shared Peripherals

All items below are present on every tablet. Full specs in [tablet-archetypes.md § Base Tablet](../../docs/tablet-archetypes.md#base-tablet-shared-across-all-archetypes).

### Displays (I2C + SPI)

| Display | Qty | Interface | Connection | Notes |
|---|---|---|---|---|
| 1.3" OLED (SSD1306/SH1106) | 5 | I2C via TCA9548A | 4-pin header (VCC, GND, SDA, SCL) per OLED | All 5 have same I2C address; mux selects channel |
| Command Screen (TFT, ILI9341/ST7789) | 1 | SPI (4-wire) | 8-pin header (VCC, GND, MOSI, SCK, CS, DC, RST, BL) | Largest display; place connector at board edge |
| 7-Segment (TM1637) | 1 | 2-wire (CLK + DIO) | 4-pin header (VCC, GND, CLK, DIO) | Player ID display |

### Feedback

| Component | Interface | Connection | Notes |
|---|---|---|---|
| WS2812B NeoPixel (status LED) | 1-wire data | SMD on base PCB | 5V-tolerant data at 3.3V — add 470Ω series resistor on data line, 100nF bypass cap |
| Piezo speaker | PWM | 2-pin header or SMD buzzer pad | |
| Coin vibration motor | Digital out via MOSFET | 2-pin JST connector | **2N7002 MOSFET + 1N4148 flyback diode.** NEVER direct GPIO drive. See schematic below. |

**Vibration motor driver:**
```
GPIO → 10kΩ → MOSFET Gate
               MOSFET Source → GND
               MOSFET Drain → Motor(−)
               Motor(+) → 3.3V
               1N4148 cathode → Motor(+), anode → Motor(−)
```

### Shared Inputs

| Component | Interface | Notes |
|---|---|---|
| Guarded Illuminated Pushbutton (crisis button) | 2 GPIO: switch (digital, 10kΩ pull-up, active-low) + LED (digital out) | Aircraft-style safety cover over lit momentary switch. Panel-mount; wire to 3-pin header (SIG, LED, GND). Hub controls LED: red=crisis, green=ready, off=idle. |
| Submit Button (12mm, tactile) | 1 GPIO, 10kΩ pull-up, active-low | Panel-mount or PCB-mount |

---

## Archetype Control Connections

Each archetype's 5 controls are through-hole / panel-mount components wired to the PCB via headers. The PCB needs labeled connection points for each slot.

The full definition of every slot across all 8 archetypes is in [tablet-archetypes.md § Archetype Definitions](../../docs/tablet-archetypes.md#archetype-definitions). Here's the summary of what connections each slot needs:

### Slot 1 — Signature Control (varies by archetype)

| Archetype | Control | Connections Needed |
|---|---|---|
| Navigator | Analog Joystick | VCC, GND, X (ADC), Y (ADC), Click (GPIO) — 5 pins |
| Engineer | 60mm Slide Pot | VCC, GND, Wiper (ADC) — 3 pins |
| Operator | Rotary Encoder (EC11) | A (GPIO), B (GPIO), Click (GPIO), GND — 4 pins |
| Sentinel | SS49E Hall Sensor (ADC) | VCC, GND, Output (ADC) — 3 pins |
| Medic | Pot + NeoPixel | VCC, GND, Wiper (ADC), NeoPixel Data (GPIO) — 4 pins |
| Analyst | 4-Button Keypad | 4× GPIO, GND — 5 pins |
| Scout | Pot + NeoPixel Ring | VCC, GND, Wiper (ADC), NeoPixel Data (GPIO) — 4 pins |
| Commander | 6-Position Rotary Switch | VCC, GND, Wiper (ADC) — 3 pins (+ resistor ladder on control side) |

### Slot 2 — Medium Control (varies by archetype)

| Archetype | Control | Connections Needed |
|---|---|---|
| Navigator | 45mm Slide Pot | VCC, GND, Wiper (ADC) — 3 pins |
| Engineer | Illuminated Arcade Button | Switch (GPIO), LED (GPIO), GND — 3 pins |
| Operator | Covered Safety Toggle | Signal (GPIO), GND — 2 pins |
| Sentinel | 3-Pos Rotary Switch | VCC, GND, Wiper (ADC) — 3 pins (+ resistor ladder) |
| Medic | Rotary Encoder (EC11) | A (GPIO), B (GPIO), Click (GPIO), GND — 4 pins |
| Analyst | Pot + 4-LED Bar | VCC, GND, Wiper (ADC), NeoPixel Data (GPIO) — 4 pins |
| Scout | Covered Safety Toggle | Signal (GPIO), GND — 2 pins |
| Commander | Illuminated Arcade Button | Switch (GPIO), LED (GPIO), GND — 3 pins |

### Slots 3–5 — Simple Controls

These are all toggle switches (SPDT) or momentary pushbuttons. Each needs:
- **Toggle:** Signal (GPIO) + GND — 2 pins. 10kΩ pull-up.
- **Momentary:** Signal (GPIO) + GND — 2 pins. 10kΩ pull-up, active-low.

Exact assignments per archetype are in the [Archetype Summary table](../../docs/tablet-archetypes.md#archetype-summary).

### Universal Connector Approach

For Option A (universal PCB), provide a generic **multi-pin header block** for each slot:

| Slot | Header | Pins |
|---|---|---|
| Slot 1 | 2×5 pin header (10 pins) | Covers all signature controls. Unused pins left NC. |
| Slot 2 | 1×6 pin header (6 pins) | Covers all medium controls. |
| Slots 3, 4, 5 | 1×3 pin header each (3 pins: SIG, VCC, GND) | Simple toggle/button. |

---

## I2C Bus Architecture

```
ESP32-S3 SDA/SCL
       │
       ▼
   TCA9548A Mux (addr 0x70)
   ├── Ch0 → OLED Slot 1 (addr 0x3C)
   ├── Ch1 → OLED Slot 2 (addr 0x3C)
   ├── Ch2 → OLED Slot 3 (addr 0x3C)
   ├── Ch3 → OLED Slot 4 (addr 0x3C)
   └── Ch4 → OLED Slot 5 (addr 0x3C)
```

- All 5 OLEDs use the same I2C address (0x3C). The mux selects which one is active.
- Pull-ups: 4.7kΩ on the main SDA/SCL bus (before mux). No pull-ups needed after mux (channels are switched, not buffered, but the mux has pull-down on outputs — check datasheet).
- I2C speed: 400kHz (Fast Mode). Keep traces short.
- The TCA9548A has 3 address bits (A0–A2) — tie to GND for address 0x70.

---

## SPI Bus Architecture

```
ESP32-S3 SPI Bus (HSPI or VSPI)
  MOSI ──── Command Screen (TFT)
  MISO ──┤      CS_TFT (GPIO)
  SCK  ──┤
         └── RC522 NFC (Commander only)
                CS_NFC (GPIO)
```

- SPI bus is shared. Each device has its own CS (chip select) line.
- On non-Commander archetypes, the NFC CS pin is unused (leave as GPIO or NC).
- SPI clock: 10–40MHz for TFT, 10MHz max for RC522.
- TFT also needs DC (data/command), RST, and backlight (BL) GPIO lines.

---

## GPIO Pin Allocation

Total available on ESP32-S3: ~36 usable GPIO (excluding strapping pins, flash/PSRAM pins).

| Function | Pins | Notes |
|---|---|---|
| I2C (SDA, SCL) | 2 | Shared bus to TCA9548A mux |
| SPI (MOSI, MISO, SCK) | 3 | Shared bus: TFT + NFC |
| TFT CS, DC, RST, BL | 4 | Command screen |
| NFC CS, IRQ, RST | 3 | Commander only (2 pins reusable on other archetypes) |
| TM1637 (CLK, DIO) | 2 | 7-segment display |
| NeoPixel Status LED | 1 | WS2812B data |
| Speaker PWM | 1 | Piezo |
| Vibration Motor | 1 | Via MOSFET |
| Crisis Button (switch) | 1 | Guarded illuminated pushbutton — switch input |
| Crisis Button (LED) | 1 | Guarded illuminated pushbutton — LED output |
| Submit Button | 1 | Analog value confirm |
| **Base subtotal** | **~20** | |
| **Archetype controls** | **6–11** | See [Pin Budget Summary](../../docs/tablet-archetypes.md#pin-budget-summary) |
| **Total** | **26–31** | Well within 36 available |

> **Important:** Consult the ESP32-S3 datasheet for strapping pin restrictions (GPIO0, GPIO3, GPIO45, GPIO46). These should NOT be used for general I/O without understanding boot-mode implications. Pins GPIO26–32 are internal flash/PSRAM on the -N16R8 module and are NOT available.

---

## Physical Constraints

| Parameter | Value | Notes |
|---|---|---|
| Chassis | 8-inch (203mm) diameter, 3D-printed PLA | Prototype enclosure |
| PCB shape | Rectangular or custom shape to fit chassis | Max ~180mm in longest dimension |
| Board thickness | 1.6mm standard | JLCPCB default |
| Layers | 2-layer (4-layer if routing gets tight) | 2-layer preferred for cost |
| Mounting | M3 standoffs (4 corners minimum) | Include M3 mounting holes in PCB outline |
| Control panel | Top face of enclosure | Controls are panel-mounted, wired to PCB headers below |
| Display cutouts | Enclosure has 5 rectangular OLED windows + 1 TFT window | OLEDs mount flush to panel; PCB sits below |
| Battery sled | Bottom or side compartment | JST cable to PCB |
| Power switch | Edge-accessible | Slide switch at PCB edge or wired to panel |

---

## Design-for-Manufacturing Notes

### JLCPCB-Specific

1. **Use LCSC part numbers** for all SMD components. JLCPCB's assembly service pulls from LCSC inventory. Tag every component with an LCSC part number in the BOM.
2. **Basic vs. Extended parts:** JLCPCB charges extra for "Extended" parts. The ESP32-S3 module, TCA9548A, and TPS61200 are likely Extended. Toggle switches and passives should be Basic.
3. **Minimum order:** JLCPCB SMT minimum is typically 5 boards. Prototype run of 5–10 is fine.
4. **Panelization:** For production, panelize boards (e.g., 2-up) to reduce per-board assembly cost.
5. **SMD on one side preferred.** If all SMD is on top, assembly cost is lower. Through-hole controls are hand-soldered separately.

### General

- **Silkscreen:** Label every connector (SLOT1, SLOT2, OLED1–5, TFT, BATT, MOTOR, SPK, CRISIS, SUBMIT). Mark pin 1 on all headers.
- **Test points:** Add labeled test points for 3V3, GND, SDA, SCL, MOSI, SCK, and at least 2 spare GPIO.
- **Grounding:** Solid ground plane on bottom layer. Star-ground or separate analog/digital ground not required at these frequencies, but keep ADC traces away from noisy digital lines (SPI, NeoPixel).
- **Antenna clearance:** The ESP32-S3-WROOM module has an onboard PCB antenna. Keep a copper-free zone (no traces, no ground pour) under and around the antenna per the module datasheet (~15mm keepout).

---

## Deliverables

What we need from the PCB designer:

| Deliverable | Format | Notes |
|---|---|---|
| Schematic | EasyEDA Pro project (or PDF export) | Full circuit for base + all archetype variants |
| PCB Layout | EasyEDA Pro project | Gerber-ready. Option A (universal) first, Option B (base+daughter) if going to production. |
| BOM (assembly) | CSV with LCSC part numbers | JLCPCB assembly-ready format. One BOM per archetype variant (same base, different control population). |
| Pick-and-Place file | CSV (JLCPCB format) | Component placement for SMT assembly. |
| 3D model (optional) | STEP export | For checking enclosure fit in CAD. |
| Design review notes | Markdown or PDF | Any concerns about layout, routing, antenna, power integrity. |

### Design Priority

1. **Base circuit first.** Get the ESP32-S3 + power + displays + feedback working on a rev 1 board.
2. **Navigator archetype second.** It has the most complex signature control (joystick = 3 ADC + 1 digital). If Navigator works, all others are simpler.
3. **Commander archetype third.** Tests SPI bus sharing (NFC + TFT on same bus).
4. **Remaining 6 archetypes** are mostly variations of simpler controls (toggles, buttons, pots, encoders, hall sensor ADC).
