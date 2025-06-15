from typing import List, Optional, Tuple

import geopandas as gpd
import numpy as np
from scipy.spatial import Voronoi
from shapely.geometry import Point, Polygon


def download_populated_places_data(zip_path: str, data_url: str) -> bool:
    """
    Download the Natural Earth populated places dataset.
    
    Args:
        zip_path: Path where to save the zip file
        data_url: URL to download the data from
        
    Returns:
        bool: True if download successful, False otherwise
    """
    import os
    import requests
    
    try:
        print(f"Downloading populated places data from Natural Earth...")
        print(f"URL: {data_url}")
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(zip_path), exist_ok=True)
        
        # Download the file
        response = requests.get(data_url, stream=True)
        response.raise_for_status()
        
        # Save the file
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Successfully downloaded: {zip_path}")
        return True
        
    except Exception as e:
        print(f"Error downloading data: {e}")
        return False


def get_admin1_capitals(country_name: str) -> gpd.GeoDataFrame:
    """
    Get admin-1 capital cities for a given country.
    Automatically downloads the data if it's missing.

    Args:
        country_name: Name of the country to filter by

    Returns:
        GeoDataFrame: Admin-1 capital cities for the specified country
    """
    import os
    import zipfile

    data_path = "data/ne_10m_populated_places"
    shp_path = f"{data_path}/ne_10m_populated_places.shp"
    zip_path = f"{data_path}.zip"
    data_url = "https://naciscdn.org/naturalearth/10m/cultural/ne_10m_populated_places.zip"

    # Extract data if needed
    if not os.path.exists(shp_path):
        if os.path.exists(zip_path):
            print("Extracting populated places data...")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(data_path)
        else:
            # Try to download the data automatically
            print("Populated places data not found. Attempting to download...")
            if download_populated_places_data(zip_path, data_url):
                print("Extracting downloaded data...")
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(data_path)
            else:
                raise FileNotFoundError(
                    f"Could not download data from {data_url}. "
                    f"Please manually download the file and place it at {zip_path}"
                )

    # Read and filter data
    print(f"Loading populated places data for {country_name}...")
    gdf = gpd.read_file(shp_path)
    filtered_gdf = gdf[gdf["ADM0NAME"] == country_name]
    admin1_capitals = filtered_gdf[filtered_gdf["FEATURECLA"] == "Admin-1 capital"]

    print(f"Found {len(admin1_capitals)} admin-1 capitals for {country_name}")
    return admin1_capitals


def extract_voronoi_points(capitals_gdf: gpd.GeoDataFrame) -> Optional[np.ndarray]:
    """Extract point coordinates from capitals GeoDataFrame for Voronoi calculation."""
    if capitals_gdf.empty:
        return None

    points = []
    for idx, row in capitals_gdf.iterrows():
        points.append([row.geometry.x, row.geometry.y])

    return np.array(points)


def create_bounding_box(country_geom, margin_factor: float = 0.1) -> Polygon:
    """Create a bounding box around the country geometry with very conservative margins."""
    bounds = country_geom.bounds
    minx, miny, maxx, maxy = bounds
    margin = max(maxx - minx, maxy - miny) * margin_factor

    return Polygon(
        [
            (minx - margin, miny - margin),
            (maxx + margin, miny - margin),
            (maxx + margin, maxy + margin),
            (minx - margin, maxy + margin),
        ]
    )


def eliminate_all_overlaps(
    voronoi_polygons: List, capitals_gdf: gpd.GeoDataFrame, vor: Voronoi
) -> List[Polygon]:
    """
    Post-process Voronoi polygons to eliminate ALL overlaps while ensuring
    all generating points remain inside their polygons.

    Args:
        voronoi_polygons: List of initial Voronoi polygons
        capitals_gdf: GeoDataFrame with capital cities
        vor: Voronoi diagram object

    Returns:
        List of non-overlapping polygons with all points inside
    """
    print("Eliminating all overlaps...")

    # Make copies to avoid modifying originals
    clean_polygons = [poly for poly in voronoi_polygons]
    max_iterations = 50
    iteration = 0

    while iteration < max_iterations:
        overlaps_found = False

        # Check all pairs for overlaps
        for i in range(len(clean_polygons)):
            if clean_polygons[i] is None or clean_polygons[i].is_empty:
                continue

            for j in range(i + 1, len(clean_polygons)):
                if clean_polygons[j] is None or clean_polygons[j].is_empty:
                    continue

                poly1 = clean_polygons[i]
                poly2 = clean_polygons[j]

                # Check for significant overlap
                if poly1.intersects(poly2):
                    intersection = poly1.intersection(poly2)
                    if not intersection.is_empty and intersection.area > 1e-10:
                        overlaps_found = True

                        # Resolve overlap by shrinking both polygons
                        clean_polygons[i], clean_polygons[j] = resolve_overlap(
                            poly1,
                            poly2,
                            capitals_gdf.iloc[i],
                            capitals_gdf.iloc[j],
                            vor.points[i],
                            vor.points[j],
                        )

        if not overlaps_found:
            print(f"All overlaps eliminated after {iteration + 1} iterations")
            break

        iteration += 1

    if iteration >= max_iterations:
        print("Warning: Maximum iterations reached. Some overlaps may remain.")

    # Final validation: ensure all points are inside their polygons
    for i, (poly, capital_row) in enumerate(
        zip(clean_polygons, capitals_gdf.iterrows())
    ):
        idx, capital_data = capital_row
        point = Point(capital_data.geometry.x, capital_data.geometry.y)

        if poly is None or poly.is_empty or not poly.contains(point):
            # Create a small guaranteed region around the point
            min_distance = float("inf")
            for k, other_point in enumerate(vor.points):
                if k != i:
                    dist = np.linalg.norm(vor.points[i] - other_point)
                    min_distance = min(min_distance, dist)

            # Very conservative radius
            radius = min_distance * 0.2
            clean_polygons[i] = point.buffer(radius)
            print(f"Fixed polygon {i+1} to ensure point is inside")

    return clean_polygons


