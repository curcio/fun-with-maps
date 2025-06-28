from unittest.mock import patch

import geopandas as gpd
from shapely.geometry import Point, Polygon

from fun_with_maps.core.point_generation import generate_random_points_in_polygon


class TestGenerateRandomPointsInPolygon:
    """Test cases for generate_random_points_in_polygon function."""

    def test_generate_points_success(self, sample_country):
        """Test successful point generation."""
        k = 10
        result = generate_random_points_in_polygon(sample_country, k)

        assert result is not None
        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) == k
        assert "geometry" in result.columns
        assert "point_id" in result.columns

        # Check that all points are actually inside the polygon
        polygon_geom = sample_country.iloc[0].geometry
        for _, row in result.iterrows():
            point = row.geometry
            assert isinstance(point, Point)
            assert polygon_geom.contains(point)

    def test_generate_points_rejection_sampling(self, sample_country):
        """Test point generation with rejection sampling method."""
        k = 5
        result = generate_random_points_in_polygon(
            sample_country, k, method="rejection_sampling"
        )

        assert result is not None
        assert len(result) == k

        # Verify all points are inside
        polygon_geom = sample_country.iloc[0].geometry
        for _, row in result.iterrows():
            assert polygon_geom.contains(row.geometry)

    def test_generate_points_triangulation(self, sample_country):
        """Test point generation with triangulation method."""
        k = 5
        result = generate_random_points_in_polygon(
            sample_country, k, method="triangulation"
        )

        assert result is not None
        # Triangulation might fall back to rejection sampling
        assert len(result) <= k  # Might generate fewer points

        # Verify points are inside
        polygon_geom = sample_country.iloc[0].geometry
        for _, row in result.iterrows():
            assert polygon_geom.contains(row.geometry)

    def test_triangulation_uses_polygon_geometry(self, sample_country):
        """Ensure triangulation is called with a polygon geometry object."""
        with patch("shapely.ops.triangulate") as mock_triangulate:
            mock_triangulate.return_value = [sample_country.iloc[0].geometry]

            generate_random_points_in_polygon(sample_country, 1, method="triangulation")

            assert mock_triangulate.called
            arg = mock_triangulate.call_args[0][0]
            assert hasattr(arg, "geom_type")

    def test_generate_points_invalid_method(self, sample_country):
        """Test with invalid method parameter."""
        k = 5
        result = generate_random_points_in_polygon(
            sample_country, k, method="invalid_method"
        )

        # Should fall back to rejection sampling
        assert result is not None
        assert len(result) == k

    def test_generate_points_zero_k(self, sample_country):
        """Test with k=0."""
        result = generate_random_points_in_polygon(sample_country, 0)

        assert result is None

    def test_generate_points_negative_k(self, sample_country):
        """Test with negative k."""
        result = generate_random_points_in_polygon(sample_country, -5)

        assert result is None

    def test_generate_points_none_input(self):
        """Test with None polygon input."""
        result = generate_random_points_in_polygon(None, 5)

        assert result is None

    def test_generate_points_empty_dataframe(self):
        """Test with empty GeoDataFrame."""
        empty_gdf = gpd.GeoDataFrame()
        result = generate_random_points_in_polygon(empty_gdf, 5)

        assert result is None

    def test_generate_points_with_max_attempts(self, sample_country):
        """Test with custom max_attempts parameter."""
        k = 3
        result = generate_random_points_in_polygon(
            sample_country, k, method="rejection_sampling", max_attempts=100
        )

        assert result is not None
        assert len(result) <= k  # Might generate fewer if max_attempts is low

    def test_generate_points_large_k(self, sample_country):
        """Test with larger number of points."""
        k = 50
        result = generate_random_points_in_polygon(sample_country, k)

        assert result is not None
        assert (
            len(result) <= k
        )  # Should generate points, might be fewer due to efficiency

        # Check point distribution
        if len(result) > 0:
            polygon_geom = sample_country.iloc[0].geometry
            for _, row in result.iterrows():
                assert polygon_geom.contains(row.geometry)

    def test_generate_points_complex_polygon(self):
        """Test with a more complex polygon shape."""
        # Create an L-shaped polygon
        l_shape = Polygon([(0, 0), (10, 0), (10, 5), (5, 5), (5, 10), (0, 10), (0, 0)])

        data = {"NAME": ["LShapedCountry"], "geometry": [l_shape]}
        gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")

        k = 20
        result = generate_random_points_in_polygon(gdf, k)

        assert result is not None
        assert len(result) <= k

        # Verify all points are inside the L-shape
        for _, row in result.iterrows():
            assert l_shape.contains(row.geometry)

    def test_generate_points_very_small_polygon(self):
        """Test with a very small polygon."""
        # Create a tiny square
        tiny_square = Polygon([(0, 0), (0.001, 0), (0.001, 0.001), (0, 0.001), (0, 0)])

        data = {"NAME": ["TinyCountry"], "geometry": [tiny_square]}
        gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")

        k = 5
        result = generate_random_points_in_polygon(gdf, k)

        # Should handle gracefully - might generate fewer points
        if result is not None:
            assert len(result) <= k
            for _, row in result.iterrows():
                assert tiny_square.contains(row.geometry)

    def test_generate_points_point_ids(self, sample_country):
        """Test that point IDs are assigned correctly."""
        k = 5
        result = generate_random_points_in_polygon(sample_country, k)

        assert result is not None
        assert "point_id" in result.columns

        # Check that point IDs are sequential starting from 1
        expected_ids = list(range(1, len(result) + 1))
        actual_ids = result["point_id"].tolist()
        assert actual_ids == expected_ids

    def test_generate_points_crs_preservation(self, sample_country):
        """Test that CRS is preserved in the output."""
        k = 5
        result = generate_random_points_in_polygon(sample_country, k)

        assert result is not None
        assert result.crs == sample_country.crs

    def test_generate_points_randomness(self, sample_country):
        """Test that generated points are actually different (random)."""
        k = 10
        result1 = generate_random_points_in_polygon(sample_country, k)
        result2 = generate_random_points_in_polygon(sample_country, k)

        if (
            result1 is not None
            and result2 is not None
            and len(result1) > 0
            and len(result2) > 0
        ):
            # Points should be different (with very high probability)
            points1 = [(p.x, p.y) for p in result1.geometry]
            points2 = [(p.x, p.y) for p in result2.geometry]

            # At least some points should be different
            assert points1 != points2

    def test_generate_points_bounds_check(self, sample_country):
        """Test that all generated points are within the polygon bounds."""
        k = 20
        result = generate_random_points_in_polygon(sample_country, k)

        if result is not None and len(result) > 0:
            polygon_geom = sample_country.iloc[0].geometry
            bounds = polygon_geom.bounds  # (minx, miny, maxx, maxy)

            for _, row in result.iterrows():
                point = row.geometry
                assert bounds[0] <= point.x <= bounds[2]  # x within bounds
                assert bounds[1] <= point.y <= bounds[3]  # y within bounds
