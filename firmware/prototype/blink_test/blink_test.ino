// Blink test — ESP32 DevKit V1 onboard LED (GPIO 2)
// Upload with: Board = "ESP32 Dev Module", 115200 baud

#define LED_PIN 2

void setup() {
  pinMode(LED_PIN, OUTPUT);
}

void loop() {
  digitalWrite(LED_PIN, HIGH);
  delay(500);
  digitalWrite(LED_PIN, LOW);
  delay(500);
}
