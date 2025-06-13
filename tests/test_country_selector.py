#!/usr/bin/env python3
"""
Test script for country selector functionality.
"""

from country_analysis import get_available_countries
from country_selector import show_country_selector
from map_fetcher import fetch_world_map


def test_country_selector():
    """Test the country selector functionality."""
    print("🧪 Testing Country Selector")
    print("=" * 40)

    # Load world map
    print("1. Loading world map...")
    world_map = fetch_world_map(resolution="low")

    if world_map is None:
        print("❌ Failed to load world map")
        return False

    print(f"✅ Loaded world map with {len(world_map)} countries/territories")

    # Get available countries
    print("2. Getting available countries...")
    countries = get_available_countries(world_map)

    if not countries:
        print("❌ No countries found")
        return False

    print(f"✅ Found {len(countries)} countries")
    print(f"   First few: {countries[:5]}")

    # Test country selector
    print("3. Testing country selector...")
    selected_country = show_country_selector(
        countries[:20], title="Test Country Selector"  # Show only first 20 for testing
    )

    if selected_country:
        print(f"✅ Selected country: {selected_country}")
        return True
    else:
        print("ℹ️  No country selected (cancelled)")
        return True


if __name__ == "__main__":
    test_country_selector()
