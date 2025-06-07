import random

import geopandas as gpd
import numpy as np
from shapely.geometry import Point


def generate_random_points_in_polygon(
    polygon_gdf, k, method="rejection_sampling", max_attempts=None
):
    """
    Generate k random points inside a polygon.

    Parameters:
    polygon_gdf (geopandas.GeoDataFrame): GeoDataFrame containing the polygon
    k (int): Number of random points to generate
    method (str): Method to use - 'rejection_sampling' or 'triangulation'
    max_attempts (int): Maximum attempts for rejection sampling (default: k * 1000)

    Returns:
    geopandas.GeoDataFrame: GeoDataFrame with k random points
    """
    if polygon_gdf is None or polygon_gdf.empty:
        print("No polygon data provided")
        return None

    if k <= 0:
        print("Number of points must be positive")
        return None

    # Get the geometry (handle both single polygon and multipolygon)
    geometry = polygon_gdf.iloc[0].geometry

    if method == "rejection_sampling":
        points = _rejection_sampling_points(geometry, k, max_attempts)
    elif method == "triangulation":
        points = _triangulation_points(geometry, k)
    else:
        print(f"Unknown method: {method}. Using rejection_sampling.")
        points = _rejection_sampling_points(geometry, k, max_attempts)

    if not points:
        print("Failed to generate points")
        return None

    # Create GeoDataFrame with the points
    points_gdf = gpd.GeoDataFrame(
        {"point_id": range(1, len(points) + 1)}, geometry=points, crs=polygon_gdf.crs
    )

    print(f"Successfully generated {len(points)} random points inside the polygon")
    return points_gdf


def _rejection_sampling_points(geometry, k, max_attempts=None):
    """
    Generate random points using rejection sampling method.
    This method generates random points in the bounding box and keeps only those inside the polygon.
    """
    if max_attempts is None:
        max_attempts = max(k * 1000, 10000)  # Ensure reasonable number of attempts

    # Get bounding box
    minx, miny, maxx, maxy = geometry.bounds

    points = []
    attempts = 0

    print(f"Generating {k} points using rejection sampling...")
    print(f"Polygon bounds: ({minx:.4f}, {miny:.4f}) to ({maxx:.4f}, {maxy:.4f})")

    while len(points) < k and attempts < max_attempts:
        # Generate random point in bounding box
        x = random.uniform(minx, maxx)
        y = random.uniform(miny, maxy)
        point = Point(x, y)

        # Check if point is inside the polygon
        if geometry.contains(point):
            points.append(point)

        attempts += 1

        # Progress indicator for large k
        if attempts % 1000 == 0 and len(points) < k:
            efficiency = len(points) / attempts * 100
            print(
                f"Progress: {len(points)}/{k} points found in {attempts} attempts ({efficiency:.1f}% efficiency)"
            )

    if len(points) < k:
        print(
            f"Warning: Only generated {len(points)} out of {k} requested points after {attempts} attempts"
        )
        print("Consider using a polygon with larger area or increasing max_attempts")

    return points


def _triangulation_points(geometry, k):
    """
    Generate random points using triangulation method.
    This method is more complex but more efficient for complex polygons.
    """
    try:
        from shapely.ops import triangulate

        print(f"Generating {k} points using triangulation method...")

        # Get polygon coordinates
        if hasattr(geometry, "exterior"):
            # Single Polygon
            coords = list(geometry.exterior.coords)
        else:
            # MultiPolygon - use the largest polygon
            largest_poly = max(geometry.geoms, key=lambda p: p.area)
            coords = list(largest_poly.exterior.coords)

        # Create triangulation
        triangles = triangulate(coords)

        # Calculate areas of triangles that are inside the polygon
        valid_triangles = []
        triangle_areas = []

        for triangle in triangles:
            if geometry.contains(triangle.centroid) or geometry.intersects(triangle):
                # Check if triangle is mostly inside the polygon
                intersection = geometry.intersection(triangle)
                if intersection.area > triangle.area * 0.5:  # At least 50% inside
                    valid_triangles.append(triangle)
                    triangle_areas.append(intersection.area)

        if not valid_triangles:
            print("Triangulation failed, falling back to rejection sampling")
            return _rejection_sampling_points(geometry, k)

        # Generate points weighted by triangle areas
        points = []
        triangle_weights = np.array(triangle_areas) / sum(triangle_areas)

        for _ in range(k):
            # Choose triangle based on area weighting
            triangle_idx = np.random.choice(len(valid_triangles), p=triangle_weights)
            triangle = valid_triangles[triangle_idx]

            # Generate random point in triangle
            point = _random_point_in_triangle(triangle)

            # Ensure point is actually inside the original polygon
            if geometry.contains(point):
                points.append(point)
            else:
                # Fall back to rejection sampling for this point
                minx, miny, maxx, maxy = geometry.bounds
                attempts = 0
                while attempts < 100:  # Limited attempts per point
                    x = random.uniform(minx, maxx)
                    y = random.uniform(miny, maxy)
                    test_point = Point(x, y)
                    if geometry.contains(test_point):
                        points.append(test_point)
                        break
                    attempts += 1

        return points

    except ImportError:
        print(
            "Triangulation method requires additional dependencies, using rejection sampling"
        )
        return _rejection_sampling_points(geometry, k)
    except Exception as e:
        print(f"Triangulation failed ({e}), using rejection sampling")
        return _rejection_sampling_points(geometry, k)


def _random_point_in_triangle(triangle):
    """Generate a random point inside a triangle using barycentric coordinates."""
    coords = list(triangle.exterior.coords)[:-1]  # Remove duplicate last point

    if len(coords) != 3:
        # Fallback for non-triangular shapes
        minx, miny, maxx, maxy = triangle.bounds
        return Point(random.uniform(minx, maxx), random.uniform(miny, maxy))

    # Barycentric coordinates method
    r1, r2 = random.random(), random.random()

    # Ensure point is inside triangle
    if r1 + r2 > 1:
        r1, r2 = 1 - r1, 1 - r2

    # Calculate point using barycentric coordinates
    x = (
        coords[0][0]
        + r1 * (coords[1][0] - coords[0][0])
        + r2 * (coords[2][0] - coords[0][0])
    )
    y = (
        coords[0][1]
        + r1 * (coords[1][1] - coords[0][1])
        + r2 * (coords[2][1] - coords[0][1])
    )

    return Point(x, y)
