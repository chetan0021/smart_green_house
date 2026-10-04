# Smart Greenhouse Automation Using IoT and Vision-Based Plant Disease Classification

## Recommended paper title

**Design and Implementation of an ESP32-S3-Based Smart Greenhouse with Automated Climate Control and Vision-Based Leaf Disease Classification**

## Abstract

This work presents a smart greenhouse prototype that combines Internet of Things (IoT) monitoring, local actuator control, cloud-ready telemetry, and vision-based plant disease classification. An ESP32-S3 DevKit collects air temperature and relative humidity from a DHT11 sensor and soil moisture from a capacitive sensor. The controller applies local fail-safe control rules: a ventilation fan turns on when the temperature reaches 35 degrees C and turns off below 32 degrees C, while a water pump runs a 10-second irrigation burst when soil moisture falls below 30 percent, followed by a 30-second soaking interval. A laptop-hosted vision module accepts either a webcam capture or an uploaded leaf image and classifies it using a locally deployed CropGuard ResNet-50 ONNX model trained for 38 PlantVillage crop-disease classes. A web dashboard provides live sensor cards, trend plots, actuator states, manual overrides, disease results, and configurable email alerts. The architecture separates time-critical control from the dashboard so the ESP32 continues fan and pump control during a dashboard or network failure. The prototype provides a low-cost platform for controlled-environment agriculture; however, disease predictions are limited to the model's supported crop classes and must be tested on real greenhouse images before agronomic use.

**Keywords:** Smart greenhouse, ESP32-S3, Internet of Things, precision agriculture, soil moisture, automated irrigation, leaf disease classification, ONNX Runtime, computer vision.

## 1. Introduction

Greenhouse cultivation needs continuous monitoring because temperature, humidity, irrigation, illumination, and plant health affect crop growth. Manual observation delays corrective action and can waste water or energy. IoT systems provide continuous sensing and remote monitoring, while local embedded control can operate equipment with low latency. Machine learning extends the system from environmental monitoring to early identification of leaf diseases.

This project integrates these elements in one prototype. The ESP32-S3 performs environmental sensing and relay control. The laptop runs disease classification because it has more memory and processing capability than the microcontroller. The dashboard presents both sensor data and image-analysis results in one interface. The intended contribution is not a claim of a newly trained disease model; it is the design and implementation of a complete, fault-aware IoT and vision integration architecture.

## 2. Problem statement

Small greenhouses often rely on manual monitoring and switching of irrigation and ventilation equipment. This can cause overwatering, delayed cooling, inconsistent plant observation, and poor visibility when the grower is away. Existing vision classifiers may also be difficult to use in daily cultivation if their result is disconnected from environmental history and actuator state.

The problem addressed is the development of an affordable greenhouse platform that can:

1. Measure environmental conditions continuously.
2. Control a pump and fan automatically from local sensor thresholds.
3. Continue essential control when the dashboard or internet is unavailable.
4. Display telemetry, trends, controls, and leaf-disease analysis in one dashboard.
5. Send alerts when a condition needs human attention.

## 3. Objectives

### Primary objective

Design and implement an ESP32-S3 smart greenhouse that combines real-time environmental monitoring, automated irrigation and ventilation, web-based supervision, and leaf disease classification.

### Specific objectives

1. Interface DHT11 and capacitive soil-moisture sensors with an ESP32-S3.
2. Implement relay-based control for a water pump, cooling fan, and grow light.
3. Apply temperature hysteresis to prevent repeated fan relay switching.
4. Apply burst-and-soak irrigation to avoid continuously running the pump.
5. Send structured JSON telemetry over Wi-Fi using HTTP.
6. Build a dashboard with KPI cards, history plots, actuator states, manual controls, and camera-based disease analysis.
7. Classify a captured or uploaded leaf image using a trained 38-class model.
8. Generate configurable email alerts for critical conditions.
9. Document the limits of the disease model and test the prototype with controlled experiments.

## 4. System architecture

### 4.1 Functional layers

**Sensing layer:** DHT11 measures temperature and relative humidity. The capacitive sensor measures soil moisture. An optional voltage-divider circuit can later provide battery voltage. An optional LDR or BH1750 can provide true light data.

**Edge control layer:** ESP32-S3 reads sensors, evaluates automation rules, drives relay inputs, and posts telemetry. The local rule engine remains responsible for critical fan and pump control.

