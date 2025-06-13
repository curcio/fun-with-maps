#!/usr/bin/env python3
"""
Refactored main script for map analysis with Voronoi diagrams.

This script demonstrates the analysis of random points within a country,
finding their closest neighboring countries, and creating Voronoi diagrams
based on capital cities.
"""

import argparse
import sys
from typing import List, Tuple

import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt

from country_analysis import get_available_countries, get_country_polygon
from country_selector import show_country_selector
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
from tsp_solver import solve_tsp
from utils import clear_plot_tracker, generate_pdf_report, set_country_info, show_plot
from visualization import visualize_country_polygon, visualize_polygon_with_points
from voronoi_analysis import get_admin1_capitals
from voronoi_visualization import display_voronoi_diagram

matplotlib.rcParams["figure.max_open_warning"] = 50


def extract_capital_coordinates(
    capitals_gdf: gpd.GeoDataFrame,
) -> List[Tuple[float, float]]:
    """
    Extract coordinates from capitals GeoDataFrame.

    Args:
        capitals_gdf: GeoDataFrame containing capital cities

    Returns:
        List of (longitude, latitude) tuples
    """
    coordinates = []
    for idx, row in capitals_gdf.iterrows():
        lon = row.geometry.x
        lat = row.geometry.y
        coordinates.append((lon, lat))

    return coordinates


