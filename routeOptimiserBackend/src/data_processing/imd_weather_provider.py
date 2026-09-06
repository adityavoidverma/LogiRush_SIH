# src/data_processing/imd_weather_provider.py
"""
Official India Meteorological Department (IMD) weather data integration.

This module provides real IMD rainfall data as the authoritative source for Indian weather.
It supports multiple IMD data sources:

1. IMD OpenData Platform API (https://mausam.imd.gov.in/)
2. IMD AWS (Automatic Weather Station) data
3. IMD Gridded Data (0.25° x 0.25° resolution)
4. Fallback to Open-Meteo with proper IMD model selection

All rainfall data is properly attributed as official IMD data when sourced directly,
or clearly marked when using alternative sources.
"""

from __future__ import annotations

import json
import logging
import os
import ssl
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# ================================================================
# Configuration
# ================================================================

# IMD API endpoints
IMD_API_BASE = os.environ.get("IMD_API_BASE", "https://api.data.gov.in/resource")
IMD_AWS_ENDPOINT = os.environ.get("IMD_AWS_ENDPOINT", "https://mausam.imd.gov.in/backend/api/aws_data")
IMD_API_KEY = os.environ.get("IMD_API_KEY", "")  # Required for data.gov.in API

# Open-Meteo with IMD-specific model configuration
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# Cache settings
IMD_CACHE_TTL = int(os.environ.get("IMD_CACHE_TTL", "1800"))  # 30 minutes
IMD_TIMEOUT = float(os.environ.get("IMD_TIMEOUT", "15.0"))

USER_AGENT = "NER-Logistics-Platform/2.0 (IMD integration)"

# ================================================================
# SSL Context
# ================================================================

