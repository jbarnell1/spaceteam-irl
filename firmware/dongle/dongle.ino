/*
 * Playset Buttons: receiver dongle
 *
 * A spare ESP32-S3 plugged into the hub Pi over USB. It listens for button
 * frames on ESP-NOW channel 1 and prints one JSON line per frame over USB CDC.
 * The radio acks unicast frames automatically. No dedupe here: the hub does it.
 *
 * Wire formats: docs/playset-protocol.md
 *
 * Arduino IDE setup:
 *   Board: "ESP32S3 Dev Module"
 *   USB CDC On Boot: Enabled   (so Serial is the native USB port on the Pi)
 *   Board package: esp32 by Espressif, 2.x or 3.x
 *
 * After flashing, open the serial monitor at 115200: the first line is
 *   {"t":"hello","fw":"dongle-0.1","mac":"..","ch":1}
 * Copy that MAC into DONGLE_MAC in firmware/button/button.ino.
 */

#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>

#define FW_VERSION "dongle-0.1"
#define ESPNOW_CHANNEL 1
#define PROTO_MAGIC 0x50
#define QUEUE_DEPTH 16

typedef struct __attribute__((packed)) {
    uint8_t magic;
    uint8_t version;
    uint8_t button_id;
    uint8_t event;
    uint32_t seq;
    uint16_t battery_mv;
} PressFrame;
static_assert(sizeof(PressFrame) == 10, "PressFrame must be 10 bytes");

typedef struct {
    PressFrame frame;
    uint8_t src[6];
    int8_t rssi;
} RxItem;

static QueueHandle_t rx_queue;

// Runs in the Wi-Fi task: copy and hand off, nothing else.
static void enqueue(const uint8_t *src, int8_t rssi, const uint8_t *data, int len) {
    if (len != sizeof(PressFrame) || data[0] != PROTO_MAGIC) return;
    RxItem item;
    memcpy(&item.frame, data, sizeof(PressFrame));
    memcpy(item.src, src, 6);
    item.rssi = rssi;
    xQueueSend(rx_queue, &item, 0);
}

#if ESP_ARDUINO_VERSION_MAJOR >= 3
static void on_recv(const esp_now_recv_info_t *info, const uint8_t *data, int len) {
    enqueue(info->src_addr, info->rx_ctrl ? info->rx_ctrl->rssi : 0, data, len);
}
#else
static void on_recv(const uint8_t *mac, const uint8_t *data, int len) {
    enqueue(mac, 0, data, len);
}
#endif

static void print_hello() {
    Serial.printf("{\"t\":\"hello\",\"fw\":\"%s\",\"mac\":\"%s\",\"ch\":%d}\n", FW_VERSION,
                  WiFi.macAddress().c_str(), ESPNOW_CHANNEL);
}

void setup() {
    Serial.begin(115200);
    rx_queue = xQueueCreate(QUEUE_DEPTH, sizeof(RxItem));

    WiFi.mode(WIFI_STA);
    WiFi.disconnect();
    esp_wifi_set_storage(WIFI_STORAGE_RAM);
    esp_wifi_set_ps(WIFI_PS_NONE);  // stay awake to receive; the dongle is USB powered
    esp_wifi_set_channel(ESPNOW_CHANNEL, WIFI_SECOND_CHAN_NONE);

    if (esp_now_init() != ESP_OK) {
        Serial.println("{\"t\":\"error\",\"msg\":\"esp_now_init failed\"}");
        return;
    }
    esp_now_register_recv_cb(on_recv);
    print_hello();
}

void loop() {
    RxItem item;
    while (xQueueReceive(rx_queue, &item, 0) == pdTRUE) {
        const PressFrame &f = item.frame;
        Serial.printf(
            "{\"t\":\"btn\",\"v\":%u,\"b\":%u,\"e\":%u,\"seq\":%lu,\"mv\":%u,\"rssi\":%d,"
            "\"src\":\"%02x:%02x:%02x:%02x:%02x:%02x\"}\n",
            f.version, f.button_id, f.event, (unsigned long)f.seq, f.battery_mv, item.rssi,
            item.src[0], item.src[1], item.src[2], item.src[3], item.src[4], item.src[5]);
    }

    // The hub sends "?" to ask which dongle this is.
    while (Serial.available()) {
        if (Serial.read() == '?') print_hello();
    }
    vTaskDelay(1);
}
