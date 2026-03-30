/*
 * =====================================================
 *  SPACETEAM IRL — Tablet Prototype (Navigator)
 *  ESP32 DevKit V1
 * =====================================================
 *
 *  WIRING:
 *    GPIO 34  ←  Joystick VRx  (ADC, input-only pin)
 *    GPIO 35  ←  Joystick VRy  (ADC, input-only pin)
 *    GPIO 27  ←  Joystick SW   (other leg to GND)
 *    GPIO 26  ←  Submit button  (other leg to GND)
 *    GPIO 25  ←  Crisis button  (other leg to GND)
 *    GPIO 33  →  LED anode (→ 220Ω → GND)
 *    GPIO 22  →  OLED SCL
 *    GPIO 21  →  OLED SDA
 *    OLED VCC →  3.3V rail
 *    OLED GND →  GND rail
 *    Joystick VCC → 3.3V,  Joystick GND → GND
 *
 *  LIBRARIES (same as Hub — install once):
 *    1. ArduinoJson by Benoit Blanchon (version 6.x)
 *    2. Adafruit SSD1306 by Adafruit
 *    3. Adafruit GFX Library by Adafruit
 *
 *  BOARD SETUP:
 *    Same as Hub — "ESP32 Dev Module" — but pick the OTHER COM port.
 *
 *  NOTE ON JOYSTICK:
 *    If the joystick axes seem swapped or inverted, swap the
 *    JOY_X / JOY_Y pin assignments or change map() direction.
 *    Center calibration happens automatically at boot (don't
 *    touch the joystick while it starts up).
 *
 * ────────────────────────────────────────
 *  COMPILE ERROR?  If you see:
 *    "invalid conversion from 'void(*)(...esp_now_recv_info_t...)'"
 *  You have Arduino-ESP32 Core v3.x.  Change the onRecv signature to:
 *    void onRecv(const esp_now_recv_info_t *info, const uint8_t *data, int len)
 *  and replace `memcpy(hubMAC, mac, 6)` with `memcpy(hubMAC, info->src_addr, 6)`.
 * ────────────────────────────────────────
 */

#include <WiFi.h>
#include <esp_now.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <ArduinoJson.h>

// ── Pin Definitions ─────────────────────────────────
#define JOY_X        34   // analog input only
#define JOY_Y        35   // analog input only
#define JOY_BTN      27
#define BTN_SUBMIT   26
#define BTN_CRISIS   25
#define LED_PIN      33

// ── OLED (0.91" 128x32 SSD1306 I2C) ────────────────
#define SCREEN_W    128
#define SCREEN_H     32
#define OLED_ADDR  0x3C
Adafruit_SSD1306 oledDisplay(SCREEN_W, SCREEN_H, &Wire, -1);

// ── State Machine ───────────────────────────────────
enum TabletState { SEEKING, CONNECTED, IN_GAME, POST_GAME };
TabletState state = SEEKING;

// ── Hub connection ──────────────────────────────────
uint8_t hubMAC[6];
bool hubFound = false;

// ── Active command ──────────────────────────────────
bool hasCmd = false;
String cmdAction;         // "JOY", "BTN", or "CRISIS"
int cmdId       = 0;
int cmdTargetX  = 50;
int cmdTargetY  = 50;
int cmdTol      = 20;

// ── Joystick calibration ────────────────────────────
int joyCenterX = 2048;
int joyCenterY = 2048;

// ── Incoming message buffer ─────────────────────────
volatile bool newMsg = false;
char msgBuf[251];

// ── Timing ──────────────────────────────────────────
unsigned long lastOledRefresh = 0;
unsigned long lastBtnSubmit   = 0;
unsigned long lastBtnCrisis   = 0;

// ═══════════════════════════════════════════════════════
//  ESP-NOW callbacks
// ═══════════════════════════════════════════════════════
void onSent(const wifi_tx_info_t *info, esp_now_send_status_t st) { (void)info; (void)st; }

void onRecv(const esp_now_recv_info_t *info, const uint8_t *data, int len) {
  if (len > 250) len = 250;
  memcpy(msgBuf, data, len);
  msgBuf[len] = '\0';
  if (!hubFound) {
    memcpy(hubMAC, info->src_addr, 6);
  }
  newMsg = true;
}

