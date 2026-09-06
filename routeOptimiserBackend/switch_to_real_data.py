#!/usr/bin/env python3
"""
Switch LogiRush to use real-time, non-fabricated data sources.

This script updates the application to use:
- RealTimeNERDataProvider instead of MockNERDataProvider
- real_data_sources.get_real_data_sources() instead of data_sources.get_data_sources()

Run this script to enable all real-time data integrations.
"""

import os
import sys

def update_accessibility_service():
    """Update accessibility_service.py to use RealTimeNERDataProvider."""
    file_path = "src/services/accessibility_service.py"
    
    if not os.path.exists(file_path):
        print(f"⚠ Warning: {file_path} not found")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace MockNERDataProvider with RealTimeNERDataProvider
    if "MockNERDataProvider" in content or "LiveWeatherNERDataProvider" in content:
        # Update imports
        content = content.replace(
            "from src.data_processing.ner_data_provider import MockNERDataProvider",
            "from src.data_processing.real_data_provider import RealTimeNERDataProvider"
        )
        content = content.replace(
            "from src.data_processing.ner_data_provider import LiveWeatherNERDataProvider",
            "from src.data_processing.real_data_provider import RealTimeNERDataProvider"
        )
        
        # Update instantiations
        content = content.replace(
            "MockNERDataProvider()",
            "RealTimeNERDataProvider()"
        )
        content = content.replace(
            "LiveWeatherNERDataProvider()",
            "RealTimeNERDataProvider()"
        )
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"✓ Updated {file_path} to use RealTimeNERDataProvider")
        return True
    else:
        print(f"ℹ {file_path} already configured or using different provider")
        return False


def update_ner_routes():
    """Update ner_routes.py to use real_data_sources."""
    file_path = "src/api/ner_routes.py"
    
    if not os.path.exists(file_path):
        print(f"⚠ Warning: {file_path} not found")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace data_sources import and usage
    if "from src.data_processing.data_sources import get_data_sources" in content:
        content = content.replace(
            "from src.data_processing.data_sources import get_data_sources",
            "from src.data_processing.real_data_sources import get_real_data_sources"
        )
        content = content.replace(
            "get_data_sources()",
            "get_real_data_sources()"
        )
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"✓ Updated {file_path} to use get_real_data_sources()")
        return True
    else:
        print(f"ℹ {file_path} already using real_data_sources or needs manual update")
        return False