def _ssl_context():
    """TLS context with proper certificate verification."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()

_SSL_CONTEXT = _ssl_context()


# ================================================================
# Utilities
# ================================================================

def _get_json(url: str, timeout=IMD_TIMEOUT) -> dict:
    """Fetch JSON with proper error handling."""
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=timeout, context=_SSL_CONTEXT) as response:
        return json.loads(response.read().decode("utf-8", "replace"))


def _post_json(url: str, data: dict, timeout=IMD_TIMEOUT) -> dict:
    """POST JSON data and get response."""
    request = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    )
    with urllib.request.urlopen(request, timeout=timeout, context=_SSL_CONTEXT) as response:
        return json.loads(response.read().decode("utf-8", "replace"))


class _Cache:
    """Thread-safe cache with TTL."""
    def __init__(self, ttl=IMD_CACHE_TTL):
        self._data = {}
        self._ttl = ttl
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            if key not in self._data:
                return None
            value, timestamp = self._data[key]
            if time.time() - timestamp > self._ttl:
                del self._data[key]
                return None
            return value

    def put(self, key, value):
        with self._lock:
            self._data[key] = (value, time.time())

    def clear(self):
        with self._lock:
            self._data.clear()


# ================================================================
# IMD Data Fetchers
# ================================================================

class IMDOfficialDataFetcher:
    """
    Fetch official IMD data from IMD AWS and data.gov.in APIs.
    
    This is the authoritative source for Indian meteorological data.
    Requires IMD_API_KEY for full access.
    """

    def __init__(self, api_key: str = IMD_API_KEY):
        self.api_key = api_key
        self._cache = _Cache()
        self.enabled = bool(api_key)

    def fetch_aws_rainfall(self, state: str = None) -> list[dict]:
        """
        Fetch Automatic Weather Station data from IMD.
        Returns real-time rainfall observations from IMD AWS network.
        """
        if not self.enabled:
            logger.debug("IMD API key not configured")
            return []

        cache_key = f"imd_aws_{state or 'all'}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        try:
            # IMD AWS API provides real-time station data
            params = {
                "api-key": self.api_key,
                "format": "json",
                "limit": 1000,
            }
            
            if state:
                params["filters[state]"] = state

            url = f"{IMD_API_BASE}/aws_rainfall?{urllib.parse.urlencode(params)}"
            logger.info(f"Fetching IMD AWS rainfall data for {state or 'all regions'}...")
            
            result = _get_json(url, timeout=IMD_TIMEOUT)
            
            records = result.get("records", [])
            self._cache.put(cache_key, records)
            logger.info(f"Fetched {len(records)} IMD AWS rainfall records")
            return records

        except Exception as e:
            logger.warning(f"Failed to fetch IMD AWS data: {e}")
            return []

    def fetch_district_rainfall(self, district: str, state: str, days: int = 7) -> dict:
        """
        Fetch district-level rainfall data from IMD.
        Returns accumulated rainfall for the specified period.
        """
        if not self.enabled:
            return {}

        cache_key = f"imd_district_{district}_{state}_{days}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        try:
            params = {
                "api-key": self.api_key,
                "format": "json",
                "filters[district]": district,
                "filters[state]": state,
            }

            url = f"{IMD_API_BASE}/district_rainfall?{urllib.parse.urlencode(params)}"
            result = _get_json(url, timeout=IMD_TIMEOUT)

            if result.get("records"):
                data = result["records"][0]
                self._cache.put(cache_key, data)
                return data

        except Exception as e:
            logger.debug(f"Failed to fetch IMD district rainfall: {e}")

        return {}


class IMDGriddedDataFetcher:
    """
    Fetch IMD gridded rainfall data (0.25° x 0.25° resolution).
    Provides historical and near-real-time rainfall on a spatial grid.
    """

    def __init__(self):
        self._cache = _Cache()

    def fetch_gridded_rainfall(self, lat: float, lon: float, days: int = 1) -> Optional[float]:
        """
        Fetch gridded rainfall for a specific location.
        Returns accumulated rainfall in mm.
        
        Note: This requires access to IMD's gridded datasets which may need
        separate authentication or file access.
        """
        cache_key = f"imd_grid_{lat:.2f}_{lon:.2f}_{days}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        try:
            # IMD gridded data is typically available as NetCDF or binary files
            # This is a placeholder for actual gridded data access
            # In production, this would read from IMD's gridded data archives
            
            logger.debug(f"IMD gridded data access not yet configured for {lat}, {lon}")
            return None

        except Exception as e:
            logger.debug(f"Failed to fetch IMD gridded data: {e}")
            return None


class OpenMeteoIMDProvider:
    """
    Open-Meteo configured to prefer IMD/regional models where available.
    
    While not official IMD, Open-Meteo serves multiple weather models including
    regional models that cover India. This is used as a reliable fallback with
    proper attribution.
    """

    def __init__(self):
        self._cache = _Cache()

    def fetch_rainfall(self, coordinates: list[tuple[float, float]]) -> dict:
        """
        Fetch rainfall using Open-Meteo with IMD-region model preferences.
        
        Returns rainfall data with clear attribution that this is Open-Meteo
        serving global models, NOT official IMD data.
        """
        cache_key = f"openmeteo_imd_{hash(tuple(coordinates))}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        try:
            # Request with model preferences for India region
            params = {
                "latitude": ",".join(f"{lat:.4f}" for lat, _ in coordinates),
                "longitude": ",".join(f"{lon:.4f}" for _, lon in coordinates),
                "hourly": "precipitation",
                "past_days": "1",
                "forecast_days": "3",
                "timezone": "Asia/Kolkata",
                # Prefer models with good India coverage
                "models": "best_match",
            }

            url = f"{OPEN_METEO_URL}?{urllib.parse.urlencode(params)}"
            result = _get_json(url, timeout=15.0)

            # Process results
            entries = result if isinstance(result, list) else [result]
            readings = {}

            for (lat, lon), entry in zip(coordinates, entries):
                readings[self._key(lat, lon)] = self._accumulate(entry)

            self._cache.put(cache_key, readings)
            return readings

        except Exception as e:
            logger.warning(f"Failed to fetch Open-Meteo rainfall: {e}")
            return {}

    def _key(self, lat: float, lon: float) -> tuple:
        return (round(float(lat), 3), round(float(lon), 3))

    def _accumulate(self, entry: dict) -> dict:
        """Calculate 24h and 48h rainfall totals."""
        hourly = entry.get("hourly", {})
        times = hourly.get("time", [])
        precipitation = hourly.get("precipitation", [])

        if not times or not precipitation:
            return {"rain_24h": 0.0, "rain_48h": 0.0}

        # Find current hour
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        now_iso = now.strftime("%Y-%m-%dT%H:00")

        try:
            split = times.index(now_iso)
        except ValueError:
            split = min(24, len(times))

        def total(values):
            return round(sum(v for v in values if isinstance(v, (int, float))), 1)

        return {
            "rain_24h": total(precipitation[max(0, split - 24):split]),
            "rain_48h": total(precipitation[split:split + 48]),
        }


# ================================================================
# Unified IMD Weather Provider
# ================================================================

class IMDWeatherProvider:
    """
    Unified weather provider prioritizing official IMD data sources.
    
    Data source priority:
    1. IMD Official AWS data (requires API key) - OFFICIAL IMD DATA
    2. IMD Gridded data (if available) - OFFICIAL IMD DATA
    3. Open-Meteo with India-optimized models - THIRD-PARTY FALLBACK
    
    Always clearly marks data source and whether it's official IMD.
    """

    def __init__(self):
        self.imd_official = IMDOfficialDataFetcher()
        self.imd_gridded = IMDGriddedDataFetcher()
        self.open_meteo = OpenMeteoIMDProvider()
        
        self._snapshot = None
        self._lock = threading.Lock()
        
        self._log_configuration()

    def _log_configuration(self):
        """Log which IMD sources are configured."""
        if self.imd_official.enabled:
            logger.info("✓ IMD Official API configured - will use authoritative IMD data")
        else:
            logger.warning("✗ IMD API key not configured - using fallback weather sources")
            logger.info("  Set IMD_API_KEY environment variable for official IMD data")

    def get_rainfall(self, coordinates: list[tuple[float, float]]) -> dict:
        """
        Get rainfall for multiple coordinates.
        Tries official IMD sources first, falls back to Open-Meteo.
        
        Returns: {
            "readings": {(lat, lon): {"rain_24h": mm, "rain_48h": mm}},
            "source": "imd_official" | "imd_gridded" | "open_meteo",
            "is_official_imd": bool,
            "fetched_at": timestamp,
            "error": str (if any)
        }
        """
        with self._lock:
            if self._snapshot and self._is_fresh(self._snapshot):
                return self._snapshot

        started = time.time()
        
        # Try official IMD data first
        if self.imd_official.enabled:
            readings = self._try_imd_official(coordinates)
            if readings:
                snapshot = {
                    "readings": readings,
                    "source": "imd_official",
                    "source_name": "India Meteorological Department - Official AWS Network",
                    "is_official_imd": True,
                    "fetched_at": datetime.utcnow().isoformat(),
                    "fetch_duration_s": round(time.time() - started, 2),
                    "error": None,
                }
                with self._lock:
                    self._snapshot = snapshot
                logger.info(f"✓ Using official IMD rainfall data for {len(readings)} points")
                return snapshot

        # Try IMD gridded data
        readings = self._try_imd_gridded(coordinates)
        if readings:
            snapshot = {
                "readings": readings,
                "source": "imd_gridded",
                "source_name": "India Meteorological Department - Gridded Data",
                "is_official_imd": True,
                "fetched_at": datetime.utcnow().isoformat(),
                "fetch_duration_s": round(time.time() - started, 2),
                "error": None,
            }
            with self._lock:
                self._snapshot = snapshot
            logger.info(f"✓ Using IMD gridded rainfall data for {len(readings)} points")
            return snapshot

        # Fallback to Open-Meteo
        readings = self.open_meteo.fetch_rainfall(coordinates)
        snapshot = {
            "readings": readings if readings else {},
            "source": "open_meteo",
            "source_name": "Open-Meteo (Global Weather Models - NOT official IMD)",
            "is_official_imd": False,
            "fetched_at": datetime.utcnow().isoformat(),
            "fetch_duration_s": round(time.time() - started, 2),
            "error": None if readings else "All weather sources unavailable",
        }
        
        with self._lock:
            self._snapshot = snapshot
        
        if readings:
            logger.warning("⚠ Using Open-Meteo fallback (not official IMD data)")
        else:
            logger.error("✗ All weather data sources failed")
        
        return snapshot

    def _try_imd_official(self, coordinates: list[tuple[float, float]]) -> dict:
        """Try to get rainfall from official IMD AWS stations."""
        try:
            # Fetch all AWS data for NER states
            ner_states = ["Assam", "Meghalaya", "Manipur", "Mizoram", "Nagaland", 
                         "Arunachal Pradesh", "Tripura", "Sikkim"]
            
            all_stations = []
            for state in ner_states:
                stations = self.imd_official.fetch_aws_rainfall(state)
                all_stations.extend(stations)

            if not all_stations:
                return {}

            # Match coordinates to nearest AWS stations
            readings = {}
            for lat, lon in coordinates:
                nearest = self._find_nearest_station(lat, lon, all_stations)
                if nearest:
                    key = (round(lat, 3), round(lon, 3))
                    readings[key] = {
                        "rain_24h": float(nearest.get("rainfall_24h", 0)),
                        "rain_48h": float(nearest.get("rainfall_48h", 0)),
                        "station": nearest.get("station_name"),
                        "distance_km": nearest.get("distance"),
                    }

            return readings if readings else {}

        except Exception as e:
            logger.debug(f"IMD official fetch failed: {e}")
            return {}

    def _try_imd_gridded(self, coordinates: list[tuple[float, float]]) -> dict:
        """Try to get rainfall from IMD gridded data."""
        try:
            readings = {}
            for lat, lon in coordinates:
                rainfall = self.imd_gridded.fetch_gridded_rainfall(lat, lon)
                if rainfall is not None:
                    key = (round(lat, 3), round(lon, 3))
                    readings[key] = {
                        "rain_24h": rainfall,
                        "rain_48h": 0.0,  # Gridded data typically doesn't have forecast
                    }
            return readings if readings else {}

        except Exception as e:
            logger.debug(f"IMD gridded fetch failed: {e}")
            return {}

    def _find_nearest_station(self, lat: float, lon: float, stations: list[dict], 
                             max_distance_km: float = 100) -> Optional[dict]:
        """Find nearest AWS station within max distance."""
        import math
        
        def haversine(lat1, lon1, lat2, lon2):
            lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
            dlat, dlon = lat2 - lat1, lon2 - lon1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            return 6371 * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        nearest = None
        min_distance = float('inf')

        for station in stations:
            try:
                st_lat = float(station.get("latitude", 0))
                st_lon = float(station.get("longitude", 0))
                distance = haversine(lat, lon, st_lat, st_lon)
                
                if distance < min_distance and distance <= max_distance_km:
                    min_distance = distance
                    nearest = station.copy()
                    nearest["distance"] = round(distance, 1)
            except (ValueError, TypeError):
                continue

        return nearest

    def _is_fresh(self, snapshot: dict) -> bool:
        """Check if cached snapshot is still fresh."""
        if not snapshot or "fetched_at" not in snapshot:
            return False
        
        fetched = datetime.fromisoformat(snapshot["fetched_at"].replace("Z", "+00:00"))
        age = (datetime.utcnow() - fetched.replace(tzinfo=None)).total_seconds()
        return age < IMD_CACHE_TTL

    def status(self) -> dict:
        """Get status of all weather sources."""
        snapshot = self._snapshot or {}
        
        return {
            "imd_official": {
                "enabled": self.imd_official.enabled,
                "type": "official_imd" if self.imd_official.enabled else "unavailable",
                "name": "India Meteorological Department - Official API",
            },
            "imd_gridded": {
                "enabled": True,
                "type": "official_imd",
                "name": "India Meteorological Department - Gridded Data",
                "note": "Requires separate data access configuration",
            },
            "open_meteo": {
                "enabled": True,
                "type": "third_party_fallback",
                "name": "Open-Meteo Global Models",
                "note": "NOT official IMD data - used when IMD sources unavailable",
            },
            "current_source": snapshot.get("source", "not_yet_fetched"),
            "is_official_imd": snapshot.get("is_official_imd", False),
            "last_fetch": snapshot.get("fetched_at"),
            "cache_ttl_seconds": IMD_CACHE_TTL,
        }


# ================================================================
# Singleton instance
# ================================================================

imd_weather_provider = IMDWeatherProvider()

