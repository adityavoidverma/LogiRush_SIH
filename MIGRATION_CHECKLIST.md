# 🚀 Real-Time Data Migration Checklist

Use this checklist to migrate LogiRush from sample/synthetic data to real-time sources.

---

## Pre-Migration

### 📋 Review & Planning
- [ ] Read [REAL_TIME_DATA_SETUP.md](./REAL_TIME_DATA_SETUP.md)
- [ ] Review [REAL_TIME_INTEGRATION_SUMMARY.md](./REAL_TIME_INTEGRATION_SUMMARY.md)
- [ ] Understand data sources in [DATA_ANALYSIS.md](./DATA_ANALYSIS.md)
- [ ] Check [REAL_TIME_DATA_QUICK_REF.md](./REAL_TIME_DATA_QUICK_REF.md) for commands

### 🔑 API Keys (Get These First)
- [ ] IMD API Key from https://data.gov.in/ (CRITICAL for official weather)
- [ ] TomTom API Key from https://developer.tomtom.com/ (OPTIONAL for traffic)
- [ ] HERE API Key from https://developer.here.com/ (OPTIONAL, alternative to TomTom)

### 💾 Backup Current State
- [ ] Backup current `.env` file: `cp .env .env.backup`
- [ ] Commit current code: `git add . && git commit -m "Pre-migration backup"`
- [ ] Note current `/api/ner/data-sources` response for comparison
- [ ] Document any custom configurations

---

## Migration Steps

### 1. Local Development Migration

#### Step 1.1: Switch to Real-Time Mode
```bash
cd routeOptimiserBackend
python switch_to_real_data.py
```

**Expected output:**
```
✓ Updated accessibility_service.py to use RealTimeNERDataProvider
✓ Updated ner_routes.py to use get_real_data_sources()
✓ Created .env.realtime template
```

- [ ] Script completed successfully
- [ ] No errors in output

#### Step 1.2: Configure Environment
```bash
# Copy template
cp .env.realtime .env

# Edit .env with your API keys
nano .env  # or code .env
```

Add at minimum:
```bash
IMD_API_KEY=your_actual_imd_key_here
```

Optionally add:
```bash
TOMTOM_API_KEY=your_tomtom_key
# OR
HERE_API_KEY=your_here_key
```

- [ ] `.env` file created
- [ ] IMD_API_KEY added
- [ ] Traffic API key added (optional)
- [ ] DATABASE_URL configured (if using PostgreSQL)

#### Step 1.3: Install Dependencies
```bash
pip install -r requirements.txt
```

- [ ] All dependencies installed
- [ ] No errors reported
- [ ] `certifi` package present (for SSL/TLS)

#### Step 1.4: Run Tests
```bash
# Unit tests (mocked, no API calls)
pytest tests/test_real_data_providers.py -v
```

- [ ] All tests pass
- [ ] No failures or errors
- [ ] Test output shows mocked API responses

#### Step 1.5: Start Backend
```bash
python main.py
```

Watch for startup messages:
- [ ] "✓ IMD Official API configured" (if IMD key set)
- [ ] "Traffic sources available: TomTom/HERE/Fallback"
- [ ] No critical errors in logs
- [ ] Server starts on port 5001

### 2. Verification

#### Step 2.1: Check Data Sources Endpoint
```bash
curl http://localhost:5001/api/ner/data-sources | jq
```

Verify:
- [ ] `"headline"` mentions "REAL-TIME" data
- [ ] No sources have `"trust": "sample"` or `"trust": "synthetic"`
- [ ] All sources are `"trust": "live"` or `"trust": "derived"`
- [ ] Attribution section includes OpenStreetMap, SRTM, GDACS

#### Step 2.2: Check IMD Status
```bash
curl http://localhost:5001/api/ner/data-sources | \
  jq '.sources[] | select(.id=="weather_rainfall")'
```

Verify:
- [ ] `"is_official_imd": true` (if IMD key configured)
- [ ] OR `"is_official_imd": false` with fallback notice (acceptable)
- [ ] `"source"` shows "imd_official" or "open_meteo"
- [ ] Recent `"fetched_at"` timestamp

#### Step 2.3: Check Traffic Status
```bash
curl http://localhost:5001/api/ner/data-sources | \
  jq '.configuration_status.traffic_apis'
```

Verify:
- [ ] Shows configured traffic source (if API key added)
- [ ] OR shows fallback estimator (acceptable without keys)

#### Step 2.4: Test Road Network
```bash
curl http://localhost:5001/api/ner/locations | jq
```

Verify:
- [ ] Returns locations (not empty)
- [ ] Locations have real coordinates
- [ ] Familiar city names (Guwahati, Shillong, etc.)

```bash
curl http://localhost:5001/api/ner/segments | jq '.[0]'
```

Verify:
- [ ] Segments have real OSM highway names
- [ ] `distance_km` looks realistic
- [ ] `weather_risk` present
- [ ] `landslide_risk` present
- [ ] `road_status` present