**Application layer:** A Flask service validates telemetry, exposes configuration endpoints, maintains local dashboard history, serves a dashboard, and runs local ONNX leaf classification.

**Presentation layer:** The browser dashboard displays live values, graph history, device state, control settings, webcam capture, image upload, annotated result imagery, and diagnosis confidence.

**Deployment layer:** For production, deploy the dashboard on Vercel, a persistent disease/telemetry service on Render or Railway, and use Supabase for permanent telemetry, images, alerts, and real-time subscriptions.

### 4.2 Data flow

1. ESP32-S3 reads temperature, humidity, soil moisture, and optional battery/light values.
2. ESP32-S3 applies fan and pump control locally.
3. ESP32-S3 posts a JSON snapshot to `POST /api/telemetry` every 10 seconds.
4. The server stores the reading and returns current control configuration.
5. The dashboard polls the API every 5 seconds and redraws KPI values and graph lines.
6. The user captures a webcam frame or uploads an image.
7. The server runs the leaf image through the disease classifier and returns a disease label, confidence, and annotated image.
8. Alerts are triggered by configured environmental or disease conditions.

## 5. Hardware design

### 5.1 Implemented bill of materials

- ESP32-S3 DevKit N16R8.
- DHT11 temperature and humidity sensor.
- Capacitive soil moisture sensor.
- 5 V relay module, used to isolate the ESP32 GPIOs from actuator circuits.
- 12 V DC cooling fan.
- DC water pump.
- LED grow strip.
- Two 18650 Li-ion cells and holder.
- TP4056 charging module.
- LM2596 buck converter for low-voltage supply.
- XL6009 boost converter for 12 V actuator supply.
- DC panel voltmeter for demonstration.

### 5.2 Prototype GPIO assignment

| Function | ESP32-S3 pin | Notes |
|---|---:|---|
| DHT11 data | GPIO 4 | Use 3.3 V, common ground, and correct pull-up configuration. |
| Soil moisture analogue output | GPIO 1 | Power the sensor at 3.3 V to protect ESP32 analogue input. |
| Pump relay | GPIO 16 | Drives relay input only, never pump power directly. |
| Fan relay | GPIO 17 | Drives relay input only. |
| Grow-light relay | GPIO 18 | Drives relay input only. |
| Optional light sensor | GPIO 2 | Requires LDR module or an appropriate sensor interface. |
| Optional battery divider | GPIO 3 | Requires a resistor divider that limits GPIO input to 3.3 V maximum. |

### 5.3 Electrical safety notes

The ESP32 GPIO pin must never power a pump, fan, or grow light. Each actuator must use an appropriately rated relay or MOSFET driver, with a common low-voltage ground where the driver requires it. The 12 V supply must be sized for the combined fan and pump current. Battery-voltage measurement requires a properly calculated voltage divider, because a two-cell battery can exceed the ESP32 analogue input limit. The digital DC panel voltmeter in the BOM is only a display and cannot provide telemetry by itself.

## 6. Software implementation

### 6.1 ESP32 firmware

The firmware is located in `esp32/SmartGreenhouse.ino`. It uses Wi-Fi, HTTPClient, ArduinoJson, and the DHT library. It connects to fixed Wi-Fi credentials, periodically downloads configuration, posts telemetry JSON, applies local control, and reports the actual relay states.

The prototype uses HTTP for LAN tests. A deployed implementation must use HTTPS and device authentication. Wi-Fi credentials, backend URLs, SMTP credentials, and database keys must never be committed to source control.

### 6.2 Server and dashboard

The local application is a Flask server in `app.py`. Main endpoints are:

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | GET | Serves the dashboard. |
| `/api/telemetry` | POST | Accepts ESP32 telemetry JSON. |
| `/api/telemetry` | GET | Returns current and recent sensor readings. |
| `/api/config` | GET | Returns automation and manual-control configuration. |
| `/api/config` | PUT | Updates dashboard control settings. |
| `/upload_json` | POST | Accepts a leaf image and returns classification and annotated image data. |

### 6.3 Dashboard functions

- Temperature, humidity, soil moisture, and battery KPI cards.
- Trend plot for the latest 60 readings.
- Live relay-state indicators for pump, fan, and grow light.
- Per-device automatic/manual toggles.
- Webcam capture and image-upload workflow.
- Disease result and confidence display.
- Email alert hooks using SMTP configuration.

