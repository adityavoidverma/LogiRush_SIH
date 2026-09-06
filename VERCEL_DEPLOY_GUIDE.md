# Deploying LogiRush Frontend to Vercel

## Overview

This guide focuses specifically on deploying the **React frontend** to Vercel. The backend will be deployed to Render (Python Flask doesn't run on Vercel).

## Architecture

```
┌─────────────────┐
│  Neon Database  │ PostgreSQL
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Render Backend  │ Python/Flask API
│  (Port 10000)   │ ML models, routing logic
└────────┬────────┘
         │
         ├─────────────────┐
         ▼                 ▼
┌──────────────┐   ┌──────────────┐
│   Vercel     │   │  Expo App    │
│  (Frontend)  │   │  (Mobile)    │
│ React + Vite │   │ React Native │
└──────────────┘   └──────────────┘
```

---

## Prerequisites

✅ Before you start:

1. **GitHub Account** - Your code must be on GitHub
2. **Vercel Account** - Sign up at [vercel.com](https://vercel.com)
3. **Backend Deployed** - You need the backend URL first
   - If not done yet, deploy backend to Render first (see QUICK_DEPLOY.md)
   - You'll need: `https://your-backend.onrender.com`

---

## Step-by-Step Deployment

### Step 1: Push to GitHub

If you haven't already:

```bash
cd /Users/user/Downloads/LogiRush

# Check git status
git status

# If not a git repo yet:
git init
git add .
git commit -m "Initial commit - ready for deployment"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy to Vercel

#### Option A: Using Deploy Button

1. Click this button:

   [![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FYOUR_USERNAME%2FYOUR_REPO&root-directory=routeOptimiserFrontend&project-name=logirush-console&env=VITE_API_BASE_URL&envDescription=URL%20of%20your%20deployed%20backend)

2. Sign in to Vercel with GitHub

3. When prompted for `VITE_API_BASE_URL`:
   - Enter your backend URL: `https://your-backend.onrender.com`
   - **Important:** No trailing slash!

4. Click **Deploy**

5. Wait 2-3 minutes ☕

6. Done! Your app is live at: `https://your-project.vercel.app`

#### Option B: Manual Import

1. **Go to Vercel Dashboard**
   - Visit: [vercel.com/new](https://vercel.com/new)
   - Sign in with GitHub

2. **Import Repository**
   - Click "Add New..." → "Project"
   - Select your GitHub repository
   - Click "Import"

3. **Configure Project** ⚠️ **CRITICAL STEP**
   
   - **Project Name:** `logirush-console` (or your choice)
   
   - **Framework Preset:** Vite ✓ (auto-detected)
   
   - **Root Directory:** Click **"Edit"** button
     - Change from `/` to: `routeOptimiserFrontend`
     - This is the most commonly missed step!
   
   - **Build Command:** `npm run build` (auto-filled)
   
   - **Output Directory:** `dist` (auto-filled)
   
   - **Install Command:** `npm install` (auto-filled)

4. **Add Environment Variable**
   
   Click "Environment Variables" section:
   
   | Name | Value |
   |------|-------|
   | `VITE_API_BASE_URL` | `https://your-backend.onrender.com` |
   
   Example: `https://ner-logistics-backend.onrender.com`
   
   **No trailing slash!**

5. **Deploy**
   - Click "Deploy" button
   - Watch the build logs
   - First deploy takes ~2-3 minutes

6. **Get Your URL**
   - After deployment: `https://your-project-xxx.vercel.app`
   - Copy this URL - you'll need it next

### Step 3: Update Backend CORS

Your backend needs to allow requests from your new Vercel domain:

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click your backend service
3. Go to **"Environment"** tab
4. Find `CORS_ORIGINS` variable
5. Update value to your Vercel URL:
   ```
   https://your-project-xxx.vercel.app
   ```
6. Click **"Save Changes"**
7. Backend will automatically redeploy (~2 mins)

### Step 4: Test Your Deployment

1. **Open your Vercel URL** in a browser

2. **Sign in** with demo credentials:
   - Username: `controller`
   - Password: `control123`

3. **Check Dashboard:**
   - Should load without errors
   - Map should display
   - Weather data should load

4. **Check Browser Console** (F12):
   - No CORS errors
   - No 404 errors
   - API calls should succeed

---

## Troubleshooting

### ❌ "Cannot connect to backend"

**Cause:** Backend URL misconfigured or CORS issue

**Fix:**
1. Check Vercel Environment Variables:
   - Go to: Vercel Dashboard → Your Project → Settings → Environment Variables
   - Verify `VITE_API_BASE_URL` is correct
   - Should be: `https://your-backend.onrender.com` (no trailing slash)

2. If you change it, you MUST redeploy:
   - Go to Deployments tab
   - Click "..." → "Redeploy"

3. Check CORS on backend:
   - Backend must have `CORS_ORIGINS` set to your Vercel URL

### ❌ "404 - Page Not Found" on Vercel

**Cause:** Root directory not set correctly

**Fix:**
1. Go to: Vercel Dashboard → Your Project → Settings → General
2. Scroll to "Root Directory"
3. Click "Edit"
4. Set to: `routeOptimiserFrontend`
5. Save and redeploy

### ❌ Build fails with "Cannot find package.json"

**Cause:** Same as above - wrong root directory

**Fix:** Set root directory to `routeOptimiserFrontend`

### ❌ Map not loading

**Cause:** Usually an API key issue or network problem

**Fix:**
1. Check browser console for errors
2. Map tiles use Esri (no key needed), should work by default
3. If still issues, check `routeOptimiserFrontend/.env.example` for map config

### ⚠️ Backend is slow on first request

**Cause:** Render free tier sleeps after inactivity

**Solution:**
- This is normal behavior on free tier
- First request after 15 mins takes ~30 seconds
- Subsequent requests are fast
- Upgrade to paid tier for always-on

---

## Environment Variables Explained

### `VITE_API_BASE_URL` (Required)

- **What:** URL of your backend API
- **Example:** `https://ner-logistics-backend.onrender.com`
- **Important:** 
  - No trailing slash
  - Must be full URL including `https://`
  - This is baked into build - changing requires redeploy

### Map Variables (Optional)

See `routeOptimiserFrontend/.env.example` for:
- `VITE_MAP_TILE_URL` - Custom map tiles
- `VITE_MAP_TILE_ATTRIBUTION` - Map attribution text
- `VITE_MAP_TILE_THEME` - Map theme (light/dark/satellite)

Default uses Esri (no configuration needed).

---

## Updating Your Deployment

### Change Environment Variables

1. Vercel Dashboard → Your Project → Settings → Environment Variables
2. Edit the variable
3. **Important:** Go to Deployments → Redeploy
   - Vite bakes variables at build time
   - Changes don't apply until rebuild

### Deploy Code Changes

Automatic! Just push to GitHub:

```bash
git add .
git commit -m "Updated feature"
git push origin main
```

Vercel automatically rebuilds and deploys.

### Manual Redeploy

1. Vercel Dashboard → Your Project → Deployments
2. Find latest deployment
3. Click "..." menu → "Redeploy"

---

## Custom Domain (Optional)

Add your own domain:

1. Vercel Dashboard → Your Project → Settings → Domains
2. Click "Add"
3. Enter your domain (e.g., `logirush.yourdomain.com`)
4. Follow DNS configuration instructions
5. **Update backend CORS:**
   - Add your custom domain to `CORS_ORIGINS` on Render
   - Example: `https://logirush.yourdomain.com`

---

## Production Checklist

Before going live:

- [ ] Backend deployed to Render with PostgreSQL
- [ ] `NER_DISABLE_DEMO_SEED=1` set on backend (if public)
- [ ] Real user accounts created (not demo credentials)
- [ ] `CORS_ORIGINS` set to your actual frontend URL (not `*`)
- [ ] Frontend environment variable set correctly
- [ ] Custom domain configured (optional)
- [ ] Test full flow: mobile app → backend → frontend
- [ ] SSL/HTTPS working (automatic on Vercel)
- [ ] Error monitoring setup (optional - Vercel has built-in)

---

## Monitoring & Logs

### View Deployment Logs

1. Vercel Dashboard → Your Project → Deployments
2. Click on a deployment
3. View build logs and function logs

### View Runtime Logs

1. Vercel Dashboard → Your Project → Logs
2. See real-time application logs
3. Filter by time, status, source

### Performance Monitoring

Vercel automatically provides:
- Speed insights
- Web vitals
- Lighthouse scores

Access at: Dashboard → Your Project → Analytics

---

## Costs

### Vercel Pricing

**Hobby (Free):**
- ✅ Perfect for demos and personal projects
- ✅ Unlimited deployments
- ✅ HTTPS included
- ✅ 100GB bandwidth/month
- ✅ Automatic HTTPS

**Pro ($20/month):**
- More team features
- Better performance
- More bandwidth
- Commercial use

For LogiRush demo: **Free tier is sufficient**

---

## Support Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Vite Documentation](https://vitejs.dev)
- [Render Documentation](https://render.com/docs)
- This repo's `QUICK_DEPLOY.md` - Full deployment guide
- This repo's `DEPLOY.md` - Original deployment instructions

---

## Quick Reference

### Vercel Dashboard URLs
- Projects: https://vercel.com/dashboard
- New Project: https://vercel.com/new
- Docs: https://vercel.com/docs

### Important Files
- `routeOptimiserFrontend/vercel.json` - Vercel configuration
- `routeOptimiserFrontend/.env.example` - Environment variable template
- `routeOptimiserFrontend/vite.config.js` - Vite configuration

### Demo Credentials
- Username: `controller`
- Password: `control123`
- ⚠️ Disable before public deployment!

---

## Success! 🎉

If everything is working:

✅ Frontend loads at your Vercel URL  
✅ Login works  
✅ Dashboard displays  
✅ Map renders  
✅ No console errors  
✅ Backend API calls succeed  

**Next:** Test the mobile app connection (see QUICK_DEPLOY.md)

---

**Questions?** Check:
1. Browser console (F12) for errors
2. Vercel deployment logs
3. Network tab for failed requests
4. Backend logs on Render
