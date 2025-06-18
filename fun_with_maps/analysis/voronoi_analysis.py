from typing import List, Optional, Tuple

import geopandas as gpd
import numpy as np
from scipy.spatial import Voronoi
from shapely.geometry import Point, Polygon


class VoronoiAnalyzer:
    """
    A class for managing Voronoi diagram analysis including data download and processing.
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize the VoronoiAnalyzer.
        
        Args:
            data_dir: Directory where data files are stored
        """
        self.data_dir = data_dir
        self.data_url = "https://naciscdn.org/naturalearth/10m/cultural/ne_10m_populated_places.zip"
        
    def download_populated_places_data(self, zip_path: str) -> bool:
        """
        Download the Natural Earth populated places dataset.
        
        Args:
            zip_path: Path where to save the zip file
            
        Returns:
            bool: True if download successful, False otherwise
        """
        import os
        import requests
        
        try:
            print(f"Downloading populated places data from Natural Earth...")
            print(f"URL: {self.data_url}")
            
            # Create data directory if it doesn't exist
            os.makedirs(os.path.dirname(zip_path), exist_ok=True)
            
            # Download the file
            response = requests.get(self.data_url, stream=True)
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

    def get_admin1_capitals(self, country_name: str) -> gpd.GeoDataFrame:
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

        data_path = f"{self.data_dir}/ne_10m_populated_places"
        shp_path = f"{data_path}/ne_10m_populated_places.shp"
        zip_path = f"{data_path}.zip"

        # Extract data if needed
        if not os.path.exists(shp_path):
            if os.path.exists(zip_path):
                print("Extracting populated places data...")
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(data_path)
            else:
                # Try to download the data automatically
                print("Populated places data not found. Attempting to download...")
                if self.download_populated_places_data(zip_path):
                    print("Extracting downloaded data...")
                    with zipfile.ZipFile(zip_path, "r") as zip_ref:
                        zip_ref.extractall(data_path)
                else:
                    raise FileNotFoundError(
                        f"Could not download data from {self.data_url}. "
                        f"Please manually download the file and place it at {zip_path}"
                    )

        # Read and filter data
        print(f"Loading populated places data for {country_name}...")
        gdf = gpd.read_file(shp_path)
        filtered_gdf = gdf[gdf["ADM0NAME"] == country_name]
        admin1_capitals = filtered_gdf[filtered_gdf["FEATURECLA"] == "Admin-1 capital"]

        print(f"Found {len(admin1_capitals)} admin-1 capitals for {country_name}")
        return admin1_capitals

    def extract_voronoi_points(self, capitals_gdf: gpd.GeoDataFrame) -> Optional[np.ndarray]:
        """Extract point coordinates from capitals GeoDataFrame for Voronoi calculation."""
        if capitals_gdf.empty:
            return None

        points = []
        for idx, row in capitals_gdf.iterrows():
            points.append([row.geometry.x, row.geometry.y])

        return np.array(points)

    def create_bounding_box(self, country_geom, margin_factor: float = 0.1) -> Polygon:
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
        self, voronoi_polygons: List, capitals_gdf: gpd.GeoDataFrame, vor: Voronoi
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
                            clean_polygons[i], clean_polygons[j] = self.resolve_overlap(
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
        self, poly1: Polygon, poly2: Polygon, capital1, capital2, point1, point2
    ) -> Tuple[Polygon, Polygon]:
        """
        Resolve overlap between two polygons by geometric clipping, preserving Voronoi structure.

        Returns:
            Tuple of (new_poly1, new_poly2) with no overlap
        """
        from shapely.ops import unary_union
        
        # Get the generating points
        point1_geom = Point(capital1.geometry.x, capital1.geometry.y)
        point2_geom = Point(capital2.geometry.x, capital2.geometry.y)

        try:
            # Get the intersection
            intersection = poly1.intersection(poly2)
            
            if intersection.is_empty or intersection.area < 1e-10:
                # No significant overlap
                return poly1, poly2
            
            # Create the perpendicular bisector line between the two points
            p1 = np.array([point1_geom.x, point1_geom.y])
            p2 = np.array([point2_geom.x, point2_geom.y])
            
            # Midpoint
            midpoint = (p1 + p2) / 2
            
            # Direction vector
            direction = p2 - p1
            direction_norm = np.linalg.norm(direction)
            
            if direction_norm < 1e-10:
                # Points are too close - fall back to buffer method
                distance_between = point1_geom.distance(point2_geom)
                safe_radius = max(distance_between * 0.3, 0.05)
                return point1_geom.buffer(safe_radius), point2_geom.buffer(safe_radius)
            
            # Perpendicular direction (rotate 90 degrees)
            perp_direction = np.array([-direction[1], direction[0]]) / direction_norm
            
            # Create a long line through the midpoint perpendicular to the line connecting the points
            # This is the proper Voronoi boundary
            line_length = max(poly1.bounds[2] - poly1.bounds[0], poly1.bounds[3] - poly1.bounds[1]) * 2
            line_start = midpoint - perp_direction * line_length
            line_end = midpoint + perp_direction * line_length
            
            from shapely.geometry import LineString
            bisector_line = LineString([line_start, line_end])
            
            # Create half-planes by buffering the line slightly and taking the difference
            buffer_size = line_length * 2
            
            # Create two large rectangles on either side of the bisector
            # Rectangle for point1 (left side)
            rect1_center = midpoint - direction / direction_norm * buffer_size
            rect1 = Point(rect1_center).buffer(buffer_size, resolution=4)  # Square-ish buffer
            
            # Rectangle for point2 (right side)  
            rect2_center = midpoint + direction / direction_norm * buffer_size
            rect2 = Point(rect2_center).buffer(buffer_size, resolution=4)
            
            # Clip the original polygons with their respective half-planes
            try:
                clipped_poly1 = poly1.intersection(rect1)
                clipped_poly2 = poly2.intersection(rect2)
                
                # Ensure the generating points are still inside
                if not clipped_poly1.is_empty and clipped_poly1.contains(point1_geom):
                    new_poly1 = clipped_poly1
                else:
                    # Fallback: create a small buffer around point1
                    distance_between = point1_geom.distance(point2_geom)
                    safe_radius = max(distance_between * 0.3, 0.05)
                    new_poly1 = point1_geom.buffer(safe_radius)
                
                if not clipped_poly2.is_empty and clipped_poly2.contains(point2_geom):
                    new_poly2 = clipped_poly2
                else:
                    # Fallback: create a small buffer around point2
                    distance_between = point1_geom.distance(point2_geom)
                    safe_radius = max(distance_between * 0.3, 0.05)
                    new_poly2 = point2_geom.buffer(safe_radius)
                
                # Final check - ensure no overlap
                if new_poly1.intersects(new_poly2):
                    overlap_area = new_poly1.intersection(new_poly2).area
                    if overlap_area > 1e-10:
                        # Still overlapping - use conservative buffer approach
                        distance_between = point1_geom.distance(point2_geom)
                        safe_radius = max(distance_between * 0.25, 0.05)
                        new_poly1 = point1_geom.buffer(safe_radius)
                        new_poly2 = point2_geom.buffer(safe_radius)
                
                return new_poly1, new_poly2
                
            except Exception as e:
                print(f"Error in geometric clipping: {e}")
                # Fallback to buffer method
                distance_between = point1_geom.distance(point2_geom)
                safe_radius = max(distance_between * 0.3, 0.05)
                return point1_geom.buffer(safe_radius), point2_geom.buffer(safe_radius)
                
        except Exception as e:
            print(f"Error resolving overlap: {e}")
            # Final fallback
            distance_between = point1_geom.distance(point2_geom)
            safe_radius = max(distance_between * 0.3, 0.05)
            return point1_geom.buffer(safe_radius), point2_geom.buffer(safe_radius)

    def construct_infinite_voronoi_region(
        self, vor: Voronoi, point_idx: int, region: List[int], bbox: Polygon, country_geom
    ) -> Optional[Polygon]:
        """
        Construct a bounded polygon for an infinite Voronoi region with proper geometric validation.

        CRITICAL FIX: Ensures the generating point is always inside the constructed polygon.
        """
        from shapely.geometry import LineString
        from shapely.ops import unary_union

        if not region:
            print(f"Empty region for point {point_idx}")
            # Create a fallback small circle around the point
            point = Point(vor.points[point_idx])
            return point.buffer(0.1)
        
        # Handle infinite regions (regions with -1 vertices)
        if -1 in region:
            # This is an infinite region - we need to construct it properly
            return self._construct_proper_infinite_region(vor, point_idx, region, bbox, country_geom)

        try:
            # Get vertices for this region
            vertices = []
            for vertex_idx in region:
                if 0 <= vertex_idx < len(vor.vertices):
                    vertex = vor.vertices[vertex_idx]
                    vertices.append([vertex[0], vertex[1]])

            if len(vertices) < 3:
                print(f"Not enough vertices for region {point_idx}")
                point = Point(vor.points[point_idx])
                return point.buffer(0.1)

            # Create polygon from vertices
            try:
                region_polygon = Polygon(vertices)

                # Validate the polygon
                if not region_polygon.is_valid:
                    region_polygon = region_polygon.buffer(0)  # Fix invalid geometry

                if region_polygon.is_empty:
                    print(f"Empty polygon for region {point_idx}")
                    point = Point(vor.points[point_idx])
                    return point.buffer(0.1)

                # Clip with bounding box and country
                clipped = region_polygon.intersection(bbox)
                if hasattr(country_geom, "iloc"):
                    country_geometry = country_geom.iloc[0].geometry
                else:
                    country_geometry = country_geom

                if not clipped.is_empty:
                    final_region = clipped.intersection(country_geometry)
                    if not final_region.is_empty and final_region.area > 1e-10:
                        # Ensure the generating point is inside
                        generating_point = Point(vor.points[point_idx])
                        if isinstance(final_region, Polygon):
                            if final_region.contains(generating_point) or final_region.touches(
                                generating_point
                            ):
                                return final_region
                        # If point not inside, create buffer around point
                        return generating_point.buffer(0.1)

                # Fallback
                point = Point(vor.points[point_idx])
                return point.buffer(0.1)

            except Exception as e:
                print(f"Error creating polygon for region {point_idx}: {e}")
                point = Point(vor.points[point_idx])
                return point.buffer(0.1)

        except Exception as e:
            print(f"Critical error in construct_infinite_voronoi_region: {e}")
            point = Point(vor.points[point_idx])
            return point.buffer(0.1)

    def _construct_proper_infinite_region(
        self, vor: Voronoi, point_idx: int, region: List[int], bbox: Polygon, country_geom
    ) -> Optional[Polygon]:
        """
        Properly construct an infinite Voronoi region using geometric extension.
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

        # Find infinite ridges for this point
        infinite_ridges = []
        for ridge_idx, (p1, p2) in enumerate(vor.ridge_points):
            if p1 == point_idx or p2 == point_idx:
                ridge_vertices = vor.ridge_vertices[ridge_idx]
                if -1 in ridge_vertices:
                    other_point_idx = p2 if p1 == point_idx else p1
                    infinite_ridges.append((ridge_idx, other_point_idx, ridge_vertices))

        if not infinite_ridges:
            # No infinite ridges - fallback to finite polygon
            if len(finite_vertices) >= 3:
                try:
                    poly = Polygon(finite_vertices)
                    if poly.is_valid:
                        return poly.intersection(country_geom)
                except Exception:
                    pass
            return None

        # Start with finite vertices and extend for infinite ridges
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
                bisector_direction = center - other_center
                bisector_direction = bisector_direction / np.linalg.norm(bisector_direction)

                # The Voronoi edge is perpendicular to the bisector direction
                edge_direction = np.array([-bisector_direction[1], bisector_direction[0]])

                # Determine which direction to extend
                test_point1 = finite_vertex + edge_direction * 0.1
                test_point2 = finite_vertex - edge_direction * 0.1

                # Check which test point is further from the other generating point
                dist1 = np.linalg.norm(test_point1 - other_center)
                dist2 = np.linalg.norm(test_point2 - other_center)

                # Choose the direction that moves away from the other point
                ray_direction = edge_direction if dist1 > dist2 else -edge_direction

                # Conservative extension
                min_distance_to_other = float("inf")
                for k, other_point in enumerate(vor.points):
                    if k != point_idx:
                        dist = np.linalg.norm(generating_point - other_point)
                        min_distance_to_other = min(min_distance_to_other, dist)

                conservative_extension = min_distance_to_other * 0.5

                # Also limit by country bounds
                bounds = country_geom.bounds
                max_country_dimension = max(bounds[2] - bounds[0], bounds[3] - bounds[1])
                conservative_extension = min(conservative_extension, max_country_dimension * 0.2)

                # Create conservative ray
                ray_end = finite_vertex + ray_direction * conservative_extension
                extended_vertices.append(ray_end)

        # Add appropriate bbox corners
        bbox_corners = [
            np.array([bbox.bounds[0], bbox.bounds[1]]),  # bottom-left
            np.array([bbox.bounds[2], bbox.bounds[1]]),  # bottom-right
            np.array([bbox.bounds[2], bbox.bounds[3]]),  # top-right
            np.array([bbox.bounds[0], bbox.bounds[3]]),  # top-left
        ]

        for corner in bbox_corners:
            distances_to_points = [
                np.linalg.norm(corner - vor.points[i]) for i in range(len(vor.points))
            ]
            closest_point_idx = np.argmin(distances_to_points)

            if closest_point_idx == point_idx:
                extended_vertices.append(corner)

        # Construct the polygon
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

                    if region_polygon.is_valid and not region_polygon.is_empty:
                        point_geom = Point(generating_point)

                        # Ensure the generating point is inside
                        if not region_polygon.contains(point_geom):
                            # Expand to include the point
                            point_buffer = point_geom.buffer(0.1)
                            region_polygon = unary_union([region_polygon, point_buffer])

                        # Final intersection with country geometry
                        result = region_polygon.intersection(country_geom)
                        if not result.is_empty:
                            return result

            except Exception as e:
                print(f"Error constructing infinite region for point {point_idx}: {e}")

        # Final fallback
        min_distance_to_other = float("inf")
        for k, other_point in enumerate(vor.points):
            if k != point_idx:
                dist = np.linalg.norm(generating_point - other_point)
                min_distance_to_other = min(min_distance_to_other, dist)

        radius = min_distance_to_other * 0.25
        circle = Point(generating_point).buffer(radius)
        result = circle.intersection(country_geom)
        return result if not result.is_empty else None

    def create_voronoi_from_capitals(
        self, capitals_gdf: gpd.GeoDataFrame, country_polygon
    ) -> Tuple[Optional[Voronoi], List, Optional[np.ndarray]]:
        """
        Create Voronoi diagram from capital cities with proper clipping and validation.

        Args:
            capitals_gdf: GeoDataFrame with capital cities
            country_polygon: Country polygon geometry for clipping

        Returns:
            Tuple of (voronoi_object, clipped_polygons, points_array)
        """
        print(f"Creating Voronoi diagram from {len(capitals_gdf)} capitals...")

        if capitals_gdf.empty:
            print("No capitals provided for Voronoi analysis")
            return None, [], None

        # Extract points
        points = self.extract_voronoi_points(capitals_gdf)
        if points is None or len(points) < 3:
            print("Not enough points for Voronoi diagram (need at least 3)")
            return None, [], points

        try:

            # Get country geometry
            if hasattr(country_polygon, "iloc"):
                country_geom = country_polygon.iloc[0].geometry
            else:
                country_geom = country_polygon

            # Create bounding box for clipping infinite regions
            bbox = self.create_bounding_box(country_geom, margin_factor=3)

            # This ensures proper mapping between points and their Voronoi regions
            voronoi_polygons = []

            # create 16 auxiliary points on the bounding box
            aux_points = []
            for i in range(4):
                aux_points.append(bbox.exterior.coords[i])

            # add aux points to the points
            points = np.concatenate([points, aux_points])

            
            # Create Voronoi diagram
            vor = Voronoi(points)


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
            # Eliminate overlaps
            if len(voronoi_polygons) == len(capitals_gdf):
                clean_polygons = self.eliminate_all_overlaps(voronoi_polygons, capitals_gdf, vor)
                print(f"Generated {len(clean_polygons)} Voronoi regions")
                return vor, clean_polygons, points
            else:
                print(
                    f"Mismatch: {len(voronoi_polygons)} polygons for {len(capitals_gdf)} capitals"
                )
                return vor, voronoi_polygons, points

        except Exception as e:
            print(f"Error creating Voronoi diagram: {e}")
            import traceback

            traceback.print_exc()
            return None, [], points


# Backward compatibility functions
def download_populated_places_data(zip_path: str, data_url: str) -> bool:
    """Backward compatibility wrapper."""
    analyzer = VoronoiAnalyzer()
    analyzer.data_url = data_url
    return analyzer.download_populated_places_data(zip_path)


def get_admin1_capitals(country_name: str) -> gpd.GeoDataFrame:
    """Backward compatibility wrapper."""
    analyzer = VoronoiAnalyzer()
    return analyzer.get_admin1_capitals(country_name)


def extract_voronoi_points(capitals_gdf: gpd.GeoDataFrame) -> Optional[np.ndarray]:
    """Backward compatibility wrapper."""
    analyzer = VoronoiAnalyzer()
    return analyzer.extract_voronoi_points(capitals_gdf)


def create_voronoi_from_capitals(
    capitals_gdf: gpd.GeoDataFrame, country_polygon
) -> Tuple[Optional[Voronoi], List, Optional[np.ndarray]]:
    """Backward compatibility wrapper."""
    analyzer = VoronoiAnalyzer()
    return analyzer.create_voronoi_from_capitals(capitals_gdf, country_polygon)
