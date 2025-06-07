import concurrent.futures
import multiprocessing as mp
import os
import time
import zipfile
from collections import Counter

import geopandas as gpd

# Configure matplotlib to be more thread-safe
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from closest_country import find_closest_country_to_point
from country_analysis import get_country_polygon
from map_fetcher import fetch_world_map
from point_generation import generate_random_points_in_polygon
from visualization import visualize_country_polygon, visualize_polygon_with_points

matplotlib.rcParams["figure.max_open_warning"] = 50

# Get the map
print("Fetching world map...")
world_map = fetch_world_map(resolution="low")

country = "China"

print(f"Getting {country} polygon...")
country_polygon = get_country_polygon(world_map, country)

# Show the country
print(f"Visualizing {country}...")
visualize_country_polygon(country_polygon, country)

factor = 10

# ============================================================================
# PARALLELIZATION FUNCTIONS
# ============================================================================


def process_points_chunk(args):
    """
    Process a chunk of points to find their closest countries.
    This reduces serialization overhead by processing multiple points per task.
    """
    world_map, points_chunk, start_idx = args
    results = []

    # Find name column once for this chunk
    name_columns = ["NAME", "name", "NAME_EN", "ADMIN", "Country", "country"]
    name_col = None
    for col in name_columns:
        if col in world_map.columns:
            name_col = col
            break

    if name_col is None:
        return [(start_idx + i, None) for i in range(len(points_chunk))]

    for i, point_geom in enumerate(points_chunk):
        try:
            closest_country = None
            min_distance = float("inf")

            # Use vectorized operations where possible
            for _, row in world_map.iterrows():
                try:
                    country_geom = row.geometry
                    country_name = row[name_col]

                    # Quick containment check first (faster than distance)
                    if country_geom.contains(point_geom):
                        # Find closest neighbor instead of containing country
                        continue

                    # Calculate distance to border
                    distance = country_geom.distance(point_geom)
                    if distance < min_distance:
                        min_distance = distance
                        closest_country = country_name

                except Exception:
                    continue

            results.append((start_idx + i, closest_country))

        except Exception:
            results.append((start_idx + i, None))

    return results


