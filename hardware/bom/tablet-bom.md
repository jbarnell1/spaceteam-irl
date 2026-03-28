# Tablet Bill of Materials

> **Version:** 0.1.0 (Draft)
>
> Complete BOM for all 8 tablet archetypes. Each tablet shares a common base PCB plus archetype-specific controls soldered/wired to fixed positions.
>
> **Reference:** [docs/tablet-archetypes.md](../../docs/tablet-archetypes.md) for full control loadouts, GPIO assignments, pin budgets, and gameplay descriptions.

---

## Table of Contents

- [Design Targets](#design-targets)
- [Base Tablet BOM (All Archetypes)](#base-tablet-bom-all-archetypes)
- [Archetype-Specific BOMs](#archetype-specific-boms)
  - [1. Navigator](#1-navigator)
  - [2. Engineer](#2-engineer)
  - [3. Operator](#3-operator)
  - [4. Sentinel](#4-sentinel)
  - [5. Medic](#5-medic)
  - [6. Analyst](#6-analyst)
  - [7. Scout](#7-scout)
  - [8. Commander](#8-commander)
- [Consolidated Cost Summary](#consolidated-cost-summary)
- [Supplier Notes](#supplier-notes)

---

## Design Targets

| Parameter | Target |
|---|---|
| **Target COGS** | ~$20/tablet at 1,000+ units |
| **MCU** | ESP32-S3-WROOM-1-N16R8 (16MB flash, 8MB PSRAM) |
| **Power** | 2× AA batteries (~3V) → TPS61200 boost to 3.3V |
| **Runtime** | 5–6 hours (~10–20 game sessions) |
| **Chassis** | 8-inch, 3D-printed PLA (prototype) |
| **Assembly** | JLCPCB SMT assembly for base PCB; through-hole controls hand-soldered or on breakout daughterboards |
| **PCB Tool** | EasyEDA (Pro recommended for JLCPCB integration) |

---

## Base Tablet BOM (All Archetypes)

These components appear on **every** tablet. See [tablet-archetypes.md § Base Tablet](../../docs/tablet-archetypes.md#base-tablet-shared-across-all-archetypes) for interface and GPIO details.

### MCU & Power

| # | Component | Qty | Package/Form | Interface | Est. Cost (1k+) | Notes |
|---|---|---|---|---|---|---|
| B1 | ESP32-S3-WROOM-1-N16R8 | 1 | Module (SMD) | — | $3.50 | 16MB flash, 8MB PSRAM. Main MCU. |
| B2 | TPS61200 Boost Converter | 1 | SOT-23-6 (SMD) | — | $0.80 | 3V → 3.3V. Inductor + caps per datasheet. |
| B3 | 2× AA Battery Sled | 1 | Through-hole/wired | — | $0.30 | Spring-contact sled, panel-mount or chassis-mount. |
| B4 | Power Switch (SPST) | 1 | Through-hole | 1 GPIO or inline | $0.10 | Simple on/off. |
| B5 | Decoupling Caps (10µF + 100nF) | 3 sets | 0402/0603 (SMD) | — | $0.05 | Per standard ESP32-S3 reference design. |
| B6 | Boost Inductor (4.7µH) | 1 | SMD | — | $0.10 | Per TPS61200 datasheet. |

### Displays

| # | Component | Qty | Package/Form | Interface | Est. Cost (1k+) | Notes |
|---|---|---|---|---|---|---|
| B7 | 1.3" OLED (SSD1306 or SH1106, 128×64, I2C) | 5 | Module/breakout | I2C (shared bus) | $1.25 ea / $6.25 total | One per control slot. Hub pushes narrative labels. |
| B8 | TCA9548A I2C Multiplexer | 1 | SOIC-24 (SMD) | I2C | $0.60 | Routes shared SDA/SCL to 5 identical-address OLEDs. |
| B9 | Command Screen (SPI TFT, 1.8"–2.4" ILI9341/ST7789) | 1 | Module | SPI (4-wire) | $2.50 | Displays commands, cross-tablet directives. Size TBD. |
| B10 | 7-Segment Display (TM1637, 4-digit) | 1 | Module | 2-wire (CLK + DIO) | $0.40 | Player ID, connection status. |

### Feedback (Shared)

| # | Component | Qty | Package/Form | Interface | Est. Cost (1k+) | Notes |
|---|---|---|---|---|---|---|
| B11 | WS2812B NeoPixel (Status RGB LED) | 1 | 5050 SMD | 1-wire data | $0.08 | Archetype color, alerts, connection state. |
| B12 | Piezo Speaker / Buzzer | 1 | Through-hole or SMD | PWM (1 GPIO) | $0.20 | Tones, jingles, identification. |
| B13 | Coin Vibration Motor (10mm) | 1 | Wired | Digital out via MOSFET | $0.30 | Haptic feedback. **Never drive directly from GPIO.** |
| B14 | 2N7002 N-Channel MOSFET | 1 | SOT-23 (SMD) | — | $0.02 | Drives vibration motor. |
| B15 | Flyback Diode (1N4148) | 1 | SOD-323 (SMD) | — | $0.01 | Motor protection. |

### Shared Inputs

| # | Component | Qty | Package/Form | Interface | Est. Cost (1k+) | Notes |
|---|---|---|---|---|---|---|
| B16 | Guarded Illuminated Pushbutton (safety cover + LED momentary) | 1 | Panel-mount TH | 2 GPIO (switch + LED) | $1.20 | Crisis response / ready-up. Aircraft-style flip cover, lit momentary underneath. Hub controls LED color via PWM or digital. |
| B17 | Submit Button (tactile, 12mm) | 1 | Panel-mount TH | 1 GPIO (digital) | $0.15 | Locks in analog values (joystick, slider, encoder, etc.). |

### Passives & Misc

| # | Component | Qty | Package/Form | Interface | Est. Cost (1k+) | Notes |
|---|---|---|---|---|---|---|
| B18 | Pull-up/pull-down resistors (10kΩ) | 10+ | 0402 (SMD) | — | $0.05 total | For buttons, I2C, etc. |
| B19 | JST-PH or Molex connectors | 3–5 | Through-hole | — | $0.30 | Battery, motor, speaker connections. |
| B20 | PCB (base, 2-layer, ~100×80mm est.) | 1 | FR4 | — | $1.50 | JLCPCB pricing at volume. Actual size TBD by layout. |

### Base Tablet Subtotal

| Category | Est. Cost |
|---|---|
| MCU & Power | ~$4.85 |
| Displays | ~$9.75 |
| Feedback | ~$0.61 |
| Shared Inputs | ~$1.35 |
| Passives & PCB | ~$1.85 |
| **Base Total** | **~$18.41** |

> **Note:** Displays are the dominant cost driver (~54% of base BOM). Sourcing OLEDs and the TFT command screen at better volume pricing or consolidating to fewer/smaller displays would have the biggest impact on COGS.

---

## Archetype-Specific BOMs

Each archetype adds its unique 5-slot control loadout to the base tablet. See [tablet-archetypes.md § Archetype Definitions](../../docs/tablet-archetypes.md#archetype-definitions) for full interface specs, GPIO counts, and gameplay descriptions.

### 1. Navigator

> Slots: Analog Joystick · Linear Slider (45mm) · Toggle · Toggle · Momentary Pushbutton
>
> Additional GPIO: 3 ADC + 5 digital = **8 pins**

| # | Component | Qty | Slot | Interface | Est. Cost (1k+) | Notes |
|---|---|---|---|---|---|---|
| N1 | Analog Joystick (PSP/thumbstick, 2-axis + click) | 1 | 1 (sig) | 2× ADC + 1 GPIO | $0.80 | X/Y require Submit to lock in. Click is separate digital. |
| N2 | Linear Slide Potentiometer (45mm, 10kΩ) | 1 | 2 (med) | 1 ADC | $0.40 | T2 throttle control. Shorter than Engineer's 60mm. |
| N3 | Toggle Switch (SPDT, mini) | 2 | 3, 4 | 2 GPIO | $0.40 | Standard toggles. |
| N4 | Momentary Pushbutton (12mm, tactile) | 1 | 5 | 1 GPIO | $0.10 | Quick-confirm action. |
| | **Navigator Controls Total** | | | | **$1.70** | |

**Navigator Total COGS: ~$19.71**

---

### 2. Engineer

> Slots: Linear Slider (60mm) · Illuminated Arcade Button · Toggle · Toggle · Toggle
>
> Additional GPIO: 1 ADC + 5 digital = **6 pins**

| # | Component | Qty | Slot | Interface | Est. Cost (1k+) | Notes |
|---|---|---|---|---|---|---|
| E1 | Linear Slide Potentiometer (60mm, 10kΩ) | 1 | 1 (sig) | 1 ADC | $0.50 | Requires Submit to lock in value. |
| E2 | Illuminated Arcade Button (24mm, LED) | 1 | 2 (med) | 2 GPIO (switch + LED) | $0.80 | LED controlled by Hub via HAPTIC message. |
| E3 | Toggle Switch (SPDT, mini) | 3 | 3, 4, 5 | 3 GPIO | $0.60 | All three are simple toggles. |
| | **Engineer Controls Total** | | | | **$1.90** | |

**Engineer Total COGS: ~$19.91**

---

### 3. Operator

> Slots: Rotary Encoder · Covered Safety Toggle · Toggle · Momentary · Momentary
>
> Additional GPIO: 7 digital = **7 pins**

| # | Component | Qty | Slot | Interface | Est. Cost (1k+) | Notes |
|---|---|---|---|---|---|---|
| O1 | Rotary Encoder (EC11, infinite scroll + click) | 1 | 1 (sig) | 2 GPIO (A, B) + 1 GPIO (btn) | $0.40 | Scroll requires Submit. Click is separate BUTTON event. |
| O2 | Covered Safety Toggle (with flip guard) | 1 | 2 (med) | 1 GPIO | $0.60 | Dramatic "open cover, flip switch" feel. |
| O3 | Toggle Switch (SPDT, mini) | 1 | 3 | 1 GPIO | $0.20 | |
| O4 | Momentary Pushbutton (12mm, tactile) | 2 | 4, 5 | 2 GPIO | $0.20 | Quick send/receive/confirm. |
| | **Operator Controls Total** | | | | **$1.40** | |

**Operator Total COGS: ~$19.41**

---

### 4. Sentinel

> Slots: NFC/RFID Scanner (RC522) · 3-Position Rotary Switch · Toggle · Toggle · Momentary
>
> Additional GPIO: 1 ADC + 7 digital = **8 pins** (NFC shares SPI bus with command screen)

| # | Component | Qty | Slot | Interface | Est. Cost (1k+) | Notes |
|---|---|---|---|---|---|---|
| S1 | RC522 NFC/RFID Module | 1 | 1 (sig) | SPI (shared bus) + CS + IRQ | $1.50 | Shares SPI with command screen. Most expensive signature control. |
| S2 | 3-Position Rotary Switch | 1 | 2 (med) | 1 ADC (resistor ladder) | $0.50 | Discrete positions; no Submit needed. |
| S3 | Toggle Switch (SPDT, mini) | 2 | 3, 4 | 2 GPIO | $0.40 | |
| S4 | Momentary Pushbutton (12mm, tactile) | 1 | 5 | 1 GPIO | $0.10 | |
| S5 | Resistor ladder (3× precision resistors) | 1 set | — | — | $0.03 | For rotary switch ADC reading. |
| | **Sentinel Controls Total** | | | | **$2.53** | |

**Sentinel Total COGS: ~$20.54**

> **Note:** The Sentinel also requires NFC "item cards" (clearance badges, key cards) included in game packs — see pack BOM, not tablet BOM.

---

### 5. Medic

> Slots: Color-Match Dial (pot + RGB LED) · Rotary Encoder (small) · Toggle · Momentary · Momentary
>
> Additional GPIO: 1 ADC + 7 digital = **8 pins**

| # | Component | Qty | Slot | Interface | Est. Cost (1k+) | Notes |
|---|---|---|---|---|---|---|
| M1 | Potentiometer (10kΩ, panel-mount) | 1 | 1 (sig) | 1 ADC | $0.20 | Sweeps through hue spectrum. |
| M2 | WS2812B NeoPixel (RGB feedback LED) | 1 | 1 (sig) | 1 GPIO (data) | $0.08 | Shows current color. Player matches target hue, then Submit. |
| M3 | Rotary Encoder (EC11, small knob) | 1 | 2 (med) | 2 GPIO (A, B) + 1 GPIO (btn) | $0.40 | Smaller knob than Operator's to differentiate feel. |
| M4 | Toggle Switch (SPDT, mini) | 1 | 3 | 1 GPIO | $0.20 | |
| M5 | Momentary Pushbutton (12mm, tactile) | 2 | 4, 5 | 2 GPIO | $0.20 | |
| | **Medic Controls Total** | | | | **$1.08** | |

**Medic Total COGS: ~$19.09**

---

### 6. Analyst

> Slots: 4-Button Keypad · LED Wave Dial (small, 4-LED bar) · Toggle · Toggle · Momentary
>
> Additional GPIO: 1 ADC + 10 digital = **11 pins** (highest GPIO usage)

| # | Component | Qty | Slot | Interface | Est. Cost (1k+) | Notes |
|---|---|---|---|---|---|---|
| A1 | Tactile Buttons (12mm, with number caps 1–4) | 4 | 1 (sig) | 4 GPIO | $0.30 | Player enters multi-digit codes, then Submit. |
| A2 | Potentiometer (10kΩ, panel-mount) | 1 | 2 (med) | 1 ADC | $0.20 | Wave dial position input. |
| A3 | WS2812B NeoPixel Stick (4-LED bar) | 1 | 2 (med) | 1 GPIO (data) | $0.60 | Shows wave position as LED bar graph. |
| A4 | Toggle Switch (SPDT, mini) | 2 | 3, 4 | 2 GPIO | $0.40 | |
| A5 | Momentary Pushbutton (12mm, tactile) | 1 | 5 | 1 GPIO | $0.10 | |
| | **Analyst Controls Total** | | | | **$1.60** | |

**Analyst Total COGS: ~$19.61**

---

### 7. Scout

> Slots: LED Wave Dial (pot + NeoPixel ring) · Covered Safety Toggle · Toggle · Toggle · Toggle
>
> Additional GPIO: 1 ADC + 5 digital = **6 pins**

| # | Component | Qty | Slot | Interface | Est. Cost (1k+) | Notes |
|---|---|---|---|---|---|---|
| R1 | Potentiometer (10kΩ, panel-mount) | 1 | 1 (sig) | 1 ADC | $0.20 | Sweeps scanner position. |
| R2 | WS2812B NeoPixel Ring (8-LED) | 1 | 1 (sig) | 1 GPIO (data) | $1.00 | Ring shows sweep point — satisfying visual feedback. Cost driver. |
| R3 | Covered Safety Toggle (with flip guard) | 1 | 2 (med) | 1 GPIO | $0.60 | Stealth mode / active scan override. |
| R4 | Toggle Switch (SPDT, mini) | 3 | 3, 4, 5 | 3 GPIO | $0.60 | Scan sectors and detection filters. |
| | **Scout Controls Total** | | | | **$2.40** | |

**Scout Total COGS: ~$20.41**

---

### 8. Commander

> Slots: Multi-Position Rotary Switch (6-pos) · Illuminated Arcade Button · Toggle · Momentary · Momentary
>
> Additional GPIO: 1 ADC + 5 digital = **6 pins**

| # | Component | Qty | Slot | Interface | Est. Cost (1k+) | Notes |
|---|---|---|---|---|---|---|
| C1 | 6-Position Rotary Switch (SP6T) | 1 | 1 (sig) | 1 ADC (resistor ladder) | $0.70 | Chunky selector knob. No Submit — position is discrete. |
| C2 | Illuminated Arcade Button (24mm, LED) | 1 | 2 (med) | 2 GPIO (switch + LED) | $0.80 | Big authority action button. LED controlled by Hub. |
| C3 | Toggle Switch (SPDT, mini) | 1 | 3 | 1 GPIO | $0.20 | |
| C4 | Momentary Pushbutton (12mm, tactile) | 2 | 4, 5 | 2 GPIO | $0.20 | |
| C5 | Resistor ladder (6× precision resistors) | 1 set | — | — | $0.05 | For rotary switch ADC reading. |
| | **Commander Controls Total** | | | | **$1.95** | |

**Commander Total COGS: ~$19.96**

---

## Consolidated Cost Summary

| Archetype | Base BOM | Controls BOM | **Total COGS** | Notes |
|---|---|---|---|---|
| Navigator | $18.41 | $1.70 | **$20.11** | |
| Engineer | $18.41 | $1.90 | **$20.31** | |
| Operator | $18.41 | $1.40 | **$19.81** | Cheapest build |
| Sentinel | $18.41 | $2.53 | **$20.94** | NFC module is cost driver |
| Medic | $18.41 | $1.08 | **$19.49** | |
| Analyst | $18.41 | $1.60 | **$20.01** | Highest GPIO usage (11 pins) |
| Scout | $18.41 | $2.40 | **$20.81** | NeoPixel ring is cost driver |
| Commander | $18.41 | $1.95 | **$20.36** | |
| | | **Average** | **$20.23** | Slightly above $20 target — display sourcing is key lever |

> **Critical cost driver:** The 5× OLED displays ($6.25) and TFT command screen ($2.50) together represent ~$8.75 or ~44% of total COGS. Negotiating volume pricing on displays has the highest impact.

---

## Supplier Notes

### Preferred Sourcing (1,000+ units)

| Component Category | Recommended Source | Notes |
|---|---|---|
| ESP32-S3 modules | LCSC / Espressif direct | JLCPCB assembly supports LCSC parts natively |
| OLEDs (SSD1306/SH1106) | LCSC or Alibaba module suppliers | Volume pricing critical — negotiate per-1k |
| TFT Command Screen | LCSC or Alibaba | ILI9341 or ST7789 modules |
| Passive components | LCSC | Standard 0402/0603 from JLCPCB Basic Parts |
| Toggle switches | LCSC or Alibaba | MTS-102 or equivalent |
| Mushroom button | Alibaba | 16mm red latching, panel-mount |
| NeoPixel (WS2812B) | LCSC | Individual LEDs for SMD placement |
| NeoPixel ring (8-LED) | Alibaba | Scout only — pre-assembled ring module |
| RC522 NFC module | LCSC or Alibaba | Sentinel only |
| Potentiometers & sliders | LCSC or Alibaba | Panel-mount for through-hole |
| Rotary encoders (EC11) | LCSC | Through-hole, 20-detent preferred |
| Arcade buttons (24mm) | Alibaba | Engineer & Commander — illuminated, LED included |
| Covered safety toggles | Alibaba | Operator & Scout — with flip guard |
| Battery sleds | Alibaba | 2× AA, spring contact |

### JLCPCB Assembly Strategy

- **SMD components** (MCU, passives, MOSFET, mux, boost converter, NeoPixel LEDs): Place on base PCB for JLCPCB SMT assembly.
- **Through-hole controls** (joystick, sliders, toggles, buttons, encoders, rotary switches): Hand-soldered or on small daughter boards. These are panel-mounted in the enclosure and wired to the main PCB via headers/connectors.
- **Modules** (OLEDs, TFT, RC522, NeoPixel ring): Connected via ribbon cables, FPC, or pin headers. Consider dedicated OLED mounting positions on an enclosure-specific carrier board.
