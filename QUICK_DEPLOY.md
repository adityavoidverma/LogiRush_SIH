# Quick Deploy Guide - LogiRush to Vercel & Render

## 🎯 What We're Deploying

- **Backend (Python/Flask)** → Render
- **Frontend (React/Vite)** → Vercel  
- **Mobile App** → Expo (runs locally or via EAS build)

**Total time:** ~20-30 minutes

---

## 📋 Pre-Flight Checklist

- [ ] Code pushed to GitHub
- [ ] GitHub account
- [ ] Accounts ready: [Neon](https://neon.tech), [Render](https://render.com), [Vercel](https://vercel.com)

---

## 🚀 Deploy Now (5 Steps)

### Step 1: Create Database (5 mins)

1. Go to **[console.neon.tech/app/projects](https://console.neon.tech/app/projects)**
2. Click **"New Project"**
3. Name it: `logirush-db`
4. Click **"Create Project"**
5. Copy the **Connection String** (looks like `postgresql://...`)
6. **Save it somewhere safe** ← you'll need this next

---

### Step 2: Deploy Backend to Render (10 mins)

#### Using the Deploy Button (Easiest):

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/AARNAV-ARYA/LogiRush)

1. Click button above (or go to [dashboard.render.com/blueprints](https://dashboard.render.com/blueprints))
2. Connect your GitHub account if needed
3. Select your repository
4. Fill in environment variables:

   ```
   DATABASE_URL = [paste your Neon connection string]
   CORS_ORIGINS = *
   NER_DISABLE_DEMO_SEED = [leave empty for demo, or "1" for production]
   PORT = 10000
   ```

5. Click **"Apply"**
6. Wait for deployment (~5-10 mins)
7. **Copy your backend URL:** `https://ner-logistics-backend-xxxx.onrender.com`

#### Manual Deploy:

1. Go to [dashboard.render.com/select-repo](https://dashboard.render.com/select-repo)
2. Click **"New Web Service"**
3. Connect repository
4. Settings:
   - **Name:** `ner-logistics-backend`
   - **Root Directory:** `routeOptimiserBackend`
   - **Runtime:** Docker
   - **Docker Build Context:** `routeOptimiserBackend`
   - **Docker Dockerfile Path:** `./Dockerfile`
5. Add environment variables (same as above)
6. Click **"Create Web Service"**

**✅ Test:** Visit `https://your-backend.onrender.com/health`
Should see: `{"status":"ok","service":"logirush-ner-platform"}`

---

### Step 3: Deploy Frontend to Vercel (5 mins)

#### Using the Deploy Button (Easiest):

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FAARNAV-ARYA%2FLogiRush&root-directory=routeOptimiserFrontend&project-name=logirush-console&env=VITE_API_BASE_URL&envDescription=URL%20of%20your%20deployed%20backend%2C%20no%20trailing%20slash)

1. Click button above
2. Sign in to Vercel
3. It will ask for `VITE_API_BASE_URL` → **paste your Render backend URL** (no trailing slash)
4. Click **"Deploy"**
5. Wait 2-3 mins
6. **Copy your frontend URL:** `https://logirush-console-xxxx.vercel.app`

#### Manual Deploy:

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your GitHub repository
3. **Important Settings:**
   - Click **"Edit"** next to Root Directory
   - Set: `routeOptimiserFrontend` ← Critical!
   - Framework: Vite (auto-detected)
   - Build Command: `npm run build`
   - Output Directory: `dist`
4. Add environment variable:
   - Name: `VITE_API_BASE_URL`
   - Value: Your Render URL (e.g., `https://ner-logistics-backend.onrender.com`)
5. Click **"Deploy"**

**✅ Test:** Open your Vercel URL - you should see the LogiRush dashboard

---

### Step 4: Connect Frontend to Backend (2 mins)

Now both are deployed, but backend needs to allow frontend:

1. Go back to [Render dashboard](https://dashboard.render.com)
2. Click your backend service
3. Go to **"Environment"** tab
4. Find `CORS_ORIGINS`
5. Change from `*` to your Vercel URL:
   ```
   https://logirush-console-xxxx.vercel.app
   ```
6. Click **"Save Changes"** (will auto-redeploy)

---

### Step 5: Setup Mobile App (5 mins)

On your computer:

```bash
cd nerFieldApp

# Create .env file with your backend URL
echo "EXPO_PUBLIC_API_BASE_URL=https://your-backend.onrender.com" > .env

# Install and start
npm install
npx expo start
```

Scan the QR code with your phone:
- **iPhone:** Use Camera app
- **Android:** Use Expo Go app (download from Play Store)

**✅ Test:** In the app, go to Sign In → "Test connection" → Should show your backend URL and connection status

---

## ✅ Verify Everything Works

### Test the Full Loop:

1. **Open Frontend** (your Vercel URL)
   - Sign in: `controller` / `control123`
   - Should see the dashboard

2. **Open Mobile App**
   - Tap "Test connection" on sign-in screen
   - Should show: Connected + number of reports

3. **File a Test Report:**
   - In mobile app: Create new incident
   - Add location, photo, description
   - Submit

4. **Check Frontend:**
   - Refresh Incidents page
   - Your report should appear with "via field app" label

**If something doesn't work**, run:
```bash
./verify-deployment.sh
```

---

## 📝 Your Deployment Info

Fill this in for your records:

```
Database (Neon):
postgresql://_______________________________________________

Backend (Render):
https://_______________________________________________

Frontend (Vercel):
https://_______________________________________________

Demo Login:
Username: controller
Password: control123
```

---

## 🔐 Going to Production

For a real deployment (not demo):

1. **Disable demo accounts:**
   - In Render → Environment → Set `NER_DISABLE_DEMO_SEED=1`

2. **Create real users:**
   - Render dashboard → your service → **Shell** tab
   - Run:
     ```python
     from src.api.auth import hash_password
     from src.db.models import User
     from src.db.session import get_session

     session = get_session()
     session.add(User(
         username="your.name",
         full_name="Your Full Name",
         password_hash=hash_password("strong-password-here"),
         role="controller",  # or "verifier" or "reporter"
         organisation="Your Organization",
         jurisdiction="Assam"  # for verifiers only
     ))
     session.commit()
     print("User created!")
     ```

3. **Lock down CORS:**
   - Already done in Step 4 ✓

---

## 🆘 Troubleshooting

### Backend won't start
- Check Render logs: Dashboard → your service → Logs
- Verify `DATABASE_URL` is set correctly
- Make sure it's a PostgreSQL URL starting with `postgresql://`

### Frontend shows "Cannot connect"
- Verify `VITE_API_BASE_URL` in Vercel settings
- Test backend health: `curl https://your-backend.onrender.com/health`
- Check `CORS_ORIGINS` includes your frontend URL

### Mobile app can't connect
- Check `.env` file has correct backend URL
- Restart Expo: `npx expo start`
- Use "Test connection" button to diagnose

### Reports don't sync between app and console
- **Most common:** Different backend URLs
- Check all three use the SAME backend URL
- Verify with "Test connection" in mobile app

### Render free tier sleeping
- First request after 15 mins of inactivity takes ~30s
- This is normal for free tier
- Upgrade to paid tier for always-on

---

## 🎉 Success Checklist

- [ ] Backend health check passes
- [ ] Frontend loads and login works
- [ ] Mobile app connects to backend
- [ ] Report filed from mobile appears in frontend
- [ ] Route planning works
- [ ] Weather data shows as "live"

---

## 📚 Additional Resources

- Full deployment guide: [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
- Platform overview: [README.md](README.md)
- Architecture details: [NER_PLATFORM.md](NER_PLATFORM.md)
- Deployment details: [DEPLOY.md](DEPLOY.md)

---

## 🔗 Useful Links

- [Render Dashboard](https://dashboard.render.com)
- [Vercel Dashboard](https://vercel.com/dashboard)
- [Neon Console](https://console.neon.tech)
- [Expo Dashboard](https://expo.dev)

---

**Need help?** Check logs in:
- Render: Dashboard → Service → Logs
- Vercel: Dashboard → Project → Deployments → View logs
- Expo: Terminal where `npx expo start` is running