## 7. Control algorithms

### 7.1 Fan hysteresis

The fan rule prevents relay chattering near the threshold:

\[
F(t) = \begin{cases}
1, & T(t) \ge 35^\circ C \\
0, & T(t) \le 32^\circ C \\
F(t-1), & 32 < T(t) < 35
\end{cases}
\]

where `F(t)` is fan state and `T(t)` is measured air temperature.

### 7.2 Burst-and-soak irrigation

When soil moisture `M(t)` drops below 30%, the pump runs for 10 seconds. It then turns off for 30 seconds so water can infiltrate the soil before a new reading is evaluated. This avoids a continuously active pump and reduces rapid switching.

\[
\text{Start pump if } M(t) < 30\% \text{ and the soak timer has expired}
\]

### 7.3 Manual override

Each actuator has an independent mode. In automatic mode, the ESP32 runs the appropriate local logic. In manual mode, the ESP32 applies the requested dashboard state. Manual mode should be used briefly and visibly because it bypasses automatic protection.

## 8. Leaf disease classification module

### 8.1 Model and input pipeline

The local implementation uses the CropGuard ResNet-50 ONNX model and a 38-label mapping. The input image is converted to RGB, resized with short-side scaling, center cropped to 224 by 224 pixels, normalized with ImageNet mean and standard deviation, converted to NCHW layout, and executed through ONNX Runtime on CPU.

The resulting logits are temperature-scaled using the published calibration value, converted to probabilities by softmax, and the highest-probability class is selected. If confidence is below 55%, the application returns an uncertain result rather than claiming a diagnosis.

### 8.2 Supported scope

The model supports 38 PlantVillage labels across 14 crop species. It includes conditions such as apple scab, apple black rot, potato early and late blight, corn rust, grape diseases, and several tomato diseases. It cannot identify every plant species or every disease.

### 8.3 Critical limitation

PlantVillage images are mainly controlled single-leaf images. Camera photos inside a greenhouse can contain uneven illumination, occlusion, multiple leaves, soil background, image blur, and plants outside the training classes. Therefore, confidence is not proof of a correct agricultural diagnosis. The research paper should report controlled test accuracy separately from field-image accuracy and should not claim universal disease detection.

## 9. Alert rules

| Event | Implemented trigger | Suggested notification content |
|---|---|---|
| Critical heat | Temperature above 38 C for five continuous minutes | Time, temperature, fan state, request for ventilation inspection. |
| Irrigation failure risk | Soil moisture below 20% while pump is reported on | Time, moisture, pump state, reservoir/pipe check. |
| Battery low | Battery voltage below 3.3 V after a real divider is fitted | Time, voltage, request for backup/grid intervention. |
| Disease detection | Disease label confidence above 85% and label is not healthy | Time, disease class, confidence, captured-image reference. |

