# Central Hub Bill of Materials

> **Version:** 0.1.0 (Draft)
>
> Complete BOM for the Spaceteam IRL Central Hub. The Hub is the game master device — it owns all game state, plays narrator audio, reads NFC game cards, and communicates with up to 8 Player Tablets over ESP-NOW.
>
> **References:**
> - [README.md § The Central Hub](../../README.md#b-the-central-hub) for component overview
> - [docs/protocol.md](../../docs/protocol.md) for ESP-NOW transport and session management
> - [docs/game-loop.md](../../docs/game-loop.md) for phase-by-phase Hub behavior
> - [docs/pack-strategy.md](../../docs/pack-strategy.md) for pack contents and COGS targets

---

## Table of Contents

- [Design Targets](#design-targets)
- [Hub BOM](#hub-bom)
- [V2 Add-On (HDMI Visual Hub)](#v2-add-on-hdmi-visual-hub)
- [Cost Summary](#cost-summary)
- [Supplier Notes](#supplier-notes)

---

## Design Targets

| Parameter | Target |
|---|---|
| **Target COGS** | ~$15 at 1,000+ units |
| **MCU** | ESP32-S3-WROOM-1-N16R8 (16MB flash, 8MB PSRAM) with external antenna |
| **Power** | 4× AA batteries (~6V) with buck regulator to 3.3V, or USB-C wall power |
| **Connectivity** | ESP-NOW (up to 8 tablets) + WiFi (content downloads) |
| **Audio** | PAM8403 Class-D amplifier + 3W speaker (narrator voice) |
| **Storage** | 16MB internal flash (scenario JSON) + 128MB SPI NAND (narrator audio) |
| **Assembly** | JLCPCB SMT assembly; speaker, button, battery sled wired |
| **PCB Tool** | EasyEDA Pro |

---

## Hub BOM

### MCU & Power

| # | Component | Qty | Package/Form | Interface | Est. Cost (1k+) | Notes |
|---|---|---|---|---|---|---|
| H1 | ESP32-S3-WROOM-1-N16R8 (external antenna variant) | 1 | Module (SMD) | — | $3.80 | 16MB flash, 8MB PSRAM. External antenna for range across large rooms. U.FL connector on module. |
| H2 | 2.4GHz External Antenna (IPEX/U.FL) | 1 | Cable + antenna | — | $0.30 | Stick or PCB-type antenna. Mount on enclosure exterior. |
| H3 | Buck Regulator (AP2112K-3.3 or similar) | 1 | SOT-23-5 (SMD) | — | $0.15 | 6V (4×AA) → 3.3V. Low dropout, 600mA output. |
| H4 | 4× AA Battery Sled | 1 | Wired | — | $0.50 | Spring-contact sled, chassis-mount. 6V nominal. |
| H5 | USB-C Connector (power input, optional) | 1 | SMD | — | $0.20 | 5V wall-power alternative to batteries. Add 3.3V LDO or share H3 regulator. |
| H6 | Power Switch (SPST slide) | 1 | Through-hole | Inline | $0.10 | Board edge for enclosure access. |
| H7 | Power Path / OR-ing Circuit | 1 | SOT-23 (SMD) | — | $0.10 | Ideal diode or Schottky OR: auto-select between USB-C and battery. Prevents backfeed. |
| H8 | Decoupling Caps (10µF + 100nF) | 3 sets | 0402/0603 (SMD) | — | $0.05 | Per ESP32-S3 reference design. |
| H9 | Input Caps (100µF electrolytic) | 1 | Radial TH or SMD | — | $0.05 | Bulk capacitance on battery input rail. |

### Audio (V1)

| # | Component | Qty | Package/Form | Interface | Est. Cost (1k+) | Notes |
|---|---|---|---|---|---|---|
| H10 | PAM8403 Class-D Amplifier | 1 | SOP-16 (SMD) | I2S or analog PWM | $0.25 | 3W per channel, filterless. Single channel used. |
| H11 | Speaker (3W, 4Ω or 8Ω) | 1 | Wired | — | $0.60 | Chassis-mount. Size TBD by enclosure (~36–40mm driver). |
| H12 | Audio Output Caps + Filter | 1 set | 0603/0805 (SMD) | — | $0.05 | LC output filter if using analog PWM input. Not needed if I2S DAC is used. |

### Storage

| # | Component | Qty | Package/Form | Interface | Est. Cost (1k+) | Notes |
|---|---|---|---|---|---|---|
| H13 | W25N01GV 128MB SPI NAND Flash | 1 | WSON-8 (SMD) | SPI | $1.20 | Permanent narrator audio cache. Shared SPI bus with NFC reader. |

### NFC Reader

| # | Component | Qty | Package/Form | Interface | Est. Cost (1k+) | Notes |
|---|---|---|---|---|---|---|
| H14 | PN532 NFC/RFID Module (or RC522) | 1 | Module / breakout | SPI (shared bus) + IRQ | $1.50 | Reads game NFC cards (NTAG213/215). PN532 preferred for broader tag support and I2C fallback. |
| H15 | NFC Antenna (if bare IC) | 1 | PCB trace antenna or coil | — | $0.00 | Included on module. If bare PN532 IC, requires tuned 13.56MHz loop antenna on PCB. |

### Display & Interaction

| # | Component | Qty | Package/Form | Interface | Est. Cost (1k+) | Notes |
|---|---|---|---|---|---|---|
| H16 | 7-Segment Display (TM1637, 4-digit) | 1 | Module | 2-wire (CLK + DIO) | $0.40 | Displays 4-character session ID (e.g., `K7X2`). |
| H17 | Illuminated Pushbutton (16mm) | 1 | Panel-mount TH | 2 GPIO (switch + LED) | $0.50 | Initiates pairing mode. LED states: steady=idle, pulsing=pairing, off=in-game. |

### Status & Feedback

| # | Component | Qty | Package/Form | Interface | Est. Cost (1k+) | Notes |
|---|---|---|---|---|---|---|
| H18 | WS2812B NeoPixel (status LED) | 1 | 5050 SMD | 1-wire data | $0.08 | Hub status indicator: white=booting, blue=pairing, green=ready, red=error. |
| H19 | NeoPixel Data Resistor (470Ω) | 1 | 0402 (SMD) | — | $0.01 | Series resistor on NeoPixel data line. |

### Passives & Connectors

| # | Component | Qty | Package/Form | Interface | Est. Cost (1k+) | Notes |
|---|---|---|---|---|---|---|
| H20 | Pull-up/pull-down resistors (10kΩ) | 5+ | 0402 (SMD) | — | $0.03 | EN pin, button, etc. |
| H21 | Boot/Reset RC (10kΩ + 1µF) | 1 set | 0402 (SMD) | — | $0.02 | EN pin power-on reset circuit. |
| H22 | JST-PH connectors | 3–4 | Through-hole | — | $0.25 | Battery, speaker, antenna connections. |
| H23 | PCB (2-layer, ~80×60mm est.) | 1 | FR4 | — | $1.00 | JLCPCB pricing at volume. Smaller than tablet (fewer controls). |

---

## V2 Add-On (HDMI Visual Hub)

V2 adds HDMI output for optional TV hookup (mission briefings, spectator view). V2 Hubs are backward-compatible with all V1 tablets. This can be a separate daughter board or a V2-specific base PCB.

| # | Component | Qty | Package/Form | Interface | Est. Cost (1k+) | Notes |
|---|---|---|---|---|---|---|
| V1 | HDMI Connector (Type A, female) | 1 | SMD or TH | — | $0.30 | Standard 19-pin. Panel-mount or board-edge. |
| V2 | HDMI Transmitter IC (e.g., CH7035B or SiI9022A) | 1 | QFP/QFN (SMD) | RGB/I2S → HDMI | $2.50 | Converts parallel RGB or SPI framebuffer to HDMI. ESP32-S3 has no native HDMI — needs external IC. |
| V3 | HDMI ESD Protection (HDMI_DP0-3 TVS array) | 1 | SOT-23-6 (SMD) | — | $0.10 | Standard HDMI protection. Required for certification. |
| V4 | Supporting passives (caps, pull-ups, crystal) | 1 set | 0402/0603 (SMD) | — | $0.20 | Per transmitter IC datasheet. |

| | |
|---|---|
| **V2 Add-On Subtotal** | **~$3.10** |

> **Note:** V2 is optional. Prototype with V1 (audio-only) first. HDMI adds significant layout complexity and firmware effort. Consider it a future revision.

---

## Cost Summary

### V1 Hub (Audio Only)

| Category | Est. Cost |
|---|---|
| MCU & Power (H1–H9) | ~$5.25 |
| Audio (H10–H12) | ~$0.90 |
| Storage (H13) | ~$1.20 |
| NFC Reader (H14–H15) | ~$1.50 |
| Display & Interaction (H16–H17) | ~$0.90 |
| Status & Feedback (H18–H19) | ~$0.09 |
| Passives & PCB (H20–H23) | ~$1.30 |
| **V1 Hub Total** | **~$11.14** |

### V2 Hub (Audio + HDMI)

| | |
|---|---|
| V1 Hub Total | ~$11.14 |
| V2 HDMI Add-On | ~$3.10 |
| **V2 Hub Total** | **~$14.24** |

> Both variants are well within the ~$15 COGS target from [pack-strategy.md](../../docs/pack-strategy.md). The V1 Hub has comfortable margin (~$4) for enclosure, packaging, and assembly overhead.

---

## Supplier Notes

### Preferred Sourcing (1,000+ units)

| Component Category | Recommended Source | Notes |
|---|---|---|
| ESP32-S3 module (ext. antenna) | LCSC / Espressif direct | U.FL variant. JLCPCB assembly compatible. |
| W25N01GV SPI NAND | LCSC / Winbond direct | WSON-8 package. Verify LCSC stock before committing. |
| PAM8403 amplifier | LCSC | Very common, Basic part likely. |
| PN532 NFC module | LCSC or Alibaba | Module with onboard antenna preferred for prototype. Bare IC for production (PCB antenna). |
| 3W speaker | Alibaba | Chassis-mount, 36–40mm, 4Ω or 8Ω. |
| TM1637 7-segment | LCSC | Same as tablet — shared part number reduces SKU count. |
| Illuminated pushbutton | Alibaba or LCSC | 16mm, LED, momentary. |
| USB-C connector | LCSC | 6-pin (power-only) or 16-pin (USB 2.0 data for future firmware updates). |
| Passive components | LCSC | Standard 0402/0603 from JLCPCB Basic Parts. |
| HDMI transmitter (V2 only) | LCSC or Mouser | Less common part — verify JLCPCB Extended availability. |

### Assembly Strategy

- **SMD components (all H-series except H4, H5, H6, H11, H17):** JLCPCB SMT assembly. Single-side preferred.
- **Through-hole / wired (H4, H6, H11, H17):** Hand-soldered or wired post-assembly.
  - Battery sled: JST cable to PCB.
  - Speaker: Soldered leads to PCB pads or JST connector.
  - Power switch: Wired to inline pads on PCB edge.
  - Pushbutton: Panel-mount, wired to 3-pin header (SIG, LED, GND).
- **NFC module (H14):** If using a module/breakout, connect via pin header. If using bare PN532 IC, SMD-place on main PCB with PCB trace antenna (saves cost at volume but requires RF tuning).
