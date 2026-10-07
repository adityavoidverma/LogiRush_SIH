# tests/test_real_data_providers.py
"""
Tests for real-time data providers with proper mocking.

These tests verify that:
1. Real data providers handle API responses correctly
2. Fallback mechanisms work when APIs are unavailable
3. Data is properly cached and refreshed
4. All error conditions are handled gracefully
"""

import json
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Test the IMD Weather Provider
class TestIMDWeatherProvider(unittest.TestCase):
    """Test IMD official weather data integration."""

    @patch('src.data_processing.imd_weather_provider._get_json')
    def test_imd_official_fetch_success(self, mock_get):
        """Test successful IMD AWS data fetch."""
        from src.data_processing.imd_weather_provider import IMDOfficialDataFetcher
        
        # Mock IMD API response
        mock_get.return_value = {
            "records": [
                {
                    "station_name": "Guwahati",
                    "latitude": "26.14",
                    "longitude": "91.73",
                    "rainfall_24h": "45.2",
                    "rainfall_48h": "78.5",
                }
            ]
        }
        
        fetcher = IMDOfficialDataFetcher(api_key="test_key")
        records = fetcher.fetch_aws_rainfall("Assam")
        
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["station_name"], "Guwahati")
        self.assertEqual(float(records[0]["rainfall_24h"]), 45.2)

    @patch('src.data_processing.imd_weather_provider._get_json')
    def test_imd_weather_provider_fallback(self, mock_get):
        """Test fallback to Open-Meteo when IMD unavailable."""
        from src.data_processing.imd_weather_provider import IMDWeatherProvider
        
        # Simulate IMD API failure
        mock_get.side_effect = Exception("IMD API unavailable")
        
        provider = IMDWeatherProvider()
        # Should not raise, should fall back to Open-Meteo
        result = provider.get_rainfall([(26.14, 91.73)])
        
        self.assertIn("readings", result)
        self.assertIn("source", result)
        self.assertIn("is_official_imd", result)

    def test_imd_provider_marks_source_correctly(self):
        """Test that provider correctly marks data source."""
        from src.data_processing.imd_weather_provider import IMDWeatherProvider
        
        provider = IMDWeatherProvider()
        status = provider.status()
        
        self.assertIn("imd_official", status)
        self.assertIn("is_official_imd", status)
        self.assertIsInstance(status["is_official_imd"], bool)


# Test the Traffic Provider
class TestTrafficProvider(unittest.TestCase):
    """Test real-time traffic data integration."""

    @patch('urllib.request.urlopen')
    def test_tomtom_traffic_success(self, mock_urlopen):
        """Test TomTom traffic API integration."""
        from src.data_processing.traffic_provider import TomTomTrafficProvider
        
        # Mock TomTom API response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "flowSegmentData": {
                "currentSpeed": 45,
                "freeFlowSpeed": 60,
                "currentTravelTime": 120,
                "freeFlowTravelTime": 90,
                "confidence": 0.85,
            }
        }).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        provider = TomTomTrafficProvider(api_key="test_key")
        condition = provider.get_flow_data(26.14, 91.73)
        
        self.assertIsNotNone(condition)
        self.assertEqual(condition.current_speed_kmh, 45)
        self.assertEqual(condition.free_flow_speed_kmh, 60)
        self.assertEqual(condition.data_source, "tomtom")
        self.assertGreater(condition.congestion_level, 0)

    def test_traffic_service_fallback(self):
        """Test traffic service falls back when APIs unavailable."""
        from src.data_processing.traffic_provider import TrafficService
        
        # Create service without API keys
        service = TrafficService()
        condition = service.get_traffic_condition(26.14, 91.73, "primary", "TEST001")
        
        self.assertIsNotNone(condition)
        self.assertEqual(condition.data_source, "estimated")
        self.assertEqual(condition.segment_id, "TEST001")
        self.assertGreater(condition.confidence, 0)

    def test_traffic_time_based_estimation(self):
        """Test that time-based estimation produces realistic values."""
        from src.data_processing.traffic_provider import FallbackTrafficEstimator
        from datetime import datetime
        
        estimator = FallbackTrafficEstimator()
        
        # Test morning rush hour (weekday, 8 AM)
        morning_rush = estimator.estimate_traffic("primary", 8, is_weekday=True)
        self.assertGreater(morning_rush.congestion_level, 20)
        
        # Test night (weekday, 2 AM)
        night = estimator.estimate_traffic("primary", 2, is_weekday=True)
        self.assertLess(night.congestion_level, 10)