Email delivery needs `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, and `ALERT_TO_EMAIL` environment variables. In production, a transactional service such as Resend or SendGrid plus a server-side function is preferable.

## 10. Experimental methodology

Do not fabricate results. Run and record the following experiments before writing the Results section.

### Experiment A: Sensor validation

Measure temperature with a calibrated thermometer, humidity with a reference hygrometer, and soil moisture at dry, medium, and wet conditions. Collect at least 30 paired readings for each sensor.

Metrics:

\[
MAE = \frac{1}{n}\sum_{i=1}^{n}|y_i-\hat{y}_i|
\]

\[
RMSE = \sqrt{\frac{1}{n}\sum_{i=1}^{n}(y_i-\hat{y}_i)^2}
\]

Report mean absolute error, root mean square error, sensor sampling interval, and calibration procedure.

### Experiment B: Fan-control validation

Gradually increase temperature or simulate DHT11 values in a safe bench test. Verify that the fan turns on at 35 C and remains on until temperature falls below 32 C. Record activation temperature, deactivation temperature, and the number of relay transitions around the threshold.

### Experiment C: Irrigation-control validation

Calibrate the soil sensor raw values in dry air and fully wet soil. Test the 10-second pump burst and 30-second soak interval. Measure water delivered in one burst and observe whether moisture rises after the soak period.

### Experiment D: Telemetry performance

Run the ESP32 for at least two hours with a 10-second interval. Record total expected messages, messages received, lost messages, mean API latency, and reconnect count.

\[
Delivery\ Rate = \frac{Received\ Messages}{Expected\ Messages} \times 100
\]

### Experiment E: Disease-classification evaluation

Use two test sets:

1. Supported, clear leaf images with known labels.
2. Real greenhouse/laptop-webcam images.

For each set, record class, predicted label, confidence, correct/incorrect status, and inference time. Report accuracy, macro precision, macro recall, macro F1 score, confusion matrix, and average inference time. Do not use images from the model's training set to make a performance claim.

### Experiment F: Reliability test

Disconnect dashboard Wi-Fi or stop the server after the ESP32 starts. Demonstrate that local fan and pump automation still works. This validates the edge-control design.

## 11. Results section template

Use this wording only after inserting measured values:

"The prototype transmitted [N] of [N] expected sensor messages during the [duration] test, giving a delivery rate of [X]%. The mean telemetry latency was [X] ms. The fan activated at [X] degrees C and deactivated at [X] degrees C, consistent with the programmed hysteresis. The pump delivered [X] mL during a 10-second burst. On the independent leaf-image test set, the classifier achieved [X]% accuracy and macro F1 of [X]. On greenhouse webcam images, performance was [X], illustrating the effect of real-world imaging conditions."

## 12. Discussion points

- Local ESP32 control improves resilience because environmental safety does not depend on a web dashboard.
- Burst-and-soak irrigation is simpler and safer for a prototype than a continuously running pump, but the threshold must be calibrated for each plant and soil medium.
- DHT11 is low cost but lower precision and slower than DHT22/SHT31. State this as a prototype trade-off.
- The laptop-based model avoids overloading the ESP32-S3 but requires a laptop or hosted inference service.
- The disease module improves operator awareness but does not replace professional plant pathology advice.
- A Vercel frontend plus Supabase/backend architecture supports remote use, but endpoint authentication and HTTPS are required before real deployment.

## 13. Conclusion

The proposed smart greenhouse prototype integrates edge sensing and actuation with browser-based monitoring and vision-assisted disease screening. The ESP32-S3 measures environmental parameters, uses local hysteresis and irrigation timing to control actuators, and posts telemetry for remote visualization. The webcam-based model enables leaf image classification without requiring a high-memory model on the microcontroller. The separation between edge control and dashboard services is a central strength because core automation can continue during application-side failures. Future work should include field-image model fine-tuning, permanent cloud storage, authenticated MQTT or HTTPS telemetry, water-level sensing, battery monitoring hardware, a true light sensor, and a controlled quantitative evaluation.

## 14. Reference list (IEEE style starting point)

[1] M. S. Farooq, R. Javid, S. Riaz, and Z. Atal, “IoT Based Smart Greenhouse Framework and Control Strategies for Sustainable Agriculture,” *IEEE Access*, vol. 10, pp. 99394-99420, 2022, doi: 10.1109/ACCESS.2022.3204066.

[2] S. P. Mohanty, D. P. Hughes, and M. Salathé, “Using Deep Learning for Image-Based Plant Disease Detection,” *Frontiers in Plant Science*, vol. 7, Art. 1419, 2016, doi: 10.3389/fpls.2016.01419.

[3] Espressif Systems, “ESP32-S3 Series Datasheet.” Accessed Sep. 30, 2026. [Online]. Available: https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf

[4] TensorFlow Datasets, “plant_village.” Accessed Sep. 30, 2026. [Online]. Available: https://www.tensorflow.org/datasets/catalog/plant_village

[5] A. Mahmood *et al.*, “ConvGeM-next: a deep learning framework for plant disease detection,” *Frontiers in Plant Science*, 2026. Use this only after verifying the author list and DOI from the final paper version.

## 15. Files supplied with the implementation

- `app.py`: Flask API, telemetry service, email hooks, and ONNX inference.
- `templates/dashboard.html`: dashboard user interface.
- `esp32/SmartGreenhouse.ino`: ESP32-S3 firmware.
- `cropguard.onnx`, `cropguard_classes.json`, `cropguard_calibration.json`: local disease model files.
- `GREENHOUSE_SETUP.md`: setup, wiring, calibration, Wi-Fi, and SMTP guidance.