#### Step 2.5: Test Route Planning
```bash
curl -X POST http://localhost:5001/api/ner/plan-route \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "LOC001",
    "destination": "LOC007",
    "cargo_type": "medicine",
    "urgency": "high"
  }' | jq
```

Verify:
- [ ] Route returned successfully
- [ ] Real distances and times
- [ ] Weather risk included
- [ ] Alternative routes provided
- [ ] Explanation present

### 3. Frontend Integration

#### Step 3.1: Update Frontend Configuration
```bash
cd ../routeOptimiserFrontend
```

Ensure `.env` points to correct backend:
```bash
VITE_API_BASE_URL=http://localhost:5001
```

- [ ] Frontend `.env` configured
- [ ] Backend URL correct

#### Step 3.2: Test Frontend
```bash
npm run dev
```

Visit http://localhost:5173 and verify:
- [ ] Dashboard loads
- [ ] Map shows corridors
- [ ] Data sources page works (`/data-sources`)
- [ ] Planner works
- [ ] No console errors

#### Step 3.3: Check Data Sources Page
Visit `/data-sources` in browser:
- [ ] Page loads
- [ ] Shows "Real-Time Data Integration"
- [ ] All sources listed
- [ ] Attribution visible
- [ ] Configuration status shown

---

## Production Deployment

### 4. Prepare for Production

#### Step 4.1: Production Environment Variables
Create production `.env` with:

```bash
# CRITICAL
IMD_API_KEY=production_imd_key
DATABASE_URL=postgresql://user:pass@host:5432/db
CORS_ORIGINS=https://your-frontend-domain.com

# RECOMMENDED
TOMTOM_API_KEY=production_tomtom_key
# OR
HERE_API_KEY=production_here_key

# SECURITY
NER_DISABLE_DEMO_SEED=1
FLASK_DEBUG=0

# CACHE & TIMEOUTS
IMD_CACHE_TTL=1800
TRAFFIC_CACHE_TTL=300
REAL_DATA_CACHE_TTL=3600
IMD_TIMEOUT=15.0
TRAFFIC_TIMEOUT=10.0
REAL_DATA_TIMEOUT=30.0
```

- [ ] All production keys obtained
- [ ] DATABASE_URL set to PostgreSQL
- [ ] CORS_ORIGINS set to frontend URL
- [ ] Demo seed disabled
- [ ] Debug mode off

#### Step 4.2: Test Locally Against Production Config
```bash
# Use production .env locally
python main.py
```

- [ ] Starts successfully with production config
- [ ] IMD connects
- [ ] Database connects (if PostgreSQL)
- [ ] No errors

### 5. Deploy to Render/Railway

#### Step 5.1: Update Backend Environment
In Render/Railway dashboard:
- [ ] Set `IMD_API_KEY`
- [ ] Set `TOMTOM_API_KEY` or `HERE_API_KEY`
- [ ] Set `DATABASE_URL` (PostgreSQL)
- [ ] Set `CORS_ORIGINS` (frontend URL)
- [ ] Set `NER_DISABLE_DEMO_SEED=1`
- [ ] Set `FLASK_DEBUG=0`

#### Step 5.2: Deploy Backend
- [ ] Push code to GitHub
- [ ] Trigger deploy on Render/Railway
- [ ] Wait for deployment
- [ ] Check deploy logs for errors

#### Step 5.3: Verify Production Backend
```bash
BACKEND_URL=https://your-backend.onrender.com

# Check health
curl $BACKEND_URL/api/ner/health

# Check data sources
curl $BACKEND_URL/api/ner/data-sources | jq '.headline'

# Check IMD status
curl $BACKEND_URL/api/ner/data-sources | \
  jq '.sources[] | select(.id=="weather_rainfall") | .is_official_imd'
```

- [ ] Health check passes
- [ ] Data sources endpoint works
- [ ] IMD status correct
- [ ] No errors

### 6. Deploy Frontend

#### Step 6.1: Update Frontend Environment
In Vercel dashboard:
- [ ] Set `VITE_API_BASE_URL` to production backend URL

#### Step 6.2: Deploy Frontend
- [ ] Push code to GitHub
- [ ] Trigger deploy on Vercel
- [ ] Wait for deployment

#### Step 6.3: Verify Production Frontend
Visit https://your-frontend.vercel.app:
- [ ] Site loads
- [ ] Dashboard shows data
- [ ] Map renders
- [ ] Data sources page works
- [ ] Route planning works
- [ ] No console errors

---

## Post-Deployment

### 7. Monitoring & Verification

#### Step 7.1: Monitor API Usage
Check dashboards:
- [ ] IMD API usage (data.gov.in dashboard)
- [ ] TomTom usage (developer.tomtom.com)
- [ ] HERE usage (developer.here.com)
- [ ] All within free tier limits