def resolve_overlap(
    poly1: Polygon, poly2: Polygon, capital1, capital2, point1, point2
) -> Tuple[Polygon, Polygon]:
    """
    Resolve overlap between two polygons by shrinking them appropriately.

    Returns:
        Tuple of (new_poly1, new_poly2) with no overlap
    """
    # Get the generating points
    point1_geom = Point(capital1.geometry.x, capital1.geometry.y)
    point2_geom = Point(capital2.geometry.x, capital2.geometry.y)

    # Calculate distance between points
    distance_between = point1_geom.distance(point2_geom)

    # Create non-overlapping regions by buffering each point with appropriate radius
    # Use half the distance minus a small margin to ensure separation
    max_radius = (distance_between / 2) * 0.8  # 80% of half-distance for safety margin

    # Calculate current radii (approximate)
    current_radius1 = np.sqrt(poly1.area / np.pi) if poly1.area > 0 else 0.1
    current_radius2 = np.sqrt(poly2.area / np.pi) if poly2.area > 0 else 0.1

    # Shrink radii if necessary
    new_radius1 = min(current_radius1, max_radius)
    new_radius2 = min(current_radius2, max_radius)

    # Create new non-overlapping polygons
    new_poly1 = point1_geom.buffer(new_radius1)
    new_poly2 = point2_geom.buffer(new_radius2)

    # Ensure they don't overlap (final check)
    if new_poly1.intersects(new_poly2):
        # Make them even smaller
        safe_radius = distance_between * 0.3
        new_poly1 = point1_geom.buffer(safe_radius)
        new_poly2 = point2_geom.buffer(safe_radius)

    return new_poly1, new_poly2


def construct_infinite_voronoi_region(
    vor: Voronoi, point_idx: int, region: List[int], bbox: Polygon, country_geom
) -> Optional[Polygon]:
    """
    Construct a bounded polygon for an infinite Voronoi region with proper geometric validation.

    CRITICAL FIX: Ensures the generating point is always inside the constructed polygon.
    """
    from shapely.geometry import LineString
    from shapely.ops import unary_union

    # Get finite vertices in the region
    finite_vertices = []
    for vertex_idx in region:
        if vertex_idx >= 0:
            finite_vertices.append(vor.vertices[vertex_idx])

    result = Polygon(finite_vertices)
    from shapely.geometry.multipolygon import MultiPolygon

    print(type(country_geom))
    for polygon in country_geom.geoms:
        if polygon.exterior.contains(finite_vertices[0]):
            break

    print(polygon)

    exit(0)

    return result


def create_voronoi_from_capitals(
    capitals_gdf: gpd.GeoDataFrame, country_polygon
) -> Tuple[Optional[Voronoi], List, Optional[np.ndarray]]:
    """
    Create a Voronoi diagram from capital cities and clip it to the country polygon.

    Args:
        capitals_gdf: GeoDataFrame containing capital cities
        country_polygon: Country boundary (GeoDataFrame or Shapely geometry)

    Returns:
        tuple: (voronoi diagram, clipped polygons, capital points array)
    """
    if capitals_gdf.empty:
        print("No capitals found for Voronoi diagram")
        return None, None, None

    points = extract_voronoi_points(capitals_gdf)

    # Handle geometry type
    if hasattr(country_polygon, "geometry"):
        country_geom = country_polygon.geometry.iloc[0]
    else:
        country_geom = country_polygon

    # determine bounding box of the country polygon
    minx, miny, maxx, maxy = country_geom.bounds

    # Calculate the width and height of the original bounding box
    width = maxx - minx
    height = maxy - miny

    # Expand the bounding box by 3 times the original size on each side
    expanded_minx = minx - 3 * width
    expanded_maxx = maxx + 3 * width
    expanded_miny = miny - 3 * height
    expanded_maxy = maxy + 3 * height

    bbox = Polygon(
        [
            (expanded_minx, expanded_miny),
            (expanded_maxx, expanded_miny),
            (expanded_maxx, expanded_maxy),
            (expanded_minx, expanded_maxy),
        ]
    )

    # create 16 auxiliary points on the bounding box
    aux_points = []
    for i in range(4):
        aux_points.append(bbox.exterior.coords[i])

    # add aux points to the points
    points = np.concatenate([points, aux_points])

    if points is None or len(points) < 3:
        print(
            f"Need at least 3 capitals for Voronoi diagram, found {len(points) if points is not None else 0}"
        )
        return None, None, None

    print(f"Creating Voronoi diagram from {len(points)} capitals...")

    # Create Voronoi diagram and process regions
    vor = Voronoi(points)
    bbox = create_bounding_box(country_geom)
    voronoi_polygons = []

    for i, region_idx in enumerate(vor.point_region):
        region = vor.regions[region_idx]

        if not region:
            print("Empty region")
            voronoi_polygons.append(None)
        elif -1 in region:
            pass
        else:
            # Finite region
            vertices = [vor.vertices[j] for j in region]
            if len(vertices) >= 3:
                try:
                    poly = Polygon(vertices)
                    if poly.is_valid:
                        clipped = poly.intersection(country_geom)
                        voronoi_polygons.append(
                            clipped if not clipped.is_empty else None
                        )
                    else:
                        voronoi_polygons.append(None)
                except Exception:
                    voronoi_polygons.append(None)
            else:
                voronoi_polygons.append(None)

    return vor, voronoi_polygons, points
