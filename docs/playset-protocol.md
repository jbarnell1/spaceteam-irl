# Playset Buttons: Protocol

Two hops: **button → dongle** over ESP-NOW (binary), and **dongle → hub** over USB CDC serial (JSON lines).

## Button → dongle (ESP-NOW, unicast)

- Channel: **1**, fixed. Neither side associates with an access point.
- Destination: the dongle's station MAC, compiled into the button (`DONGLE_MAC`). The dongle prints its MAC on boot.
- Unicast, so the radio's MAC-layer ack tells the button the frame arrived. The send callback reports success/failure; the button retries on failure.

Payload: 10 bytes, little-endian, packed.

| Offset | Type | Field | Notes |
|---|---|---|---|
| 0 | `uint8` | `magic` | `0x50` (`'P'`). Lets the dongle ignore stray ESP-NOW traffic. |
| 1 | `uint8` | `version` | `1` |
| 2 | `uint8` | `button_id` | 1–5 |
| 3 | `uint8` | `event` | `1` = press. Reserved: `2` = long press, `3` = double press. |
| 4 | `uint32` | `seq` | Increments per press, kept in RTC memory across deep sleep. Restarts at a random value after a cold boot. |
| 8 | `uint16` | `battery_mv` | Cell voltage in millivolts. `0` = not measured (bench button). |

A retry resends the same `seq`. A new press always gets a new `seq`.

## Dongle → hub (USB CDC, 115200 baud, newline-delimited JSON)

One JSON object per line. Lines that don't parse as JSON (boot noise, debug prints) are ignored by the hub.

**Boot / hello** (printed on boot and in reply to a `?` line from the hub):

```json
{"t":"hello","fw":"dongle-0.1","mac":"f4:12:fa:00:11:22","ch":1}
```

**Press** (one per received frame; the dongle does not dedupe):

```json
{"t":"btn","v":1,"b":3,"e":1,"seq":4021,"mv":3912,"rssi":-58,"src":"34:85:18:aa:bb:cc"}
```

| Key | Meaning |
|---|---|
| `v` | protocol version from the frame |
| `b` | button ID |
| `e` | event type |
| `seq` | sequence number |
| `mv` | battery millivolts |
| `rssi` | received signal strength (dBm) |
| `src` | sender MAC |

## Hub rules

- **Dedupe:** drop an event whose `(b, seq)` was seen in the last 2 seconds.
- **Unknown version:** log and drop.
- **Low battery:** `mv` below 3500 (configurable) flags the button in the phone UI. `mv == 0` means unknown.

## Future room

- Long/double press: new `event` values, same frame.
- Hub → button (lights for games): needs the button to listen after a press. The frame format doesn't change; a new dongle → button message would be added then.
