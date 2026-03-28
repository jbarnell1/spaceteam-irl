# PCB Design Brief — Spaceteam IRL Central Hub

> **Purpose:** This document gives a PCB designer everything needed to lay out the Central Hub board. The Hub is the game master — it plays narrator audio, reads NFC game cards, and coordinates up to 8 Player Tablets over ESP-NOW.
>
> **Key references (read these first):**
> - [hardware/bom/hub-bom.md](../bom/hub-bom.md) — Complete Hub bill of materials
> - [README.md § The Central Hub](../../README.md#b-the-central-hub) — Component overview
> - [docs/protocol.md](../../docs/protocol.md) — ESP-NOW transport, session management, multi-hub isolation
> - [docs/game-loop.md](../../docs/game-loop.md) — Phase-by-phase Hub behavior
> - [hardware/pcb/pcb-design-brief.md](pcb-design-brief.md) — Tablet PCB brief (for shared conventions)

---

## Table of Contents

- [Project Context](#project-context)
- [Board Strategy](#board-strategy)
- [MCU & Antenna](#mcu--antenna)
- [Power Supply](#power-supply)
- [Audio Circuit](#audio-circuit)
- [SPI Bus Architecture](#spi-bus-architecture)
- [NFC Reader](#nfc-reader)
- [Display & Interaction](#display--interaction)
- [GPIO Pin Allocation](#gpio-pin-allocation)
- [V2 HDMI Expansion](#v2-hdmi-expansion)
- [Physical Constraints](#physical-constraints)
- [Design-for-Manufacturing Notes](#design-for-manufacturing-notes)
- [Deliverables](#deliverables)

---

## Project Context

The Central Hub sits at the center of the play area. Players place an NFC game card on top of it to load a scenario, then the Hub runs the entire game — dispatching commands to tablets, playing narrator audio through its speaker, and tracking score/health. It communicates with up to 8 Player Tablets over ESP-NOW (2.4GHz, encrypted, sub-10ms latency).

The Hub is simpler than the tablets — no joysticks, sliders, or per-slot OLEDs. It has fewer components but needs good RF performance (external antenna) and clean audio output.

**Target COGS:** ~$15 at 1,000+ units (V1 audio-only). See [hub-bom.md](../bom/hub-bom.md) for the full BOM (~$11.14 V1).

---

## Board Strategy

Unlike the tablets (which have 8 archetype variants), the Hub has a **single PCB design**. There are two product tiers:

| Tier | Description | Board Approach |
|---|---|---|
| **V1 (Audio Hub)** | ESP32-S3 + speaker + NFC + button + 7-segment | Single PCB, all SMD on one side |
| **V2 (Visual Hub)** | V1 + HDMI output for TV | V1 board + HDMI daughterboard, OR a V2-specific PCB with HDMI onboard |

**Recommendation:** Design the V1 board first. Leave a footprint/connector for a V2 HDMI daughter board (a pin header or FPC connector) so V2 can be added without re-spinning the base board.

---

## MCU & Antenna

### ESP32-S3-WROOM-1-N16R8 (External Antenna Variant)

The Hub uses the **U.FL (IPEX) antenna connector variant** of the ESP32-S3-WROOM-1 module, NOT the PCB antenna variant used on tablets. This is because the Hub needs range across large rooms, forts, and play areas.

- **Module:** ESP32-S3-WROOM-1-N16R8 (U.FL variant)
- **Antenna:** External 2.4GHz antenna connected via U.FL cable
- Decoupling: 10µF + 100nF on 3V3 pin
- EN pin: RC circuit (10kΩ pull-up + 1µF to GND) for clean power-on reset
- GPIO0: 10kΩ pull-up (boot mode select)
- USB D+/D−: Route to USB-C connector for firmware flashing and optional power input

**Key difference from tablet:** No antenna keepout zone needed on PCB (antenna is external). The U.FL connector pigtail routes to an antenna mounted on the outside of the enclosure.

---

## Power Supply

The Hub supports **two power sources** with automatic switching:

### Source 1: 4× AA Batteries (Portable Play)

```
4× AA (6.0V nom, 4.8V min) → Buck Regulator (AP2112K-3.3) → 3.3V rail
```

- **AP2112K-3.3TRG1** (SOT-23-5): 600mA LDO, low dropout (~250mV). Input range 2.5V–6.5V.
- 4× AA provides ~6V nominal — well within input range.
- Alternatively, use a more efficient buck converter (e.g., TLV62569) for longer battery life. LDO is simpler but wastes ~45% of battery energy as heat at 6V→3.3V.
- Battery connector: JST-PH 2-pin, keyed. Add reverse-polarity protection (Schottky diode or P-MOSFET).
- Estimated current draw: ~200–350mA average (ESP32-S3 WiFi/ESP-NOW + amplifier + NFC). Runtime: ~6–10 hours on quality alkaline AAs.

### Source 2: USB-C (Stationary Play)

```
USB-C 5V → Same regulator path → 3.3V rail
```

- USB-C connector: 6-pin (power-only, CC resistors for 5V default) or 16-pin (USB 2.0 data for firmware updates).
- CC1/CC2: 5.1kΩ pull-down resistors to GND (required by USB-C spec to request 5V).
- Route USB D+/D− to ESP32-S3 USB pins for firmware flashing (development use).

### Power Path OR-ing

- Use a pair of Schottky diodes or an ideal diode IC to auto-select the higher-voltage source.
- When USB-C is connected, it powers the board and batteries are disconnected (no charging — AAs are not rechargeable).
- Add a power indicator LED (green, via 1kΩ series resistor) near the power switch.

### Power Switch

SPST slide switch inline with battery positive. Place at board edge for enclosure access. USB-C power bypasses the switch (always-on when plugged in), or route through switch if desired.

---

## Audio Circuit

### PAM8403 Class-D Amplifier

```
ESP32-S3 (I2S or DAC/PWM) → RC low-pass filter → PAM8403 input → 3W Speaker
```

- **PAM8403** (SOP-16): Filterless Class-D, 3W per channel into 4Ω. Use single channel (mono).
- **Input options:**
  - **Option A (simple):** ESP32-S3 DAC output (GPIO17/GPIO18) → RC filter (10kΩ + 100nF) → PAM8403 analog input. Simplest, adequate quality for voice narration.
  - **Option B (better):** ESP32-S3 I2S output → external I2S DAC (e.g., MAX98357A) → speaker directly. Better audio quality, one IC does both DAC and amp. Consider this if narrator voice quality is a priority.
- **Speaker connector:** 2-pin JST-PH or solder pads. Keep amp-to-speaker traces short and wide (high-current AC path).
- **Volume control:** Software-controlled via ESP32-S3 (I2S gain or PWM duty). No hardware pot needed.
- **Shutdown pin:** PAM8403 has a shutdown pin — tie to a GPIO so the Hub can mute the amp when not playing audio (saves ~10mA quiescent).

### Layout Notes

- Place PAM8403 close to speaker connector (short output traces).
- Separate analog input traces from digital lines (SPI, NeoPixel). Run analog on opposite side of board or with ground guard traces.
- Bulk capacitor (100µF) on PAM8403 VCC pin to handle current spikes.

---

## SPI Bus Architecture

The Hub shares a single SPI bus across two peripherals:

```
ESP32-S3 SPI Bus (HSPI)
  MOSI ──┬── W25N01GV SPI NAND Flash
  MISO ──┤      CS_NAND (GPIO)
  SCK  ──┤
         └── PN532 NFC Reader
                CS_NFC (GPIO)
                IRQ_NFC (GPIO, input)
```

- Both devices share MOSI, MISO, SCK. Each has its own chip select (CS) line.
- SPI clock: 104MHz max for W25N01GV (use 40–80MHz). 5MHz max for PN532 in SPI mode.
- **Important:** Set SPI clock to the NFC reader's max (5MHz) when talking to NFC, then switch back to high speed for NAND flash. Or use two SPI buses if the ESP32-S3 pin budget allows (HSPI for flash, VSPI for NFC).
- W25N01GV uses standard SPI (Mode 0). PN532 also supports SPI Mode 0.

### NAND Flash Layout

- Place W25N01GV close to ESP32-S3 for short SPI traces.
- Decoupling: 100nF on VCC pin.
- WP# (write protect) and HOLD# pins: tie to VCC via 10kΩ pull-up.

---

## NFC Reader

### PN532 Module (Prototype) / Bare IC (Production)

The Hub's NFC reader sits under the top surface of the enclosure. Players place NFC game cards flat on top of the Hub.

**Prototype approach:** Use a PN532 breakout module connected via pin header. Module has onboard antenna.

**Production approach:** Place bare PN532 IC (QFP-32) on PCB with a **13.56MHz PCB trace antenna** on the top copper layer. This eliminates the module cost and bulk.

### PCB Antenna Design (Production)

- **Frequency:** 13.56 MHz (ISO 14443A)
- **Antenna:** Rectangular loop, ~40×30mm, on top copper layer. Follow NXP AN1445 or PN532 application note for trace geometry.
- **Keepout:** No copper pour or other traces inside the antenna loop. Ground plane below antenna should have a cutout (window) matching the loop area.
- **Tuning:** Series capacitor + parallel capacitor to tune resonance to 13.56MHz. Values depend on loop inductance — measure on prototype and adjust.
- **Read range:** Target ~3–5cm (adequate for placing a card flat on the Hub enclosure lid).

### Connection

| Pin | GPIO | Notes |
|---|---|---|
| CS | GPIO (output) | Active low |
| IRQ | GPIO (input) | Interrupt when card detected. Pull-up. |
| RSTPDN | GPIO (output) | Hardware reset (optional — can tie high) |
| MOSI/MISO/SCK | Shared SPI bus | See SPI Bus Architecture above |

---

## Display & Interaction

### 7-Segment Display (TM1637)

- Same part as tablets — shared SKU.
- Displays the 4-character session ID (e.g., `K7X2`) that players use to verify they're connecting to the right Hub.
- Connection: 4-pin header (VCC, GND, CLK, DIO). Two GPIO lines.
- Place connector at board edge so the display module can mount flush to the enclosure panel.

### Illuminated Pushbutton (16mm)

- Initiates pairing mode when pressed. LED controlled by Hub firmware.
- LED states: steady glow = idle/ready, pulsing = pairing mode active, off = game in progress.
- Connection: 3-pin header (SIG, LED, GND).
  - SIG: GPIO input, 10kΩ pull-up, active low.
  - LED: GPIO output (directly or via small MOSFET if LED current > 12mA).

### Status LED (WS2812B NeoPixel)

- SMD on PCB. Same component as tablets.
- Hub status: white=booting, blue=pairing, green=ready/in-game, red=error, amber=WiFi downloading.
- 470Ω series resistor on data line, 100nF bypass cap.

---

## GPIO Pin Allocation

Total available on ESP32-S3: ~36 usable GPIO.

| Function | Pins | Notes |
|---|---|---|
| SPI (MOSI, MISO, SCK) | 3 | Shared bus: NAND flash + NFC reader |
| NAND Flash CS | 1 | W25N01GV chip select |
| NFC CS | 1 | PN532 chip select |
| NFC IRQ | 1 | Card-detected interrupt (input) |
| NFC RST | 1 | Optional hardware reset (can tie high to save a pin) |
| TM1637 (CLK, DIO) | 2 | 7-segment session ID display |
| Pairing Button (switch) | 1 | Input, pull-up |
| Pairing Button (LED) | 1 | Output |
| NeoPixel Status LED | 1 | WS2812B data |
| Audio Output (DAC/PWM or I2S) | 1–3 | 1 pin for DAC/PWM, or 3 for I2S (BCLK, LRCLK, DATA) |
| PAM8403 Shutdown | 1 | Amp mute control |
| USB D+/D− | 2 | Firmware flashing (shared with USB-C connector) |
| **Total** | **~16–18** | |

> **Headroom:** Only ~16–18 of ~36 GPIO used. This leaves plenty of room for V2 HDMI (needs ~8–12 additional pins for parallel RGB or I2S audio to HDMI transmitter) and future expansion.

---

## V2 HDMI Expansion

V2 adds HDMI output for TV display (mission briefings, spectator scoreboard, countdown visuals). V2 is a **future revision** — design V1 first but plan for it.

### Approach

| Option | Description | Pros | Cons |
|---|---|---|---|
| **Daughterboard** | V1 base PCB + HDMI daughter via pin header/FPC | No V1 re-spin. Modular. | Inter-board connector cost. Slightly bulkier. |
| **V2-specific PCB** | New base PCB with HDMI onboard | Cleaner layout. Better signal integrity for HDMI. | Separate board design to maintain. |

**Recommendation:** Design V1 with a 2×10 (20-pin) expansion header breaking out: 3.3V, GND, I2C (SDA/SCL), I2S (BCLK, LRCLK, DATA), and 8–10 spare GPIO. This lets a V2 daughterboard connect an HDMI transmitter IC without any V1 board changes.

### HDMI IC Options

| IC | Interface | Resolution | Notes |
|---|---|---|---|
| CH7035B | Parallel RGB → HDMI | Up to 1080p | Common, cheap. Needs many GPIO for parallel RGB (not ideal for ESP32-S3). |
| SiI9022A | I2S audio + parallel RGB → HDMI | Up to 720p | I2C control, I2S audio input. Same parallel RGB problem. |
| LT8618SXB | Parallel RGB or BT.656 → HDMI | Up to 1080p | Supports 8-bit BT.656 (fewer pins than full RGB). |

> **Challenge:** The ESP32-S3 has no native parallel RGB output or HDMI. A framebuffer-over-SPI approach (render to RAM, push via SPI to HDMI IC) may work for simple display content (scoreboard, briefing text) but won't do video. Evaluate feasibility during V1 firmware development.

---

## Physical Constraints

| Parameter | Value | Notes |
|---|---|---|
| Enclosure | Custom 3D-printed PLA (prototype) | Larger than tablet — needs room for speaker + battery sled |
| PCB dimensions | ~80×60mm (estimated) | Smaller than tablet PCB (fewer components) |
| Board thickness | 1.6mm standard | JLCPCB default |
| Layers | 2-layer | 2-layer sufficient — lower component density than tablet |
| Mounting | M3 standoffs (4 corners) | Include M3 mounting holes |
| NFC read surface | Top of enclosure | Enclosure lid must be thin/non-metallic over NFC antenna area. No metal near antenna. |
| Speaker | Bottom or side-firing | Speaker grille cutout in enclosure. Place speaker connector near board edge. |
| 7-Segment display | Front panel | Display module mounts flush to enclosure via cutout |
| Pairing button | Top or front panel | Panel-mount, wired to PCB header |
| Battery sled | Internal compartment | Bottom-access battery door in enclosure |
| USB-C | Side edge | Board-edge mount for cable access |
| External antenna | Rear/top of enclosure | U.FL pigtail from PCB to antenna mounted externally |

---

## Design-for-Manufacturing Notes

### JLCPCB-Specific

1. **Use LCSC part numbers** for all SMD components.
2. **Basic parts preferred:** PAM8403, passives, NeoPixel, regulator are likely Basic. ESP32-S3 module, W25N01GV NAND, and PN532 are likely Extended.
3. **Single-side SMD:** All SMD on top side for lowest assembly cost.
4. **NFC antenna (production):** If using PCB trace antenna, it goes on the top copper layer with a ground plane cutout below. Discuss this with the fabrication house — it's non-standard routing.
5. **Minimum order:** 5 boards for prototype.

### General

- **Silkscreen:** Label all connectors (BATT, SPK, NFC, BTN, 7SEG, USB, ANT, EXPANSION). Mark pin 1 on all headers.
- **Test points:** Add labeled test points for 3.3V, GND, MOSI, MISO, SCK, SDA (if I2C used), audio output, and 2 spare GPIO.
- **Grounding:** Solid ground plane on bottom layer.
- **Audio trace routing:** Keep analog audio traces away from SPI bus and NeoPixel data lines. Guard with ground traces if routing near digital signals.
- **NFC antenna keepout:** No ground pour, no traces, no copper within the antenna loop area. This is critical for read range.

---

## Deliverables

| Deliverable | Format | Notes |
|---|---|---|
| Schematic | EasyEDA Pro project (or PDF) | Full V1 Hub circuit + expansion header for V2 |
| PCB Layout | EasyEDA Pro project | Gerber-ready V1 board |
| BOM (assembly) | CSV with LCSC part numbers | JLCPCB assembly-ready format |
| Pick-and-Place file | CSV (JLCPCB format) | Component placement for SMT assembly |
| 3D model (optional) | STEP export | For checking enclosure fit |
| NFC antenna notes | Markdown or PDF | If using PCB trace antenna: loop dimensions, tuning component values, ground plane cutout geometry |

### Design Priority

1. **Power circuit first.** Get 4×AA → 3.3V and USB-C → 3.3V working with auto-switching. Everything depends on clean power.
2. **ESP32-S3 + SPI NAND flash.** Verify firmware can read/write audio from W25N01GV.
3. **Audio output.** PAM8403 + speaker — verify narrator playback quality.
4. **NFC reader.** Card detection and read. Start with module, migrate to bare IC + PCB antenna later.
5. **Display + button + status LED.** Simplest components — last because lowest risk.
