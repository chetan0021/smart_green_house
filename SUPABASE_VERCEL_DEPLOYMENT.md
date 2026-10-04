# Supabase + Vercel deployment guide

This setup uses a secure split architecture:

```text
ESP32-S3 -- HTTPS + device secret --> Supabase Edge Function --> Supabase Postgres
Vercel dashboard -- publishable key, read only --> Supabase Postgres
```

The device secret stays only in the ESP32 and Supabase Edge Function. Do not put it in Vercel, browser JavaScript, GitHub, or a screenshot.

## 1. Create a Supabase project

1. Open [Supabase](https://supabase.com/dashboard) and sign in.
2. Select **New project**.
3. Choose an organization, project name, database password, and region nearest to you.
4. Wait for the project to finish provisioning.
5. Open **SQL Editor**, choose **New query**, paste all of `supabase/schema.sql`, and click **Run**.
6. Open **Settings -> API Keys**. Copy the project URL and the **publishable** key. The publishable key is used only by the Vercel browser dashboard.
7. In **Settings -> API Keys**, copy the secret/service-role key only for the Edge Function secret configuration. Never place it in frontend code.

## 2. Create the secure telemetry function

Install and authenticate the Supabase CLI, then run these commands from the `LeafDiseaseDetector` folder:

```powershell
npm install -g supabase
supabase login
supabase link --project-ref YOUR_PROJECT_REF
```

`YOUR_PROJECT_REF` is the identifier in your Supabase URL, for example `abcdxyz` from `https://abcdxyz.supabase.co`.

Create a local `supabase/functions/.env` from the example file. For temporary testing, set only your Supabase secret/service-role key as `SERVICE_ROLE_KEY`. `DEVICE_INGEST_KEY` is optional: adding it later requires the matching value from the ESP32.

```powershell
supabase secrets set SERVICE_ROLE_KEY="your-supabase-secret-service-role-key"
supabase functions deploy greenhouse-ingest --no-verify-jwt
```

The `--no-verify-jwt` flag is intentional: ESP32 does not use a Supabase user JWT. While testing with no `DEVICE_INGEST_KEY`, the endpoint is open and should not be used for a real deployment. Later, set `DEVICE_INGEST_KEY` in Edge Function Secrets and the function will validate `X-Device-Key` automatically.

Your final ESP32 URL is:

```text
https://YOUR_PROJECT_REF.supabase.co/functions/v1/greenhouse-ingest
```

## 3. Configure and upload ESP32-S3

Open `esp32/SmartGreenhouse.ino` and set:

```cpp
const char* WIFI_SSID = "your-wifi-name";
const char* WIFI_PASSWORD = "your-wifi-password";
const char* SERVER_URL = "https://YOUR_PROJECT_REF.supabase.co/functions/v1/greenhouse-ingest";
const char* DEVICE_INGEST_KEY = ""; // Set later to enable device authentication.
```

The soil sensor input is now **GPIO 36**. First run `esp32/tests/SoilMoisture_Calibration/SoilMoisture_Calibration.ino` and copy your dry/wet raw values into the final sketch. Then upload the final sketch. Serial Monitor at `115200` should show `Telemetry status: 200`.

Open Supabase **Table Editor -> greenhouse_telemetry**. New rows should appear roughly every 10 seconds.

## 4. Deploy the dashboard to Vercel

1. Create a GitHub repository and push this project.
2. In Vercel, select **Add New -> Project**, import the repository, and set **Root Directory** to `LeafDiseaseDetector/vercel-dashboard`.
3. Vercel detects it as **Other**. Keep the build command `npm run build` and output directory unset.
4. Before deployment, edit `vercel-dashboard/public/config.js`:

```js
window.GREENHOUSE_CONFIG = {
  supabaseUrl: "https://YOUR_PROJECT_REF.supabase.co",
  supabasePublishableKey: "YOUR_SUPABASE_PUBLISHABLE_KEY",
  deviceId: "greenhouse-esp32-s3-01"
};
```

5. Commit and push, then deploy in Vercel.

The deployed dashboard polls Supabase every five seconds and displays the latest telemetry, trend chart, and actuator states. It uses a public **read-only** policy; the ESP32 can only write through the protected Edge Function.

## 5. Production hardening before public use

- Change the placeholder device secret before first upload.
- Use a unique secret for every device when you add more than one greenhouse.
- Keep `SERVICE_ROLE_KEY`, Wi-Fi password, and SMTP credentials outside Git.
- Add Supabase Auth and owner-specific RLS policies before sharing the dashboard with other people.
- Add an LDR/BH1750 and a calibrated battery voltage-divider circuit if you want true light and battery telemetry.
- Use cloud storage and a persistent ML service such as Render/Railway for disease-image uploads. The Vercel static dashboard in this folder covers environmental telemetry; it does not run the 95 MB disease model.
