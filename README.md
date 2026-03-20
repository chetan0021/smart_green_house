# PlantScan Server

A Flask-based backend for plant leaf detection and plant disease classification using TensorFlow models.

The server supports:
- Manual image upload from the web UI
- ESP32-CAM/live device image prediction via API
- Latest image/result polling for a dashboard-style interface

## Features

- Leaf presence detection before disease classification
- Confidence and prediction-gap thresholds to reduce false positives
- Upload-and-analyze web interface
- Live feed panel for latest ESP32/device frame
- JSON APIs for direct integration with mobile or embedded clients

## Project Structure

- `app.py` - Flask application, model loading, prediction pipeline, and routes
- `plant_disease_model.h5` - disease classification model
- `leaf_detector.h5` - binary leaf detector model
- `class_indices.json` - disease class index-to-name mapping
- `leaf_detector_config.json` - leaf detector class configuration
- `uploads/` - uploaded images storage
- `latest.jpg` - most recently processed frame (created/updated at runtime)
- `yolov8n.pt` - model asset in project folder (currently not used by `app.py`)

## Requirements

- Python 3.9+
- pip

Python packages:
- flask
- numpy
- opencv-python
- tensorflow
- pillow

## Installation

1. Create and activate a virtual environment (recommended).

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
pip install flask numpy opencv-python tensorflow pillow
```

## Run the Server

```powershell
python app.py
```

Default host/port:
- Host: `0.0.0.0`
- Port: `5000`

Open in browser:
- `http://localhost:5000`

## API Endpoints

### `GET /`
Returns the upload/live-monitoring web interface.

### `POST /upload_json`
Upload an image via multipart form data.

- Form field: `image`
- Response:

```json
{
  "prediction": "Tomato___Late_blight",
  "confidence": 0.934
}
```

### `POST /predict`
Predict from:
- multipart form field `image`, or
- raw image bytes in request body.

Also stores the frame as `latest.jpg` and updates in-memory `latest_result`.

- Success response:

```json
{
  "prediction": "No leaf detected",
  "confidence": 0.0
}
```

- Error response examples:

```json
{ "error": "Empty request body" }
```

```json
{ "error": "Failed to decode image" }
```

### `GET /latest.jpg`
Returns most recently processed image frame if available.

### `GET /latest_result`
Returns latest prediction result.

```json
{
  "prediction": "Pepper__bell___Bacterial_spot",
  "confidence": 0.881
}
```

## Prediction Logic

The processing pipeline in `app.py` performs:

1. Leaf check (`is_leaf`)
2. Disease classification (`predict_disease`) only if a leaf is detected
3. Confidence filtering:
   - Reject if top class confidence < `CONFIDENCE_THRESHOLD` (`0.50`)
   - Reject if `(top1 - top2) < GAP_THRESHOLD` (`0.05`)

Fallback outputs include:
- `No leaf detected`
- `Plant not present in DB`
- `Processing error`

## Notes

- Model files are loaded at startup. If any file is missing/corrupt, app startup will fail.
- `latest_result` is stored in memory and resets when the server restarts.
- `debug=False` is currently set in `app.py`.

## Quick Test with cURL

### Upload image to `/upload_json`

```bash
curl -X POST -F "image=@leaf.jpg" http://localhost:5000/upload_json
```

### Send raw image bytes to `/predict`

```bash
curl -X POST --data-binary "@leaf.jpg" http://localhost:5000/predict
```

## License

No license file is currently included in this repository.
