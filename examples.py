from closest_country import analyze_point_location
from map_fetcher import fetch_world_map
from visualization import visualize_point_and_closest_countries


def example_closest_country_analysis():
    """
    Example function demonstrating closest country analysis for various points.
    """
    print("Loading world map for closest country analysis...")
    world_map = fetch_world_map(resolution="low")

    if world_map is None:
        print("Failed to load world map")
        return

    # Test points around the world
    test_points = [
        (-74.0, 40.7, "New York City"),
        (2.3, 48.9, "Paris"),
        (139.7, 35.7, "Tokyo"),
        (0.0, 0.0, "Equator & Prime Meridian (Gulf of Guinea)"),
        (-58.4, -34.6, "Buenos Aires"),
        (151.2, -33.9, "Sydney"),
        (-0.1, 51.5, "London"),
        (55.3, 25.3, "Dubai"),
        (-122.4, 37.8, "San Francisco"),
        (12.5, 41.9, "Rome"),
    ]

    print(f"\nAnalyzing {len(test_points)} test points around the world...")
    print("=" * 60)

    for lon, lat, description in test_points:
        print(f"\n📍 {description}")
        print(f"   Coordinates: ({lon:.1f}, {lat:.1f})")

        # Get comprehensive analysis
        analysis = analyze_point_location(world_map, (lon, lat))

        if analysis["is_inside_country"]:
            print(f"   ✓ Located in: {analysis['containing_country']}")
        else:
            print(f"   → Located in: {analysis['ocean_or_land']}")
            if analysis["closest_country"] and analysis["distance_to_closest"]:
                km_dist = analysis["distance_to_closest"] * 111.32
                print(
                    f"   → Closest country: {analysis['closest_country']} ({km_dist:.0f} km)"
                )

        # Show nearest neighbors
        if analysis["top_5_closest"] and len(analysis["top_5_closest"]) > 1:
            print("   → Nearby countries:")
            for i, (country, dist) in enumerate(analysis["top_5_closest"][:3]):
                km_dist = dist * 111.32
                if i == 0 and dist == 0:
                    continue  # Skip the containing country
                print(f"     {i+1}. {country} ({km_dist:.0f} km)")

        print("-" * 60)


def run_comprehensive_demo():
    """
    Run a comprehensive demonstration of all functionality.
    """
    print("🌍 Fun with Maps - Comprehensive Demo")
    print("=" * 50)

    # 1. Fetch world map
    print("\n1. Fetching World Map Data...")
    world_map = fetch_world_map(resolution="low")

    if world_map is None:
        print("❌ Failed to fetch world map data")
        return

    print(f"✅ Successfully loaded world map with {len(world_map)} countries")

    # 2. Basic map information
    print("\n2. Map Information:")
    print(f"   Shape: {world_map.shape}")
    print(f"   CRS: {world_map.crs}")
    print(f"   Columns: {list(world_map.columns)}")

    # Show first few countries
    name_col = None
    name_columns = ["NAME", "name", "NAME_EN", "ADMIN"]
    for col in name_columns:
        if col in world_map.columns:
            name_col = col
            break

    if name_col:
        print(f"   First 5 countries: {world_map[name_col].head().tolist()}")

    # 3. Test closest country analysis
    print("\n3. Testing Closest Country Analysis...")

    test_points = [
        (-74.0, 40.7, "New York City area"),  # Should be USA
        (2.3, 48.9, "Paris area"),  # Should be France
        (0.0, 0.0, "Gulf of Guinea"),  # Ocean point
        (139.7, 35.7, "Tokyo area"),  # Should be Japan
        (-58.4, -34.6, "Buenos Aires area"),  # Should be Argentina
    ]

    for lon, lat, description in test_points:
        print(f"\n   📍 Analyzing: {description}")
        print(f"      Coordinates: ({lon}, {lat})")

        # Get comprehensive analysis
        analysis = analyze_point_location(world_map, (lon, lat))

        # Also call find_closest_country_to_point for testing purposes
        # simple_closest = find_closest_country_to_point(world_map, (lon, lat))

        if analysis["is_inside_country"]:
            print(f"      ✓ Point is INSIDE {analysis['containing_country']}")
        else:
            print(f"      → Point is in {analysis['ocean_or_land']}")
            print(f"      → Closest country: {analysis['closest_country']}")
            if analysis["distance_to_closest"]:
                km_dist = analysis["distance_to_closest"] * 111.32
                print(f"      → Distance: {km_dist:.1f} km")

        # Show top 3 closest countries
        if analysis["top_5_closest"]:
            print("      → Top 3 closest countries:")
            for i, (country, dist) in enumerate(analysis["top_5_closest"][:3]):
                km_dist = dist * 111.32
                print(f"        {i+1}. {country}: {km_dist:.1f} km")

    # 4. Visualize one example
    print("\n4. Creating Visualization...")
    example_point = (-74.0, 40.7)  # New York area
    print(f"   Visualizing closest countries to point {example_point}")
    visualize_point_and_closest_countries(world_map, example_point, n_countries=3)

    print("\n✅ Demo completed successfully!")
    print("📁 World map data can be saved for future use.")


if __name__ == "__main__":
    run_comprehensive_demo()
