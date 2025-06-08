from typing import List, Optional, Tuple

import geopandas as gpd
import numpy as np
from scipy.spatial import Voronoi
from shapely.geometry import Point, Polygon


def get_admin1_capitals(country_name: str) -> gpd.GeoDataFrame:
    """
    Get admin-1 capital cities for a given country.

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

    # Extract data if needed
    if not os.path.exists(shp_path):
        if os.path.exists(zip_path):
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(data_path)
        else:
            raise FileNotFoundError(f"Data file '{zip_path}' not found")

    # Read and filter data
    gdf = gpd.read_file(shp_path)
    filtered_gdf = gdf[gdf["ADM0NAME"] == country_name]
    admin1_capitals = filtered_gdf[filtered_gdf["FEATURECLA"] == "Admin-1 capital"]

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

    generating_point = vor.points[point_idx]

    if not finite_vertices:
        # If no finite vertices, create a circular region around the point
        bounds = country_geom.bounds
        radius = min(bounds[2] - bounds[0], bounds[3] - bounds[1]) / 6
        circle = Point(generating_point).buffer(radius)
        result = circle.intersection(country_geom)
        return result if not result.is_empty else None

    # CRITICAL CHECK: Ensure generating point can be inside final polygon
    # For infinite regions, we need to extend in directions that keep the generating point included

    # Find infinite ridges for this point
    infinite_ridges = []
    for ridge_idx, (p1, p2) in enumerate(vor.ridge_points):
        if p1 == point_idx or p2 == point_idx:
            ridge_vertices = vor.ridge_vertices[ridge_idx]
            if -1 in ridge_vertices:
                other_point_idx = p2 if p1 == point_idx else p1
                infinite_ridges.append((ridge_idx, other_point_idx, ridge_vertices))

    if not infinite_ridges:
        # No infinite ridges - this shouldn't happen for infinite regions
        # Fallback to finite polygon
        if len(finite_vertices) >= 3:
            try:
                poly = Polygon(finite_vertices)
                if poly.is_valid:
                    return poly.intersection(country_geom)
            except Exception:
                pass
        return None

    # Start with a conservative approach: create a large polygon that definitely contains the point
    # then intersect with proper Voronoi boundaries

    # Method 1: Create a polygon from finite vertices + extended boundary points
    extended_vertices = list(finite_vertices)

    # For each infinite ridge, extend properly using correct Voronoi geometry
    for ridge_idx, other_point_idx, ridge_vertices in infinite_ridges:
        # Get the finite vertex
        finite_vertex = None
        for rv in ridge_vertices:
            if rv >= 0:
                finite_vertex = vor.vertices[rv]
                break

        if finite_vertex is not None:
            center = vor.points[point_idx]
            other_center = vor.points[other_point_idx]

            # The infinite ray direction: perpendicular to the perpendicular bisector
            # of the line segment connecting the two generating points
            bisector_direction = center - other_center
            bisector_direction = bisector_direction / np.linalg.norm(bisector_direction)

            # The Voronoi edge is perpendicular to the bisector direction
            edge_direction = np.array([-bisector_direction[1], bisector_direction[0]])

            # Determine which direction to extend (there are two possibilities)
            # We want the direction that keeps our generating point on the correct side
            test_point1 = finite_vertex + edge_direction * 0.1
            test_point2 = finite_vertex - edge_direction * 0.1

            # Check which test point is further from the other generating point
            dist1 = np.linalg.norm(test_point1 - other_center)
            dist2 = np.linalg.norm(test_point2 - other_center)

            # Choose the direction that moves away from the other point
            if dist1 > dist2:
                ray_direction = edge_direction
            else:
                ray_direction = -edge_direction

            # MUCH MORE CONSERVATIVE extension - limit to reasonable distance
            # Use distance to closest other point as a guide
            min_distance_to_other = float("inf")
            for k, other_point in enumerate(vor.points):
                if k != point_idx:
                    dist = np.linalg.norm(generating_point - other_point)
                    min_distance_to_other = min(min_distance_to_other, dist)

            # Extend only a fraction of the distance to nearest neighbor
            conservative_extension = (
                min_distance_to_other * 0.5
            )  # Even more conservative

            # Also limit by country bounds
            bounds = country_geom.bounds
            max_country_dimension = max(bounds[2] - bounds[0], bounds[3] - bounds[1])
            conservative_extension = min(
                conservative_extension, max_country_dimension * 0.2
            )

            # Create conservative ray
            ray_end = finite_vertex + ray_direction * conservative_extension

            # Check if extension stays within country boundary (approximately)
            ray_point = Point(ray_end)
            if (
                country_geom.contains(ray_point)
                or country_geom.distance(ray_point) < conservative_extension * 0.2
            ):
                extended_vertices.append(ray_end)
            else:
                # If ray goes too far outside, find intersection with country boundary instead
                ray_line = LineString([finite_vertex, ray_end])
                country_intersection = ray_line.intersection(country_geom.boundary)
                if not country_intersection.is_empty:
                    if hasattr(country_intersection, "coords"):
                        coords = list(country_intersection.coords)
                        if coords:
                            extended_vertices.append(np.array(coords[0]))
                    elif hasattr(country_intersection, "geoms"):
                        # Take the first valid intersection
                        for geom in country_intersection.geoms:
                            if hasattr(geom, "coords"):
                                coords = list(geom.coords)
                                if coords:
                                    extended_vertices.append(np.array(coords[0]))
                                    break

    # CONSERVATIVE APPROACH: Only add bbox corners if really necessary and far from other points
    bbox_corners = [
        np.array([bbox.bounds[0], bbox.bounds[1]]),  # bottom-left
        np.array([bbox.bounds[2], bbox.bounds[1]]),  # bottom-right
        np.array([bbox.bounds[2], bbox.bounds[3]]),  # top-right
        np.array([bbox.bounds[0], bbox.bounds[3]]),  # top-left
    ]

    for corner in bbox_corners:
        # Much more restrictive corner inclusion
        distances_to_points = [
            np.linalg.norm(corner - vor.points[i]) for i in range(len(vor.points))
        ]
        closest_point_idx = np.argmin(distances_to_points)
        closest_distance = distances_to_points[closest_point_idx]

        # Only include corner if:
        # 1. It's closest to our point
        # 2. It's significantly closer to our point than to any other point
        # 3. It's within the country boundary or very close to it
        if (
            closest_point_idx == point_idx
            and closest_distance < min(distances_to_points) * 1.5
            and (  # Much closer than alternatives
                country_geom.contains(Point(corner))
                or country_geom.distance(Point(corner)) < closest_distance * 0.3
            )
        ):
            extended_vertices.append(corner)

    # Construct the polygon and VALIDATE that it contains the generating point
    if len(extended_vertices) >= 3:
        try:
            # Remove duplicates
            unique_vertices = []
            for v in extended_vertices:
                is_duplicate = False
                for uv in unique_vertices:
                    if np.linalg.norm(v - uv) < 1e-8:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    unique_vertices.append(v)

            if len(unique_vertices) >= 3:
                # Sort vertices counter-clockwise
                centroid = np.mean(unique_vertices, axis=0)
                angles = [
                    np.arctan2(v[1] - centroid[1], v[0] - centroid[0])
                    for v in unique_vertices
                ]
                sorted_indices = np.argsort(angles)
                sorted_vertices = [unique_vertices[i] for i in sorted_indices]

                # Create polygon
                region_polygon = Polygon(sorted_vertices)

                # CRITICAL VALIDATION: Check if generating point is inside
                if region_polygon.is_valid and not region_polygon.is_empty:
                    point_geom = Point(generating_point)

                    if not region_polygon.contains(point_geom):
                        # If point is not inside, expand the polygon to include it
                        print(
                            f"Warning: Expanding region for point {point_idx} to include generating point"
                        )

                        # Method: buffer the point and union with the polygon
                        point_buffer = point_geom.buffer(
                            0.1
                        )  # Small buffer around point
                        region_polygon = unary_union([region_polygon, point_buffer])

                        # If still not working, create a larger region around the point
                        if not region_polygon.contains(point_geom):
                            bounds = country_geom.bounds
                            radius = (
                                min(bounds[2] - bounds[0], bounds[3] - bounds[1]) / 10
                            )
                            region_polygon = point_geom.buffer(radius)

                    # Final intersection with country geometry
                    result = region_polygon.intersection(country_geom)

                    # Final validation
                    if not result.is_empty and result.contains(point_geom):
                        return result
                    else:
                        # Last resort: create a small buffer around the point
                        # Use distance to nearest neighbor as guide for radius
                        min_distance_to_other = float("inf")
                        for k, other_point in enumerate(vor.points):
                            if k != point_idx:
                                dist = np.linalg.norm(generating_point - other_point)
                                min_distance_to_other = min(min_distance_to_other, dist)

                        radius = min_distance_to_other * 0.3  # Much smaller fallback
                        fallback = point_geom.buffer(radius).intersection(country_geom)
                        return fallback if not fallback.is_empty else None

        except Exception as e:
            print(f"Error constructing infinite region for point {point_idx}: {e}")

    # Final fallback: very small region guaranteed to contain the generating point
    # Use distance to nearest neighbor to avoid overlaps
    min_distance_to_other = float("inf")
    for k, other_point in enumerate(vor.points):
        if k != point_idx:
            dist = np.linalg.norm(generating_point - other_point)
            min_distance_to_other = min(min_distance_to_other, dist)

    radius = min_distance_to_other * 0.25  # Very conservative fallback
    circle = Point(generating_point).buffer(radius)
    result = circle.intersection(country_geom)
    return result if not result.is_empty else None


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
    if points is None or len(points) < 3:
        print(
            f"Need at least 3 capitals for Voronoi diagram, found {len(points) if points is not None else 0}"
        )
        return None, None, None

    print(f"Creating Voronoi diagram from {len(points)} capitals...")

    # Handle geometry type
    if hasattr(country_polygon, "geometry"):
        country_geom = country_polygon.geometry.iloc[0]
    else:
        country_geom = country_polygon

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
            # Handle infinite regions properly
            infinite_region = construct_infinite_voronoi_region(
                vor, i, region, bbox, country_geom
            )
            voronoi_polygons.append(infinite_region)
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
