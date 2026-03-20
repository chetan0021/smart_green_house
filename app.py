from flask import Flask, request, jsonify, render_template_string, send_file
import numpy as np
import cv2
import tensorflow as tf
from PIL import Image
import json
import os

# ─── CONFIG ───────────────────────────────────────────────────────────────────
IMG_SIZE             = 224
LEAF_IMG_SIZE        = 64
CONFIDENCE_THRESHOLD = 0.50
GAP_THRESHOLD        = 0.05

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ─── LOAD MODELS ──────────────────────────────────────────────────────────────
print("Loading disease model...")
disease_model = tf.keras.models.load_model("plant_disease_model.h5")

print("Loading leaf detector...")
leaf_detector_model = tf.keras.models.load_model("leaf_detector.h5")

print("Loading class labels...")
class_indices = json.load(open("class_indices.json"))
class_indices = {int(k): v for k, v in class_indices.items()}

print("Loading leaf detector config...")
leaf_config   = json.load(open("leaf_detector_config.json"))
LEAF_CLASS    = leaf_config["leaf_class_index"]

print("✅ All models loaded")

# ─── LEAF DETECTOR ────────────────────────────────────────────────────────────
def is_leaf(image):
    img  = cv2.resize(image, (LEAF_IMG_SIZE, LEAF_IMG_SIZE))
    img  = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img  = img / 255.0
    img  = np.expand_dims(img, axis=0)

    prob = leaf_detector_model.predict(img, verbose=0)[0][0]

    if LEAF_CLASS == 1:
        detected = prob > 0.5
        conf     = float(prob)
    else:
        detected = prob < 0.5
        conf     = float(1 - prob)

    print(f"Leaf detector: {conf:.3f} → {'LEAF' if detected else 'NOT LEAF'}")
    return detected

# ─── DISEASE CLASSIFIER ───────────────────────────────────────────────────────
def predict_disease(image):
    img  = cv2.resize(image, (IMG_SIZE, IMG_SIZE))
    img  = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img  = img / 255.0
    img  = np.expand_dims(img, axis=0)

    preds        = disease_model.predict(img, verbose=0)[0]
    sorted_probs = np.sort(preds)
    top1         = sorted_probs[-1]
    top2         = sorted_probs[-2]
    class_id     = np.argmax(preds)
    gap          = top1 - top2

    print(f"Disease model: top1={top1:.3f} gap={gap:.3f}")

    if top1 < CONFIDENCE_THRESHOLD or gap < GAP_THRESHOLD:
        return "Plant not present in DB", float(top1)

    return class_indices[class_id], float(top1)

# ─── MAIN PIPELINE ────────────────────────────────────────────────────────────
def plant_pipeline(image):
    try:
        # Step 1 — check if leaf is present
        if not is_leaf(image):
            return "No leaf detected", 0.0

        # Step 2 — classify disease
        return predict_disease(image)

    except Exception as e:
        print(f"Pipeline error: {e}")
        return "Processing error", 0.0

# ─── DECODE IMAGE ─────────────────────────────────────────────────────────────
def decode_image(req):
    if "image" in req.files:
        file = req.files["image"]
        img  = Image.open(file.stream).convert("RGB")
        img  = np.array(img)
        img  = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        return img

    raw = req.data
    if len(raw) == 0:
        raise ValueError("Empty request body")

    npimg = np.frombuffer(raw, dtype=np.uint8)
    img   = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Failed to decode image")

    return img

