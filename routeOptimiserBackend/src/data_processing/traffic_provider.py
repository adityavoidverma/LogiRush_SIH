# src/data_processing/traffic_provider.py
"""
Real-time traffic and road condition data provider.

Integrates multiple traffic data sources:
1. TomTom Traffic Flow API (commercial, requires API key)
2. HERE Traffic API (commercial, requires API key)
3. OpenStreetMap road status updates (free, community-sourced)
4. Fallback to calculated estimates based on time of day and road type

All sources provide real-time road conditions, congestion levels, and incidents.
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
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# ================================================================
# Configuration
# ================================================================

# Commercial API keys (optional - system works without them)
TOMTOM_API_KEY = os.environ.get("TOMTOM_API_KEY", "")
HERE_API_KEY = os.environ.get("HERE_API_KEY", "")

# API endpoints
TOMTOM_FLOW_API = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
HERE_TRAFFIC_API = "https://traffic.ls.hereapi.com/traffic/6.3/flow.json"

# Cache and timeout settings
TRAFFIC_CACHE_TTL = int(os.environ.get("TRAFFIC_CACHE_TTL", "300"))  # 5 minutes
TRAFFIC_TIMEOUT = float(os.environ.get("TRAFFIC_TIMEOUT", "10.0"))

USER_AGENT = "NER-Logistics-Platform/2.0 (Traffic integration)"

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
# Data Models
# ================================================================

@dataclass
class TrafficCondition:
    """Real-time traffic condition for a road segment."""
    segment_id: str
    road_status: str  # "Open", "Congested", "Slow", "Blocked", "Closed"
    current_speed_kmh: float
    free_flow_speed_kmh: float
    congestion_level: float  # 0-100
    delay_minutes: float
    last_updated: str
    data_source: str  # "tomtom", "here", "osm", "estimated"
    confidence: float  # 0-1


@dataclass
class RoadIncident:
    """Real-time road incident from traffic APIs."""
    incident_id: str
    incident_type: str  # "accident", "construction", "closure", "congestion"
    severity: int  # 1-5
    latitude: float
    longitude: float
    description: str
    start_time: str
    end_time: Optional[str]
    affected_roads: list[str]
    data_source: str


# ================================================================
# Cache
# ================================================================

class _TrafficCache:
    """Thread-safe cache for traffic data."""
    def __init__(self, ttl=TRAFFIC_CACHE_TTL):
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
# TomTom Traffic Provider
# ================================================================

class TomTomTrafficProvider:
    """Fetch real-time traffic from TomTom Traffic Flow API."""

    def __init__(self, api_key: str = TOMTOM_API_KEY):
        self.api_key = api_key
        self._cache = _TrafficCache()
        self.enabled = bool(api_key)

    def get_flow_data(self, lat: float, lon: float) -> Optional[TrafficCondition]:
        """Get traffic flow data for a specific point."""
        if not self.enabled:
            return None

        cache_key = f"tomtom_{lat:.4f}_{lon:.4f}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        try:
            params = {
                "key": self.api_key,
                "point": f"{lat},{lon}",
                "unit": "KMPH",
            }
            url = f"{TOMTOM_FLOW_API}?{urllib.parse.urlencode(params)}"
            
            request = urllib.request.Request(
                url,
                headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
            )
            
            with urllib.request.urlopen(request, timeout=TRAFFIC_TIMEOUT, context=_SSL_CONTEXT) as response:
                data = json.loads(response.read().decode("utf-8"))

            condition = self._parse_tomtom_response(data)
            if condition:
                self._cache.put(cache_key, condition)
            return condition

        except Exception as e:
            logger.debug(f"TomTom API request failed: {e}")
            return None

    def _parse_tomtom_response(self, data: dict) -> Optional[TrafficCondition]:
        """Parse TomTom API response into TrafficCondition."""
        flow_data = data.get("flowSegmentData", {})
        if not flow_data:
            return None

        current_speed = flow_data.get("currentSpeed", 0)
        free_flow_speed = flow_data.get("freeFlowSpeed", 50)
        
        # Calculate congestion level
        if free_flow_speed > 0:
            speed_ratio = current_speed / free_flow_speed
            congestion = max(0, min(100, (1 - speed_ratio) * 100))
        else:
            congestion = 0

        # Determine road status
        if congestion < 20:
            status = "Open"
        elif congestion < 50:
            status = "Moderate Traffic"
        elif congestion < 80:
            status = "Congested"
        else:
            status = "Severely Congested"

        # Calculate delay
        delay = flow_data.get("currentTravelTime", 0) - flow_data.get("freeFlowTravelTime", 0)
        delay_minutes = max(0, delay / 60)

        return TrafficCondition(
            segment_id="",  # Will be set by caller
            road_status=status,
            current_speed_kmh=current_speed,
            free_flow_speed_kmh=free_flow_speed,
            congestion_level=round(congestion, 1),
            delay_minutes=round(delay_minutes, 1),
            last_updated=datetime.utcnow().isoformat(),
            data_source="tomtom",
            confidence=flow_data.get("confidence", 0.8),
        )


# ================================================================
# HERE Traffic Provider
# ================================================================

class HERETrafficProvider:
    """Fetch real-time traffic from HERE Traffic API."""

    def __init__(self, api_key: str = HERE_API_KEY):
        self.api_key = api_key
        self._cache = _TrafficCache()
        self.enabled = bool(api_key)

    def get_flow_data(self, lat: float, lon: float, radius: int = 1000) -> Optional[TrafficCondition]:
        """Get traffic flow data for a specific area."""
        if not self.enabled:
            return None

        cache_key = f"here_{lat:.4f}_{lon:.4f}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        try:
            params = {
                "apiKey": self.api_key,
                "prox": f"{lat},{lon},{radius}",
                "responseattributes": "sh,fc",
            }
            url = f"{HERE_TRAFFIC_API}?{urllib.parse.urlencode(params)}"
            
            request = urllib.request.Request(
                url,
                headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
            )
            
            with urllib.request.urlopen(request, timeout=TRAFFIC_TIMEOUT, context=_SSL_CONTEXT) as response:
                data = json.loads(response.read().decode("utf-8"))

            condition = self._parse_here_response(data)
            if condition:
                self._cache.put(cache_key, condition)
            return condition

        except Exception as e:
            logger.debug(f"HERE API request failed: {e}")
            return None

    def _parse_here_response(self, data: dict) -> Optional[TrafficCondition]:
        """Parse HERE API response into TrafficCondition."""
        rws = data.get("RWS", [])
        if not rws or not rws[0].get("RW"):
            return None

        road_items = rws[0]["RW"][0].get("FIS", [{}])[0].get("FI", [])
        if not road_items:
            return None

        fi = road_items[0]
        cf = fi.get("CF", [{}])[0]

        current_speed = cf.get("SP", 0)
        free_flow_speed = cf.get("FF", 50)
        jam_factor = cf.get("JF", 0)  # 0-10 scale

        # Convert jam factor to congestion level (0-100)
        congestion = min(100, jam_factor * 10)

        # Determine road status
        if congestion < 20:
            status = "Open"
        elif congestion < 50:
            status = "Moderate Traffic"
        elif congestion < 80:
            status = "Congested"
        else:
            status = "Severely Congested"

        return TrafficCondition(
            segment_id="",
            road_status=status,
            current_speed_kmh=current_speed,
            free_flow_speed_kmh=free_flow_speed,
            congestion_level=round(congestion, 1),
            delay_minutes=0,  # HERE doesn't provide direct delay estimate
            last_updated=datetime.utcnow().isoformat(),
            data_source="here",
            confidence=cf.get("CN", 0.7),
        )


# ================================================================
# Fallback Traffic Estimator
# ================================================================

class FallbackTrafficEstimator:
    """Estimate traffic conditions when live APIs are unavailable."""

    def estimate_traffic(self, highway_type: str, hour: int, is_weekday: bool) -> TrafficCondition:
        """
        Estimate traffic based on time of day and road type.
        Uses realistic patterns but clearly marks as estimated.
        """
        # Base speeds by road type
        base_speeds = {
            "motorway": 80,
            "trunk": 65,
            "primary": 50,
            "secondary": 40,
        }
        free_flow = base_speeds.get(highway_type, 45)

        # Time-based congestion patterns
        congestion = 0
        if is_weekday:
            if 7 <= hour <= 9:  # Morning rush
                congestion = 40
            elif 17 <= hour <= 19:  # Evening rush
                congestion = 50
            elif 10 <= hour <= 16:  # Midday
                congestion = 20
            else:  # Night/early morning
                congestion = 5
        else:  # Weekend
            if 10 <= hour <= 18:
                congestion = 25
            else:
                congestion = 10

        current_speed = free_flow * (1 - congestion / 100)

        # Determine status
        if congestion < 20:
            status = "Open"
        elif congestion < 50:
            status = "Moderate Traffic"
        else:
            status = "Congested"

        return TrafficCondition(
            segment_id="",
            road_status=status,
            current_speed_kmh=round(current_speed, 1),
            free_flow_speed_kmh=free_flow,
            congestion_level=congestion,
            delay_minutes=0,
            last_updated=datetime.utcnow().isoformat(),
            data_source="estimated",
            confidence=0.5,  # Lower confidence for estimates
        )


# ================================================================
# Main Traffic Service
# ================================================================

class TrafficService:
    """
    Unified traffic service that tries multiple sources in order:
    1. TomTom (if API key available)
    2. HERE (if API key available)
    3. Fallback estimation
    
    Always returns traffic data, prioritizing real-time sources.
    """

    def __init__(self):
        self.tomtom = TomTomTrafficProvider()
        self.here = HERETrafficProvider()
        self.fallback = FallbackTrafficEstimator()
        
        self._log_available_sources()

    def _log_available_sources(self):
        """Log which traffic sources are available."""
        sources = []
        if self.tomtom.enabled:
            sources.append("TomTom")
        if self.here.enabled:
            sources.append("HERE")
        sources.append("Fallback Estimator")
        
        logger.info(f"Traffic sources available: {', '.join(sources)}")

    def get_traffic_condition(
        self,
        lat: float,
        lon: float,
        highway_type: str = "primary",
        segment_id: str = ""
    ) -> TrafficCondition:
        """
        Get traffic condition, trying real-time sources first.
        Always returns a result (falls back to estimation if needed).
        """
        # Try TomTom
        if self.tomtom.enabled:
            condition = self.tomtom.get_flow_data(lat, lon)
            if condition:
                condition.segment_id = segment_id
                logger.debug(f"Got traffic data from TomTom for segment {segment_id}")
                return condition

        # Try HERE
        if self.here.enabled:
            condition = self.here.get_flow_data(lat, lon)
            if condition:
                condition.segment_id = segment_id
                logger.debug(f"Got traffic data from HERE for segment {segment_id}")
                return condition

        # Fallback to estimation
        now = datetime.now()
        is_weekday = now.weekday() < 5
        condition = self.fallback.estimate_traffic(highway_type, now.hour, is_weekday)
        condition.segment_id = segment_id
        logger.debug(f"Using estimated traffic for segment {segment_id}")
        return condition

    def get_status_summary(self) -> dict:
        """Get status of all traffic data sources."""
        return {
            "tomtom": {
                "enabled": self.tomtom.enabled,
                "source": "TomTom Traffic Flow API",
                "type": "real-time" if self.tomtom.enabled else "unavailable",
            },
            "here": {
                "enabled": self.here.enabled,
                "source": "HERE Traffic API",
                "type": "real-time" if self.here.enabled else "unavailable",
            },
            "fallback": {
                "enabled": True,
                "source": "Time-based estimation",
                "type": "estimated",
            },
            "active_source": (
                "tomtom" if self.tomtom.enabled
                else "here" if self.here.enabled
                else "fallback"
            ),
        }

    def update_segment_with_traffic(self, segment: dict, highway: dict) -> dict:
        """
        Update a road segment with real-time traffic data.
        Returns updated segment with current conditions.
        """
        midpoint = highway.get("midpoint", (0, 0))
        highway_type = highway.get("highway_type", "primary")
        
        traffic = self.get_traffic_condition(
            midpoint[0],
            midpoint[1],
            highway_type,
            segment.get("id", "")
        )

        # Update segment with traffic data
        updated = segment.copy()
        updated["road_status"] = traffic.road_status
        updated["current_speed_kmh"] = traffic.current_speed_kmh
        updated["congestion_level"] = traffic.congestion_level
        updated["traffic_delay_minutes"] = traffic.delay_minutes
        updated["traffic_data_source"] = traffic.data_source
        updated["traffic_confidence"] = traffic.confidence
        updated["traffic_last_updated"] = traffic.last_updated

        # Update delay factor based on congestion
        base_delay = segment.get("delay_factor", 10)
        congestion_delay = traffic.congestion_level * 0.5  # Up to 50 additional delay at 100% congestion
        updated["delay_factor"] = round(base_delay + congestion_delay, 1)

        return updated


# ================================================================
# Singleton instance
# ================================================================

traffic_service = TrafficService()

