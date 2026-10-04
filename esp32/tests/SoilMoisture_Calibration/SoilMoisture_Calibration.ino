/* Capacitive soil-moisture sensor calibration - ESP32-S3
   Wiring: Sensor VCC -> 3.3V, GND -> GND, AO -> GPIO 36
   Never power the sensor from 5V when AO goes directly to ESP32.
   Record the raw reading in dry air and fully wet soil, then copy those
   values to SOIL_DRY_RAW and SOIL_WET_RAW in SmartGreenhouse.ino.
*/
constexpr uint8_t SOIL_PIN = 36;
constexpr int SOIL_DRY_RAW = 3000; // temporary values until calibration completes
constexpr int SOIL_WET_RAW = 1300;

int averageRawReading() {
  long total = 0;
  for (int sample = 0; sample < 20; sample++) {
    total += analogRead(SOIL_PIN);
    delay(20);
  }
  return total / 20;
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(12); // ESP32-S3 ADC output: 0 to 4095
  Serial.println("Soil sensor calibration test started");
  Serial.println("First hold probe in dry air; then insert it into wet soil.");
}

void loop() {
  int raw = averageRawReading();
  int moisture = constrain(map(raw, SOIL_DRY_RAW, SOIL_WET_RAW, 0, 100), 0, 100);
  Serial.printf("Raw ADC: %d | Estimated moisture: %d %%\n", raw, moisture);
  delay(1000);
}