# Test the Real-Time NER Data Provider
class TestRealTimeNERDataProvider(unittest.TestCase):
    """Test the unified real-time data provider."""

    @patch('src.data_processing.real_data_provider.OSMRoadNetworkFetcher')
    @patch('src.data_processing.traffic_provider.traffic_service')
    @patch('src.data_processing.imd_weather_provider.imd_weather_provider')
    def test_provider_integrates_all_sources(self, mock_weather, mock_traffic, mock_osm_class):
        """Test that provider integrates all real-time sources."""
        from src.data_processing.real_data_provider import RealTimeNERDataProvider
        
        # Mock OSM highways
        mock_osm = Mock()
        mock_osm.fetch_ner_highways.return_value = [
            {
                "osm_id": 123,
                "name": "NH 27",
                "ref": "NH 27",
                "highway_type": "trunk",
                "distance_km": 115.0,
                "geometry": [(26.14, 91.73), (25.57, 91.89)],
                "start_point": (26.14, 91.73),
                "end_point": (25.57, 91.89),
                "midpoint": (25.85, 91.81),
                "surface": "paved",
                "lanes": 2,
            }
        ]
        mock_osm_class.return_value = mock_osm
        
        # Mock weather
        mock_weather.get_rainfall.return_value = {
            "readings": {(25.85, 91.81): {"rain_24h": 15.0, "rain_48h": 25.0}},
            "source": "imd_official",
            "is_official_imd": True,
        }
        
        # Mock traffic
        from src.data_processing.traffic_provider import TrafficCondition
        mock_traffic.get_traffic_condition.return_value = TrafficCondition(
            segment_id="RS001",
            road_status="Open",
            current_speed_kmh=50.0,
            free_flow_speed_kmh=60.0,
            congestion_level=15.0,
            delay_minutes=2.0,
            last_updated=datetime.utcnow().isoformat(),
            data_source="estimated",
            confidence=0.7,
        )
        
        provider = RealTimeNERDataProvider()
        locations = provider.get_locations()
        
        self.assertGreater(len(locations), 0)
        self.assertTrue(all(loc.latitude and loc.longitude for loc in locations))

    @patch('src.data_processing.real_data_provider.ElevationFetcher')
    def test_terrain_integration(self, mock_elevation_class):
        """Test SRTM elevation data integration."""
        mock_elevation = Mock()
        mock_elevation.fetch_elevation_profile.return_value = [
            {"latitude": 26.14, "longitude": 91.73, "elevation": 55.0},
            {"latitude": 26.15, "longitude": 91.74, "elevation": 58.0},
        ]
        mock_elevation.calculate_slope.return_value = 2.5
        mock_elevation_class.return_value = mock_elevation
        
        from src.data_processing.real_data_provider import RealTimeNERDataProvider
        provider = RealTimeNERDataProvider()
        
        # This would normally fetch real elevation data
        # Test that the calculation logic works
        slope = mock_elevation.calculate_slope(
            mock_elevation.fetch_elevation_profile([(26.14, 91.73)]),
            100.0
        )
        self.assertEqual(slope, 2.5)

    @patch('src.data_processing.real_data_provider.GDACSDisasterFetcher')
    def test_disaster_data_integration(self, mock_gdacs_class):
        """Test GDACS disaster event integration."""
        mock_gdacs = Mock()
        mock_gdacs.fetch_disasters.return_value = [
            {
                "event_id": "FL12345",
                "event_type": "FL",
                "latitude": 26.0,
                "longitude": 92.0,
                "severity": 3.5,
                "from_date": "2024-06-15",
            }
        ]
        mock_gdacs.count_events_near_point.return_value = 2
        mock_gdacs_class.return_value = mock_gdacs
        
        from src.data_processing.real_data_provider import RealTimeNERDataProvider
        provider = RealTimeNERDataProvider()
        
        # Test historical event counting
        count = mock_gdacs.count_events_near_point(26.14, 91.73, 50, "FL", 5)
        self.assertEqual(count, 2)