// ═══════════════════════════════════════════════════════
//  Helpers
// ═══════════════════════════════════════════════════════
void oled(const char* l1, const char* l2 = "",
          const char* l3 = "", const char* l4 = "") {
  oledDisplay.clearDisplay();
  oledDisplay.setTextSize(1);
  oledDisplay.setTextColor(SSD1306_WHITE);
  oledDisplay.setCursor(0,  0); oledDisplay.print(l1);
  oledDisplay.setCursor(0,  8); oledDisplay.print(l2);
  oledDisplay.setCursor(0, 16); oledDisplay.print(l3);
  oledDisplay.setCursor(0, 24); oledDisplay.print(l4);
  oledDisplay.display();
}

void sendToHub(const char* json) {
  esp_now_send(hubMAC, (const uint8_t*)json, strlen(json));
  Serial.printf("[TAB TX] %s\n", json);
}

int readJoyX() { return map(analogRead(JOY_X), 0, 4095, 0, 100); }
int readJoyY() { return map(analogRead(JOY_Y), 0, 4095, 0, 100); }

void blinkLED(int times, int onMs, int offMs) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_PIN, HIGH); delay(onMs);
    digitalWrite(LED_PIN, LOW);  delay(offMs);
  }
}

// ═══════════════════════════════════════════════════════
//  SETUP
// ═══════════════════════════════════════════════════════
void setup() {
  Serial.begin(115200);
  Serial.println("\n=== SPACETEAM IRL — TABLET PROTOTYPE ===\n");

  pinMode(JOY_BTN,    INPUT_PULLUP);
  pinMode(BTN_SUBMIT, INPUT_PULLUP);
  pinMode(BTN_CRISIS, INPUT_PULLUP);
  pinMode(LED_PIN,    OUTPUT);

  // ── OLED init ──
  Wire.begin();
  if (!oledDisplay.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
    Serial.println("ERROR: OLED not found! Check wiring.");
    while (true) { delay(1000); }
  }
  oled("SPACETEAM IRL", "Tablet Prototype", "", "Booting...");
  delay(1000);

  // ── Calibrate joystick center (hands off!) ──
  joyCenterX = analogRead(JOY_X);
  joyCenterY = analogRead(JOY_Y);
  Serial.printf("Joystick center: X=%d  Y=%d\n", joyCenterX, joyCenterY);

  // ── WiFi + ESP-NOW init ──
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();

  if (esp_now_init() != ESP_OK) {
    Serial.println("ERROR: ESP-NOW init failed!");
    oled("ESP-NOW FAILED!", "Restart board", "", "");
    while (true) { delay(1000); }
  }
  esp_now_register_send_cb(onSent);
  esp_now_register_recv_cb(onRecv);

  state = SEEKING;
  oled("SEEKING HUB...", "", "Waiting for", "beacon...");
  Serial.println("Tablet seeking Hub...");
}

