const fs = require("fs");
const path = require("path");

const config = {
  supabaseUrl: process.env.SUPABASE_URL || "https://wclsupskijbczcwocmze.supabase.co",
  supabasePublishableKey:
    process.env.SUPABASE_PUBLISHABLE_KEY ||
    "sb_publishable_TQFVK7KytP0H-x_3yylRjQ_8wMcWO3u",
  deviceId: process.env.GREENHOUSE_DEVICE_ID || "greenhouse-esp32-s3-01",
  diseaseApiUrl: process.env.DISEASE_API_URL || ""
};

if (!config.supabaseUrl || !config.supabasePublishableKey) {
  throw new Error("SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY are required.");
}

const output = `// Generated at build time. Values below are public browser configuration.\nwindow.GREENHOUSE_CONFIG = ${JSON.stringify(config, null, 2)};\n(function(){const s=document.createElement("script");s.src="/leaf-disease.js";s.defer=true;document.head.appendChild(s);})();\n`;
fs.writeFileSync(path.join(__dirname, "..", "public", "config.js"), output);
console.log("Static dashboard configuration generated.");
