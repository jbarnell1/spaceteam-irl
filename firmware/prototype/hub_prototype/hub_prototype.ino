/*
 * =====================================================
 *  SPACETEAM IRL — Hub Prototype
 *  ESP32 DevKit V1
 * =====================================================
 *
 *  WIRING:
 *    GPIO 27  ←  Start button (other leg to GND)
 *    GPIO 22  →  OLED SCL
 *    GPIO 21  →  OLED SDA
 *    GPIO  2  =  Onboard blue LED (no wiring)
 *    OLED VCC →  3.3V rail
 *    OLED GND →  GND rail
 *
 *  LIBRARIES (install via Arduino IDE Library Manager):
 *    1. ArduinoJson by Benoit Blanchon (version 6.x)
 *    2. Adafruit SSD1306 by Adafruit
 *    3. Adafruit GFX Library by Adafruit (installed automatically with SSD1306)
 *
 *  BOARD SETUP (Arduino IDE):
 *    1. File → Preferences → Additional Board URLs → add:
 *       https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
 *    2. Tools → Board → Board Manager → search "esp32" → install "ESP32 by Espressif"
 *    3. Tools → Board → ESP32 Arduino → "ESP32 Dev Module"
 *    4. Tools → Port → select the COM port for THIS board
 *    5. Upload Speed → 115200
 *
 *  HOW TO PLAY:
 *    1. Flash this sketch to the HUB ESP32
 *    2. Flash tablet_prototype.ino to the TABLET ESP32
 *    3. Both boards power up → Hub blinks, sends beacons
 *    4. Tablet finds Hub → auto-connects
 *    5. Hub OLED says "Press button to start"
 *    6. Press the Hub button → 3-2-1 countdown → game begins!
 *    7. Hub sends 10 commands to the tablet. Player must:
 *       - JOYSTICK commands: move joystick to target position, press SUBMIT
 *       - BUTTON commands:   press SUBMIT button
 *       - CRISIS commands:   press CRISIS button before time runs out
 *    8. After 10 commands → score screen. Press button to play again.
 */

#include <WiFi.h>
#include <esp_now.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <ArduinoJson.h>

// ── Pin Definitions ─────────────────────────────────
#define BTN_PIN      27
#define LED_PIN       2   // onboard blue LED

// ── OLED (0.91" 128x32 SSD1306 I2C) ────────────────
#define SCREEN_W    128
#define SCREEN_H     32
#define OLED_ADDR  0x3C
Adafruit_SSD1306 oledDisplay(SCREEN_W, SCREEN_H, &Wire, -1);

// ── Game State Machine ──────────────────────────────
enum HubState { PAIRING, READY, PLAYING, GAME_OVER };
HubState state = PAIRING;

// ── Tablet connection ───────────────────────────────
uint8_t tabletMAC[6];
bool tabletConnected = false;

// ── Command tracking ────────────────────────────────
int currentCmd      = 0;
const int TOTAL_CMDS = 10;
int score           = 0;
bool waitingForResp = false;
unsigned long cmdSentAt  = 0;
unsigned long cmdTimeout = 0;
int targetX, targetY;
String cmdType;         // "JOY", "BTN", or "CRISIS"

// ── Incoming message buffer ─────────────────────────
// (filled by ESP-NOW callback, consumed by loop)
volatile bool newMsg = false;
char msgBuf[251];

// ── Timing ──────────────────────────────────────────
unsigned long lastBeacon  = 0;
unsigned long lastBtnTime = 0;

// ═══════════════════════════════════════════════════════
//  ESP-NOW callbacks (run in WiFi task — keep fast!)
// ═══════════════════════════════════════════════════════
void onSent(const wifi_tx_info_t *info, esp_now_send_status_t st) {
  // nothing needed for prototype
  (void)info; (void)st;
}

void onRecv(const esp_now_recv_info_t *info, const uint8_t *data, int len) {
  if (len > 250) len = 250;
  memcpy(msgBuf, data, len);
  msgBuf[len] = '\0';
  // Capture MAC of sender (for pairing)
  if (!tabletConnected) {
    memcpy(tabletMAC, info->src_addr, 6);
  }
  newMsg = true;
}

// ═══════════════════════════════════════════════════════
//  Helper: write 4 lines to OLED (21 chars max per line)
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

