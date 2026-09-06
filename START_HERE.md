# 🚀 START HERE - Deploy LogiRush to Vercel & Render

Welcome! This guide will get your LogiRush platform deployed in ~20 minutes.

## 📁 What You Have

This is a complete logistics platform with three components:

1. **Backend** - Python/Flask API with ML models (→ Render)
2. **Frontend** - React dashboard (→ Vercel)
3. **Mobile App** - React Native field reporter (→ Expo)

## ⚡ Quick Start (Choose One)

### Option 1: I Want Everything Explained 📚
→ Read **[QUICK_DEPLOY.md](QUICK_DEPLOY.md)**
- Step-by-step with screenshots
- Full explanations
- Troubleshooting tips

### Option 2: I Just Want It Deployed ⚡
→ Follow this:

```bash
# 1. Initialize Git (if needed)
cd /Users/user/Downloads/LogiRush
git init
git add .
git commit -m "Initial commit"

# 2. Create GitHub repo and push
# Go to github.com/new, then:
git remote add origin https://github.com/YOUR_USERNAME/LogiRush.git
git push -u origin main

# 3. Deploy Backend to Render
# Click: https://render.com/deploy?repo=https://github.com/YOUR_USERNAME/LogiRush
# Set DATABASE_URL from Neon (get at: https://console.neon.tech)

# 4. Deploy Frontend to Vercel  
# Click: https://vercel.com/new
# Set root directory: routeOptimiserFrontend
# Set VITE_API_BASE_URL to your Render URL

# 5. Run verification
./verify-deployment.sh
```

### Option 3: I Only Want Vercel 🎯
→ Read **[VERCEL_DEPLOY_GUIDE.md](VERCEL_DEPLOY_GUIDE.md)**
- Focuses only on frontend deployment
- Assumes backend is done

## 🎯 What Gets Deployed Where

| Component | Where | Why |
|-----------|-------|-----|
| Backend (Python) | **Render** | Vercel doesn't support Python Flask |
| Frontend (React) | **Vercel** | Perfect for React/Vite apps |
| Database | **Neon** | Free PostgreSQL hosting |
| Mobile App | **Expo** | Runs on phones, not "deployed" |

## 📋 Prerequisites Checklist

Before you start, you need:

- [ ] GitHub account → [github.com](https://github.com)
- [ ] Neon account (database) → [neon.tech](https://neon.tech)
- [ ] Render account (backend) → [render.com](https://render.com)
- [ ] Vercel account (frontend) → [vercel.com](https://vercel.com)
- [ ] Code pushed to GitHub

## 🔍 Pre-Deployment Check

Run this to verify everything is ready:

```bash
./pre-deploy-check.sh
```

If you see errors, fix them before deploying.

## 📖 All Available Guides

| Guide | What It Covers | When to Use |
|-------|---------------|-------------|
| **[QUICK_DEPLOY.md](QUICK_DEPLOY.md)** | Full deployment (all 3 components) | First time deploying everything |
| **[VERCEL_DEPLOY_GUIDE.md](VERCEL_DEPLOY_GUIDE.md)** | Just the frontend to Vercel | Backend already deployed |
| **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** | Detailed checklist format | Prefer step-by-step boxes |
| **[DEPLOY.md](DEPLOY.md)** | Original technical guide | Want deep technical details |
| **[README.md](README.md)** | Project overview | Understanding the platform |

## 🎬 Deploy Sequence

**Important:** Deploy in this order!

1. **Database** (Neon) - 5 mins
2. **Backend** (Render) - 10 mins
3. **Frontend** (Vercel) - 5 mins
4. **Update CORS** - 2 mins
5. **Mobile App** - 5 mins

Total: ~27 minutes

## 🚨 Common Mistakes

❌ **Wrong root directory on Vercel**
   - Must be: `routeOptimiserFrontend`
   - Not: `/` or blank

❌ **Different backend URLs**
   - Frontend, mobile, and backend CORS must all agree
   - Use the same Render URL everywhere

❌ **Forgetting to update CORS**
   - After Vercel deploys, update Render's `CORS_ORIGINS`

❌ **Not redeploying after env variable change**
   - Vercel: Variables are baked at build time
   - Must redeploy to see changes

## 🎯 Your Deployment URLs

Fill this in as you go:

```
Database:  postgresql://________________________________
Backend:   https://________________________________
Frontend:  https://________________________________

Demo Login:
  Username: controller
  Password: control123
```

## ✅ Success Checklist

After deployment, verify:

- [ ] Backend health check works: `curl YOUR_BACKEND/health`
- [ ] Frontend loads in browser
- [ ] Can sign in with demo credentials
- [ ] Dashboard displays
- [ ] Mobile app connects (use "Test connection" button)
- [ ] File report from mobile → appears in frontend

## 🆘 Need Help?

1. **Run diagnostics:**
   ```bash
   ./verify-deployment.sh
   ```

2. **Check logs:**
   - Render: Dashboard → Service → Logs
   - Vercel: Dashboard → Project → Deployments → View logs

3. **Common issues:**
   - CORS errors → Update `CORS_ORIGINS` on Render
   - "Cannot connect" → Check `VITE_API_BASE_URL`
   - 404 on Vercel → Check root directory setting

## 📚 Learn More

- [NER_PLATFORM.md](NER_PLATFORM.md) - Platform architecture
- [DATA_ANALYSIS.md](DATA_ANALYSIS.md) - Data sources
- [README.md](README.md) - Full project documentation

## 🎉 You're Ready!

Choose your guide above and get started. Everything is configured and ready to deploy.

**Fastest path:**
1. Push to GitHub (if not done)
2. Click deploy buttons in QUICK_DEPLOY.md
3. Fill in environment variables
4. Run verify-deployment.sh

Good luck! 🚀

---

**Quick Links:**
- [Render Dashboard](https://dashboard.render.com)
- [Vercel Dashboard](https://vercel.com/dashboard)
- [Neon Console](https://console.neon.tech)
- [GitHub](https://github.com)
