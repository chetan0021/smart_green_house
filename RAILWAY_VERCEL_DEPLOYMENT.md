# Railway disease API + Vercel dashboard

Both services deploy from this one repository.

## Railway: Python disease-detection backend

1. In Railway, select **New Project** → **Deploy from GitHub repo** and select `chetan0021/smart_green_house`.
2. In the service settings, set **Root Directory** to `.` (the repository root). Do **not** select `vercel-dashboard`.
3. Railway reads `requirements.txt` and `railway.json` from that root. It installs the Python/ONNX dependencies, starts `app:app` with Gunicorn, and checks `/health`.
4. After the deployment is green, open **Settings** → **Networking** → **Generate Domain**. Copy the full `https://...up.railway.app` address.
5. Check `https://YOUR_RAILWAY_DOMAIN/health`; it must return JSON with `"ok": true`.

## Vercel: dashboard frontend

Vercel continues to use **Root Directory** `vercel-dashboard`.

In Vercel Project Settings → Environment Variables, add this value for Production and Preview:

```text
DISEASE_API_URL=https://YOUR_RAILWAY_DOMAIN
```

Keep the existing `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, and `GREENHOUSE_DEVICE_ID` values. Do not put the Railway URL behind a secret: browsers must call it for image analysis. Redeploy Vercel after adding the variable.

## Security note

The Railway API accepts public image uploads so the Vercel browser dashboard can analyze leaves. Do not put Supabase secret keys, device Wi-Fi credentials, or mail passwords in Vercel. Configure `CORS_ORIGIN` in Railway later with your exact Vercel domain to restrict browser calls.