// ═══════════════════════════════════════════════════════
//  Helper: send JSON to tablet (direct, not broadcast)
// ═══════════════════════════════════════════════════════
void sendToTablet(const char* json) {
  esp_now_send(tabletMAC, (const uint8_t*)json, strlen(json));
  Serial.printf("[HUB TX] %s\n", json);
}

void sendBroadcast(const char* json) {
  uint8_t bcast[] = {0xFF,0xFF,0xFF,0xFF,0xFF,0xFF};
  esp_now_send(bcast, (const uint8_t*)json, strlen(json));
}

// ═══════════════════════════════════════════════════════
//  Generate and send the next command
// ═══════════════════════════════════════════════════════
void sendNextCommand() {
  StaticJsonDocument<200> doc;
  doc["type"] = "CMD";
  doc["cid"]  = currentCmd;

  int r = random(0, 10);  // 0-9

  if (r < 5) {
    // ── Joystick: move to target ──
    targetX = random(15, 86);   // avoid extremes
    targetY = random(15, 86);
    doc["act"]     = "JOY";
    doc["x"]       = targetX;
    doc["y"]       = targetY;
    doc["tol"]     = 20;
    doc["timeout"] = 10000;
    cmdType    = "JOY";
    cmdTimeout = 10000;
  } else if (r < 8) {
    // ── Press submit button ──
    doc["act"]     = "BTN";
    doc["timeout"] = 6000;
    cmdType    = "BTN";
    cmdTimeout = 6000;
  } else {
    // ── Crisis: press crisis button ──
    doc["act"]     = "CRISIS";
    doc["timeout"] = 4000;
    cmdType    = "CRISIS";
    cmdTimeout = 4000;
  }

  char buf[200];
  serializeJson(doc, buf, sizeof(buf));
  sendToTablet(buf);

  cmdSentAt       = millis();
  waitingForResp  = true;

  // Update Hub OLED
  char line1[22], line2[22], line3[22], line4[22];
  snprintf(line1, 22, "Cmd %d/%d  Score:%d", currentCmd + 1, TOTAL_CMDS, score);

  if (cmdType == "JOY") {
    snprintf(line2, 22, "JOYSTICK -> %d,%d", targetX, targetY);
    snprintf(line3, 22, "Tolerance: +/- 20");
  } else if (cmdType == "BTN") {
    snprintf(line2, 22, "PRESS SUBMIT!");
    line3[0] = '\0';
  } else {
    snprintf(line2, 22, "** CRISIS!! **");
    snprintf(line3, 22, "Press crisis btn!");
  }
  snprintf(line4, 22, "Timeout: %lus", cmdTimeout / 1000);
  oled(line1, line2, line3, line4);
}

// ═══════════════════════════════════════════════════════
//  Handle command result and advance game
// ═══════════════════════════════════════════════════════
void resolveCommand(bool success, bool timeout) {
  if (success) score++;
  waitingForResp = false;
  currentCmd++;

  // Send result to tablet
  StaticJsonDocument<100> res;
  res["type"]  = "RESULT";
  res["ok"]    = success;
  res["score"] = score;
  if (timeout) res["timeout"] = true;
  char buf[100];
  serializeJson(res, buf, sizeof(buf));
  sendToTablet(buf);

  // Show result on Hub OLED
  char line1[22], line2[22];
  if (timeout)     snprintf(line1, 22, "** TIMEOUT! **");
  else if (success) snprintf(line1, 22, "** SUCCESS! **");
  else              snprintf(line1, 22, "** MISS! **");
  snprintf(line2, 22, "Score: %d / %d", score, currentCmd);

  if (currentCmd >= TOTAL_CMDS) {
    // ── Game Over ──
    oled(line1, line2, "", "");
    delay(1500);
    state = GAME_OVER;

    float pct = (float)score / TOTAL_CMDS * 100.0f;
    char g2[22], g3[22];
    snprintf(g2, 22, "Score: %d / %d", score, TOTAL_CMDS);
    snprintf(g3, 22, "Accuracy: %.0f%%", pct);
    oled("== GAME OVER ==", g2, g3, "Press btn to replay");
    Serial.printf("GAME OVER — Score: %d/%d (%.0f%%)\n", score, TOTAL_CMDS, pct);
  } else {
    // ── Next command after brief pause ──
    oled(line1, line2, "", "Next in 2s...");
    delay(2000);
    sendNextCommand();
  }
}