# ─── WEB PAGE ─────────────────────────────────────────────────────────────────
UPLOAD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PhytoScan — Plant Disease Intelligence</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg:         #080e0b;
    --surface:    #0d1a13;
    --card:       #111f17;
    --border:     #1e3828;
    --accent:     #3dffa0;
    --accent-dim: #1a7d4f;
    --accent-glow:rgba(61,255,160,0.15);
    --warn:       #ffb547;
    --danger:     #ff5e5e;
    --text:       #d4f0e0;
    --muted:      #556b5e;
    --font-head:  'Syne', sans-serif;
    --font-mono:  'DM Mono', monospace;
  }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--font-head);
    min-height: 100vh;
  }
  .bg-blob {
    position: fixed; border-radius: 50%;
    filter: blur(120px); pointer-events: none;
    z-index: 0; opacity: 0.18;
    animation: drift 18s ease-in-out infinite alternate;
  }
  .bg-blob:nth-child(1) { width:600px; height:600px; background:#0d5c35; top:-200px; left:-200px; }
  .bg-blob:nth-child(2) { width:400px; height:400px; background:#1a4d2e; bottom:-100px; right:-100px; animation-delay:-7s; }
  .bg-blob:nth-child(3) { width:300px; height:300px; background:#062918; top:40%; left:50%; animation-delay:-13s; }
  @keyframes drift {
    from { transform: translate(0,0) scale(1); }
    to   { transform: translate(40px,30px) scale(1.08); }
  }
  .wrapper {
    position: relative; z-index: 1;
    max-width: 1100px; margin: 0 auto;
    padding: 40px 24px 80px;
  }
  header {
    display: flex; align-items: center;
    justify-content: space-between; margin-bottom: 56px;
  }
  .logo { display: flex; align-items: center; gap: 14px; }
  .logo-icon {
    width:46px; height:46px; background:var(--accent);
    border-radius:12px; display:flex; align-items:center;
    justify-content:center; font-size:22px;
    box-shadow: 0 0 24px var(--accent-glow);
  }
  .logo-text { font-size:22px; font-weight:800; color:#fff; }
  .logo-text span { color:var(--accent); }
  .status-pill {
    display:flex; align-items:center; gap:8px;
    background:var(--card); border:1px solid var(--border);
    border-radius:100px; padding:8px 16px;
    font-family:var(--font-mono); font-size:12px; color:var(--muted);
  }
  .status-dot {
    width:8px; height:8px; border-radius:50%;
    background:var(--accent); animation:pulse-dot 2s ease infinite;
  }
  @keyframes pulse-dot {
    0%,100% { opacity:1; box-shadow:0 0 0 0 rgba(61,255,160,0.4); }
    50%      { opacity:0.7; box-shadow:0 0 0 5px rgba(61,255,160,0); }
  }
  .grid {
    display:grid; grid-template-columns:1fr 1fr;
    gap:24px; margin-bottom:24px;
  }
  @media(max-width:700px) { .grid { grid-template-columns:1fr; } }
  .card {
    background:var(--card); border:1px solid var(--border);
    border-radius:20px; padding:28px; position:relative;
    overflow:hidden; transition:border-color 0.3s,box-shadow 0.3s;
  }
  .card:hover {
    border-color:var(--accent-dim);
    box-shadow:0 0 40px rgba(61,255,160,0.06);
  }
  .section-label {
    font-family:var(--font-mono); font-size:11px;
    letter-spacing:2px; text-transform:uppercase;
    color:var(--accent); margin-bottom:10px; opacity:0.8;
  }
  .card-title { font-size:18px; font-weight:700; color:#fff; margin-bottom:6px; }
  .card-subtitle {
    font-family:var(--font-mono); font-size:12px;
    color:var(--muted); margin-bottom:22px;
  }
  .drop-zone {
    border:2px dashed var(--border); border-radius:14px;
    padding:36px 20px; text-align:center; cursor:pointer;
    transition:all 0.3s; background:rgba(0,0,0,0.2); position:relative;
  }
  .drop-zone:hover { border-color:var(--accent); background:var(--accent-glow); }
  .drop-zone input[type=file] {
    position:absolute; inset:0; opacity:0;
    cursor:pointer; width:100%; height:100%;
  }
  .drop-icon { font-size:40px; margin-bottom:12px; display:block; }
  .drop-text { font-size:14px; color:var(--muted); line-height:1.6; }
  .drop-text strong { color:var(--accent); font-weight:600; }
  #preview-wrap {
    display:none; margin-top:16px;
    border-radius:12px; overflow:hidden;
    border:1px solid var(--border);
  }
  #preview-img { width:100%; display:block; max-height:220px; object-fit:cover; }
  .btn {
    display:inline-flex; align-items:center; gap:8px;
    margin-top:18px; padding:13px 28px;
    border:none; border-radius:10px;
    background:var(--accent); color:#050f09;
    font-family:var(--font-head); font-size:14px;
    font-weight:700; cursor:pointer; transition:all 0.2s;
    width:100%; justify-content:center;
  }
  .btn:hover {
    background:#6effbc;
    box-shadow:0 0 28px rgba(61,255,160,0.35);
    transform:translateY(-1px);
  }
  .btn.loading { background:var(--accent-dim); pointer-events:none; }
  .spinner {
    width:16px; height:16px;
    border:2px solid rgba(5,15,9,0.3);
    border-top-color:#050f09; border-radius:50%;
    animation:spin 0.7s linear infinite; display:none;
  }
  .btn.loading .spinner { display:block; }
  .btn.loading .btn-icon { display:none; }
  @keyframes spin { to { transform:rotate(360deg); } }
  .feed-frame {
    border-radius:12px; overflow:hidden;
    border:1px solid var(--border); background:rgba(0,0,0,0.3);
    aspect-ratio:4/3; display:flex; align-items:center;
    justify-content:center; position:relative;
  }
  .feed-frame img { width:100%; height:100%; object-fit:cover; display:block; }
  .feed-overlay {
    position:absolute; top:10px; right:10px;
    background:rgba(0,0,0,0.6); backdrop-filter:blur(6px);
    border-radius:8px; padding:5px 10px;
    font-family:var(--font-mono); font-size:10px;
    color:var(--accent); display:flex; align-items:center; gap:5px;
  }
  .live-dot {
    width:6px; height:6px; border-radius:50%;
    background:var(--accent); animation:pulse-dot 1.5s ease infinite;
  }
  .no-feed-msg {
    text-align:center; color:var(--muted);
    font-family:var(--font-mono); font-size:12px; line-height:1.8;
  }
  .no-feed-msg .icon { font-size:36px; display:block; margin-bottom:10px; opacity:0.5; }
  .result-box {
    margin-top:18px; background:rgba(0,0,0,0.25);
    border:1px solid var(--border); border-radius:12px;
    padding:16px 18px; font-family:var(--font-mono);
    font-size:13px; color:var(--muted); min-height:56px;
    transition:all 0.4s;
  }
  .result-box.has-result { border-color:var(--accent-dim); color:var(--text); }
  .r-label { font-size:10px; letter-spacing:1.5px; text-transform:uppercase; color:var(--muted); margin-bottom:6px; }
  .r-name { font-size:16px; font-weight:500; color:#fff; font-family:var(--font-head); }
  .conf-bar-track {
    height:4px; background:var(--border);
    border-radius:4px; margin-top:6px; overflow:hidden;
  }
  .conf-bar-fill {
    height:100%; border-radius:4px;
    background:linear-gradient(90deg,var(--accent-dim),var(--accent));
    transition:width 0.8s cubic-bezier(0.22,1,0.36,1);
  }
  .conf-pct { font-size:11px; color:var(--accent); }
  .timestamp {
    font-family:var(--font-mono); font-size:10px;
    color:var(--muted); margin-top:8px;
  }
  footer {
    margin-top:48px; padding-top:24px;
    border-top:1px solid var(--border);
    display:flex; align-items:center; justify-content:space-between;
    font-family:var(--font-mono); font-size:11px; color:var(--muted);
  }
</style>
</head>
<body>
<div class="bg-blob"></div>
<div class="bg-blob"></div>
<div class="bg-blob"></div>
<div class="wrapper">

  <header>
    <div class="logo">
      <div class="logo-icon">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
             stroke="#050f09" stroke-width="2.2"
             stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2C6 2 3 8 3 12c0 5 4 9 9 9s9-4 9-9c0-3-1.5-6-4-8"/>
          <path d="M12 2c2 3 3 6 3 10"/>
          <path d="M7 15c1-3 3-5 5-6"/>
        </svg>
      </div>
      <div class="logo-text">Plant<span>Scan</span></div>
    </div>
    <div class="status-pill">
      <div class="status-dot"></div>
      Models Online
    </div>
  </header>

  <div class="grid">

    <!-- Upload Card -->
    <div class="card">
      <div class="section-label">Manual Analysis</div>
      <div class="card-title">Upload Leaf Image</div>
      <div class="card-subtitle">Supports JPG, PNG, WEBP</div>
      <form id="upload-form">
        <div class="drop-zone" id="drop-zone">
          <input type="file" name="image" id="file-input" accept="image/*">
          <span class="drop-icon">📷</span>
          <div class="drop-text">
            <strong>Click to browse</strong> or drag & drop
          </div>
        </div>
        <div id="preview-wrap">
          <img id="preview-img" src="" alt="Preview">
        </div>
        <button type="submit" class="btn" id="analyze-btn">
          <div class="spinner"></div>
          <svg class="btn-icon" width="16" height="16" fill="none"
               viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round"
              d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0
                 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0
                 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0
                 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0
                 00-3.09 3.09z"/>
          </svg>
          Run Analysis
        </button>
      </form>
      <div class="result-box" id="upload-result">
        <span style="opacity:0.4">Result will appear here</span>
      </div>
    </div>

    <!-- ESP32 Card -->
    <div class="card">
      <div class="section-label">Live Feed</div>
      <div class="card-title">ESP32-CAM Stream</div>
      <div class="card-subtitle">Auto-refreshes every 15 seconds</div>
      <div class="feed-frame" id="feed-frame">
        <img id="espimg" src="/latest.jpg" alt="ESP32 Feed"
             onerror="handleFeedError(this)">
        <div class="feed-overlay">
          <div class="live-dot"></div> LIVE
        </div>
      </div>
      <div class="result-box has-result" id="esp-result">
        <div class="r-label">Waiting for device</div>
        <div class="r-name">—</div>
      </div>
      <div class="timestamp" id="esp-timestamp">No frames received yet</div>
    </div>

  </div>

  <footer>
    <div>PhytoScan · ESP32 + MobileNetV2 + TensorFlow</div>
    <div>Smart Plant Health Monitoring</div>
  </footer>

</div>

<script>
  const fileInput   = document.getElementById('file-input');
  const previewWrap = document.getElementById('preview-wrap');
  const previewImg  = document.getElementById('preview-img');

  fileInput.addEventListener('change', () => {
    const file = fileInput.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = e => {
      previewImg.src = e.target.result;
      previewWrap.style.display = 'block';
    };
    reader.readAsDataURL(file);
  });

  document.getElementById('upload-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const btn = document.getElementById('analyze-btn');
    btn.classList.add('loading');
    const formData = new FormData(this);
    try {
      const res  = await fetch('/upload_json', { method:'POST', body:formData });
      const data = await res.json();
      showResult('upload-result', data.prediction, data.confidence);
    } catch(err) {
      showResult('upload-result', 'Error processing image', 0);
    } finally {
      btn.classList.remove('loading');
    }
  });

  function showResult(boxId, prediction, confidence) {
    const box   = document.getElementById(boxId);
    const pct   = (confidence * 100).toFixed(1);
    const color = confidence > 0.75 ? '#3dffa0'
                : confidence > 0.50 ? '#ffb547' : '#ff5e5e';
    box.classList.add('has-result');
    box.innerHTML = `
      <div class="r-label">Diagnosis</div>
      <div class="r-name">${prediction}</div>
      <div class="r-conf">
        <span class="conf-pct" style="color:${color}">${pct}% confidence</span>
        <div class="conf-bar-track">
          <div class="conf-bar-fill"
               style="width:0%;background:linear-gradient(90deg,${color}88,${color})">
          </div>
        </div>
      </div>`;
    setTimeout(() => {
      box.querySelector('.conf-bar-fill').style.width = pct + '%';
    }, 50);
  }

  function handleFeedError(img) {
    img.style.display = 'none';
    const frame = document.getElementById('feed-frame');
    if (!frame.querySelector('.no-feed-msg')) {
      const msg = document.createElement('div');
      msg.className = 'no-feed-msg';
      msg.innerHTML = '<span class="icon">📡</span>Waiting for ESP32<br><small>Connect device to start</small>';
      frame.appendChild(msg);
    }
  }

  function pollESP() {
    const img = document.getElementById('espimg');
    img.src = '/latest.jpg?t=' + Date.now();
    img.style.display = 'block';
    const noFeed = document.querySelector('.no-feed-msg');
    if (noFeed) noFeed.remove();

    fetch('/latest_result')
      .then(r => r.json())
      .then(data => {
        if (!data.prediction) return;
        showResult('esp-result', data.prediction, data.confidence);
        document.getElementById('esp-result')
                .querySelector('.r-label').textContent = 'Live Diagnosis';
        document.getElementById('esp-timestamp').textContent =
          'Last updated: ' + new Date().toLocaleTimeString();
      })
      .catch(() => {});
  }

  setInterval(pollESP, 15000);
</script>
</body>
</html>
"""

# ─── ROUTES ───────────────────────────────────────────────────────────────────
@app.route("/")
def home():
    return render_template_string(UPLOAD_HTML)

@app.route("/latest.jpg")
def latest_image():
    if os.path.exists("latest.jpg"):
        return send_file("latest.jpg", mimetype="image/jpeg")
    return "", 204

latest_result = {}

@app.route("/latest_result")
def get_latest_result():
    return jsonify(latest_result)

@app.route("/upload_json", methods=["POST"])
def upload_json():
    try:
        file     = request.files["image"]
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        img = Image.open(filepath).convert("RGB")
        img = np.array(img)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        prediction, confidence = plant_pipeline(img)

        return jsonify({
            "prediction": prediction,
            "confidence": round(confidence, 3)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/predict", methods=["POST"])
def predict():
    global latest_result
    try:
        img = decode_image(request)
        cv2.imwrite("latest.jpg", img)

        prediction, confidence = plant_pipeline(img)

        latest_result = {
            "prediction": prediction,
            "confidence": round(confidence, 3)
        }

        print(f"ESP32 → {prediction} ({round(confidence * 100, 1)}%)")
        return jsonify(latest_result)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ─── RUN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)