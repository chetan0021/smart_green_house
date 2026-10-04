(() => {
  const mount = () => {
    const root = document.querySelector("main.shell");
    if (!root || document.getElementById("leaf-disease-panel")) return;
    const style = document.createElement("style");
    style.textContent = `.leaf-panel{margin-top:14px}.leaf-grid{display:grid;grid-template-columns:1.15fr .85fr;gap:14px}.leaf-frame{background:#1c2940;border-radius:11px;overflow:hidden;aspect-ratio:16/9;display:grid;place-items:center}.leaf-frame video,.leaf-frame img{width:100%;height:100%;object-fit:contain}.leaf-placeholder{color:#d8e3f3;padding:20px;text-align:center}.leaf-actions{display:flex;gap:9px;flex-wrap:wrap;margin-top:10px}.leaf-button,.leaf-upload{border:0;border-radius:9px;padding:10px 13px;background:#4a78e8;color:#fff;font-weight:700;cursor:pointer}.leaf-button.alt,.leaf-upload{background:#eef3ff;color:#315daf;border:1px solid #cddaff}.leaf-upload input{display:none}.leaf-result{min-height:230px;background:#f8faff;border:1px dashed #c5d5ee;border-radius:11px;padding:15px}.leaf-result img{max-width:100%;max-height:205px;border-radius:8px;display:none}.leaf-result h3{margin:0 0 8px}.leaf-result p{color:#6e7b91}.leaf-name{font-size:20px;font-weight:750;line-height:1.3}.leaf-confidence{color:#4a78e8;font-weight:650}@media(max-width:800px){.leaf-grid{grid-template-columns:1fr}}`;
    document.head.appendChild(style);
    root.insertAdjacentHTML("beforeend", `<section class="card leaf-panel" id="leaf-disease-panel"><h2>Leaf disease scan</h2><p class="muted">Use the webcam or upload a clear photo of one supported plant leaf.</p><div class="leaf-grid"><div><div class="leaf-frame"><video id="leaf-video" autoplay muted playsinline></video><div id="leaf-placeholder" class="leaf-placeholder">Open the camera, then hold one leaf in clear light.</div></div><div class="leaf-actions"><button class="leaf-button alt" id="open-leaf-camera">Open camera</button><button class="leaf-button" id="capture-leaf">Capture & analyze</button><label class="leaf-upload">Upload image<input id="leaf-file" type="file" accept="image/*"></label></div></div><div class="leaf-result"><h3>Diagnosis</h3><p id="leaf-message">Checking disease-analysis service…</p><img id="leaf-annotated" alt="Annotated leaf diagnosis"><div id="leaf-name" class="leaf-name"></div><div id="leaf-confidence" class="leaf-confidence"></div></div></div></section>`);

    const $ = (id) => document.getElementById(id);
    const apiUrl = (window.GREENHOUSE_CONFIG?.diseaseApiUrl || "").replace(/\/+$/, "");
    let stream;
    const setMessage = (message) => { $("leaf-message").textContent = message; };
    async function openCamera() {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: "environment" } }, audio: false });
        $("leaf-video").srcObject = stream;
        $("leaf-placeholder").style.display = "none";
        setMessage("Camera ready. Capture a well-lit leaf photo.");
      } catch {
        setMessage("Camera access was not granted. You can still upload an image.");
      }
    }
    async function analyze(file) {
      if (!apiUrl) { setMessage("Add DISEASE_API_URL in Vercel after Railway gives you its public domain."); return; }
      setMessage("Analyzing image…");
      $("leaf-name").textContent = ""; $("leaf-confidence").textContent = "";
      try {
        const form = new FormData(); form.append("image", file, file.name || "webcam-leaf.jpg");
        const response = await fetch(`${apiUrl}/upload_json`, { method: "POST", body: form });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Analysis failed");
        setMessage("Analysis complete");
        $("leaf-name").textContent = String(data.prediction || "Unknown").replaceAll("___", " - ").replaceAll("_", " ");
        $("leaf-confidence").textContent = `${(Number(data.confidence || 0) * 100).toFixed(1)}% confidence`;
        if (data.annotated_image) { $("leaf-annotated").src = data.annotated_image; $("leaf-annotated").style.display = "block"; }
      } catch (error) { setMessage(`Analysis unavailable: ${error.message}`); }
    }
    $("open-leaf-camera").onclick = openCamera;
    $("capture-leaf").onclick = () => {
      const video = $("leaf-video"); if (!video.videoWidth) { openCamera(); return; }
      const canvas = document.createElement("canvas"); canvas.width = video.videoWidth; canvas.height = video.videoHeight;
      canvas.getContext("2d").drawImage(video, 0, 0);
      canvas.toBlob((blob) => blob && analyze(new File([blob], "webcam-leaf.jpg", { type: "image/jpeg" })), "image/jpeg", 0.92);
    };
    $("leaf-file").onchange = (event) => { const file = event.target.files?.[0]; if (file) analyze(file); };
    setMessage(apiUrl ? "Ready for a leaf image." : "Add DISEASE_API_URL in Vercel after Railway deployment.");
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount); else mount();
})();