// ═══════════════════════════════════════════════════════
//  SETUP
// ═══════════════════════════════════════════════════════
void setup() {
  Serial.begin(115200);
  Serial.println("\n=== SPACETEAM IRL — HUB PROTOTYPE ===\n");

  pinMode(BTN_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);

  // ── OLED init ──
  Wire.begin();
  if (!oledDisplay.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
    Serial.println("ERROR: OLED not found! Check wiring.");
    while (true) { delay(1000); }
  }
  oled("SPACETEAM IRL", "Hub Prototype", "", "Booting...");
  delay(1000);

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

  // Register broadcast address for beacons
  esp_now_peer_info_t bcastPeer;
  memset(&bcastPeer, 0, sizeof(bcastPeer));
  memset(bcastPeer.peer_addr, 0xFF, 6);
  bcastPeer.channel = 0;
  bcastPeer.encrypt = false;
  esp_now_add_peer(&bcastPeer);

  randomSeed(analogRead(0) ^ micros());

  state = PAIRING;
  oled("PAIRING MODE", "Waiting for", "tablet...", "");
  Serial.println("Hub in pairing mode — waiting for tablet");
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
      Serial.println("[HUB] JSON parse error");
    } else {
      const char* type = doc["type"];
      Serial.printf("[HUB RX] %s\n", msgBuf);

      // ── PAIRING: tablet wants to join ──
      if (state == PAIRING && strcmp(type, "JOIN") == 0) {
        Serial.printf("Tablet connected! MAC: %02X:%02X:%02X:%02X:%02X:%02X\n",
          tabletMAC[0], tabletMAC[1], tabletMAC[2],
          tabletMAC[3], tabletMAC[4], tabletMAC[5]);

        // Add tablet as direct peer
        esp_now_peer_info_t peer;
        memset(&peer, 0, sizeof(peer));
        memcpy(peer.peer_addr, tabletMAC, 6);
        peer.channel = 0;
        peer.encrypt = false;
        esp_now_add_peer(&peer);
        tabletConnected = true;

        sendToTablet("{\"type\":\"ACK\",\"pid\":1}");

        state = READY;
        oled("TABLET JOINED!", "Archetype: NAV", "", "Press btn to start");
        digitalWrite(LED_PIN, HIGH);
      }

      // ── PLAYING: tablet submitted a response ──
      else if (state == PLAYING && waitingForResp && strcmp(type, "SUBMIT") == 0) {
        bool success = false;

        if (cmdType == "JOY") {
          int sx = doc["x"];
          int sy = doc["y"];
          success = (abs(sx - targetX) <= 20 && abs(sy - targetY) <= 20);
          Serial.printf("  Joystick: got(%d,%d) want(%d,%d) → %s\n",
            sx, sy, targetX, targetY, success ? "HIT" : "MISS");
        }
        else if (cmdType == "BTN" || cmdType == "CRISIS") {
          success = true;  // pressing the right button is always success
          Serial.printf("  %s button pressed → HIT\n", cmdType.c_str());
        }

        resolveCommand(success, false);
      }
    }
  }

  // ── State-specific logic ──────────────────────────
  switch (state) {

    case PAIRING:
      // Blink LED + send beacons every second
      if (millis() - lastBeacon > 1000) {
        lastBeacon = millis();
        sendBroadcast("{\"type\":\"BEACON\"}");
        digitalWrite(LED_PIN, !digitalRead(LED_PIN));
      }
      break;

    case READY:
      // Wait for button press → start game
      if (digitalRead(BTN_PIN) == LOW && millis() - lastBtnTime > 300) {
        lastBtnTime = millis();
        currentCmd = 0;
        score      = 0;
        state      = PLAYING;

        sendToTablet("{\"type\":\"START\",\"total\":10}");

        oled("GET READY!", "", "  3 . . .", "");   delay(1000);
        oled("GET READY!", "", "  2 . . .", "");   delay(1000);
        oled("GET READY!", "", "  1 . . .", "");   delay(1000);
        oled("", "     G O !", "", "");            delay(600);

        sendNextCommand();
      }
      break;

    case PLAYING:
      // Check for timeout
      if (waitingForResp && millis() - cmdSentAt > cmdTimeout) {
        Serial.printf("  Command %d TIMED OUT\n", currentCmd + 1);
        resolveCommand(false, true);
      }
      break;

    case GAME_OVER:
      // Button press → play again
      if (digitalRead(BTN_PIN) == LOW && millis() - lastBtnTime > 300) {
        lastBtnTime = millis();
        state = READY;
        oled("TABLET CONNECTED!", "", "Press btn to start", "");
      }
      break;
  }
}
