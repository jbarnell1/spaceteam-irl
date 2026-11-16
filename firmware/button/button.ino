/*
 * Playset Buttons: button firmware (bench + alpha)
 *
 * One job: wake on press, tell the dongle, confirm it was heard, sleep.
 * Wire format: docs/playset-protocol.md (10-byte packed struct).
 *
 * BENCH (phase 1): a spare ESP32-S3 dev board with a tactile switch
 *   between BUTTON_PIN and GND, powered from USB. Leave BENCH_NO_SLEEP = 1
 *   so the board stays awake and the serial monitor keeps working.
 *
 * ALPHA PCB (phase 4): ESP32-C3. Set BENCH_NO_SLEEP = 0, BATTERY_ADC_PIN to
 *   the divider pin, and check BATTERY_DIVIDER_RATIO against the schematic.
 *
 * Arduino IDE setup:
 *   Board: "ESP32S3 Dev Module" (bench) or "ESP32C3 Dev Module" (PCB)
 *   USB CDC On Boot: Enabled
 *   Board package: esp32 by Espressif, 2.x or 3.x
 *
 * Before flashing: set BUTTON_ID (1-5, one per button) and DONGLE_MAC
 * (the dongle prints its MAC on boot).
 */

#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>
#include <esp_sleep.h>
#include <esp_random.h>
#include <esp_idf_version.h>

// ── Per-button configuration ───────────────────────────────────────
#define BUTTON_ID 1  // 1..5, unique per button

// Dongle station MAC, printed by the dongle on boot ("mac":"..").
static const uint8_t DONGLE_MAC[6] = {0xF4, 0x12, 0xFA, 0x00, 0x00, 0x00};

// ── Build options ──────────────────────────────────────────────────
#define BENCH_NO_SLEEP 1  // 1 = stay awake and poll (bench); 0 = deep sleep (battery)

// ── Pins ───────────────────────────────────────────────────────────
// GPIO 4 is deep-sleep wake capable on both the S3 (RTC GPIO) and the C3 (GPIO 0-5).
#define BUTTON_PIN 4
#define BATTERY_ADC_PIN -1           // -1 = no battery sense (bench). PCB: set to divider pin.
#define BATTERY_DIVIDER_RATIO 2.0f   // Vbat = Vadc * ratio (2.0 for two equal resistors)
#define LED_PIN -1                   // Optional status LED (bench only). -1 = none.

// ── Protocol ───────────────────────────────────────────────────────
#define ESPNOW_CHANNEL 1
#define PROTO_MAGIC 0x50
#define PROTO_VERSION 1
#define EVENT_PRESS 1

typedef struct __attribute__((packed)) {
    uint8_t magic;
    uint8_t version;
    uint8_t button_id;
    uint8_t event;
    uint32_t seq;
    uint16_t battery_mv;
} PressFrame;
static_assert(sizeof(PressFrame) == 10, "PressFrame must be 10 bytes");

// ── Timing ─────────────────────────────────────────────────────────
#define SEND_ATTEMPTS 4
#define ACK_WAIT_MS 30
#define DEBOUNCE_MS 30
#define STUCK_BUTTON_MS 10000        // held longer than this: stop waiting for release
#define STUCK_RECHECK_US (2ULL * 1000000ULL)

// ── Battery protection ─────────────────────────────────────────────
#define LOW_BATTERY_CUTOFF_MV 3300   // below this: stop answering presses, sleep hard
#define LOW_BATTERY_RECHECK_US (30ULL * 60ULL * 1000000ULL)  // wake every 30 min to see if charged

// Survives deep sleep. Re-randomized on cold boot so the hub's dedupe window
// never mistakes a fresh press for a retry.
RTC_DATA_ATTR static uint32_t rtc_seq = 0;
RTC_DATA_ATTR static bool rtc_seq_valid = false;

static volatile int8_t send_result = -1;  // -1 pending, 0 fail, 1 ok

