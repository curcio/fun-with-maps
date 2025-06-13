"""
Utility functions for TSP solving and geographic calculations.
"""

import math
from typing import List, Tuple


def haversine_distance(
    point1: Tuple[float, float], point2: Tuple[float, float]
) -> float:
    """
    Calculate the great circle distance between two points on Earth using haversine formula.

    Args:
        point1: (longitude, latitude) in degrees
        point2: (longitude, latitude) in degrees

    Returns:
        Distance in kilometers
    """
    # Convert decimal degrees to radians
    lon1, lat1 = math.radians(point1[0]), math.radians(point1[1])
    lon2, lat2 = math.radians(point2[0]), math.radians(point2[1])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    # Radius of earth in kilometers
    r = 6371

    return c * r


def print_solution_details(
    points: List[Tuple[float, float]], tour: List[int], cost: float
):
    """
    Print detailed information about the TSP solution.

    Args:
        points: Original list of coordinate points
        tour: Optimal tour as list of indices
        cost: Total tour cost in kilometers
    """
    print(f"\n{'='*60}")
    print(f"TSP SOLUTION DETAILS (OR-Tools)")
    print(f"{'='*60}")
    print(f"Total tour distance: {cost:.1f} km")
    print(f"Number of cities: {len(tour)}")
    print(f"Average distance between cities: {cost/len(tour):.1f} km")

    print(f"\nTour sequence:")
    for i, city_idx in enumerate(tour):
        lon, lat = points[city_idx]
        print(f"  {i+1:2d}. City {city_idx:<3d} ({lon:8.4f}, {lat:8.4f})")

    # Show return to start
    if tour:
        start_lon, start_lat = points[tour[0]]
        print(
            f"  {len(tour)+1:2d}. City {tour[0]:<3d} ({start_lon:8.4f}, {start_lat:8.4f}) [return to start]"
        )

    # Calculate some statistics
    if len(tour) > 1:
        distances = []
        for i in range(len(tour)):
            current_idx = tour[i]
            next_idx = tour[(i + 1) % len(tour)]
            dist = haversine_distance(points[current_idx], points[next_idx])
            distances.append(dist)

        print(f"\nDistance statistics:")
        print(f"  Shortest segment: {min(distances):.1f} km")
        print(f"  Longest segment:  {max(distances):.1f} km")
        print(f"  Average segment:  {sum(distances)/len(distances):.1f} km")
