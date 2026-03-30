# Pack Strategy — Retail Bundles & Pricing

> **Version:** 0.1.0 (Draft)
>
> How we package, price, and sell Spaceteam IRL hardware bundles and NFC game packs.
>
> **See also:** [scenario-schema.md](scenario-schema.md) for what's on each NFC card, [tablet-archetypes.md](tablet-archetypes.md) for archetype details.

---

## Table of Contents

- [Hardware Tiers](#hardware-tiers)
  - [Duo Pack (2 Tablets)](#duo-pack-2-tablets)
  - [Crew Pack (4 Tablets)](#crew-pack-4-tablets)
  - [Ultimate Pack (8 Tablets)](#ultimate-pack-8-tablets)
  - [Expansion Packs (Add-On Tablets)](#expansion-packs-add-on-tablets)
  - [Hub + Tablet Bundles vs. Hub-Separate](#hub--tablet-bundles-vs-hub-separate)
- [NFC Scenario Packs](#nfc-scenario-packs)
  - [Pack Structure](#pack-structure)
  - [Starter Scenarios (Included with Hardware)](#starter-scenarios-included-with-hardware)
  - [Retail NFC Packs](#retail-nfc-packs)
  - [Premium / Deluxe Packs](#premium--deluxe-packs)
  - [Institutional Packs](#institutional-packs)
- [Pricing Summary](#pricing-summary)
- [Retail & Channel Strategy](#retail--channel-strategy)
- [Archetype Pairing Philosophy](#archetype-pairing-philosophy)
- [Upgrade Path](#upgrade-path)

---

## Hardware Tiers

Every hardware tier includes **one Hub** and a set of tablets. The Hub is the same across all tiers — only the tablet count and archetype selection varies.

### Duo Pack (2 Tablets)

> *Entry point. Two players, one game. Perfect for couples, parent-child, or trying before buying.*

| Contents | Details |
|---|---|
| 1× Central Hub | Standard Hub with NFC reader, speaker, illuminated button |
| 2× Tablets | **Navigator** + **Engineer** |
| 1× Starter NFC Card | "First Voyage" — a short introductory scenario (~3 min) |
| Batteries | 2× AA per tablet + 4× AA for Hub (10 total included) |
| Quick-start guide | Printed card |

**Why Navigator + Engineer:** These two cover the most intuitive controls (joystick, slider) and create a natural captain/mechanic dynamic. Every scenario can work with just these two — other archetypes are additive, not required.

| | |
|---|---|
| **Target Price** | $79 |
| **Target COGS** | ~$35 (Hub ~$15 + 2 tablets ~$10 each) |
| **Margin** | ~55% |

---

### Crew Pack (4 Tablets)

> *The core experience. Four players, full teamwork chaos. Recommended for families and friend groups.*

| Contents | Details |
|---|---|
| 1× Central Hub | Standard |
| 4× Tablets | **Navigator**, **Engineer**, **Operator**, **Sentinel** |
| 2× Starter NFC Cards | "First Voyage" + "Storm Warning" (~3 min + ~5 min) |
| Batteries | 2× AA per tablet + 4× AA for Hub (12 total included) |
| Quick-start guide | |

**Why these 4:** Navigator (steering), Engineer (power), Operator (comms), Sentinel (defense) — the four fundamental crew roles. Cooperative commands across these four create rich cross-talk. The Sentinel’s spring-return trigger adds a unique analog squeeze mechanic that showcases the hardware.

| | |
|---|---|
| **Target Price** | $129 |
| **Target COGS** | ~$55 (Hub ~$15 + 4 tablets ~$10 each) |
| **Margin** | ~57% |

---

### Ultimate Pack (8 Tablets)

> *The full crew. Maximum chaos, maximum fun. For parties, game nights, team-building events.*

| Contents | Details |
|---|---|
| 1× Central Hub | Standard |
| 8× Tablets | All 8 archetypes |
| 4× Starter NFC Cards | "First Voyage" + "Storm Warning" + "The Crimson Galleon" + "Deep Dive" |
| Batteries | 2× AA per tablet + 4× AA for Hub (20 total included) |
| Quick-start guide + full manual | |
| Carrying case | Foam-insert case for all 8 tablets + Hub |

| | |
|---|---|
| **Target Price** | $249 |
| **Target COGS** | ~$100 (Hub ~$15 + 8 tablets ~$10 each + case ~$5) |
| **Margin** | ~60% |

---

### Expansion Packs (Add-On Tablets)

For customers who bought a smaller tier and want to grow.

| Pack | Tablets | Price | Notes |
|---|---|---|---|
| **Expansion Duo A** | Medic + Analyst | $49 | Color matching + code entry |
| **Expansion Duo B** | Scout + Commander | $49 | Wave dial + rotary authority switch |
| **Expansion Quad** | Medic, Analyst, Scout, Commander | $89 | All 4 expansion archetypes |

Expansion packs do **not** include a Hub. Packaging clearly states "Requires Spaceteam IRL Hub (sold separately or in starter packs)."

---

### Hub + Tablet Bundles vs. Hub-Separate

We **do not sell the Hub alone**. The Hub has zero value without tablets, and selling it separately creates a confusing purchase experience. The Hub is always bundled.

However, we could offer a **Tablet-Only Upgrade Pack** for customers who already own a Hub:

| Pack | Contents | Price |
|---|---|---|
| 2-Tablet Upgrade | Any 2 archetypes | $39 |
| 4-Tablet Upgrade | Any 4 archetypes | $69 |

These are **direct/online-only** (companion app purchase or website) since they require choosing specific archetypes.

---

## NFC Scenario Packs

### Pack Structure

Each NFC pack is a single physical card with themed artwork. The card holds a scenario ID; the full scenario data lives on the Hub (auto-downloaded on first tap via WiFi, or pre-loaded via companion app).

| Component | Details |
|---|---|
| **NFC Card** | PVC card, NTAG215 or similar, full-color print both sides |
| **Packaging** | Branded sleeve or mini box with scenario title, player count, difficulty, age rating |
| **Contents on card** | Scenario ID + optional authentication signature |
| **Scenario JSON** | Stored on Hub's 16MB internal flash (~22–28 KB per scenario) |
| **Narrator audio** | Stored on Hub's 128MB SPI NAND flash (~540 KB–1.4 MB per scenario depending on codec) |
| **First-tap download** | Hub auto-downloads content over WiFi when an unrecognized card is tapped (Toniebox-style). No phone needed. |
| **Permanent cache** | All downloaded content stays on the Hub permanently. Plays fully offline after first download. |

### Starter Scenarios (Included with Hardware)

Each hardware tier comes with starter scenarios to play out of the box.

| Scenario | Theme | Difficulty | Duration | Min Players | Included With |
|---|---|---|---|---|---|
| **First Voyage** | Space (tutorial) | Easy | ~3 min | 2 | All tiers |
| **Storm Warning** | Nautical | Easy | ~5 min | 3 | Crew + Ultimate |
| **The Crimson Galleon** | Pirate | Medium | ~7 min | 4 | Ultimate |
| **Deep Dive** | Submarine | Medium | ~7 min | 4 | Ultimate |

"First Voyage" is specifically designed as a **tutorial scenario** — it uses only low-complexity commands (T1, T2), introduces one mechanic at a time, has generous timeouts, and always ends in a SURVIVE or SUCCESS outcome. It teaches the game without overwhelming.

### Retail NFC Packs

Sold individually or in themed bundles. Each card = 1 scenario. Bundles group 3–5 thematically related scenarios.

#### Single Cards ($10 each)

| Card | Theme | Difficulty | Duration | Min Players |
|---|---|---|---|---|
| Asteroid Belt | Space | Hard | ~8 min | 4 |
| Ghost Ship | Pirate | Medium | ~6 min | 3 |
| Kraken Attack | Pirate | Hard | ~8 min | 4 |
| Arctic Expedition | Submarine | Medium | ~7 min | 3 |
| Virus Outbreak | Sci-Fi | Medium | ~6 min | 4 |
| Dragon's Lair | Fantasy | Medium | ~7 min | 4 |
| Volcano Escape | Adventure | Hard | ~8 min | 3 |

#### Theme Bundles ($25 for 3 cards, $35 for 5 cards)

| Bundle | Cards | Theme | Price |
|---|---|---|---|
| **Pirates of the Seven Seas** | Crimson Galleon, Ghost Ship, Kraken Attack, Treasure Island, Mutiny! | Pirate | $35 |
| **Deep Space Collection** | Asteroid Belt, Wormhole, Station Breach, Solar Flare, First Contact | Space | $35 |
| **Ocean Depths** | Deep Dive, Arctic Expedition, Volcano Vent | Submarine | $25 |
| **Fantasy Quest** | Dragon's Lair, Wizard's Tower, Goblin Siege | Fantasy | $25 |
| **Action Adventures** | Volcano Escape, Virus Outbreak, Time Vortex | Mixed | $25 |

Bundle discount: ~17–30% off individual card prices. Encourages multi-buy.

### Premium / Deluxe Packs ($15 per card)

These include **physical extras** beyond the NFC card:

| Extra | Description | Which Packs |
|---|---|---|
| Commander NFC Item Cards | 2–4 additional themed NFC item cards for the Commander's scanner | Any pack with Commander-heavy scenarios |
| Map/Poster | Fold-out themed map or poster (adds to table atmosphere) | Premium theme bundles |
| Character Cards | Printed role cards with archetype art and quick-reference controls | Deluxe bundles |

### Institutional Packs ($50–$100)

Designed for schools, museums, camps, and team-building workshops.

| Pack | Contents | Price |
|---|---|---|
| **STEM: Space Math** | 5 scenarios (math-integrated space theme, ages 10+) | $50 |
| **STEM: Ocean Science** | 5 scenarios (marine biology/physics, ages 10+) | $50 |
| **History: Age of Sail** | 5 scenarios (historical naval events, ages 12+) | $50 |
| **Team Building** | 8 scenarios (workplace-appropriate themes, adults) + facilitator guide card | $100 |

Institutional packs emphasize the educational `subject` field in scenario metadata and have extended post-game debrief narrator scripts.

Sold in bulk (10+ pack discount) via direct sales or the companion app's institutional portal.

---

## Pricing Summary

| Product | Price | COGS Est. | Margin |
|---|---|---|---|
| Duo Pack (Hub + 2 tablets) | $79 | ~$35 | ~55% |
| Crew Pack (Hub + 4 tablets) | $129 | ~$55 | ~57% |
| Ultimate Pack (Hub + 8 tablets) | $249 | ~$100 | ~60% |
| Expansion Duo (2 tablets) | $49 | ~$20 | ~59% |
| Expansion Quad (4 tablets) | $89 | ~$40 | ~55% |
| Single NFC Card | $10 | ~$0.75 | ~92% |
| 3-Card Bundle | $25 | ~$2.50 | ~90% |
| 5-Card Bundle | $35 | ~$4.00 | ~89% |
| Premium Card | $15 | ~$2.00 | ~87% |
| Institutional Pack (5 scenarios) | $50 | ~$5.00 | ~90% |

**Revenue model:** Hardware drives adoption; NFC cards drive recurring high-margin revenue. A customer who buys a Crew Pack ($129) and 5 card bundles over 2 years ($175) generates $304 total revenue at blended ~72% margin.

---

## Retail & Channel Strategy

### Direct (Online)
- **Website + Companion App** — Full catalog, digital + physical options.
- Digital-only game packs available for customers who don't want physical cards (same price, delivered via app).
- Archetype-specific tablet upgrades (choose your archetypes).

### Retail (Physical)
- **Board game stores** — Crew Pack and Ultimate Pack on shelves. NFC cards near checkout (impulse buy zone).
- **Toy stores / electronics stores** — Duo Pack as entry point. Card bundles as follow-on.
- **Gift shops / museum stores** — Institutional packs, themed bundles (space museum → Deep Space Collection).
- **Amazon / online marketplaces** — All tiers + cards. Bundle deals.

### Key Retail Positioning

| Shelf Position | Product | Why |
|---|---|---|
| **Checkout/impulse** | Single NFC cards ($10) | Low price point, collectible artwork, fits in hand |
| **Games aisle** | Crew Pack ($129) | Competes with mid-tier board games |
| **Premium/gifts** | Ultimate Pack ($249) | Gift-worthy, carrying case, "the whole collection" |
| **Kids' section** | Duo Pack ($79) + easy-theme cards | Entry-level, parent-child play |

---

## Archetype Pairing Philosophy

### Why Navigator + Engineer First

These two archetypes have the widest command vocabulary (joystick covers 2D space, slider covers continuous range) and the most intuitive physical metaphors. Any theme works with a "steer" + "power" dynamic.

### Crew Pack Composition

| Archetype | Role in Group Dynamic |
|---|---|
| Navigator | Direction, course — the "driver" |
| Engineer | Power, systems — the "engine room" |
| Operator | Communication — bridges the gap between players (encoder tuning = "finding the right channel") |
| Sentinel | Defense + trigger precision — adds a unique analog squeeze mechanic (spring-return hall trigger) |

This 4-player composition hits every cooperative command axis:
- Navigator ↔ Engineer (steering + power coordination)
- Operator ↔ Sentinel (signals + security coordination)
- Cross-group (Navigator tells Sentinel to lock down, Operator relays to Engineer)

### Expansion Composition

| Archetype | What It Adds |
|---|---|
| Medic | Color-matching precision + "administer carefully" drama |
| Analyst | Code entry + data processing — cerebral under pressure |
| Scout | Wave-dial sweeping + stealth mechanics |
| Commander | Mode selection + authority — "the one who gives the big orders" |

The expansion archetypes layer in more specialized mechanics without duplicating what the core 4 already cover.

---

## Upgrade Path

The ideal customer journey:

```
 ┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌───────────────┐
 │ Duo Pack │────►│ NFC Cards    │────►│ Expansion    │────►│ More NFC      │
 │ $79      │     │ (3-5 cards)  │     │ Duo/Quad     │     │ Cards + Prem  │
 │ 2 tablets│     │ $25-35       │     │ $49-89       │     │ $10-15 each   │
 └──────────┘     └──────────────┘     └──────────────┘     └───────────────┘

 OR

 ┌──────────┐     ┌──────────────┐     ┌───────────────┐
 │ Crew Pack│────►│ NFC Cards    │────►│ Expansion     │
 │ $129     │     │ (bundles)    │     │ Quad $89      │
 │ 4 tablets│     │ $25-35       │     │ → 8 players   │
 └──────────┘     └──────────────┘     └───────────────┘

 OR

 ┌───────────┐     ┌──────────────┐
 │ Ultimate  │────►│ NFC Cards    │  (Already has all tablets)
 │ $249      │     │ (all themes) │
 │ 8 tablets │     │ $10-35 each  │
 └───────────┘     └──────────────┘
```

Every path leads to NFC card purchases. The hardware is the platform; the cards are the content.

---

## Seasonal & Event Strategy

| Timing | Release | Type |
|---|---|---|
| **Launch** | First Voyage, Storm Warning, Crimson Galleon, Deep Dive | Starter scenarios (included with hardware) |
| **Month 1–3** | Deep Space Collection, Pirates of the Seven Seas | First retail bundles — maximize early NFC card attachment |
| **Month 4–6** | Ocean Depths, Fantasy Quest, Action Adventures | Expand theme library |
| **Back-to-School** | STEM packs (Space Math, Ocean Science) | Institutional push |
| **Holiday** | Gift bundles (Hardware + curated card set at slight discount) | Retail spike |
| **Ongoing** | 1–2 new single cards per month | Keep the catalog fresh, give loyal customers a reason to return |

---

## Companion App Role in Pack Strategy

The companion app handles **initial Hub setup** and serves as the **digital storefront**. After WiFi is configured, the Hub downloads content autonomously — no phone required.

| Function | Description |
|---|---|
| **WiFi Setup** | Configure the Hub's home WiFi credentials so it can auto-download content. One-time setup. |
| **Browse & Purchase** | Full NFC pack catalog. Buy digital-only packs or order physical cards for delivery. |
| **Load without NFC** | Digital packs load directly to Hub via BLE/USB/WiFi — no physical card needed. |
| **Storage Management** | View cached packs on Hub's 128MB audio flash. Remove packs to free space when full. |
| **Pack Library** | View all owned scenarios, play history, high scores. |
| **Wishlist & Notifications** | Alert when new packs release in themes you like. |
| **Gift Cards** | Send a digital scenario pack as a gift (recipient loads via their app). |
| **Institutional Portal** | Bulk ordering, facilitator guides, classroom management features. |

The Hub's direct WiFi download capability (Toniebox-style) means the app is needed only for initial setup and optional store browsing. Physical NFC cards remain the hero product — tap a new card, Hub downloads the content automatically, plays forever offline.
