from fun_with_maps import fetch_world_map
from fun_with_maps.core.closest_country import (
    analyze_point_location,
    find_closest_country_to_point,
)
from fun_with_maps.visualization.visualization import (
    visualize_point_and_closest_countries,
)


def run_comprehensive_demo():
    """Run a demo showcasing closest country lookup."""
    world = fetch_world_map(resolution="low")
    if world is None:
        return
    points = [(-10, 0), (0, 0), (10, 0)]
    for point in points:
        country = find_closest_country_to_point(world, point)
        analyze_point_location(world, point)
        print(f"Closest to {point}: {country}")

    # Visualize results for the last point
    visualize_point_and_closest_countries(world, points[-1])

def example_closest_country_analysis() -> None:
    """Demonstrate closest country analysis for a few sample points."""
    print("Loading world map for closest country analysis...")
    world_map = fetch_world_map(resolution="low")
    if world_map is None:
        print("Failed to load world map")
        return

    test_points = [
        (-74.0, 40.7, "New York City"),
        (2.3, 48.9, "Paris"),
        (139.7, 35.7, "Tokyo"),
    ]

    for lon, lat, desc in test_points:
        print(f"\nAnalyzing {desc} ({lon}, {lat})")
        analysis = analyze_point_location(world_map, (lon, lat))
        if analysis.get("is_inside_country"):
            print(f"  ✓ Located in: {analysis.get('containing_country')}")
        else:
            print(f"  → Closest country: {analysis.get('closest_country')}")


def run_comprehensive_demo() -> None:
    """Run a small demonstration covering multiple features."""
    print("🌍 Fun with Maps Demo")
    world_map = fetch_world_map(resolution="low")
    if world_map is None:
        print("Failed to load world map")
        return

    point = (-74.0, 40.7)
    find_closest_country_to_point(world_map, point)
    _analysis = analyze_point_location(world_map, point)  # noqa: F841

    visualize_point_and_closest_countries(world_map, point, n_countries=3)

    print("Demo completed")


if __name__ == "__main__":
    run_comprehensive_demo()
