from collections import Counter
from typing import Dict, List, Tuple

import geopandas as gpd


def area_of_polygon(polygon) -> float:
    """Calculate the area of a polygon."""
    return polygon.area


def calculate_point_count(
    country_polygon, factor: int = 10, min_points: int = 300
) -> int:
    """
    Calculate number of points to generate based on polygon area.

    Args:
        country_polygon: Country polygon geometry
        factor: Multiplication factor for area
        min_points: Minimum number of points to generate

    Returns:
        Number of points to generate
    """
    area = area_of_polygon(country_polygon)
    k = area * factor
    k = max(int(k), min_points)
    return k


def filter_points_by_country_frequency(
    points: gpd.GeoDataFrame, closest_countries: List[str], min_frequency: int = 10
) -> Tuple[gpd.GeoDataFrame, List[str], Dict[str, int]]:
    """
    Filter points to keep only those from countries with at least min_frequency points.

    Args:
        points: GeoDataFrame of points
        closest_countries: List of closest countries for each point
        min_frequency: Minimum number of points required per country

    Returns:
        Tuple of (filtered_points, filtered_countries, removed_countries_info)
    """
    if points is None or len(closest_countries) == 0:
        return points, closest_countries, {}

    # Count points per country
    country_counts = Counter(closest_countries)

    # Find countries with at least min_frequency points
    valid_countries = {
        country: count
        for country, count in country_counts.items()
        if count >= min_frequency
    }

    if not valid_countries:
        print(f"No countries have >= {min_frequency} points. Keeping all points.")
        return points, closest_countries, {}

    # Filter points to keep only those from valid countries
    mask = points["closest_country"].isin(valid_countries.keys())
    points_filtered = points[mask].copy()
    closest_countries_filtered = [c for c in closest_countries if c in valid_countries]

    removed_countries = set(closest_countries) - set(valid_countries.keys())

    print(f"Filtered from {len(points)} to {len(points_filtered)} points")
    print(f"Removed countries with < {min_frequency} points: {removed_countries}")

    return points_filtered, closest_countries_filtered, dict(country_counts)


def calculate_country_statistics(
    closest_countries: List[str],
) -> List[Tuple[str, int, float]]:
    """
    Calculate statistics for countries based on point distribution.

    Args:
        closest_countries: List of closest countries for each point

    Returns:
        List of tuples (country_name, count, percentage) sorted by percentage descending
    """
    if not closest_countries:
        return []

    country_stats = []
    total_points = len(closest_countries)

    # Calculate counts and percentages for all countries
    country_counts = Counter(closest_countries)
    for country, count in country_counts.items():
        percentage = (count / total_points) * 100
        country_stats.append((country, count, percentage))

    # Sort by percentage in descending order
    country_stats.sort(key=lambda x: x[2], reverse=True)

    return country_stats


def print_country_statistics(
    closest_countries: List[str], title: str = "Country Statistics"
):
    """
    Print formatted country statistics.

    Args:
        closest_countries: List of closest countries for each point
        title: Title for the statistics section
    """
    country_stats = calculate_country_statistics(closest_countries)

    print(f"\n{title}:")
    print(f"Total points: {len(closest_countries)}")

    for country, count, percentage in country_stats:
        print(f"  {country}: {count} points ({percentage:.1f}%)")


def add_closest_countries_to_points(
    points: gpd.GeoDataFrame, closest_countries: List[str]
) -> gpd.GeoDataFrame:
    """
    Add closest countries as a column to the points dataframe.

    Args:
        points: GeoDataFrame containing points
        closest_countries: List of closest countries for each point

    Returns:
        GeoDataFrame with added 'closest_country' column
    """
    if points is not None and closest_countries:
        points = points.copy()
        points["closest_country"] = closest_countries
    return points


def get_unique_countries_from_list(closest_countries: List[str]) -> List[str]:
    """Get unique countries from the closest countries list."""
    return list(set(closest_countries)) if closest_countries else []