// ═══════════════════════════════════════════════════════
//  MAIN LOOP
// ═══════════════════════════════════════════════════════
void loop() {

  // ── Process incoming message ──────────────────────
  if (newMsg) {
    newMsg = false;

    StaticJsonDocument<200> doc;
    if (deserializeJson(doc, msgBuf)) {
      Serial.println("[TAB] JSON parse error");
    } else {
      const char* type = doc["type"];
      Serial.printf("[TAB RX] %s\n", msgBuf);

      // ── SEEKING: Hub beacon found ──
      if (state == SEEKING && strcmp(type, "BEACON") == 0) {
        Serial.printf("Hub found! MAC: %02X:%02X:%02X:%02X:%02X:%02X\n",
          hubMAC[0], hubMAC[1], hubMAC[2],
          hubMAC[3], hubMAC[4], hubMAC[5]);

        // Register Hub as peer
        esp_now_peer_info_t peer;
        memset(&peer, 0, sizeof(peer));
        memcpy(peer.peer_addr, hubMAC, 6);
        peer.channel = 0;
        peer.encrypt = false;
        esp_now_add_peer(&peer);
        hubFound = true;

        sendToHub("{\"type\":\"JOIN\",\"arch\":\"NAV\"}");
        oled("HUB FOUND!", "Joining...", "", "");
      }

      // ── SEEKING: Hub acknowledged us ──
      else if (state == SEEKING && strcmp(type, "ACK") == 0) {
        int pid = doc["pid"];
        state = CONNECTED;

        char l2[22];
        snprintf(l2, 22, "Player ID: %d", pid);
        oled("CONNECTED!", l2, "", "Waiting for game...");
        digitalWrite(LED_PIN, HIGH);
        Serial.printf("Joined as Player %d\n", pid);
      }

      // ── Game starting! ──
      else if (strcmp(type, "START") == 0) {
        state  = IN_GAME;
        hasCmd = false;
        oled("GAME STARTING!", "", "  Get ready!", "");
        Serial.println("Game starting!");
      }

      // ── New command from Hub ──
      else if (state == IN_GAME && strcmp(type, "CMD") == 0) {
        const char* act = doc["act"];
        cmdId     = doc["cid"];
        cmdAction = String(act);
        hasCmd    = true;

        if (cmdAction == "JOY") {
          cmdTargetX = doc["x"];
          cmdTargetY = doc["y"];
          cmdTol     = doc["tol"];
          // OLED updated in live-refresh below
          Serial.printf("CMD: Joystick → (%d, %d)\n", cmdTargetX, cmdTargetY);

        } else if (cmdAction == "BTN") {
          oled(">> PRESS <<", "", " Hit SUBMIT btn!", "");
          Serial.println("CMD: Press SUBMIT");

        } else if (cmdAction == "CRISIS") {
          oled("!! CRISIS !!", "", "  HIT CRISIS", "  BUTTON NOW!!");
          blinkLED(3, 80, 80);   // alarm blink
          Serial.println("CMD: CRISIS!");
        }
      }

      // ── Result from Hub ──
      else if (strcmp(type, "RESULT") == 0) {
        bool ok      = doc["ok"];
        bool timeout = doc.containsKey("timeout");
        int  sc      = doc["score"] | 0;
        hasCmd = false;

        if (timeout) {
          oled("  TOO SLOW!", "", "  Timed out!", "");
          blinkLED(5, 40, 40);
        } else if (ok) {
          oled("  SUCCESS!", "", "  Nice work!", "");
          blinkLED(2, 150, 150);
        } else {
          oled("  MISS!", "", "  Not quite...", "");
          blinkLED(4, 60, 60);
        }

        Serial.printf("Result: %s  Score: %d\n", ok ? "HIT" : "MISS", sc);
      }
    }
  }

  // ── Live joystick display (JOY commands only) ─────
  if (state == IN_GAME && hasCmd && cmdAction == "JOY") {
    if (millis() - lastOledRefresh > 100) {
      lastOledRefresh = millis();

      int jx = readJoyX();
      int jy = readJoyY();
      int dx = abs(jx - cmdTargetX);
      int dy = abs(jy - cmdTargetY);
      bool inRange = (dx <= cmdTol && dy <= cmdTol);

      char l1[22], l2[22], l3[22], l4[22];
      snprintf(l1, 22, "TARGET: %d , %d", cmdTargetX, cmdTargetY);
      snprintf(l2, 22, "NOW:    %d , %d", jx, jy);
      snprintf(l3, 22, "diff:   %d , %d", dx, dy);
      snprintf(l4, 22, "%s", inRange ? "> IN RANGE! SUBMIT <" : "   keep moving...");

      oled(l1, l2, l3, l4);
      digitalWrite(LED_PIN, inRange ? HIGH : LOW);
    }
  }

  // ── Submit button ─────────────────────────────────
  if (state == IN_GAME && hasCmd &&
      (cmdAction == "JOY" || cmdAction == "BTN") &&
      digitalRead(BTN_SUBMIT) == LOW &&
      millis() - lastBtnSubmit > 250) {

    lastBtnSubmit = millis();

    StaticJsonDocument<100> doc;
    doc["type"] = "SUBMIT";
    doc["cid"]  = cmdId;
    if (cmdAction == "JOY") {
      doc["x"] = readJoyX();
      doc["y"] = readJoyY();
    }
    char buf[100];
    serializeJson(doc, buf, sizeof(buf));
    sendToHub(buf);

    hasCmd = false;
    oled("  SENT!", "", "  Waiting...", "");
    Serial.printf("Submitted: %s\n", buf);
  }

  // ── Crisis button ─────────────────────────────────
  if (state == IN_GAME && hasCmd &&
      cmdAction == "CRISIS" &&
      digitalRead(BTN_CRISIS) == LOW &&
      millis() - lastBtnCrisis > 250) {

    lastBtnCrisis = millis();

    StaticJsonDocument<64> doc;
    doc["type"] = "SUBMIT";
    doc["cid"]  = cmdId;
    char buf[64];
    serializeJson(doc, buf, sizeof(buf));
    sendToHub(buf);

    hasCmd = false;
    oled(" CRISIS HANDLED!", "", "", "");
    blinkLED(1, 300, 0);
    Serial.println("Crisis button pressed!");
  }

  // ── SEEKING: blink LED while searching ────────────
  if (state == SEEKING) {
    static unsigned long lastBlink = 0;
    if (millis() - lastBlink > 500) {
      lastBlink = millis();
      digitalWrite(LED_PIN, !digitalRead(LED_PIN));
    }
  }
}
