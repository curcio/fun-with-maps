#!/usr/bin/env python3
"""
Fun with Maps - A comprehensive geospatial analysis toolkit

This modular toolkit provides functionality for:
- Fetching world map data
- Analyzing countries and polygons
- Finding closest countries to points
- Generating random points in polygons
- Creating visualizations

Modules:
- map_fetcher: Download and load world map data
- country_analysis: Country polygon extraction and analysis
- closest_country: Find closest countries to points
- point_generation: Generate random points in polygons
- visualization: Create maps and visualizations
- examples: Demonstration and example functions
"""

from closest_country import analyze_point_location
from examples import example_closest_country_analysis, run_comprehensive_demo
from map_fetcher import fetch_world_map
from visualization import visualize_point_and_closest_countries, visualize_world_map


def main():
    """
    Main function to fetch and display world political map.
    """
    print("World Political Map Fetcher")
    print("=" * 40)

    # Fetch low resolution world map
    world_map = fetch_world_map(resolution="low")

    if world_map is not None:
        # Display basic information
        print("\nMap Information:")
        print(f"Shape: {world_map.shape}")
        print(f"CRS: {world_map.crs}")
        print(f"Columns: {list(world_map.columns)}")

        # Show first few countries
        print("\nFirst 5 countries:")
        if "NAME" in world_map.columns:
            print(world_map["NAME"].head().tolist())
        elif "name" in world_map.columns:
            print(world_map["name"].head().tolist())
        else:
            print("Country names column not found")

        # Visualize the world map
        visualize_world_map(world_map, "Low Resolution World Political Map")

        # Example: Find closest country to a point
        print("\n" + "=" * 40)
        print("Closest Country Analysis Example")
        print("=" * 40)

        # Test with different points
        test_points = [
            (-74.0, 40.7, "New York City area"),  # Should be USA
            (2.3, 48.9, "Paris area"),  # Should be France
            (0.0, 0.0, "Gulf of Guinea"),  # Ocean point
            (139.7, 35.7, "Tokyo area"),  # Should be Japan
            (-58.4, -34.6, "Buenos Aires area"),  # Should be Argentina
        ]

        for lon, lat, description in test_points:
            print(f"\n--- Analyzing point: {description} ---")
            print(f"Coordinates: ({lon}, {lat})")

            # Get comprehensive analysis
            analysis = analyze_point_location(world_map, (lon, lat))

            if analysis["is_inside_country"]:
                print(f"✓ Point is INSIDE {analysis['containing_country']}")
            else:
                print(f"→ Point is in {analysis['ocean_or_land']}")
                print(f"→ Closest country: {analysis['closest_country']}")
                if analysis["distance_to_closest"]:
                    km_dist = analysis["distance_to_closest"] * 111.32
                    print(f"→ Distance: {km_dist:.1f} km")

            # Show top 3 closest countries
            if analysis["top_5_closest"]:
                print("Top 3 closest countries:")
                for i, (country, dist) in enumerate(analysis["top_5_closest"][:3]):
                    km_dist = dist * 111.32
                    print(f"  {i+1}. {country}: {km_dist:.1f} km")

            print("-" * 50)

        # Visualize one example
        example_point = (-74.0, 40.7)  # New York area
        print(f"\nVisualizing closest countries to point {example_point}")
        visualize_point_and_closest_countries(world_map, example_point, n_countries=3)

        # Optional: Save world map to file
        output_file = "world_political_map.geojson"
        world_map.to_file(output_file, driver="GeoJSON")
        print(f"\nWorld map data saved to: {output_file}")

    else:
        print("Failed to fetch world map data")


if __name__ == "__main__":
    print("🌍 Fun with Maps - Modular Geospatial Toolkit")
    print("=" * 50)
    print("\nAvailable options:")
    print("1. Run main demo (default)")
    print("2. Run comprehensive demo")
    print("3. Run closest country analysis example")

    try:
        choice = input(
            "\nEnter your choice (1-3, or press Enter for default): "
        ).strip()

        if choice == "2":
            run_comprehensive_demo()
        elif choice == "3":
            example_closest_country_analysis()
        else:
            main()

    except KeyboardInterrupt:
        print("\n\nGoodbye! 👋")
    except Exception as e:
        print(f"\nError: {e}")
        print("Running default main function...")
        main()
