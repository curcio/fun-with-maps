"""Example workflows for fun-with-maps."""

from fun_with_maps import fetch_world_map
from fun_with_maps.core.closest_country import (
    analyze_point_location,
    find_closest_country_to_point,
)
from fun_with_maps.visualization.visualization import (
    visualize_point_and_closest_countries,
)


def example_closest_country_analysis():
    """Simple example that fetches a map and analyzes a test point."""
    world = fetch_world_map(resolution="low")
    if world is None:
        return
    point = (0, 0)
    result = analyze_point_location(world, point)
    print(result)


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
