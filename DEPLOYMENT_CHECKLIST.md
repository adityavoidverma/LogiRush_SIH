# LogiRush Deployment Checklist

Complete guide to deploying the full LogiRush platform to production.

## Overview

```
Database (Neon)
    ↓
Backend (Render) ←─── Frontend (Vercel)
    ↓                      
Field App (Expo)
```

## Prerequisites

- [ ] GitHub account (to connect repositories)
- [ ] Neon account (database) - https://neon.tech
- [ ] Render account (backend) - https://render.com
- [ ] Vercel account (frontend) - https://vercel.com
- [ ] Expo account (optional, for mobile builds) - https://expo.dev

---

## Step 1: Database Setup (Neon) ✓

1. Go to [neon.tech](https://neon.tech) and sign up
2. Click **"Create a project"**
3. Choose a name (e.g., "logirush-db")
4. Select region closest to your users
5. Copy the **connection string** - looks like:
   ```
   postgresql://user:password@ep-xxx.aws.neon.tech/neondb?sslmode=require
   ```
6. **Save this** - you'll need it for Render

**✅ Checkpoint:** You have a Postgres connection string saved

---

## Step 2: Backend Deployment (Render) ✓

### Option A: Deploy with Blueprint (Recommended)

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repository (or this one: `AARNAV-ARYA/LogiRush`)
4. Render will detect `render.yaml` automatically
5. Set these environment variables:

   | Variable | Value | Example |
   |----------|-------|---------|
   | `DATABASE_URL` | Your Neon connection string | `postgresql://user:pass@...` |
   | `CORS_ORIGINS` | Leave as `*` for now (update after Vercel) | `*` |
   | `NER_DISABLE_DEMO_SEED` | `1` (for production) or leave empty (for demo) | `1` |
   | `PORT` | `10000` | `10000` |

6. Click **"Apply"**
7. Wait for deployment to complete (~5-10 minutes)
8. Your backend URL will be: `https://ner-logistics-backend.onrender.com`

### Option B: Manual Docker Deployment

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your repository
4. Configure:
   - **Name:** `ner-logistics-backend`
   - **Region:** Choose closest to users
   - **Branch:** `main`
   - **Root Directory:** `routeOptimiserBackend`
   - **Runtime:** `Docker`
   - **Dockerfile Path:** `./Dockerfile`
   - **Instance Type:** Free (for demo) or Starter
5. Add environment variables (same as Option A above)
6. Click **"Create Web Service"**

### Verify Backend

Once deployed, test these URLs (replace with your actual URL):

```bash
# Health check
curl https://your-backend.onrender.com/health
# Should return: {"status":"ok","service":"logirush-ner-platform"}

# Weather endpoint (tests live data)
curl https://your-backend.onrender.com/api/ner/weather
# Should return JSON with "live": true
```

**✅ Checkpoint:** Backend is running and health check passes

---

## Step 3: Frontend Deployment (Vercel) ✓

### Deploy to Vercel

1. Go to [vercel.com/new](https://vercel.com/new)
2. Click **"Import Project"**
3. Import your GitHub repository
4. **CRITICAL:** Configure these settings:
   - **Framework Preset:** Vite (should auto-detect)
   - **Root Directory:** Click **"Edit"** → Set to `routeOptimiserFrontend`
   - **Build Command:** `npm run build` (auto-filled)
   - **Output Directory:** `dist` (auto-filled)

5. Add environment variable:
   
   | Name | Value |
   |------|-------|
   | `VITE_API_BASE_URL` | Your Render backend URL (no trailing slash) |
   
   Example: `https://ner-logistics-backend.onrender.com`

6. Click **"Deploy"**
7. Wait ~2-3 minutes for build
8. Your frontend URL will be: `https://logirush-xxx.vercel.app`

### Update CORS on Backend

Now that you have your Vercel URL:

1. Go back to Render dashboard
2. Select your backend service
3. Go to **"Environment"**
4. Update `CORS_ORIGINS` from `*` to your Vercel URL:
   ```
   https://logirush-xxx.vercel.app
   ```
5. Click **"Save Changes"** (this will redeploy)

### Verify Frontend

1. Open your Vercel URL in a browser
2. Try signing in with demo credentials:
   - Username: `controller`
   - Password: `control123`
3. Check the dashboard loads

**✅ Checkpoint:** Frontend loads and connects to backend

---

## Step 4: Mobile App Setup (Expo) ✓

### Local Development/Testing

1. On your computer:
   ```bash
   cd nerFieldApp
   ```

2. Create `.env` file:
   ```bash
   echo "EXPO_PUBLIC_API_BASE_URL=https://your-backend.onrender.com" > .env
   ```

3. Install dependencies and start:
   ```bash
   npm install
   npx expo start
   ```

4. Scan QR code with:
   - **iPhone:** Camera app
   - **Android:** Expo Go app

### Verify Connection

1. Open the app on your phone
2. Go to **Sign In** screen
3. Tap **"Test connection"** button
4. Should show:
   - Backend URL
   - Number of reports in database
   - Connection status

**✅ Checkpoint:** Mobile app connects to backend

### Build Standalone App (Optional)

For production builds (TestFlight, Play Store):

```bash
# Install EAS CLI
npm install -g eas-cli

# Login
eas login

# Configure
eas build:configure

# Build for iOS
eas build --platform ios --profile production

# Build for Android
eas build --platform android --profile production
```

---

## Step 5: End-to-End Testing ✓

Test the complete flow:

1. **File report from mobile app:**
   - Open field app
   - Sign in (or use "Continue as Guest")
   - Create new incident report
   - Add photo, location, description
   - Submit

2. **Verify in console:**
   - Open frontend (Vercel URL)
   - Sign in as `controller` / `control123`
   - Go to **Incidents** page
   - Report should appear with label **"via field app"**

3. **Test routing:**
   - Go to **Route Planning** tab
   - Enter origin and destination
   - Check that route calculates with accessibility scores

**✅ Checkpoint:** Full loop working - phone → backend → console

---

## Important Security Notes ⚠️

### For Demo/Testing
- Demo credentials are fine: `controller`/`control123`, `verifier.as`/`verify123`
- Leave `NER_DISABLE_DEMO_SEED` unset or set to `0`
- `CORS_ORIGINS` can be `*` for testing

### For Production
1. **Disable demo accounts:**
   ```
   NER_DISABLE_DEMO_SEED=1
   ```

2. **Create real users** via Render Shell:
   ```python
   # Render dashboard → your service → Shell → python
   from src.api.auth import hash_password
   from src.db.models import User
   from src.db.session import get_session

   session = get_session()
   session.add(User(
       username="your.username",
       full_name="Your Name",
       password_hash=hash_password("strong-password-here"),
       role="controller",  # or "verifier" or "reporter"
       organisation="Your Org",
       jurisdiction="Assam,Meghalaya"  # for verifiers
   ))
   session.commit()
   ```

3. **Lock down CORS:**
   ```
   CORS_ORIGINS=https://your-frontend.vercel.app
   ```

---

## Environment Variables Summary

### Backend (Render)
```bash
DATABASE_URL=postgresql://user:pass@ep-xxx.aws.neon.tech/neondb?sslmode=require
CORS_ORIGINS=https://your-frontend.vercel.app
NER_DISABLE_DEMO_SEED=1  # for production
PORT=10000
MAX_CONTENT_MB=16  # optional
```

### Frontend (Vercel)
```bash
VITE_API_BASE_URL=https://your-backend.onrender.com
```

### Mobile App (Expo)
```bash
EXPO_PUBLIC_API_BASE_URL=https://your-backend.onrender.com
```

---

## Troubleshooting

### "Cannot connect to backend"
- Check `VITE_API_BASE_URL` is correct (no trailing slash)
- Verify `CORS_ORIGINS` includes your frontend URL
- Test backend `/health` endpoint directly

### "Reports not appearing in console"
- Verify all three parts use the SAME backend URL
- Check `DATABASE_URL` is set (not using SQLite)
- Use "Test connection" in mobile app to verify backend

### "Live weather not working"
- Check backend logs in Render dashboard
- Test `/api/ner/weather` endpoint
- `"live": false` in response means fallback is active

### Render free tier sleeping
- First request after inactivity takes ~30s
- Consider upgrading to paid tier for always-on
- Or accept the cold-start delay

---

## Deployment URLs Template

Fill this in as you deploy:

```
Database:  postgresql://_______________
Backend:   https://_______________
Frontend:  https://_______________
```

---

## Quick Deploy Commands

Once everything is set up, redeployment is automatic:

- **Backend:** Push to GitHub → Render auto-deploys
- **Frontend:** Push to GitHub → Vercel auto-deploys  
- **Mobile:** Change `.env` → `npx expo start` (or `eas build`)

---

## Need Help?

- Backend logs: Render dashboard → your service → Logs
- Frontend logs: Vercel dashboard → your project → Deployments → View logs
- Mobile logs: Run `npx expo start` and check terminal

**Note:** The backend takes ~30-60 seconds on first deploy while it warms up the ML models.