def create_env_template():
    """Create .env.realtime template with all API key configurations."""
    template = """# Real-Time Data Configuration for LogiRush
# ================================================

# ================================================================
# IMD (India Meteorological Department) Official Weather Data
# ================================================================
# Required for official IMD rainfall data from AWS stations
# Without this, system falls back to Open-Meteo (still live, but not official IMD)
# Get API key from: https://data.gov.in/ or https://mausam.imd.gov.in/
IMD_API_KEY=your_imd_api_key_here

# IMD API endpoints (default values shown)
# IMD_API_BASE=https://api.data.gov.in/resource
# IMD_AWS_ENDPOINT=https://mausam.imd.gov.in/backend/api/aws_data

# IMD cache and timeout settings
# IMD_CACHE_TTL=1800  # 30 minutes
# IMD_TIMEOUT=15.0    # seconds


# ================================================================
# Traffic Data APIs (Optional but Recommended)
# ================================================================
# TomTom Traffic Flow API
# Get API key from: https://developer.tomtom.com/
TOMTOM_API_KEY=your_tomtom_api_key_here

# HERE Traffic API
# Get API key from: https://developer.here.com/
HERE_API_KEY=your_here_api_key_here

# Traffic cache and timeout
# TRAFFIC_CACHE_TTL=300  # 5 minutes
# TRAFFIC_TIMEOUT=10.0   # seconds


# ================================================================
# OpenStreetMap / Overpass API
# ================================================================
# No API key needed, but can be configured for custom endpoints
# OVERPASS_URL=https://overpass-api.de/api/interpreter
# OSM_USER_AGENT=NER-Logistics-Platform/2.0


# ================================================================
# Elevation Data
# ================================================================
# Open-Elevation API for SRTM data (no API key needed)
# ELEVATION_API_URL=https://api.open-elevation.com/api/v1/lookup


# ================================================================
# Disaster Data
# ================================================================
# GDACS API (no API key needed)
# GDACS_API_URL=https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH


# ================================================================
# Cache and Performance Settings
# ================================================================
# General data cache TTL
# REAL_DATA_CACHE_TTL=3600  # 1 hour
# REAL_DATA_TIMEOUT=30.0    # seconds

# Weather cache (separate from IMD cache)
# WEATHER_CACHE_TTL_S=900   # 15 minutes
# WEATHER_TIMEOUT_S=4.0     # seconds

# Places/geocoding cache
# PLACES_CACHE_TTL_S=900    # 15 minutes
# PLACES_TIMEOUT_S=4.0      # seconds


# ================================================================
# Database Configuration
# ================================================================
# DATABASE_URL=postgresql://user:password@host:port/database
# DATABASE_URL=sqlite:///./logirust.db  # Default


# ================================================================
# CORS Settings
# ================================================================
# CORS_ORIGINS=https://your-frontend-domain.com
# CORS_ORIGINS=*  # For development only


# ================================================================
# Feature Flags
# ================================================================
# Disable live weather (uses fallback CSV data)
# NER_LIVE_WEATHER=0

# Disable demo data seeding
# NER_DISABLE_DEMO_SEED=1

# Flask debug mode (development only)
# FLASK_DEBUG=1


# ================================================================
# Priority Configuration Guide
# ================================================================
# CRITICAL:
#   - IMD_API_KEY: Required for official weather data
#
# HIGHLY RECOMMENDED:
#   - TOMTOM_API_KEY or HERE_API_KEY: For real-time traffic
#   - DATABASE_URL: PostgreSQL for production
#
# OPTIONAL:
#   - Custom API endpoints if using private instances
#
# NO API KEY NEEDED:
#   - OpenStreetMap (Overpass API)
#   - SRTM elevation (open-elevation.com)
#   - GDACS disaster data
#   - Open-Meteo weather (fallback)

"""
    
    output_file = ".env.realtime"
    with open(output_file, 'w') as f:
        f.write(template)
    
    print(f"✓ Created {output_file} template")
    print(f"  → Copy to .env and fill in your API keys")
    return True


def main():
    print("=" * 60)
    print("LogiRush Real-Time Data Integration Switcher")
    print("=" * 60)
    print()
    
    # Change to backend directory if not already there
    if os.path.exists("routeOptimiserBackend"):
        os.chdir("routeOptimiserBackend")
        print("📁 Changed to routeOptimiserBackend directory")
    
    if not os.path.exists("src"):
        print("❌ Error: Cannot find src/ directory")
        print("   Please run this script from the LogiRush root or routeOptimiserBackend directory")
        sys.exit(1)
    
    print()
    print("Updating application to use real-time data providers...")
    print()
    
    updates = []
    
    # Update files
    if update_accessibility_service():
        updates.append("accessibility_service.py")
    
    if update_ner_routes():
        updates.append("ner_routes.py")
    
    if create_env_template():
        updates.append(".env.realtime")
    
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    
    if updates:
        print(f"✓ Successfully updated {len(updates)} file(s):")
        for f in updates:
            print(f"  - {f}")
    else:
        print("ℹ No files needed updating (already configured)")
    
    print()
    print("Next Steps:")
    print("-" * 60)
    print("1. Review and copy .env.realtime to .env")
    print("2. Add your API keys (at minimum IMD_API_KEY)")
    print("3. Restart the backend: python main.py")
    print("4. Check /api/ner/data-sources to verify real-time data")
    print()
    print("API Keys You'll Need:")
    print("  • CRITICAL: IMD_API_KEY from https://data.gov.in/")
    print("  • Recommended: TOMTOM_API_KEY or HERE_API_KEY")
    print("  • Optional: All others (OSM, SRTM, GDACS work without keys)")
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