def visualize_tsp_tour(
    country_polygon,
    capitals_gdf: gpd.GeoDataFrame,
    tour: List[int],
    tour_cost: float,
    country_name: str,
):
    """
    Visualize the TSP tour on a map with the country and capitals.

    Args:
        country_polygon: Country polygon geometry
        capitals_gdf: GeoDataFrame with capital cities
        tour: Optimal tour as list of city indices
        tour_cost: Total cost of the tour
        country_name: Name of the country
    """
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))

    # Plot country polygon
    if hasattr(country_polygon, "plot"):
        country_polygon.plot(ax=ax, color="lightblue", alpha=0.7, edgecolor="navy")
    else:
        # If it's a shapely geometry, create a GeoDataFrame
        gdf_temp = gpd.GeoDataFrame([1], geometry=[country_polygon])
        gdf_temp.plot(ax=ax, color="lightblue", alpha=0.7, edgecolor="navy")

    # Get coordinates for plotting
    coordinates = extract_capital_coordinates(capitals_gdf)

    # Plot capital cities
    capitals_gdf.plot(
        ax=ax,
        color="darkred",
        markersize=120,
        alpha=0.9,
        label="Capital Cities",
        zorder=3,
    )

    # Add city labels
    for idx, row in capitals_gdf.iterrows():
        city_name = row.get("NAME", f"City {idx}")
        ax.annotate(
            city_name,
            (row.geometry.x, row.geometry.y),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
            ha="left",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7),
        )

    # Draw tour lines between consecutive cities in the tour
    print(f"Drawing OR-Tools tour with {len(tour)} cities...")
    for i in range(len(tour)):
        current_city_idx = tour[i]
        next_city_idx = tour[(i + 1) % len(tour)]  # Loop back to start for last city

        if current_city_idx >= len(coordinates) or next_city_idx >= len(coordinates):
            print(
                f"ERROR: Invalid city index! current={current_city_idx}, next={next_city_idx}, max={len(coordinates)-1}"
            )
            continue

        start_coord = coordinates[current_city_idx]
        end_coord = coordinates[next_city_idx]

        print(f"  Edge {i+1}: City {current_city_idx} -> City {next_city_idx}")

        # Draw the line
        ax.plot(
            [start_coord[0], end_coord[0]],
            [start_coord[1], end_coord[1]],
            color="red",
            linewidth=4,
            alpha=0.9,
            label="TSP Tour (OR-Tools)" if i == 0 else "",
            zorder=4,  # Draw lines above everything except annotations
            solid_capstyle="round",
        )

    # Add tour order numbers - use the actual city coordinates from the GeoDataFrame
    print(f"Adding tour order annotations...")
    for i, city_idx in enumerate(tour):
        if city_idx >= len(capitals_gdf):
            print(f"ERROR: Invalid city index {city_idx} for annotation")
            continue

        # Get the actual row from the GeoDataFrame
        city_row = capitals_gdf.iloc[city_idx]
        city_coord = (city_row.geometry.x, city_row.geometry.y)
        city_name = city_row.get("NAME", f"City {city_idx}")

        print(f"  Annotation {i+1}: City {city_idx} ({city_name}) at {city_coord}")

        # Place annotation directly on the city coordinate
        ax.annotate(
            str(i + 1),
            city_coord,
            xytext=(15, 15),  # Larger offset
            textcoords="offset points",
            fontsize=12,
            ha="center",
            va="center",
            bbox=dict(
                boxstyle="circle,pad=0.5",
                facecolor="yellow",
                alpha=0.95,
                edgecolor="black",
                linewidth=2,
            ),
            weight="bold",
            zorder=6,  # Draw annotations on top of everything
        )

    # Formatting
    ax.set_title(
        f"TSP Tour of Capital Cities in {country_name} (OR-Tools)\nTotal Distance: {tour_cost:.1f} km",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Set equal aspect ratio and tight layout
    ax.set_aspect("equal")
    plt.tight_layout()

    # Use enhanced show_plot with description
    show_plot(
        title=f"TSP Tour - {country_name}",
        description=f"Optimal traveling salesman tour through {len(tour)} capital cities using OR-Tools solver. Total distance: {tour_cost:.1f} km",
    )


def print_tour_details(
    capitals_gdf: gpd.GeoDataFrame, tour: List[int], tour_cost: float
):
    """
    Print detailed information about the TSP tour.

    Args:
        capitals_gdf: GeoDataFrame with capital cities
        tour: Optimal tour as list of city indices
        tour_cost: Total cost of the tour
    """
    print(f"\n{'='*50}")
    print(f"TSP TOUR DETAILS")
    print(f"{'='*50}")
    print(f"Total distance: {tour_cost:.1f} km")
    print(f"Number of cities: {len(tour)}")
    print(f"Average distance between cities: {tour_cost/len(tour):.1f} km")

    print(f"\nTour sequence:")
    for i, city_idx in enumerate(tour):
        if city_idx < len(capitals_gdf):
            city_row = capitals_gdf.iloc[city_idx]
            city_name = city_row.get("NAME", f"City {city_idx}")
            print(f"  {i+1:2d}. {city_name}")


def solve_tsp_for_country(capitals: gpd.GeoDataFrame, country_name: str = "Argentina"):
    """
    Solve Traveling Salesman Problem for capital cities and visualize the result.

    Args:
        capitals: GeoDataFrame containing capital cities
        country_name: Name of the country for visualization
    """
    print(f"\n{'='*60}")
    print(f"SOLVING TSP FOR {country_name.upper()} CAPITAL CITIES")
    print(f"{'='*60}")

    try:
        if capitals.empty:
            print(f"❌ No capital cities found for {country_name}")
            return

        print(f"Found {len(capitals)} capital cities for {country_name}:")
        for idx, row in capitals.iterrows():
            print(f"  - {row.get('NAME', 'Unknown')}")

        # Extract coordinates
        coordinates = extract_capital_coordinates(capitals)
        print(f"\nExtracted {len(coordinates)} coordinates for TSP solving...")

        # Solve TSP
        print("🔄 Solving TSP using OR-Tools...")
        tour, tour_cost = solve_tsp(coordinates)

        if tour:
            print(f"✅ TSP solved successfully!")
            print(f"   Total distance: {tour_cost:.1f} km")
            print(f"   Tour length: {len(tour)} cities")

            # Print tour details
            print_tour_details(capitals, tour, tour_cost)

            # Get country polygon for visualization
            from country_analysis import get_country_polygon
            from map_fetcher import fetch_world_map

            print("📊 Creating TSP visualization...")
            world_map = fetch_world_map(resolution="low")
            country_polygon = get_country_polygon(world_map, country_name)

            # Visualize the tour
            visualize_tsp_tour(country_polygon, capitals, tour, tour_cost, country_name)

        else:
            print("❌ Failed to solve TSP")

        print(f"\n✅ OR-Tools TSP analysis completed successfully!")

    except Exception as e:
        print(f"❌ Error during TSP analysis: {e}")
        import traceback

        traceback.print_exc()


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


def create_voronoi_analysis(country_polygon, country_name: str, capitals):
    """
    Create and display Voronoi diagram based on capital cities.

    Args:
        country_polygon: Country polygon geometry
        country_name: Name of the country
    """
    print(f"\nCreating Voronoi diagram for {country_name} using capital cities...")

    try:
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


def main(country_name: str = None):
    """Main function orchestrating the entire analysis.

    Args:
        country_name: Name of the country to analyze. If None, will show selector.
    """
    # Configuration
    point_generation_factor = 10
    min_country_frequency = 10

    # Handle country selection
    if country_name is None:
        print("No country specified. Loading world map to show country selector...")
        world_map_temp = fetch_world_map(resolution="low")
        if world_map_temp is None:
            print("❌ Failed to load world map. Cannot show country selector.")
            return

        available_countries = get_available_countries(world_map_temp)
        if not available_countries:
            print("❌ No countries found in world map data.")
            return

        country_name = show_country_selector(
            available_countries, title="Fun with Maps - Select Country"
        )

        if not country_name:
            print("No country selected. Exiting.")
            return

    print(f"🌍 Starting analysis for: {country_name}")

    try:
        # Clear any previous plot tracking
        clear_plot_tracker()

        # Step 1: Setup country analysis
        world_map, country_polygon = setup_country_analysis(country_name)

        # Initialize country info for plot tracking and PDF generation
        set_country_info(country_name, country_polygon=country_polygon)

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

        capitals = get_admin1_capitals(country_name)

        # Step 5: Create Voronoi analysis
        create_voronoi_analysis(country_polygon, country_name, capitals)

        # Step 6: Solve TSP for capital cities
        solve_tsp_for_country(capitals, country_name)

        # Step 7: Generate comprehensive PDF report
        print(f"\n{'='*60}")
        print("GENERATING COMPREHENSIVE PDF REPORT")
        print(f"{'='*60}")
        generate_pdf_report()

    except Exception as e:
        print(f"Error in main analysis: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run geographic map analysis with Voronoi diagrams and TSP solutions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # Show country selector GUI
  python main.py --country Argentina      # Analyze Argentina
  python main.py --country "United States" # Analyze United States
        """,
    )
    parser.add_argument(
        "--country",
        type=str,
        help="Name of the country to analyze (if not provided, a GUI selector will appear)",
    )

    args = parser.parse_args()

    # Pass the country argument to main function
    main(country_name=args.country)
