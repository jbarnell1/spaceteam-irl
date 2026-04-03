# Prototype Shopping List — Full Build

> **Scope:** 1 Hub + 4 Tablets (Navigator, Engineer, Operator, Sentinel)
>
> Everything you need to go from bare PCBs to working prototypes: manufacturing tools, PCB components (SMD + through-hole), off-board parts, wiring, and assembly hardware.
>
> **Assembly approach:** JLCPCB fabricates bare PCBs + frameless stencils. You order SMD parts from LCSC and reflow at home with a hot plate + stencil. Through-hole connectors hand-soldered after reflow.
>
> **References:** [hub-bom.md](bom/hub-bom.md) · [tablet-bom.md](bom/tablet-bom.md) · [tablet-archetypes.md](../docs/tablet-archetypes.md)

---

## A. Manufacturing & Reflow Tools

> One-time purchases. These cover Hub + all Tablet builds.

| Tool | Spec | Qty | Source | Est. Price | Notes |
|---|---|---|---|---|---|
| Hot Plate | Soiiw 100×100mm, 350W, PID, 30–400°C | 1 | Amazon (B0CN19C4DC) | ~$36.00 | Reflow soldering. Fits boards up to 100mm. |
| Solder Paste | Sn63/Pb37 leaded, syringe, 50g | 1 | AliExpress | ~$5.00 | Leaded paste matches HASL finish. Store in fridge. |
| PCB Stencil (Hub) | Frameless, top-side only | 1 | JLCPCB (order with PCBs) | ~$4.00 | Ships with Hub PCB order. |
| PCB Stencil (Tablet) | Frameless, top-side only | 1 | JLCPCB (order with PCBs) | ~$4.00 | Ships with Tablet PCB order. |
| ESD Tweezers | Fine-tip, anti-static, curved + straight set | 1 set | AliExpress | ~$3.00 | For placing SMD parts on paste. |
| Flux Pen | No-clean, rosin-based | 1 | AliExpress | ~$3.00 | Helps rework and through-hole joints. |
| Solder Wick | 2.5mm desoldering braid | 1 roll | AliExpress | ~$2.00 | For fixing bridges. |
| Isopropyl Alcohol | 99% IPA, 8oz+ | 1 | Local pharmacy / Amazon | ~$5.00 | Board cleaning after reflow. |
| Magnification | USB microscope or magnifying headset | 1 | AliExpress / Amazon | ~$15.00 | Joint inspection. USB microscope preferred. |
| Squeegee | Old credit card or plastic scraper | 1 | Free | $0.00 | For paste application through stencil. |
| Kapton Tape | 10mm width, heat-resistant | 1 roll | AliExpress | ~$2.00 | Masks areas, secures stencil. |
| Soldering Iron | Any temp-controlled iron (if you don't have one) | 1 | Amazon | ~$25.00 | For through-hole parts + rework. Skip if you have one. |

---

## B. Hub PCB — JLCPCB Order

> Order PCBs + stencils from JLCPCB. Qty 5 minimum.

| Item | Spec | Qty | Est. Price | Notes |
|---|---|---|---|---|
| Hub PCB (bare) | 2-layer, ~50×60mm, 1.6mm, HASL leaded | 5 | ~$5.00 | JLCPCB minimum order. |
| Top Stencil | Frameless, laser-cut | 1 | ~$4.00 | Order with PCBs for combined shipping. |

---

## C. Hub PCB — SMD Components (LCSC Order)

> Order from LCSC. Quantities below are per-board × 5 boards + spares. LCSC has minimum order quantities — buy the minimum pack where it exceeds what you need.

| Ref | Value | LCSC # | Per Board | ×5 Boards | Package | Est. Price | Notes |
|---|---|---|---|---|---|---|---|
| ESP32S3 | ESP32-S3-WROOM-1U-N16R8 | C3013946 | 1 | 5 | Module | ~$5.50 ea / $27.50 | U.FL antenna variant. |
| U5 | AP2112K-3.3TRG1 | C23380830 | 1 | 5 | SOT-23-5 | ~$0.15 ea / $0.75 | 3.3V LDO regulator. |
| U2 | PAM8403DR-H | C17337 | 1 | 5 | SOIC-16 | ~$0.40 ea / $2.00 | Audio amplifier. |
| U3 | W25N01GVZEIT | C17656808 | 1 | 5 | WSON-8 | ~$6.00 ea / $30.00 | 128MB SPI NAND flash. |
| D1 | USBLC6-2SC6 | C2827654 | 1 | 5 | SOT-23-6 | ~$0.30 ea / $1.50 | USB ESD protection. |
| D5,D6 | 1N5819WS | C191023 | 2 | 10 | SOD-323 | ~$0.03 ea / $0.30 | Schottky diodes. |
| USB1 | TYPE-C 16PIN 2MD(073) | C2765186 | 1 | 5 | SMD | ~$0.15 ea / $0.75 | USB-C connector. |
| LED2 | WS2812B-V6 | C52917433 | 1 | 5 | 5050 | ~$0.10 ea / $0.50 | Status NeoPixel. |
| SW1,SW2 | Tact Switch 3×6×2.5mm | C49234125 | 2 | 10 | SMD | ~$0.05 ea / $0.50 | BOOT + RESET buttons. |
| C1 | 10µF | C19702 | 1 | 5 | 0603 | ~$0.01 ea / $0.05 | |
| C10 | 4.7µF | C19666 | 1 | 5 | 0603 | ~$0.01 ea / $0.05 | |
| C13–18 | 100nF | C14663 | 6 | 30 | 0603 | ~$0.003 ea / $0.10 | |
| C21,C22 | 100µF | C15008 | 2 | 10 | 1206 | ~$0.10 ea / $1.00 | Samsung ceramic. |
| C24,C25 | 1µF | C15849 | 2 | 10 | 0603 | ~$0.01 ea / $0.10 | |
| R35 | 220Ω | C22962 | 1 | 5 | 0603 | ~$0.003 ea / $0.02 | |
| R36–R47 | 10kΩ | C25804 | 12 | 60 | 0603 | ~$0.003 ea / $0.20 | |
| R48 | 470Ω | C23179 | 1 | 5 | 0603 | ~$0.003 ea / $0.02 | |
| R49,R50 | 5.1kΩ | C23186 | 2 | 10 | 0603 | ~$0.003 ea / $0.03 | USB-C CC pull-downs. |

---

## D. Hub PCB — Through-Hole Connectors (Hand-Solder After Reflow)

| Ref | Part | LCSC # | Per Board | ×5 Boards | Est. Price | Notes |
|---|---|---|---|---|---|---|
| J1,J2 | JST-PH 2-pin (S2B-PH-K-S) | C173752 | 2 | 10 | ~$0.08 ea / $0.80 | Battery + speaker. |
| J3 | JST-PH 3-pin (S3B-PH-K-S) | C157929 | 1 | 5 | ~$0.10 ea / $0.50 | Pairing button. |
| H1 | 2.54mm 4-pin header | C52016392 | 1 | 5 | ~$0.05 ea / $0.25 | TM1637 display. |
| H2 | 2.54mm 8-pin header | C32713274 | 1 | 5 | ~$0.08 ea / $0.40 | PN532 NFC module. |

---

## E. Displays & Modules

| Part | Spec | Qty | Source | Est. Price | Notes |
|---|---|---|---|---|---|
| 1.3" OLED Display | SSD1306 or SH1106, 128×64, I2C, 4-pin | 22 | AliExpress | ~$2.00 ea / $44.00 | 5 per tablet × 4 = 20. +2 spares. |
| SPI TFT Screen | 1.8", ST7789 or ILI9341, SPI | 5 | AliExpress | ~$3.50 ea / $17.50 | 1 per tablet × 4. +1 spare. |
| TM1637 7-Segment Display | 4-digit, 0.56", 2-wire module | 6 | AliExpress | ~$0.90 ea / $5.40 | 1 Hub + 4 tablets. +1 spare. |
| PN532 NFC Module | Breakout board w/ onboard antenna, SPI + I2C | 1 | AliExpress | ~$4.00 | Hub only. Module version for prototype. |

---

## F. Controls — Shared (All 4 Tablets)

| Part | Spec | Per Tablet | Total Qty | Source | Est. Price | Notes |
|---|---|---|---|---|---|---|
| Guarded Illuminated Pushbutton | Aircraft-style flip cover + LED momentary, panel-mount | 1 | 5 | AliExpress | ~$3.50 ea / $17.50 | Crisis button. +1 spare. |
| Submit Button | 12mm tactile pushbutton, panel-mount | 1 | 5 | AliExpress | ~$0.15 ea / $0.75 | Locks in analog values. +1 spare. |

---

## G. Controls — Navigator

| Part | Spec | Qty | Source | Est. Price | Notes |
|---|---|---|---|---|---|
| Analog Joystick | PSP/thumbstick, 2-axis + click | 1 | AliExpress | ~$1.50 | X/Y + digital click. |
| Linear Slide Potentiometer | 45mm travel, 10kΩ | 1 | AliExpress | ~$1.50 | |
| Toggle Switch (SPDT mini) | MTS-102 or equiv | 2 | AliExpress | (see bulk below) | |
| Momentary Pushbutton (12mm) | Tactile, panel-mount | 1 | AliExpress | (see bulk below) | |

## H. Controls — Engineer

| Part | Spec | Qty | Source | Est. Price | Notes |
|---|---|---|---|---|---|
| Linear Slide Potentiometer | 60mm travel, 10kΩ | 1 | AliExpress | ~$1.80 | |
| Illuminated Arcade Button | 24mm, LED, panel-mount | 1 | AliExpress | ~$1.50 | |
| Toggle Switch (SPDT mini) | MTS-102 or equiv | 3 | AliExpress | (see bulk below) | |

## I. Controls — Operator

| Part | Spec | Qty | Source | Est. Price | Notes |
|---|---|---|---|---|---|
| Rotary Encoder | EC11, 20-detent, infinite scroll + click | 1 | AliExpress | ~$0.80 | |
| Covered Safety Toggle | SPST with flip guard | 1 | AliExpress | ~$2.50 | |
| Toggle Switch (SPDT mini) | MTS-102 or equiv | 1 | AliExpress | (see bulk below) | |
| Momentary Pushbutton (12mm) | Tactile, panel-mount | 2 | AliExpress | (see bulk below) | |

## J. Controls — Sentinel

| Part | Spec | Qty | Source | Est. Price | Notes |
|---|---|---|---|---|---|
| SS49E Linear Hall Sensor | Analog output | 2 | AliExpress | ~$0.50 ea / $1.00 | +1 spare. Wired to trigger assembly. |
| Neodymium Magnet | 6×3mm disc | 5 | AliExpress | ~$1.00 (pack) | Mounted on trigger lever tip. |
| Compression Spring | ~25mm, ~1 lbf | 3+ | AliExpress | ~$1.50 (assortment) | Returns trigger lever to zero. |
| 3-Position Rotary Switch | SP3T, panel-mount | 1 | AliExpress | ~$1.50 | |
| Toggle Switch (SPDT mini) | MTS-102 or equiv | 2 | AliExpress | (see bulk below) | |
| Momentary Pushbutton (12mm) | Tactile, panel-mount | 1 | AliExpress | (see bulk below) | |

---

## K. Bulk Controls (Buy in Packs)

| Part | Spec | Total Needed | Order Qty | Source | Est. Price | Notes |
|---|---|---|---|---|---|---|
| Toggle Switch (SPDT mini) | MTS-102, 6mm, 3-pin | 8 | 10-pack | AliExpress | ~$2.50 | Nav 2 + Eng 3 + Op 1 + Sen 2. |
| Momentary Pushbutton (12mm) | Tactile, 4-pin, panel-mount | 4 | 10-pack | AliExpress | ~$1.50 | Nav 1 + Op 2 + Sen 1. Same part as Submit buttons — buy 20. |
| Knobs (assorted) | 6mm shaft, push-fit | ~6 | 10-pack | AliExpress | ~$1.50 | For encoder, pots, rotary switches. |

---

## L. Hub Off-Board Parts

| Part | Spec | Qty | Source | Est. Price | Notes |
|---|---|---|---|---|---|
| 2.4GHz FPC Antenna | IPEX/U.FL connector | 1 | AliExpress or LCSC (C454912) | ~$1.50 | Peel-and-stick inside Hub enclosure lid. |
| Speaker | 3W, 4Ω or 8Ω, 36–40mm driver | 1 | AliExpress | ~$1.50 | Chassis-mount in Hub enclosure. |
| Illuminated Pushbutton | 16mm, LED, momentary, panel-mount | 1 | AliExpress | ~$1.50 | Pairing button. |

---

## M. Power & Wiring

| Part | Spec | Qty | Source | Est. Price | Notes |
|---|---|---|---|---|---|
| 2× AA Battery Sled | Spring-contact, panel-mount, wired | 5 | AliExpress | ~$0.60 ea / $3.00 | 4 tablets. +1 spare. |
| 4× AA Battery Sled | Spring-contact, panel-mount, wired | 1 | AliExpress | ~$0.80 | Hub. |
| Power Switch (SPST slide) | 2-pin, panel-mount | 6 | AliExpress | ~$0.30 ea / $1.80 | 1 Hub + 4 tablets. +1 spare. |
| Piezo Buzzer | 12mm, 3.3V, through-hole or wired | 5 | AliExpress | ~$0.40 ea / $2.00 | 4 tablets. +1 spare. |
| Coin Vibration Motor | 10mm, 3V, wired | 5 | AliExpress | ~$0.60 ea / $3.00 | 4 tablets. +1 spare. |
| JST-PH Pigtail Cables | 2-pin and 3-pin, pre-crimped, 150mm | 1 set | AliExpress | ~$4.00 | Assorted pack. For battery, motor, speaker, button connections. |
| AA Batteries | Standard alkaline | 20 | Local | ~$8.00 | 8 for Hub (4×AA), 8 for tablets (2×AA × 4). +4 spare. |

---

## N. Assembly Hardware

| Part | Spec | Qty | Source | Est. Price | Notes |
|---|---|---|---|---|---|
| M3 Heat-Set Brass Inserts | M3 × 5mm, standard knurl | 50 | AliExpress | ~$3.00 | PCB mounting + enclosure assembly. |
| M3 Screws (assorted) | M3 × 6mm, 8mm, 10mm, Phillips/hex | 1 set | AliExpress | ~$3.00 | |
| PLA Filament | 1.75mm, 1kg spool | 1 | Local / Amazon | ~$20.00 | For 5 enclosures (Hub + 4 tablets). |
| USB-C Cable | USB-A to USB-C, data-capable, 1m | 1 | Local / Amazon | ~$5.00 | For firmware flashing. NOT charge-only. |

---

## O. Hand Tools (If You Don't Have)

| Tool | Est. Price | Notes |
|---|---|---|
| JST-PH Crimping Tool (Engineer PA-09) | ~$25.00 | For making custom wiring harnesses. One-time buy. |
| Brass Tip Cleaner (wire ball) | ~$5.00 | Keeps soldering iron tip clean. |
| Heat-Set Insert Tip (M3, for soldering iron) | ~$8.00 | Threaded tip attachment for pressing inserts into PLA. |

---

## Cost Estimate

| # | Category | Est. Total | Notes |
|---|---|---|---|
| A | Manufacturing & Reflow Tools | ~$100 | One-time investment. ~$75 without soldering iron. |
| B | Hub PCBs + Stencil (JLCPCB) | ~$9 | 5 bare boards + 1 frameless stencil. |
| C | Hub SMD Components (LCSC) | ~$66 | ×5 boards. W25N01GV is ~$30 of this. |
| D | Hub Through-Hole Connectors (LCSC) | ~$2 | JST-PH, pin headers. |
| E | Displays & Modules | ~$71 | OLEDs, TFTs, TM1637s, PN532. |
| F–K | Controls (all archetypes) | ~$37 | Shared + per-archetype + bulk packs. |
| L | Hub Off-Board Parts | ~$5 | Antenna, speaker, pairing button. |
| M | Power & Wiring | ~$23 | Battery sleds, switches, buzzers, motors, JST cables, batteries. |
| N | Assembly Hardware | ~$31 | Inserts, screws, filament, USB cable. |
| O | Hand Tools (if needed) | ~$38 | Crimper, tip cleaner, heat-set tip. |
| | | | |
| | **Total (all new — no tools on hand)** | **~$382** | |
| | **Total (have soldering iron + hand tools)** | **~$319** | |
| | **Total (have all tools already)** | **~$244** | Parts only, no tools. |

> Prices are AliExpress/LCSC prototype quantities (1–5 units). LCSC shipping is ~$5–15 depending on weight.
> This covers **1 Hub + 4 Tablets** with spares. Tablet PCBs/SMD parts not yet listed (pending Tablet PCB design).

---

## LCSC Part Numbers (Quick Reference)

All Hub SMD parts verified on LCSC. Detailed BOM in section C above.

| Part | LCSC # | Basic? | Role |
|---|---|---|---|
| ESP32-S3-WROOM-1U-N16R8 | C3013946 | Ext | Hub MCU (U.FL antenna) |
| ESP32-S3-WROOM-1-N16R8 | C2913202 | Ext | Tablet MCU (PCB antenna) |
| AP2112K-3.3TRG1 | C23380830 | Ext | 3.3V LDO |
| PAM8403DR-H | C17337 | Ext | Audio amp |
| W25N01GVZEIT | C17656808 | Ext | 128MB SPI NAND |
| USBLC6-2SC6 | C2827654 | Ext | USB ESD protection |
| 1N5819WS | C191023 | Basic | Schottky diode |
| TYPE-C 16PIN 2MD(073) | C2765186 | Ext | USB-C connector |
| WS2812B-V6 | C52917433 | Ext | NeoPixel 5050 |
| Tact Switch 3×6×2.5mm | C49234125 | Ext | BOOT/RESET buttons |
| 10µF 0603 | C19702 | Basic | Decoupling |
| 4.7µF 0603 | C19666 | Basic | Decoupling |
| 100nF 0603 | C14663 | Basic | Decoupling |
| 100µF 1206 | C15008 | Basic | Bulk cap (ceramic) |
| 1µF 0603 | C15849 | Basic | DC blocking |
| 10kΩ 0603 | C25804 | Basic | Pull-ups/pull-downs |
| 5.1kΩ 0603 | C23186 | Basic | USB-C CC resistors |
| 470Ω 0603 | C23179 | Basic | NeoPixel series |
| 220Ω 0603 | C22962 | Basic | LED current limit |
| S2B-PH-K-S (2-pin JST) | C173752 | — | TH: battery, speaker |
| S3B-PH-K-S (3-pin JST) | C157929 | — | TH: pairing button |
| 4-pin header 2.54mm | C52016392 | — | TH: TM1637 |
| 8-pin header 2.54mm | C32713274 | — | TH: PN532 NFC |
| ZIISOR TX2400-FPC-5015 | C454912 | — | Hub FPC antenna (off-board) |
