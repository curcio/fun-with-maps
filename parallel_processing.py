import concurrent.futures
import multiprocessing as mp
import time
from typing import List, Optional, Tuple

import geopandas as gpd

from closest_country import find_closest_country_to_point


def process_points_chunk(args: Tuple) -> List[Tuple[int, Optional[str]]]:
    """
    Process a chunk of points to find their closest countries.
    This reduces serialization overhead by processing multiple points per task.

    Args:
        args: Tuple containing (world_map, points_chunk, start_idx)

    Returns:
        List of tuples (index, closest_country)
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


def calculate_chunk_size(num_points: int, max_workers: int) -> int:
    """Calculate optimal chunk size based on number of points and workers."""
    return max(10, num_points // (max_workers * 4))


def split_points_into_chunks(
    points: gpd.GeoDataFrame, world_map: gpd.GeoDataFrame, chunk_size: int
) -> List[Tuple]:
    """Split points into chunks for parallel processing."""
    point_geometries = [row.geometry for _, row in points.iterrows()]
    chunks = []
    for i in range(0, len(point_geometries), chunk_size):
        chunk = point_geometries[i : i + chunk_size]
        chunks.append((world_map, chunk, i))
    return chunks


def process_with_progress_updates(
    executor,
    future_to_chunk: dict,
    total_points: int,
    chunk_size: int,
    start_time: float,
) -> List[Optional[str]]:
    """Process futures with progress updates."""
    closest_countries = [None] * total_points
    completed_points = 0

    for future in concurrent.futures.as_completed(future_to_chunk):
        chunk_results = future.result()
        for idx, closest_country in chunk_results:
            closest_countries[idx] = closest_country

        completed_points += len(chunk_results)
        if completed_points % (chunk_size * 2) == 0 or completed_points == total_points:
            _print_progress(completed_points, total_points, start_time)

    return closest_countries


def _print_progress(completed: int, total: int, start_time: float):
    """Print progress update with ETA calculation."""
    elapsed = time.time() - start_time
    rate = completed / elapsed if elapsed > 0 else 0
    eta = (total - completed) / rate if rate > 0 else 0
    print(
        f"  Processed {completed}/{total} points... "
        f"({rate:.1f} points/sec, ETA: {eta:.1f}s)"
    )


def find_closest_countries_parallel(
    world_map: gpd.GeoDataFrame,
    points: gpd.GeoDataFrame,
    max_workers: Optional[int] = None,
    chunk_size: Optional[int] = None,
) -> List[Optional[str]]:
    """
    Find closest countries for all points using efficient chunked multiprocessing.

    Args:
        world_map: GeoDataFrame with world countries
        points: GeoDataFrame with points
        max_workers: Number of processes to use (default: CPU count)
        chunk_size: Points per chunk (default: automatically calculated)

    Returns:
        List of closest countries in the same order as points
    """
    if max_workers is None:
        max_workers = min(mp.cpu_count(), 12)  # Cap at 12 to avoid too much overhead

    if chunk_size is None:
        chunk_size = calculate_chunk_size(len(points), max_workers)

    print(
        f"Using {max_workers} processes with chunk size {chunk_size} for parallel processing..."
    )

    # Split points into chunks
    chunks = split_points_into_chunks(points, world_map, chunk_size)
    start_time = time.time()

    # Use ProcessPoolExecutor with chunks
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit chunk tasks
        future_to_chunk = {
            executor.submit(process_points_chunk, chunk_args): chunk_args[2]
            for chunk_args in chunks
        }

        # Collect results with progress updates
        closest_countries = process_with_progress_updates(
            executor, future_to_chunk, len(points), chunk_size, start_time
        )

    elapsed = time.time() - start_time
    rate = len(points) / elapsed if elapsed > 0 else 0
    print(f"Parallel processing completed in {elapsed:.2f}s ({rate:.1f} points/sec)")

    return closest_countries


def find_closest_countries_threaded(
    world_map: gpd.GeoDataFrame,
    points: gpd.GeoDataFrame,
    max_workers: Optional[int] = None,
) -> List[Optional[str]]:
    """
    Alternative threading approach for comparison - better for I/O bound operations.

    Args:
        world_map: GeoDataFrame with world countries
        points: GeoDataFrame with points
        max_workers: Number of threads to use

    Returns:
        List of closest countries in the same order as points
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

        # Collect results with progress updates
        completed = 0
        for future in concurrent.futures.as_completed(future_to_idx):
            idx, closest_country = future.result()
            closest_countries[idx] = closest_country
            completed += 1

            if completed % 50 == 0:
                _print_progress_threaded(completed, len(points), start_time)

    elapsed = time.time() - start_time
    rate = len(points) / elapsed if elapsed > 0 else 0
    print(f"Threaded processing completed in {elapsed:.2f}s ({rate:.1f} points/sec)")

    return closest_countries


def _print_progress_threaded(completed: int, total: int, start_time: float):
    """Print progress update for threaded processing."""
    elapsed = time.time() - start_time
    rate = completed / elapsed if elapsed > 0 else 0
    eta = (total - completed) / rate if rate > 0 else 0
    print(
        f"  Processed {completed}/{total} points... "
        f"({rate:.1f} points/sec, ETA: {eta:.1f}s)"
    )


def find_closest_countries_sequential(
    world_map: gpd.GeoDataFrame, points: gpd.GeoDataFrame
) -> List[Optional[str]]:
    """
    Sequential processing for small datasets.

    Args:
        world_map: GeoDataFrame with world countries
        points: GeoDataFrame with points

    Returns:
        List of closest countries in the same order as points
    """
    print("Using sequential processing (small dataset)...")
    start_time = time.time()
    closest_countries = []

    for idx, point_row in points.iterrows():
        point_geom = point_row.geometry
        closest_country = find_closest_country_to_point(world_map, point_geom)
        closest_countries.append(closest_country)

        if (idx + 1) % 25 == 0:  # Progress update every 25 points
            print(f"  Processed {idx + 1}/{len(points)} points...")

    elapsed = time.time() - start_time
    print(
        f"Sequential processing completed in {elapsed:.2f}s ({len(points)/elapsed:.1f} points/sec)"
    )

    return closest_countries


def choose_processing_method(
    world_map: gpd.GeoDataFrame, points: gpd.GeoDataFrame
) -> List[Optional[str]]:
    """
    Choose the best processing method based on dataset size.

    Args:
        world_map: GeoDataFrame with world countries
        points: GeoDataFrame with points

    Returns:
        List of closest countries in the same order as points
    """
    num_points = len(points)
    print(f"Processing {num_points} points...")

    if num_points < 50:
        return find_closest_countries_parallel(world_map, points)
    elif num_points < 500:
        print("Using threaded processing (medium dataset)...")
        return find_closest_countries_parallel(world_map, points)
    else:
        print("Using parallel processing (large dataset)...")
        return find_closest_countries_parallel(world_map, points)