#### Step 7.2: Monitor Application Logs
Check Render/Railway logs:
- [ ] No repeated API failures
- [ ] IMD fetches succeed
- [ ] Traffic fetches succeed
- [ ] OSM requests succeed
- [ ] No critical errors

#### Step 7.3: Test End-to-End
- [ ] File incident from mobile app
- [ ] See incident in web console
- [ ] Plan route with live data
- [ ] Check weather updates (wait 30 min)
- [ ] Verify traffic updates (if configured)

### 8. Documentation

#### Step 8.1: Update Team Documentation
- [ ] Share [REAL_TIME_DATA_QUICK_REF.md](./REAL_TIME_DATA_QUICK_REF.md) with team
- [ ] Document API key rotation procedure
- [ ] Document troubleshooting steps
- [ ] Update deployment runbook

#### Step 8.2: Update README
- [ ] Add note about real-time data
- [ ] Link to setup guide
- [ ] Update deployment instructions
- [ ] Add data source attribution

---

## Rollback Procedure (If Needed)

### Emergency Rollback

If something goes wrong:

#### Step 1: Restore Local Environment
```bash
cd routeOptimiserBackend
cp .env.backup .env
git checkout src/services/accessibility_service.py
git checkout src/api/ner_routes.py
python main.py
```

#### Step 2: Revert Production Deploy
- In Render/Railway: Revert to previous deployment
- OR redeploy previous Git commit
- Update frontend to point to rolled-back backend

#### Step 3: Investigate
- Check logs for error messages
- Verify API keys are correct
- Test individual components
- Review [Troubleshooting](#troubleshooting) section

---

## Troubleshooting

### Issue: IMD API Not Working

**Symptoms:**
- `"is_official_imd": false`
- Logs show IMD fetch failures

**Checks:**
- [ ] Verify IMD_API_KEY is set: `echo $IMD_API_KEY`
- [ ] Test IMD API directly with curl
- [ ] Check IMD dashboard for quota/status
- [ ] Check firewall/network access

**Resolution:**
- System automatically falls back to Open-Meteo
- Still live data, just not official IMD
- Fix key and restart backend

### Issue: Traffic Data Always "Estimated"

**Symptoms:**
- All segments show `"data_source": "estimated"`

**Checks:**
- [ ] Verify TOMTOM_API_KEY or HERE_API_KEY is set
- [ ] Check API dashboard for quota
- [ ] Test API directly with curl

**Resolution:**
- System falls back to time-based estimation
- Still provides reasonable delays
- Fix key and restart backend

### Issue: No Road Segments

**Symptoms:**
- `/api/ner/segments` returns empty or very few

**Checks:**
- [ ] Check OSM Overpass API status
- [ ] Increase REAL_DATA_TIMEOUT
- [ ] Try alternative Overpass endpoint

**Resolution:**
- Set `OVERPASS_URL=https://overpass.kumi.systems/api/interpreter`
- Set `REAL_DATA_TIMEOUT=60.0`
- Restart backend

### Issue: Missing Elevation Data

**Symptoms:**
- Elevation values are 0 or missing
- Slope calculations show 0

**Checks:**
- [ ] Check open-elevation.com status
- [ ] Try alternative elevation API

**Resolution:**
- Set `ELEVATION_API_URL=https://api.opentopodata.org/v1/srtm30m`
- Increase `REAL_DATA_TIMEOUT=45.0`
- Restart backend

---

## Success Criteria

Migration is complete when:

### Required ✅
- [ ] Backend starts without errors
- [ ] `/api/ner/data-sources` shows no synthetic/sample data
- [ ] All trust levels are 'live' or 'derived'
- [ ] Road network from OSM loads
- [ ] Elevation data from SRTM works
- [ ] GDACS disaster data loads
- [ ] Routes can be planned
- [ ] Tests pass

### Optimal ✅ 
- [ ] IMD API configured (`is_official_imd: true`)
- [ ] Traffic API configured (TomTom or HERE)
- [ ] Frontend connects successfully
- [ ] No errors in production logs
- [ ] API usage within limits

---

## Timeline Estimate

- **Quick start (no keys)**: 15 minutes
- **With IMD key**: 30 minutes (including key acquisition)
- **Full setup (all keys)**: 1 hour
- **Production deployment**: 2 hours (including testing)

---

## Support

If you get stuck:

1. Check [REAL_TIME_DATA_SETUP.md](./REAL_TIME_DATA_SETUP.md) for detailed guides
2. Check [REAL_TIME_DATA_QUICK_REF.md](./REAL_TIME_DATA_QUICK_REF.md) for commands
3. Review [Troubleshooting](#troubleshooting) section above
4. Check `/api/ner/data-sources` for runtime status
5. Review application logs

---

**Status**: Ready for migration 🚀  
**Date**: January 2025  
**Version**: 2.0 - Real-Time Integration