// The send-callback signature changed in ESP-IDF 5.5 (arduino-esp32 3.3+).
#if ESP_IDF_VERSION >= ESP_IDF_VERSION_VAL(5, 5, 0)
static void on_sent(const wifi_tx_info_t *info, esp_now_send_status_t status) {
#else
static void on_sent(const uint8_t *mac, esp_now_send_status_t status) {
#endif
    send_result = (status == ESP_NOW_SEND_SUCCESS) ? 1 : 0;
}

static void led(bool on) {
#if LED_PIN >= 0
    digitalWrite(LED_PIN, on ? HIGH : LOW);
#endif
}

static uint16_t read_battery_mv() {
#if BATTERY_ADC_PIN >= 0
    uint32_t sum = 0;
    for (uint8_t i = 0; i < 4; i++) sum += analogReadMilliVolts(BATTERY_ADC_PIN);
    return (uint16_t)((sum / 4) * BATTERY_DIVIDER_RATIO);
#else
    return 0;  // not measured
#endif
}

static bool radio_start() {
    WiFi.mode(WIFI_STA);
    esp_wifi_set_storage(WIFI_STORAGE_RAM);
    esp_wifi_set_channel(ESPNOW_CHANNEL, WIFI_SECOND_CHAN_NONE);
    if (esp_now_init() != ESP_OK) return false;
    esp_now_register_send_cb(on_sent);

    esp_now_peer_info_t peer = {};
    memcpy(peer.peer_addr, DONGLE_MAC, 6);
    peer.channel = ESPNOW_CHANNEL;
    peer.ifidx = WIFI_IF_STA;
    peer.encrypt = false;
    return esp_now_add_peer(&peer) == ESP_OK;
}

// Sends one press. Retries reuse the same seq so the hub can drop duplicates.
static bool send_press(uint16_t battery_mv) {
    if (!rtc_seq_valid) {
        rtc_seq = esp_random();
        rtc_seq_valid = true;
    }
    rtc_seq++;

    PressFrame frame = {PROTO_MAGIC, PROTO_VERSION, BUTTON_ID, EVENT_PRESS, rtc_seq, battery_mv};
    uint32_t backoff_ms = 5;
    for (uint8_t attempt = 0; attempt < SEND_ATTEMPTS; attempt++) {
        send_result = -1;
        if (esp_now_send(DONGLE_MAC, (const uint8_t *)&frame, sizeof(frame)) == ESP_OK) {
            uint32_t start = millis();
            while (send_result < 0 && millis() - start < ACK_WAIT_MS) delay(1);
            if (send_result == 1) return true;
        }
        delay(backoff_ms);
        backoff_ms *= 2;
    }
    return false;
}

// Returns true when released, false if the button looks stuck.
static bool wait_for_release() {
    uint32_t start = millis();
    uint32_t high_since = 0;
    while (millis() - start < STUCK_BUTTON_MS) {
        if (digitalRead(BUTTON_PIN) == HIGH) {
            if (high_since == 0) high_since = millis();
            if (millis() - high_since >= DEBOUNCE_MS) return true;
        } else {
            high_since = 0;
        }
        delay(2);
    }
    return false;
}

static void arm_button_wake() {
#if CONFIG_IDF_TARGET_ESP32C3 || CONFIG_IDF_TARGET_ESP32C6
    esp_deep_sleep_enable_gpio_wakeup(1ULL << BUTTON_PIN, ESP_GPIO_WAKEUP_GPIO_LOW);
#else
    esp_sleep_enable_ext0_wakeup((gpio_num_t)BUTTON_PIN, 0);
#endif
}

static void sleep_until_press() {
    arm_button_wake();
    esp_deep_sleep_start();
}

static void sleep_for_us(uint64_t us) {
    esp_sleep_enable_timer_wakeup(us);
    esp_deep_sleep_start();
}

static void handle_press() {
    uint16_t mv = read_battery_mv();
    led(true);
    uint32_t t0 = millis();
    bool ok = send_press(mv);
    Serial.printf("press seq=%lu mv=%u %s in %lums\n", (unsigned long)rtc_seq, mv,
                  ok ? "acked" : "NOT acked", (unsigned long)(millis() - t0));
    led(false);
}

void setup() {
    pinMode(BUTTON_PIN, INPUT_PULLUP);
#if LED_PIN >= 0
    pinMode(LED_PIN, OUTPUT);
#endif
    Serial.begin(115200);

#if BENCH_NO_SLEEP
    radio_start();
    Serial.printf("button %d ready (bench, no sleep). MAC %s\n", BUTTON_ID, WiFi.macAddress().c_str());
#else
    // Battery protection first: a flat cell must not keep waking the radio.
    uint16_t mv = read_battery_mv();
    if (mv != 0 && mv < LOW_BATTERY_CUTOFF_MV) {
        sleep_for_us(LOW_BATTERY_RECHECK_US);  // timer only; presses ignored until charged
    }

    esp_sleep_wakeup_cause_t cause = esp_sleep_get_wakeup_cause();
    bool woke_from_press = (cause == ESP_SLEEP_WAKEUP_EXT0 || cause == ESP_SLEEP_WAKEUP_GPIO);
    if (woke_from_press) {
        // The wake itself is the press, even if a quick tap is already released.
        if (radio_start()) handle_press();
        if (!wait_for_release()) sleep_for_us(STUCK_RECHECK_US);  // don't re-trigger on a held button
    } else if (digitalRead(BUTTON_PIN) == LOW) {
        // Cold boot or timer wake with the button held: wait it out without sending.
        if (!wait_for_release()) sleep_for_us(STUCK_RECHECK_US);
    }
    sleep_until_press();
#endif
}

void loop() {
#if BENCH_NO_SLEEP
    static uint32_t low_since = 0;
    if (digitalRead(BUTTON_PIN) == LOW) {
        if (low_since == 0) low_since = millis();
        if (millis() - low_since >= DEBOUNCE_MS) {
            handle_press();
            wait_for_release();
            low_since = 0;
        }
    } else {
        low_since = 0;
    }
    delay(1);
#endif
}
