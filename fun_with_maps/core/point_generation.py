import random
from typing import List, Optional
from enum import Enum

import geopandas as gpd
import numpy as np
from shapely.geometry import Point


class GenerationMethod(Enum):
    """Enum for different point generation methods."""
    REJECTION_SAMPLING = "rejection_sampling"
    TRIANGULATION = "triangulation"
    AUTO = "auto"


class PointGenerator:
    """
    A class for generating random points within polygons using different strategies.
    """
    
    def __init__(self, method: GenerationMethod = GenerationMethod.AUTO, seed: Optional[int] = None):
        """
        Initialize the PointGenerator.
        
        Args:
            method: Default generation method to use
            seed: Random seed for reproducible results
        """
        self.method = method
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
    
    def generate_random_points_in_polygon(self, polygon_gdf, k: int, 
                                        method: Optional[GenerationMethod] = None, 
                                        max_attempts: Optional[int] = None) -> Optional[gpd.GeoDataFrame]:
        """
        Generate k random points inside a polygon.

        Parameters:
        polygon_gdf (geopandas.GeoDataFrame): GeoDataFrame containing the polygon
        k (int): Number of random points to generate
        method (GenerationMethod): Method to use (overrides default)
        max_attempts (int): Maximum attempts for rejection sampling

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
        
        # Choose method
        chosen_method = method or self.method
        if chosen_method == GenerationMethod.AUTO:
            chosen_method = self._choose_optimal_method(geometry, k)

        # Generate points based on method
        if chosen_method == GenerationMethod.REJECTION_SAMPLING:
            points = self._rejection_sampling_points(geometry, k, max_attempts)
        elif chosen_method == GenerationMethod.TRIANGULATION:
            points = self._triangulation_points(geometry, k)
        else:
            print(f"Unknown method: {chosen_method}. Using rejection_sampling.")
            points = self._rejection_sampling_points(geometry, k, max_attempts)

        if not points:
            print("Failed to generate points")
            return None

        # Create GeoDataFrame with the points
        points_gdf = gpd.GeoDataFrame(
            {"point_id": range(1, len(points) + 1)}, 
            geometry=points, 
            crs=polygon_gdf.crs
        )

        print(f"Successfully generated {len(points)} random points using {chosen_method.value}")
        return points_gdf

    def _choose_optimal_method(self, geometry, k: int) -> GenerationMethod:
        """
        Choose the optimal generation method based on polygon characteristics.
        
        Args:
            geometry: Polygon geometry
            k: Number of points to generate
            
        Returns:
            Optimal generation method
        """
        # Calculate polygon area and complexity
        area = geometry.area
        bounds = geometry.bounds
        bbox_area = (bounds[2] - bounds[0]) * (bounds[3] - bounds[1])
        
        # Ratio of polygon area to bounding box area (efficiency metric)
        efficiency_ratio = area / bbox_area if bbox_area > 0 else 0
        
        # For simple, filled polygons with high efficiency, use rejection sampling
        # For complex polygons or when generating many points, consider triangulation
        if efficiency_ratio > 0.5 and k < 5000:
            return GenerationMethod.REJECTION_SAMPLING
        elif k > 10000:
            return GenerationMethod.TRIANGULATION
        else:
            return GenerationMethod.REJECTION_SAMPLING

    def _rejection_sampling_points(self, geometry, k: int, max_attempts: Optional[int] = None) -> List[Point]:
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

    def _triangulation_points(self, geometry, k: int) -> List[Point]:
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
                return self._rejection_sampling_points(geometry, k)

            # Generate points weighted by triangle areas
            points = []
            triangle_weights = np.array(triangle_areas) / sum(triangle_areas)

            for _ in range(k):
                # Choose triangle based on area weighting
                triangle_idx = np.random.choice(len(valid_triangles), p=triangle_weights)
                triangle = valid_triangles[triangle_idx]

                # Generate random point in triangle
                point = self._random_point_in_triangle(triangle)

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
            return self._rejection_sampling_points(geometry, k)
        except Exception as e:
            print(f"Triangulation failed ({e}), using rejection sampling")
            return self._rejection_sampling_points(geometry, k)

    def _random_point_in_triangle(self, triangle) -> Point:
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

    def generate_grid_points(self, polygon_gdf, spacing: float) -> Optional[gpd.GeoDataFrame]:
        """
        Generate grid points within a polygon.
        
        Args:
            polygon_gdf: GeoDataFrame containing the polygon
            spacing: Distance between grid points
            
        Returns:
            GeoDataFrame with grid points inside the polygon
        """
        if polygon_gdf is None or polygon_gdf.empty:
            print("No polygon data provided")
            return None

        geometry = polygon_gdf.iloc[0].geometry
        minx, miny, maxx, maxy = geometry.bounds

        # Generate grid coordinates
        x_coords = np.arange(minx, maxx + spacing, spacing)
        y_coords = np.arange(miny, maxy + spacing, spacing)

        # Create grid points and filter those inside polygon
        points = []
        point_id = 1
        
        for x in x_coords:
            for y in y_coords:
                point = Point(x, y)
                if geometry.contains(point):
                    points.append(point)
                    point_id += 1

        if not points:
            print("No grid points found inside polygon")
            return None

        # Create GeoDataFrame
        points_gdf = gpd.GeoDataFrame(
            {"point_id": range(1, len(points) + 1)},
            geometry=points,
            crs=polygon_gdf.crs
        )

        print(f"Generated {len(points)} grid points with spacing {spacing}")
        return points_gdf

    def get_statistics(self, polygon_gdf, points_gdf) -> dict:
        """
        Calculate statistics about the generated points.
        
        Args:
            polygon_gdf: Original polygon
            points_gdf: Generated points
            
        Returns:
            Dictionary with statistics
        """
        if not points_gdf or points_gdf.empty:
            return {}

        geometry = polygon_gdf.iloc[0].geometry
        bounds = geometry.bounds
        
        stats = {
            "total_points": len(points_gdf),
            "polygon_area": geometry.area,
            "bbox_area": (bounds[2] - bounds[0]) * (bounds[3] - bounds[1]),
            "point_density": len(points_gdf) / geometry.area if geometry.area > 0 else 0,
            "bbox_efficiency": geometry.area / ((bounds[2] - bounds[0]) * (bounds[3] - bounds[1])) if (bounds[2] - bounds[0]) * (bounds[3] - bounds[1]) > 0 else 0
        }
        
        return stats


# Backward compatibility functions
def generate_random_points_in_polygon(polygon_gdf, k, method="rejection_sampling", max_attempts=None):
    """Backward compatibility wrapper."""
    method_enum = GenerationMethod.REJECTION_SAMPLING if method == "rejection_sampling" else GenerationMethod.TRIANGULATION
    generator = PointGenerator(method=method_enum)
    return generator.generate_random_points_in_polygon(polygon_gdf, k, max_attempts=max_attempts)


def _rejection_sampling_points(geometry, k, max_attempts=None):
    """Backward compatibility wrapper."""
    generator = PointGenerator()
    return generator._rejection_sampling_points(geometry, k, max_attempts)


def _triangulation_points(geometry, k):
    """Backward compatibility wrapper."""
    generator = PointGenerator()
    return generator._triangulation_points(geometry, k)
    

def _random_point_in_triangle(triangle):
    """Backward compatibility wrapper."""
    generator = PointGenerator()
    return generator._random_point_in_triangle(triangle)