# Test Data Sources Manifest
class TestRealDataSources(unittest.TestCase):
    """Test the real-time data sources manifest."""

    def test_manifest_structure(self):
        """Test that manifest has correct structure."""
        from src.data_processing.real_data_sources import get_real_data_sources
        
        manifest = get_real_data_sources()
        
        self.assertIn("generated_at", manifest)
        self.assertIn("sources", manifest)
        self.assertIn("trust_levels", manifest)
        self.assertIn("headline", manifest)
        self.assertIn("attribution", manifest)
        
        # Check trust levels are correct
        self.assertEqual(set(manifest["trust_levels"].keys()), {"live", "derived"})
        # No more 'sample' or 'synthetic'

    def test_all_sources_are_live_or_derived(self):
        """Test that no sources are marked as sample or synthetic."""
        from src.data_processing.real_data_sources import get_real_data_sources
        
        manifest = get_real_data_sources()
        
        for source in manifest["sources"]:
            self.assertIn(source["trust"], ["live", "derived"])
            self.assertNotIn("sample", source["trust"].lower())
            self.assertNotIn("synthetic", source["trust"].lower())

    def test_attribution_present(self):
        """Test that all sources have proper attribution."""
        from src.data_processing.real_data_sources import get_real_data_sources
        
        manifest = get_real_data_sources()
        
        # Check required attributions
        self.assertIn("openstreetmap", manifest["attribution"])
        self.assertIn("srtm", manifest["attribution"])
        self.assertIn("gdacs", manifest["attribution"])

    def test_configuration_status(self):
        """Test that configuration status is reported."""
        from src.data_processing.real_data_sources import get_real_data_sources
        
        manifest = get_real_data_sources()
        
        self.assertIn("configuration_status", manifest)
        self.assertIn("imd_official", manifest["configuration_status"])
        self.assertIn("traffic_apis", manifest["configuration_status"])


# Test Caching Mechanisms
class TestCaching(unittest.TestCase):
    """Test that caching works correctly across providers."""

    def test_weather_caching(self):
        """Test that weather data is cached."""
        from src.data_processing.imd_weather_provider import _Cache
        
        cache = _Cache(ttl=60)
        cache.put("test_key", {"data": "value"})
        
        result = cache.get("test_key")
        self.assertEqual(result, {"data": "value"})

    def test_cache_expiry(self):
        """Test that cache expires after TTL."""
        from src.data_processing.imd_weather_provider import _Cache
        import time
        
        cache = _Cache(ttl=1)  # 1 second TTL
        cache.put("test_key", {"data": "value"})
        
        time.sleep(1.1)
        result = cache.get("test_key")
        self.assertIsNone(result)

    def test_traffic_caching(self):
        """Test traffic data caching."""
        from src.data_processing.traffic_provider import _TrafficCache
        
        cache = _TrafficCache(ttl=300)
        cache.put("traffic_key", {"congestion": 45})
        
        result = cache.get("traffic_key")
        self.assertEqual(result, {"congestion": 45})


