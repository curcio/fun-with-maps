import logging

import numpy as np
from shapely.geometry import Point

log = logging.getLogger(__name__)


def find_closest_country_to_point(
    world_gdf, point, return_distance=False, max_countries=None
):
    """
    Find the closest country to a given point based on distance to the country's border.

    Parameters:
    world_gdf (geopandas.GeoDataFrame): World map data
    point (tuple or shapely.geometry.Point): Point coordinates as
        (longitude, latitude) or Point object
    return_distance (bool): Whether to return the distance along with
        the country
    max_countries (int): Maximum number of countries to consider
        (for performance, default: all)

    Returns:
    str or tuple: Country name, or (country_name, distance) if
        return_distance=True
    None: If no countries found or error occurred
    """
    if world_gdf is None or world_gdf.empty:
        log.error("No world map data provided")
        return None

    # Convert point to shapely Point if needed
    if isinstance(point, (tuple, list)):
        if len(point) != 2:
            log.error("Point must be a tuple/list of (longitude, latitude)")
            return None
        point_geom = Point(point[0], point[1])
        log.debug(
            f"Finding closest country to point: " f"({point[0]:.4f}, {point[1]:.4f})"
        )
    elif hasattr(point, "x") and hasattr(point, "y"):
        point_geom = point
        log.debug(
            f"Finding closest country to point: " f"({point.x:.4f}, {point.y:.4f})"
        )
    else:
        log.error("Point must be a tuple (lon, lat) or shapely Point object")
        return None

    # Find the name column
    name_columns = ["NAME", "name", "NAME_EN", "ADMIN", "Country", "country"]
    name_col = None

    for col in name_columns:
        if col in world_gdf.columns:
            name_col = col
            break

    if name_col is None:
        log.error("No name column found in the dataset")
        return None

    # Limit countries for performance if specified
    countries_to_check = world_gdf.copy()
    if max_countries is not None and len(countries_to_check) > max_countries:
        # Sort by rough distance to point's bounding box for better performance
        countries_to_check["rough_distance"] = countries_to_check.geometry.apply(
            lambda geom: point_geom.distance(geom.centroid)
        )
        countries_to_check = countries_to_check.nsmallest(
            max_countries, "rough_distance"
        )
        countries_to_check = countries_to_check.drop("rough_distance", axis=1)

    # Calculate distances to each country's border
    distances = []
    country_names = []
    containing_country = None

    log.debug(f"Calculating distances to {len(countries_to_check)} countries...")

    for idx, row in countries_to_check.iterrows():
        try:
            country_geom = row.geometry
            country_name = row[name_col]

            # Calculate distance to border
            if country_geom.contains(point_geom):
                # Point is inside the country - distance is 0
                distance = 0.0
                containing_country = country_name
            else:
                # Calculate distance to the border (exterior boundary)
                distance = country_geom.distance(point_geom)

            distances.append(distance)
            country_names.append(country_name)

        except Exception as e:
            log.error(
                f"Error calculating distance for country {row.get(name_col, 'Unknown')}: {e}"
            )
            continue

    if not distances:
        log.error("No valid distances calculated")
        return None

    # Find the country with minimum distance
    min_distance_idx = np.argmin(distances)
    closest_country = country_names[min_distance_idx]
    min_distance = distances[min_distance_idx]

    if containing_country:
        log.debug(f"Point is inside: {containing_country}")
        log.debug(f"Closest neighboring country: {closest_country}")
    else:
        log.debug(f"Closest country: {closest_country}")

    log.debug(f"Distance to border: {min_distance:.6f} degrees")

    # Convert distance to approximate kilometers (rough estimate)
    km_distance = min_distance * 111.32  # 1 degree ≈ 111.32 km at equator
    log.debug(f"Approximate distance: {km_distance:.2f} km")

    if return_distance:
        return closest_country, min_distance
    else:
        return closest_country


def find_multiple_closest_countries(world_gdf, point, n_countries=5):
    """
    Find the n closest countries to a given point.

    Parameters:
    world_gdf (geopandas.GeoDataFrame): World map data
    point (tuple or shapely.geometry.Point): Point coordinates
    n_countries (int): Number of closest countries to return

    Returns:
    list: List of tuples (country_name, distance) sorted by distance
    """
    if world_gdf is None or world_gdf.empty:
        log.error("No world map data provided")
        return None

    # Convert point to shapely Point if needed
    if isinstance(point, (tuple, list)):
        point_geom = Point(point[0], point[1])
    else:
        point_geom = point

    # Find the name column
    name_columns = ["NAME", "name", "NAME_EN", "ADMIN", "Country", "country"]
    name_col = None

    for col in name_columns:
        if col in world_gdf.columns:
            name_col = col
            break

    if name_col is None:
        log.error("No name column found in the dataset")
        return None

    # Calculate distances to all countries
    country_distances = []

    for idx, row in world_gdf.iterrows():
        try:
            country_geom = row.geometry
            country_name = row[name_col]

            # Calculate distance to border
            if country_geom.contains(point_geom):
                distance = 0.0
            else:
                distance = country_geom.distance(point_geom)

            country_distances.append((country_name, distance))

        except Exception:
            continue

    # Sort by distance and return top n
    country_distances.sort(key=lambda x: x[1])

    return country_distances[:n_countries]


def analyze_point_location(world_gdf, point):
    """
    Comprehensive analysis of a point's location relative to countries.

    Parameters:
    world_gdf (geopandas.GeoDataFrame): World map data
    point (tuple or shapely.geometry.Point): Point coordinates

    Returns:
    dict: Dictionary with detailed location analysis
    """
    if isinstance(point, (tuple, list)):
        point_geom = Point(point[0], point[1])
        lon, lat = point[0], point[1]
    else:
        point_geom = point
        lon, lat = point.x, point.y

    analysis = {
        "coordinates": (lon, lat),
        "closest_country": None,
        "distance_to_closest": None,
        "is_inside_country": False,
        "containing_country": None,
        "nearest_countries": [],
        "top_5_closest": [],
        "ocean_or_land": "unknown",
    }

    # Check if point is inside any country
    name_columns = ["NAME", "name", "NAME_EN", "ADMIN", "Country", "country"]
    name_col = None

    for col in name_columns:
        if col in world_gdf.columns:
            name_col = col
            break

    if name_col is None:
        return analysis

    for idx, row in world_gdf.iterrows():
        try:
            country_geom = row.geometry
            country_name = row[name_col]

            if country_geom.contains(point_geom):
                analysis["is_inside_country"] = True
                analysis["containing_country"] = country_name
                analysis["closest_country"] = country_name
                analysis["distance_to_closest"] = 0.0
                analysis["ocean_or_land"] = "land"
                break

        except Exception:
            continue

    # If not inside any country, find closest
    if not analysis["is_inside_country"]:
        closest_result = find_closest_country_to_point(
            world_gdf, point, return_distance=True
        )
        if closest_result:
            analysis["closest_country"] = closest_result[0]
            analysis["distance_to_closest"] = closest_result[1]
        analysis["ocean_or_land"] = "ocean_or_water"

    # Get nearest countries (top 5 closest)
    nearest_countries = find_multiple_closest_countries(world_gdf, point, n_countries=5)
    analysis["nearest_countries"] = nearest_countries
    analysis["top_5_closest"] = nearest_countries

    return analysis
