# tests/conftest_realdata.py
"""
Pytest configuration for real-time data provider tests.

This configuration:
1. Mocks external API calls by default
2. Provides fixtures for common test data
3. Sets environment variables for testing
4. Can enable real API calls for integration testing
"""

import os
import pytest
from unittest.mock import Mock, patch


# Set test environment variables
os.environ["NER_LIVE_WEATHER"] = "0"  # Disable live weather by default in tests
os.environ["IMD_API_KEY"] = "test_key_for_testing"
os.environ["TOMTOM_API_KEY"] = ""  # No keys in tests
os.environ["HERE_API_KEY"] = ""


@pytest.fixture
def mock_osm_highways():
    """Fixture providing mock OSM highway data."""
    return [
        {
            "osm_id": 123456,
            "name": "National Highway 27",
            "ref": "NH 27",
            "highway_type": "trunk",
            "surface": "paved",
            "lanes": 2,
            "maxspeed": "60",
            "distance_km": 115.0,
            "geometry": [
                (26.1445, 91.7362),  # Guwahati
                (26.0, 91.5),
                (25.8, 91.3),
                (25.5788, 91.8933),  # Shillong
            ],
            "start_point": (26.1445, 91.7362),
            "end_point": (25.5788, 91.8933),
            "midpoint": (25.85, 91.81),
        },
        {
            "osm_id": 123457,
            "name": "National Highway 10",
            "ref": "NH 10",
            "highway_type": "primary",
            "surface": "asphalt",
            "lanes": 2,
            "maxspeed": "50",
            "distance_km": 78.0,
            "geometry": [
                (26.7271, 88.3953),  # Siliguri
                (27.0, 88.5),
                (27.3314, 88.6138),  # Gangtok
            ],
            "start_point": (26.7271, 88.3953),
            "end_point": (27.3314, 88.6138),
            "midpoint": (27.0, 88.5),
        },
    ]


@pytest.fixture
def mock_imd_rainfall_data():
    """Fixture providing mock IMD rainfall data."""
    return {
        "readings": {
            (26.14, 91.74): {"rain_24h": 45.2, "rain_48h": 78.5},
            (25.58, 91.89): {"rain_24h": 32.1, "rain_48h": 55.0},
            (26.73, 88.40): {"rain_24h": 12.5, "rain_48h": 20.0},
            (27.33, 88.61): {"rain_24h": 8.0, "rain_48h": 15.0},
        },
        "source": "imd_official",
        "source_name": "India Meteorological Department - Official AWS Network",
        "is_official_imd": True,
        "fetched_at": "2024-01-15T10:30:00Z",
        "error": None,
    }


@pytest.fixture
def mock_elevation_data():
    """Fixture providing mock SRTM elevation data."""
    return [
        {"latitude": 26.14, "longitude": 91.74, "elevation": 55.0},
        {"latitude": 26.0, "longitude": 91.5, "elevation": 58.0},
        {"latitude": 25.8, "longitude": 91.3, "elevation": 890.0},  # Shillong plateau
        {"latitude": 25.58, "longitude": 91.89, "elevation": 920.0},
    ]


@pytest.fixture
def mock_gdacs_disasters():
    """Fixture providing mock GDACS disaster data."""
    return [
        {
            "event_id": "FL-2023-000045-IND",
            "event_type": "FL",
            "event_name": "Assam Floods 2023",
            "severity": 3.5,
            "latitude": 26.2,
            "longitude": 91.8,
            "from_date": "2023-06-15",
            "to_date": "2023-07-10",
            "description": "Severe flooding in Assam state",
        },
        {
            "event_id": "LS-2023-000012-IND",
            "event_type": "LS",
            "event_name": "Meghalaya Landslides 2023",
            "severity": 2.8,
            "latitude": 25.6,
            "longitude": 91.9,
            "from_date": "2023-07-20",
            "to_date": "2023-07-25",
            "description": "Multiple landslides in Meghalaya",
        },
    ]


@pytest.fixture
def mock_traffic_condition():
    """Fixture providing mock traffic condition data."""
    from src.data_processing.traffic_provider import TrafficCondition
    from datetime import datetime
    
    return TrafficCondition(
        segment_id="RS001",
        road_status="Open",
        current_speed_kmh=50.0,
        free_flow_speed_kmh=60.0,
        congestion_level=16.7,
        delay_minutes=2.3,
        last_updated=datetime.utcnow().isoformat(),
        data_source="estimated",
        confidence=0.7,
    )


@pytest.fixture(autouse=True)
def mock_external_apis():
    """Auto-use fixture that mocks all external API calls."""
    with patch('urllib.request.urlopen') as mock_urlopen:
        # Default: return empty successful responses
        mock_response = Mock()
        mock_response.read.return_value = b'{"records": []}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        yield mock_urlopen


@pytest.fixture
def enable_real_apis():
    """
    Fixture to enable real API calls for integration testing.
    Use with caution - requires actual API keys and network access.
    
    Usage:
        @pytest.mark.integration
        def test_with_real_apis(enable_real_apis):
            # This test will make real API calls
            pass
    """
    # Store original env vars
    original_env = {
        "NER_LIVE_WEATHER": os.environ.get("NER_LIVE_WEATHER", "0"),
    }
    
    # Enable live data
    os.environ["NER_LIVE_WEATHER"] = "1"
    
    yield
    
    # Restore original env
    for key, value in original_env.items():
        os.environ[key] = value


# Mark for integration tests (skipped by default)
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires real APIs)"
    )


def pytest_collection_modifyitems(config, items):
    """Skip integration tests by default unless --integration flag is passed."""
    if not config.getoption("--integration", default=False):
        skip_integration = pytest.mark.skip(reason="need --integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)


def pytest_addoption(parser):
    """Add command-line option to run integration tests."""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="run integration tests with real API calls"
    )


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (deselected by default)"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselected by default)"
    )
