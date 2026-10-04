/* Optional battery-voltage test - ESP32-S3
   Requires a resistor divider connected to GPIO 3. Never connect a 2-cell
   18650 battery directly to an ESP32 GPIO. This sketch assumes a 1:1 divider;
   replace DIVIDER_RATIO after measuring/calibrating against a multimeter.
*/
constexpr uint8_t BATTERY_PIN = 3;
constexpr float ADC_REFERENCE_VOLTAGE = 3.3;
constexpr float ADC_MAX = 4095.0;
constexpr float DIVIDER_RATIO = 2.0;

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  Serial.println("Battery divider test started");
}

void loop() {
  int raw = analogRead(BATTERY_PIN);
  float voltage = raw * (ADC_REFERENCE_VOLTAGE / ADC_MAX) * DIVIDER_RATIO;
  Serial.printf("Battery ADC: %d | Estimated voltage: %.2f V\n", raw, voltage);
  delay(1000);
}