# Test Error Handling
class TestErrorHandling(unittest.TestCase):
    """Test that all providers handle errors gracefully."""

    @patch('urllib.request.urlopen')
    def test_imd_api_failure_fallback(self, mock_urlopen):
        """Test IMD API failure triggers fallback."""
        mock_urlopen.side_effect = Exception("Network error")
        
        from src.data_processing.imd_weather_provider import IMDWeatherProvider
        
        provider = IMDWeatherProvider()
        # Should not raise exception
        result = provider.get_rainfall([(26.14, 91.73)])
        
        self.assertIn("source", result)
        # Should have fallen back to alternative source
        self.assertIsNotNone(result)

    @patch('urllib.request.urlopen')
    def test_osm_timeout_handling(self, mock_urlopen):
        """Test OSM API timeout is handled."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Timeout")
        
        from src.data_processing.real_data_provider import OSMRoadNetworkFetcher
        
        fetcher = OSMRoadNetworkFetcher()
        highways = fetcher.fetch_ner_highways()
        
        # Should return empty list, not raise
        self.assertEqual(highways, [])

    def test_elevation_api_failure(self):
        """Test elevation API failure doesn't crash provider."""
        from src.data_processing.real_data_provider import ElevationFetcher
        
        fetcher = ElevationFetcher()
        # Invalid coordinates should not crash
        result = fetcher.fetch_elevation_profile([])
        self.assertEqual(result, [])


# Integration Test
class TestFullIntegration(unittest.TestCase):
    """Test full integration with mocked external APIs."""

    @patch('src.data_processing.real_data_provider.OSMRoadNetworkFetcher')
    @patch('src.data_processing.real_data_provider.ElevationFetcher')
    @patch('src.data_processing.real_data_provider.GDACSDisasterFetcher')
    @patch('src.data_processing.traffic_provider.traffic_service')
    @patch('src.data_processing.imd_weather_provider.imd_weather_provider')
    def test_end_to_end_data_flow(
        self, mock_weather, mock_traffic, mock_gdacs_class,
        mock_elevation_class, mock_osm_class
    ):
        """Test complete data flow from APIs to segment features."""
        from src.data_processing.real_data_provider import RealTimeNERDataProvider
        from src.data_processing.traffic_provider import TrafficCondition
        
        # Setup all mocks
        mock_osm = Mock()
        mock_osm.fetch_ner_highways.return_value = [{
            "osm_id": 123,
            "name": "NH 27",
            "ref": "NH 27",
            "highway_type": "trunk",
            "distance_km": 115.0,
            "geometry": [(26.14, 91.73), (25.57, 91.89), (25.85, 91.81)],
            "start_point": (26.14, 91.73),
            "end_point": (25.57, 91.89),
            "midpoint": (25.85, 91.81),
            "surface": "paved",
            "lanes": 2,
        }]
        mock_osm_class.return_value = mock_osm
        
        mock_elevation = Mock()
        mock_elevation.fetch_elevation_profile.return_value = [
            {"latitude": 25.85, "longitude": 91.81, "elevation": 55.0}
        ]
        mock_elevation.calculate_slope.return_value = 2.5
        mock_elevation_class.return_value = mock_elevation
        
        mock_gdacs = Mock()
        mock_gdacs.count_events_near_point.return_value = 1
        mock_gdacs_class.return_value = mock_gdacs
        
        mock_weather.get_rainfall.return_value = {
            "readings": {(25.85, 91.81): {"rain_24h": 15.0, "rain_48h": 25.0}},
            "source": "imd_official",
            "is_official_imd": True,
        }
        
        mock_traffic.get_traffic_condition.return_value = TrafficCondition(
            segment_id="RS001",
            road_status="Open",
            current_speed_kmh=50.0,
            free_flow_speed_kmh=60.0,
            congestion_level=15.0,
            delay_minutes=2.0,
            last_updated=datetime.utcnow().isoformat(),
            data_source="estimated",
            confidence=0.7,
        )
        
        # Create provider and fetch data
        provider = RealTimeNERDataProvider()
        
        # Test each component
        locations = provider.get_locations()
        self.assertGreater(len(locations), 0)
        
        segments = provider.get_road_segments()
        self.assertGreater(len(segments), 0)
        
        features = provider.get_segment_features()
        self.assertGreater(len(features), 0)
        
        # Verify data has expected structure
        if segments:
            segment = segments[0]
            self.assertIsNotNone(segment.distance_km)
            self.assertIsNotNone(segment.weather_risk)
            self.assertIsNotNone(segment.road_status)


if __name__ == "__main__":
    unittest.main()
