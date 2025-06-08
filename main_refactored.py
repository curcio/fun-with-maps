#!/usr/bin/env python3
"""
Refactored main script for map analysis with Voronoi diagrams.

This script demonstrates the analysis of random points within a country,
finding their closest neighboring countries, and creating Voronoi diagrams
based on capital cities.
"""

import matplotlib

from country_analysis import get_country_polygon
from data_processing import (
    add_closest_countries_to_points,
    calculate_point_count,
    filter_points_by_country_frequency,
    get_unique_countries_from_list,
    print_country_statistics,
)
from map_fetcher import fetch_world_map
from parallel_processing import choose_processing_method
from point_generation import generate_random_points_in_polygon
from visualization import visualize_country_polygon, visualize_polygon_with_points
from voronoi_analysis import get_admin1_capitals
from voronoi_visualization import display_voronoi_diagram

matplotlib.rcParams["figure.max_open_warning"] = 50


def setup_country_analysis(country_name: str):
    """
    Setup country analysis by fetching map data and getting country polygon.

    Args:
        country_name: Name of the country to analyze

    Returns:
        tuple: (world_map, country_polygon)
    """
    print("Fetching world map...")
    world_map = fetch_world_map(resolution="low")

    print(f"Getting {country_name} polygon...")
    country_polygon = get_country_polygon(world_map, country_name)

    print(f"Visualizing {country_name}...")
    visualize_country_polygon(country_polygon, country_name)

    return world_map, country_polygon


def generate_and_visualize_points(country_polygon, country_name: str, factor: int = 10):
    """
    Generate random points within country and visualize them.

    Args:
        country_polygon: Country polygon geometry
        country_name: Name of the country
        factor: Factor for calculating number of points

    Returns:
        GeoDataFrame of generated points
    """
    k = calculate_point_count(country_polygon, factor)

    print(f"Generating {k} random points inside {country_name}...")
    points = generate_random_points_in_polygon(country_polygon, k)

    print(f"Visualizing {country_name} with random points...")
    if points is not None:
        visualize_polygon_with_points(
            country_polygon, points, f"{country_name} with Random Points"
        )
    else:
        print("Failed to generate points")

    return points


def analyze_closest_countries(world_map, points):
    """
    Analyze closest countries for each point using appropriate processing method.

    Args:
        world_map: World map GeoDataFrame
        points: GeoDataFrame of points to analyze

    Returns:
        List of closest countries for each point
    """
    if points is None:
        return []

    print("Finding closest country to each point...")
    closest_countries = choose_processing_method(world_map, points)
    return closest_countries


def create_colored_visualization(
    world_map,
    country_polygon,
    points,
    closest_countries,
    country_name: str,
    min_frequency: int = 10,
):
    """
    Create visualization with color-coded points by closest country.

    Args:
        world_map: World map GeoDataFrame
        country_polygon: Country polygon geometry
        points: GeoDataFrame of points
        closest_countries: List of closest countries
        country_name: Name of the country
        min_frequency: Minimum points per country to include
    """
    # Add closest countries to points and filter
    points = add_closest_countries_to_points(points, closest_countries)
    points, closest_countries, _ = filter_points_by_country_frequency(
        points, closest_countries, min_frequency
    )

    if not closest_countries:
        print("No countries meet the minimum frequency requirement")
        return

    print("Creating visualization with color-coded points...")
    unique_countries = get_unique_countries_from_list(closest_countries)

    # Create colored visualization (using existing visualization module)
    from visualization import create_country_visualization_with_colors

    create_country_visualization_with_colors(
        world_map, country_polygon, points, unique_countries, country_name
    )

    # Print statistics
    print_country_statistics(
        closest_countries, "Closest Country Statistics (after filtering)"
    )


def create_voronoi_analysis(country_polygon, country_name: str):
    """
    Create and display Voronoi diagram based on capital cities.

    Args:
        country_polygon: Country polygon geometry
        country_name: Name of the country
    """
    print(f"\nCreating Voronoi diagram for {country_name} using capital cities...")

    try:
        capitals = get_admin1_capitals(country_name)
        if not capitals.empty:
            print(f"Found {len(capitals)} capital cities for {country_name}:")
            for idx, row in capitals.iterrows():
                print(f"  - {row.get('NAME', 'Unknown')}")

            # Create and display Voronoi diagram
            display_voronoi_diagram(country_polygon, capitals, country_name)
        else:
            print(f"No capital cities found for {country_name}")

    except Exception as e:
        print(f"Error creating Voronoi diagram: {e}")
        import traceback

        traceback.print_exc()


def main():
    """Main function orchestrating the entire analysis."""
    # Configuration
    country_name = "Argentina"
    point_generation_factor = 10
    min_country_frequency = 10

    try:
        # Step 1: Setup country analysis
        world_map, country_polygon = setup_country_analysis(country_name)

        # Step 2: Generate and visualize random points
        points = generate_and_visualize_points(
            country_polygon, country_name, point_generation_factor
        )

        # Step 3: Analyze closest countries
        closest_countries = analyze_closest_countries(world_map, points)

        # Step 4: Create colored visualization
        if closest_countries:
            create_colored_visualization(
                world_map,
                country_polygon,
                points,
                closest_countries,
                country_name,
                min_country_frequency,
            )

        # Step 5: Create Voronoi analysis
        create_voronoi_analysis(country_polygon, country_name)

    except Exception as e:
        print(f"Error in main analysis: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