def find_closest_countries_parallel(
    world_map, points, max_workers=None, chunk_size=None
):
    """
    Find closest countries for all points using efficient chunked multiprocessing.

    Args:
        world_map: GeoDataFrame with world countries
        points: GeoDataFrame with points
        max_workers: Number of processes to use (default: CPU count)
        chunk_size: Points per chunk (default: automatically calculated)

    Returns:
        list: List of closest countries in the same order as points
    """
    if max_workers is None:
        max_workers = min(mp.cpu_count(), 12)  # Cap at 8 to avoid too much overhead

    if chunk_size is None:
        # Adaptive chunk size: more points = larger chunks to reduce overhead
        chunk_size = max(10, len(points) // (max_workers * 4))

    print(
        f"Using {max_workers} processes with chunk size {chunk_size} for parallel processing..."
    )

    # Split points into chunks
    point_geometries = [row.geometry for _, row in points.iterrows()]
    chunks = []
    for i in range(0, len(point_geometries), chunk_size):
        chunk = point_geometries[i : i + chunk_size]
        chunks.append((world_map, chunk, i))

    closest_countries = [None] * len(points)
    start_time = time.time()

    # Use ProcessPoolExecutor with chunks
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit chunk tasks
        future_to_chunk = {
            executor.submit(process_points_chunk, chunk_args): chunk_args[2]
            for chunk_args in chunks
        }

        # Collect results
        completed_points = 0
        for future in concurrent.futures.as_completed(future_to_chunk):
            chunk_results = future.result()
            for idx, closest_country in chunk_results:
                closest_countries[idx] = closest_country

            completed_points += len(chunk_results)
            if completed_points % (chunk_size * 2) == 0 or completed_points == len(
                points
            ):
                elapsed = time.time() - start_time
                rate = completed_points / elapsed if elapsed > 0 else 0
                eta = (len(points) - completed_points) / rate if rate > 0 else 0
                print(
                    f"  Processed {completed_points}/{len(points)} points... "
                    f"({rate:.1f} points/sec, ETA: {eta:.1f}s)"
                )

    elapsed = time.time() - start_time
    rate = len(points) / elapsed if elapsed > 0 else 0
    print(f"Parallel processing completed in {elapsed:.2f}s ({rate:.1f} points/sec)")

    return closest_countries


def find_closest_countries_threaded(world_map, points, max_workers=None):
    """
    Alternative threading approach for comparison - better for I/O bound operations.
    """
    if max_workers is None:
        max_workers = min(mp.cpu_count() * 2, 16)

    print(f"Using {max_workers} threads for threaded processing...")

    closest_countries = [None] * len(points)
    start_time = time.time()

    def process_single_point(args):
        idx, point_row = args
        point_geom = point_row.geometry
        closest_country = find_closest_country_to_point(world_map, point_geom)
        return idx, closest_country

    # Use ThreadPoolExecutor for shared memory access
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        tasks = [(idx, point_row) for idx, point_row in points.iterrows()]
        future_to_idx = {
            executor.submit(process_single_point, task): task[0] for task in tasks
        }

        # Collect results
        completed = 0
        for future in concurrent.futures.as_completed(future_to_idx):
            idx, closest_country = future.result()
            closest_countries[idx] = closest_country
            completed += 1

            if completed % 50 == 0:
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                eta = (len(points) - completed) / rate if rate > 0 else 0
                print(
                    f"  Processed {completed}/{len(points)} points... "
                    f"({rate:.1f} points/sec, ETA: {eta:.1f}s)"
                )

    elapsed = time.time() - start_time
    rate = len(points) / elapsed if elapsed > 0 else 0
    print(f"Threaded processing completed in {elapsed:.2f}s ({rate:.1f} points/sec)")

    return closest_countries


def area_of_polygon(polygon):
    return polygon.area


k = area_of_polygon(country_polygon) * factor
k = max(int(k), 300)

print(f"Generating {k} random points inside {country}...")
points = generate_random_points_in_polygon(country_polygon, k)

# Show the country and the points
print(f"Visualizing {country} with random points...")
if points is not None:
    visualize_polygon_with_points(
        country_polygon, points, f"{country} with Random Points"
    )
else:
    print("Failed to generate points")

# find the closest country to each point
print("Finding closest country to each point...")
closest_countries = []
if points is not None:
    num_points = len(points)
    print(f"Processing {num_points} points...")

    # Choose the best processing method based on number of points
    if num_points < 50:
        print("Using sequential processing (small dataset)...")
        start_time = time.time()
        for idx, point_row in points.iterrows():
            point_geom = point_row.geometry
            closest_country = find_closest_country_to_point(world_map, point_geom)
            closest_countries.append(closest_country)
            if (idx + 1) % 25 == 0:  # Progress update every 25 points
                print(f"  Processed {idx + 1}/{num_points} points...")

        elapsed = time.time() - start_time
        print(
            f"Sequential processing completed in {elapsed:.2f}s ({num_points/elapsed:.1f} points/sec)"
        )

    elif num_points < 500:
        print("Using threaded processing (medium dataset)...")
        closest_countries = find_closest_countries_threaded(world_map, points)
    else:
        print("Using parallel processing (large dataset)...")
        closest_countries = find_closest_countries_parallel(world_map, points)

    # Add closest countries to the points dataframe
    points["closest_country"] = closest_countries

q = 10
# Remove points that are in countries with less than q points
if points is not None and len(closest_countries) > 0:
    # Count points per country
    country_counts = Counter(closest_countries)

    # Find countries with at least q points
    valid_countries = {
        country: count for country, count in country_counts.items() if count >= q
    }

    if valid_countries:
        # Filter points to keep only those from countries with >= q points
        mask = points["closest_country"].isin(valid_countries.keys())
        points_filtered = points[mask].copy()
        closest_countries_filtered = [
            c for c in closest_countries if c in valid_countries
        ]

        print(f"Filtered from {len(points)} to {len(points_filtered)} points")
        print(
            f"Removed countries with < {q} points: {set(closest_countries) - set(valid_countries.keys())}"
        )

        # Update points and closest_countries for visualization
        points = points_filtered
        closest_countries = closest_countries_filtered
    else:
        print(f"No countries have >= {q} points. Keeping all points.")


def get_admin1_capitals(country_name):
    """
    Get admin-1 capital cities for a given country.

    Args:
        country_name (str): Name of the country to filter by

    Returns:
        GeoDataFrame: Admin-1 capital cities for the specified country
    """
    # Check if data is already extracted, if not, unzip it
    if not os.path.exists("data/ne_10m_populated_places/ne_10m_populated_places.shp"):
        if os.path.exists("data/ne_10m_populated_places.zip"):
            with zipfile.ZipFile("data/ne_10m_populated_places.zip", "r") as zip_ref:
                zip_ref.extractall("data/ne_10m_populated_places")
        else:
            raise FileNotFoundError(
                "Data file 'data/ne_10m_populated_places.zip' not found"
            )

    # Read data with geopandas
    gdf = gpd.read_file("data/ne_10m_populated_places/ne_10m_populated_places.shp")

    # Filter by country and admin-1 capitals
    filtered_gdf = gdf[gdf["ADM0NAME"] == country_name]
    admin1_capitals = filtered_gdf[filtered_gdf["FEATURECLA"] == "Admin-1 capital"]

    return admin1_capitals


# Note: Async functions removed to avoid event loop conflicts with matplotlib
# Using threaded approach instead for better compatibility


# for each country use a color pallete and panint the points according to the country
print("Creating visualization with color-coded points...")
if points is not None and len(closest_countries) > 0:
    # Get unique countries and assign colors
    unique_countries = list(set(closest_countries))

    # Use a better color palette for discrete categorical data
    if len(unique_countries) <= 10:
        # Use Set1 for up to 10 categories - bright, highly distinguishable colors
        colors = plt.cm.Set1(np.linspace(0, 1, max(len(unique_countries), 3)))
    elif len(unique_countries) <= 12:
        # Use Paired for up to 12 categories - pairs of related but distinct colors
        colors = plt.cm.Paired(np.linspace(0, 1, len(unique_countries)))
    else:
        # Fall back to tab20 for many categories
        colors = plt.cm.tab20(np.linspace(0, 1, len(unique_countries)))

    country_color_map = {
        country: colors[i] for i, country in enumerate(unique_countries)
    }

    # Find name column for world map
    name_columns = ["NAME", "name", "NAME_EN", "ADMIN", "Country", "country"]
    name_col = None
    for col in name_columns:
        if col in world_map.columns:
            name_col = col
            break

    # Create the plot
    fig, ax = plt.subplots(1, 1, figsize=(15, 12))

    # Plot the main country
    country_polygon.plot(
        ax=ax,
        color="lightblue",
        edgecolor="navy",
        linewidth=2,
        alpha=0.6,
        label=country,
    )

    # Plot closest country polygons with matching colors
    if name_col:
        for closest_country in unique_countries:
            # Find the country polygon in world_map
            country_mask = world_map[name_col].str.contains(
                closest_country, case=False, na=False
            )
            if country_mask.any():
                closest_country_polygon = world_map[country_mask]
                closest_country_polygon.plot(
                    ax=ax,
                    color=country_color_map[closest_country],
                    edgecolor="black",
                    linewidth=1,
                    alpha=0.4,
                    label=f"{closest_country} (country)",
                )

    # Plot points colored by closest country
    for closest_country in unique_countries:
        country_points = points[points["closest_country"] == closest_country]
        if not country_points.empty:
            country_points.plot(
                ax=ax,
                color=country_color_map[closest_country],
                markersize=20,
                alpha=0.9,
                label=f"{closest_country} ({len(country_points)} points)",
                edgecolors="white",
                linewidth=0.5,
            )

    # Plot capital cities for the main country
    print(f"Adding capital cities for {country}...")
    try:
        capitals = get_admin1_capitals(country)
        if not capitals.empty:
            capitals.plot(
                ax=ax,
                color="red",
                marker="*",
                markersize=150,
                alpha=0.9,
                label=f"{country} Capitals ({len(capitals)})",
                edgecolors="darkred",
                linewidth=1,
            )
            print(f"Added {len(capitals)} capital cities for {country}")
        else:
            print(f"No capital cities found for {country}")
    except Exception as e:
        print(f"Error loading capitals for {country}: {e}")

    # Get bounding box of the original country and add 10% margin
    bounds = country_polygon.total_bounds  # [minx, miny, maxx, maxy]
    minx, miny, maxx, maxy = bounds

    # Calculate 10% margin
    width = maxx - minx
    height = maxy - miny
    margin_x = width * 0.1
    margin_y = height * 0.1

    # Load capitals for closest countries (sequential to avoid matplotlib threading issues)
    print("Loading capitals for neighboring countries...")

    print(
        f"Finished loading capitals for {len(unique_countries)} neighboring countries"
    )

    # Set plot bounds with margin
    ax.set_xlim(minx - margin_x, maxx + margin_x)
    ax.set_ylim(miny - margin_y, maxy + margin_y)

    # Customize the plot
    ax.set_title(
        f"{country} with {k} Points Colored by Closest Country (min {q} points)",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    ax.grid(True, alpha=0.3)
    ax.set_facecolor("lightcyan")

    plt.tight_layout()
    from utils import show_plot

    # Print statistics
    print("\nClosest Country Statistics (after filtering):")
    print(f"Total points: {len(points)}")

    # Calculate counts and percentages for all countries
    country_stats = []
    for closest_country in unique_countries:
        count = sum([1 for c in closest_countries if c == closest_country])
        percentage = (count / len(closest_countries)) * 100
        country_stats.append((closest_country, count, percentage))

    # Sort by percentage in descending order
    country_stats.sort(key=lambda x: x[2], reverse=True)

    # Print sorted statistics
    for closest_country, count, percentage in country_stats:
        print(f"  {closest_country}: {count} points ({percentage:.1f}%)")

    show_plot()
else:
    print("No points generated or closest countries found")
