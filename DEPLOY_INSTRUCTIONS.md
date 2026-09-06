# Deploy LogiRush - Simple Steps

Your code is ready to deploy. Here's what to do:

## Step 1: Push to GitHub

```bash
# If you don't have a GitHub repo yet:
# 1. Go to github.com/new
# 2. Create a new repository (name it "LogiRush")
# 3. Then run:

cd /Users/user/Downloads/LogiRush
git remote add origin https://github.com/YOUR_USERNAME/LogiRush.git
git push -u origin main
```

## Step 2: Deploy Frontend to Vercel

**Easy way - Use the website:**

1. Go to: https://vercel.com/new
2. Sign in with GitHub
3. Click "Import Project"
4. Select your LogiRush repository
5. **Important settings:**
   - Framework: Vite
   - Root Directory: `routeOptimiserFrontend` ⚠️ (Click Edit to change)
   - Build Command: `npm run build`
   - Output Directory: `dist`
6. Add environment variable:
   - Name: `VITE_API_BASE_URL`
   - Value: `https://your-backend-url.onrender.com` (get this from Step 3)
7. Click Deploy

## Step 3: Deploy Backend to Render

1. Go to: https://render.com/deploy?repo=https://github.com/YOUR_USERNAME/LogiRush
2. Sign in and connect GitHub
3. It will read `render.yaml` automatically
4. Set environment variables:
   - `DATABASE_URL` - Get from Neon.tech (create a free PostgreSQL database)
   - `CORS_ORIGINS` - Put your Vercel URL here after Step 2
   - `PORT` - 10000 (already set)
5. Click "Apply"

## Step 4: Update CORS

After both are deployed:

1. Go to Render dashboard
2. Click your backend service
3. Environment tab
4. Change `CORS_ORIGINS` from `*` to your actual Vercel URL
5. Save

## Done!

Test it:
- Open your Vercel URL
- Login: `controller` / `control123`

---

**OR use Vercel CLI after installing it:**

```bash
# Install Vercel CLI (if permission error, open new terminal)
npm install -g vercel

# Deploy
cd routeOptimiserFrontend
vercel

# Follow the prompts
# When asked for settings, set root to: routeOptimiserFrontend
```

That's it!
