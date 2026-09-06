# Real-Time Data Quick Reference

## 🚀 Quick Start (3 Commands)

```bash
cd routeOptimiserBackend
python switch_to_real_data.py  # Switch to real-time mode
cp .env.realtime .env            # Copy environment template
python main.py                   # Start with free data sources
```

## 📊 Data Sources Status

| Data Type | Source | Status | API Key? | Fallback |
|-----------|--------|--------|----------|----------|
| **Weather** | IMD Official | ✅ Live | YES* | Open-Meteo |
| **Roads** | OpenStreetMap | ✅ Live | NO | Cached |
| **Terrain** | SRTM/NASA | ✅ Live | NO | None needed |
| **Disasters** | GDACS/UN | ✅ Live | NO | None needed |
| **Traffic** | TomTom/HERE | ✅ Live | YES* | Time-based |
| **Incidents** | Community | ✅ Live | NO | None needed |

*Optional but recommended

## 🔑 API Keys

### Critical (Official Gov Data)
```bash
# India Meteorological Department
IMD_API_KEY=get_from_data.gov.in
```

### Recommended (Real-Time Traffic)
```bash
# Choose one:
TOMTOM_API_KEY=get_from_developer.tomtom.com    # 2,500/day free
HERE_API_KEY=get_from_developer.here.com         # 250k/month free
```

### No Keys Needed
- OpenStreetMap (free)
- SRTM elevation (free)
- GDACS disasters (free)
- Open-Meteo weather fallback (free)

## ✅ Verification

```bash
# Check all data sources
curl http://localhost:5001/api/ner/data-sources | jq

# Check if IMD is active
curl http://localhost:5001/api/ner/data-sources | \
  jq '.sources[] | select(.id=="weather_rainfall") | .is_official_imd'
# Should return: true (with IMD key) or false (fallback)

# Check traffic source
curl http://localhost:5001/api/ner/data-sources | \
  jq '.configuration_status.traffic_apis'

# Test route with live data
curl -X POST http://localhost:5001/api/ner/plan-route \
  -H "Content-Type: application/json" \
  -d '{"origin":"LOC001","destination":"LOC007","cargo_type":"medicine"}'
```

## 🔧 Environment Variables (Copy-Paste Ready)

```bash
# ============ CRITICAL ============
IMD_API_KEY=your_key_here

# ============ RECOMMENDED ============
TOMTOM_API_KEY=your_key_here
# OR
HERE_API_KEY=your_key_here

# ============ DATABASE ============
DATABASE_URL=postgresql://user:pass@host:5432/db

# ============ OPTIONAL ============
IMD_CACHE_TTL=1800              # 30 minutes
TRAFFIC_CACHE_TTL=300           # 5 minutes
REAL_DATA_CACHE_TTL=3600        # 1 hour
IMD_TIMEOUT=15.0
TRAFFIC_TIMEOUT=10.0
REAL_DATA_TIMEOUT=30.0
```

## 📝 Files Modified by switch_to_real_data.py

1. `src/services/accessibility_service.py` → Uses `RealTimeNERDataProvider`
2. `src/api/ner_routes.py` → Uses `get_real_data_sources()`
3. `.env.realtime` → Created with template

## 🧪 Testing

```bash
# Unit tests (mocked, no keys needed)
pytest tests/test_real_data_providers.py -v

# Integration tests (real APIs, keys needed)
pytest tests/test_real_data_providers.py --integration -v
```

## 🚨 Troubleshooting

| Problem | Quick Fix |
|---------|-----------|
| `is_official_imd: false` | Add IMD_API_KEY to .env |
| Traffic always "estimated" | Add TOMTOM_API_KEY or HERE_API_KEY |
| Empty road segments | Check OVERPASS_URL, increase timeout |
| SSL certificate errors | `pip install --upgrade certifi` |
| Missing elevations | Increase REAL_DATA_TIMEOUT |

## 📍 Key Endpoints

- `/api/ner/data-sources` - Full data source manifest
- `/api/ner/weather` - Live weather status
- `/api/ner/segments` - Road segments with live data
- `/api/ner/locations` - Real OSM locations
- `/api/ner/plan-route` - Route with live conditions

## 💰 Cost (Free Tier)

| Service | Free Limit | Typical Usage | Cost |
|---------|------------|---------------|------|
| IMD | Varies | ~10k/day | $0 |
| TomTom | 2,500/day | ~500/day | $0 |
| HERE | 250k/month | ~15k/month | $0 |
| OSM | Fair use | ~1k/day | $0 |
| SRTM | Unlimited | ~1k/day | $0 |
| GDACS | Unlimited | ~10/day | $0 |

**Total: $0/month** for moderate usage

## 📚 Full Documentation

See [REAL_TIME_DATA_SETUP.md](./REAL_TIME_DATA_SETUP.md) for complete guide.

## 🎯 What Changed

### Before (Sample/Synthetic)
- Road risks: hand-typed CSV values
- Weather: frozen snapshot
- Terrain: approximations
- Disasters: invented counts
- Traffic: none

### After (Real-Time)
- Road risks: calculated from real terrain + historical events
- Weather: **official IMD** or live Open-Meteo
- Terrain: **real SRTM** elevation data
- Disasters: **real GDACS** events
- Traffic: **real-time** TomTom/HERE (optional)

### Trust Levels
- ❌ `synthetic` - REMOVED
- ❌ `sample` - REMOVED
- ✅ `live` - Real-time authoritative data
- ✅ `derived` - Calculated from live inputs

## 🔗 Get API Keys

1. **IMD**: https://data.gov.in/ → Sign up → Request API access
2. **TomTom**: https://developer.tomtom.com/ → Get started free
3. **HERE**: https://developer.here.com/ → Sign up → Create project

## ✨ Features

- ✅ All data real-time or derived from live sources
- ✅ Graceful fallbacks (never breaks)
- ✅ Proper attribution (OpenStreetMap, SRTM, etc.)
- ✅ Free tier available
- ✅ Production-ready
- ✅ Comprehensive tests
- ✅ No fabricated data

---

**Status**: 🟢 Production Ready with Real-Time Data Integration
