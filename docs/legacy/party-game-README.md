> **Parked.** This is the original Spaceteam IRL party-game design, set aside on 2026-11-16 in favor of the Playset Buttons alpha. See [the current README](../../README.md). Kept for reference; nothing here is in scope for the alpha.

# Spaceteam IRL

A physical cooperative multiplayer game inspired by Spaceteam. Players (up to 8) use hardware tablets with fixed control loadouts to execute frantic, time-sensitive commands dictated by a Central Hub — surviving dynamic narrative scenarios like Space Battles, 1700s Naval Hunts, and Submarine Dives.

---

## Table of Contents

- [System Architecture & Tech Stack](#system-architecture--tech-stack)
- [Hardware Specifications](#hardware-specifications)
  - [Player Tablets](#a-player-tablets-up-to-8-per-hub)
  - [Central Hub](#b-the-central-hub)
- [Tablet Archetypes](#tablet-archetypes-control-loadouts)
- [Network Protocol & Logic Flow](#network-protocol--logic-flow)
- [Mechanical Design & Manufacturing](#mechanical-design--manufacturing-strategy)
- [Mission Architect (Content Engine)](#the-mission-architect-content-engine)
- [Repository Structure](#repository-structure)

---

## System Architecture & Tech Stack

| Layer | Technology |
|---|---|
| **Firmware** | C++ / ESP-IDF (or Arduino IDE via PlatformIO) |
| **Companion App** | Flutter (hub configuration, account login, game/scenario management) |
| **Networking** | ESP-NOW (2.4GHz, ultra-low latency, router-free) |
| **PCB Design** | EasyEDA (optimized for JLCPCB SMT assembly) |
| **Target MCU** | Espressif ESP32-S3-WROOM-1-N16R8 (16MB flash, 8MB PSRAM) |

---

## Hardware Specifications

### A. Player Tablets (Up to 8 per Hub)

Each tablet is a dynamic workstation with fixed base components and a dedicated control loadout (see [Tablet Archetypes](#tablet-archetypes-control-loadouts)).

**Core PCBA:** ESP32-S3-WROOM-1-N16R8 module on a custom PCB.

**Power:** 2× AA Battery Sled (~3V nominal) with boost converter (e.g., TPS61200) to 3.3V. Estimated **5–6 hours runtime** (~10–20 game sessions). 2× AA chosen over 4× to reduce per-pack battery cost (a 4-tablet pack needs only 8 AAs instead of 16).

#### Base Tablet Components (Fixed on every tablet)

| Component | Purpose |
|---|---|
| 1× Guarded Illuminated Pushbutton (safety cover + LED momentary) | "Shared Crisis" mechanic; flip cover and press to "Ready Up" |
| 1× 7-Segment Display (TM1637) | Displays assigned Player ID / Connection Status |
| 1× Coin Vibration Motor | Haptic feedback (ship damage, environmental shaking) + tablet identification buzz pattern |
| 1× Small Speaker (piezo or similar) | Audio cues, tablet identification tones |
| 1× Status RGB LED | Tablet identity color, connection state, in-game alerts |
| 1× "Submit" Button | Locks in analog calibrations; prevents network spam |
| 5× 1.3" I2C OLED Displays | One per control slot — Hub pushes narrative labels (e.g., "Oxygen Pump") |
| 1× Tablet Screen (small TFT or e-ink, TBD) | Displays commands for this player, or cross-tablet commands in chaotic modes |

#### Tablet Identification

When a tablet connects to the Hub, it reports its **archetype** (e.g., `NAVIGATOR`, `ENGINEER`). The Hub confirms the assignment and the tablet signals its identity to the player through a combination of:
- **Status RGB LED color** — each archetype gets a unique color (visible at a glance across the table)
- **Speaker tone** — a short identification jingle unique to the role
- **Vibration pattern** — a distinct haptic buzz pattern

This lets players quickly locate and confirm their assigned tablet without any screen UI.

#### Dynamic OLED Labels

Each of the 5 control positions is paired with a **1.3" I2C OLED Display**. The Hub pushes narrative-appropriate text to each OLED based on the tablet's archetype and the active mission theme (e.g., "Main Thruster" → "Oxygen Pump" → "Sail Trim").

#### Tablet Command Screen

Each tablet includes a **dedicated screen** (small TFT or e-ink, form factor TBD) that displays:
- **Commands for this player** — what the Hub is telling them to do right now.
- **Cross-tablet commands** (in chaotic modes) — instructions meant for *other* players that this player must shout across the table.

### B. The Central Hub

The master controller that dictates game state, audio, and pacing.

| Component | Details |
|---|---|
| **Brain** | ESP32-S3-WROOM-1-N16R8 with External Antenna (range across large rooms/forts) |
| **Audio Storage** | W25N01GV 128MB SPI NAND Flash — permanent cache for narrator audio across all owned packs |
| **V1 (Audio Hub)** | PAM8403 Amplifier + 3W Speaker (Narrator voice projection) |
| **V2 (Visual Hub)** | Adds HDMI output for optional TV hookup (mission briefings, spectator view) — backward-compatible with V1 tablets |
| **NFC Reader** | Reads game/scenario NFC cards to load new content packs |
| **WiFi** | Connects to home WiFi for direct content downloads (Toniebox-style) — no phone needed after initial setup |
| **Interaction** | 16mm Illuminated Push Button (initiates connection handshake) |

---

## Tablet Archetypes (Control Loadouts)

Each tablet has a **fixed** 5-control loadout soldered/wired to the main PCB, creating distinct gameplay roles. Controls are not swappable — each archetype is a unique hardware build.

> **Full specification:** [docs/tablet-archetypes.md](../tablet-archetypes.md) — per-archetype pin budgets, BOM impact, narrative label examples, and scaling notes.

Every archetype follows the same complexity curve: **1 signature control** (high complexity, unique per archetype) + **1 medium control** (covered safety toggle or illuminated arcade button) + **3 simple controls** (toggle switches and momentary pushbuttons).

| # | Archetype | LED Color | Signature Control | Theme |
|---|---|---|---|---|
| 1 | **Navigator** | Blue | Analog Joystick (2-axis) | Direction & course-plotting |
| 2 | **Engineer** | Orange | Linear Slider (60mm) | Power & machinery |
| 3 | **Operator** | Green | Rotary Encoder (infinite scroll + click) | Signals & communication |
| 4 | **Sentinel** | Purple | Hall Effect Analog Trigger | Security & defense |
| 5 | **Medic** | White | Color-Match Dial (pot + RGB LED) | Diagnostics & repair |
| 6 | **Analyst** | Cyan | 4-Button Keypad | Data entry & research |
| 7 | **Scout** | Yellow | LED Wave Dial (pot + NeoPixel ring) | Reconnaissance & detection |
| 8 | **Commander** | Red | Multi-Position Rotary Switch (6-pos) | Authority & decisions |

**Starter pack (4 tablets):** Navigator, Engineer, Operator, Sentinel — covers steering, power, comms, defense.
**Expansion pack (4 tablets):** Medic, Analyst, Scout, Commander — adds color matching, NFC scanning, data entry, authority.

---

## Network Protocol & Logic Flow

> **Full specification:** [docs/protocol.md](../protocol.md) — message schemas, state machines, timing, and payload budgets.
>
> **Gameplay lifecycle:** [docs/game-loop.md](../game-loop.md) — step-by-step walkthrough of every phase from power-on to power-down.

### Connection Handshake

1. Hub enters pairing mode (illuminated button press).
2. Tablet boots → 7-Segment shows `-`, Status LED pulses white.
3. Tablet sends join request with its archetype ID (e.g., `NAVIGATOR`).
4. Hub assigns Player ID → 7-Segment shows `1` (or assigned number).
5. Tablet confirms identity: Status LED changes to archetype color, speaker plays role jingle, vibration motor buzzes pattern.
6. Player flips crisis button cover and presses → LED flashes ("Ready").

### State-Change Reporting

Tablets **do not stream continuously**. They push a JSON payload via ESP-NOW only when:
- A state changes (toggle flipped, dial adjusted, "Submit" pressed for analog values)
- 500ms heartbeat ping (keep-alive)

### Command Types

| Type | Description | Example |
|---|---|---|
| **Direct Command** | Narrator → specific Tablet screen | "Engineer, full thrust!" |
| **Cooperative Command** | Tablet A's screen shows command meant for Player B → Player A shouts it | "Tell the Navigator to rotate 90°!" |
| **Shared Crisis** | Narrator triggers siren → ALL players flip covers and press crisis buttons simultaneously | Ship-wide hull breach alarm |

### Command Randomization

Each run **randomly selects commands** from the allowed command maps for the active scenario and connected archetypes. This ensures gameplay is fresh every session, even when replaying the same mission theme.

---

## Mechanical Design & Manufacturing Strategy

**Target Retail Price:** $129 (requires COGS ~$20/tablet at 1,000+ units)

### Prototyping Phase

- **Housings:** 8-inch chassis, 3D printed in PLA
- **Assembly:** Top/bottom shells joined with 2° tapered pin-and-socket design, secured with cyanoacrylate or 2-part epoxy
- **Electronics:** "Box Build" — integrated PCBAs from JLCPCB (SMT assembled) dropped into PLA shells

### Production Phase

- Transition to wholesale raw ESP32-S3 modules
- ABS Injection Molding for housings

---

## Content Delivery & Business Model

### Companion App

The **Flutter companion app** connects to the Hub (via BLE or USB) for initial setup and management:
- **WiFi setup** — configure the Hub's home WiFi credentials so it can download content directly.
- **Account login** — ties the Hub to a user account.
- **Game management** — browse, purchase, and manage game/scenario packs. The Hub auto-downloads content over WiFi.
- **Hub configuration** — adjust settings, update firmware, view connected tablets.
- **Storage management** — view cached packs, free up space when flash is full.

After initial WiFi setup, the Hub can download new content autonomously — no phone needed.

### Game Packs via NFC Cards (Tonies-Style)

The Hub **plays the scenario for the NFC card currently placed on top** — exactly like a Toniebox plays the figurine sitting on it. Remove the card, the game stops. Place a different card, a different scenario loads. One Hub, unlimited game packs.

New games and scenarios are sold as **physical NFC cards at ~$10 each**. Players place a card on the Hub's NFC reader to load and play.

#### Why This Model Works

| Factor | Impact |
|---|---|
| **Low card COGS** | NFC card + themed printed packaging costs ~$0.50–$1.00 at volume. At $10 retail, margins are **~85–90%**. |
| **Sticky recurring revenue** | No subscriptions to cancel — just a steady stream of impulse-friendly $10 purchases. Players buy more as new themes release. |
| **No subscription fatigue** | Buy-once-and-own. Customers never feel nickeled-and-dimed, improving brand affinity and word-of-mouth. |
| **Physical collectibility** | Themed art/designs on each card (pirate map, space badge, submarine insignia). Kids collect them; parents gift them. |
| **Gifting & retail presence** | Cards can sit on store shelves, in gift shops, at checkout counters. Low price point = impulse buy territory. |
| **Seasonal & event releases** | Holiday packs, school-themed STEM packs, limited editions — each a new revenue event with near-zero marginal cost. |
| **Institutional sales** | Educational packs (math, history, science) can be sold in bulk to schools, museums, camps. |
| **Offline-first** | No internet required to play. All owned content is permanently cached on the Hub's 128MB audio flash. Just place and go. |
| **Digital fallback** | Companion app can also sell digital game packs (purchased once) for users who prefer app-based loading. |

#### Revenue Illustration

| Scenario | Revenue |
|---|---|
| Sell 10,000 Hubs at $129 | $1.29M (hardware, lower margin) |
| Average customer buys 5 NFC packs in Year 1 | 50,000 cards × $10 = **$500K** (~$425K gross profit) |
| Average customer buys 3 NFC packs/year ongoing | Recurring high-margin revenue without subscription mechanics |

The real money is in the cards, not the box — same economics that make Tonies a billion-dollar company.

---

## The "Mission Architect" (Content Engine)

A structured LLM prompt system used internally to generate curated, scalable scenarios for game packs.

> **Full specification:** [docs/scenario-schema.md](../scenario-schema.md) — scenario file format, command capability matrix, branching outcome system, difficulty curves, validation rules, and the complete generation pipeline.

### How It Works

1. **Inputs:** Theme, subject, age rating, difficulty, archetype focus.
2. **Command Pool Build:** Generates direct and cooperative command pools using the [command capability matrix](../scenario-schema.md#command-capability-matrix). Every command maps to a real physical control on a real archetype.
3. **Phase & Difficulty Curves:** Designs escalating pressure ramps — commands/minute increase, cooperative ratio rises, crisis probability grows.
4. **Branching Outcomes:** Each scenario has 5–7 endings based on how the crew performed:
   - **Communication failure** — players couldn't relay cooperative commands across the table.
   - **Execution failure** — players fumbled their own direct commands.
   - **Timeout failure** — too slow, commands expired.
   - **Survive / Success / Triumph** — increasingly heroic endings based on composite score.
5. **Validation:** Every generated scenario is checked against capability compliance, pool coverage, tier balance, payload budgets, and duration feasibility.

---

## Repository Structure

```
spaceteam_irl/
├── README.md                   # This file — project overview
├── AGENTS.md                   # Copilot agent instructions
├── firmware/                   # ESP-IDF / PlatformIO firmware
│   ├── hub/                    # Central Hub firmware
│   ├── tablet/                 # Player Tablet firmware
│   └── shared/                 # Shared libraries (ESP-NOW, protocol, tablet identity, NFC)
├── hardware/                   # PCB & mechanical design files
│   ├── pcb/                    # EasyEDA / Gerber files
│   ├── 3d/                     # 3D print files (STL, STEP)
│   └── bom/                    # Bill of Materials
├── app/                        # Flutter companion app
├── missions/                   # Mission Architect templates & generated scenarios
│   ├── templates/              # LLM prompt templates
│   └── scenarios/              # Generated mission files
├── docs/                       # Extended documentation
│   ├── protocol.md             # ESP-NOW message spec
│   ├── tablet-archetypes.md    # Archetype definitions & control mappings
│   ├── scenario-schema.md      # Scenario file format & Mission Architect
│   ├── pack-strategy.md        # Retail pack tiers, pricing, bundling
│   ├── manufacturing.md        # BOM, assembly, cost notes
│   └── hardware-guide.md       # Wiring, pinouts, schematics
└── tools/                      # Build scripts, flashing utilities
```
