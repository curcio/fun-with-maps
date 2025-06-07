import geopandas as gpd
from shapely.geometry import Polygon

from country_analysis import get_country_info, get_country_polygon


class TestGetCountryPolygon:
    """Test cases for get_country_polygon function."""

    def test_get_country_polygon_success(self, sample_world_map):
        """Test successful country extraction."""
        result = get_country_polygon(sample_world_map, "TestCountryA")

        assert result is not None
        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) == 1
        assert result.iloc[0]["NAME"] == "TestCountryA"

    def test_get_country_polygon_case_insensitive(self, sample_world_map):
        """Test case-insensitive country search."""
        result = get_country_polygon(sample_world_map, "testcountrya")

        assert result is not None
        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) == 1
        assert result.iloc[0]["NAME"] == "TestCountryA"

    def test_get_country_polygon_partial_match(self, sample_world_map):
        """Test partial name matching."""
        result = get_country_polygon(sample_world_map, "CountryA")

        assert result is not None
        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) == 1
        assert result.iloc[0]["NAME"] == "TestCountryA"

    def test_get_country_polygon_not_found(self, sample_world_map):
        """Test behavior when country is not found."""
        result = get_country_polygon(sample_world_map, "NonExistentCountry")

        assert result is None

    def test_get_country_polygon_multiple_matches(self, sample_world_map):
        """Test behavior with multiple matches."""
        # Add another country with similar name
        new_row = {
            "NAME": "TestCountryA_Extended",
            "geometry": Polygon([(50, 50), (50, 60), (60, 60), (60, 50), (50, 50)]),
        }
        extended_map = sample_world_map.copy()
        new_gdf = gpd.GeoDataFrame([new_row], crs=sample_world_map.crs)
        extended_map = pd.concat([extended_map, new_gdf], ignore_index=True)

        result = get_country_polygon(extended_map, "TestCountryA")

        # Should return the first match
        assert result is not None
        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) == 1

    def test_get_country_polygon_none_input(self):
        """Test with None input."""
        result = get_country_polygon(None, "TestCountry")

        assert result is None

    def test_get_country_polygon_empty_dataframe(self):
        """Test with empty GeoDataFrame."""
        empty_gdf = gpd.GeoDataFrame()
        result = get_country_polygon(empty_gdf, "TestCountry")

        assert result is None

    def test_get_country_polygon_no_name_column(self):
        """Test with GeoDataFrame that has no name column."""
        data = {
            "OTHER_COLUMN": ["TestCountry"],
            "geometry": [Polygon([(-5, -5), (-5, 5), (5, 5), (5, -5), (-5, -5)])],
        }
        gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")

        result = get_country_polygon(gdf, "TestCountry")

        assert result is None


class TestGetCountryInfo:
    """Test cases for get_country_info function."""

    def test_get_country_info_success(self, sample_country):
        """Test successful country info extraction."""
        info = get_country_info(sample_country)

        assert info is not None
        assert isinstance(info, dict)

        # Check required fields
        required_fields = ["geometry_type", "bounds", "area", "centroid", "crs"]
        for field in required_fields:
            assert field in info

        # Check bounds structure
        assert "west" in info["bounds"]
        assert "south" in info["bounds"]
        assert "east" in info["bounds"]
        assert "north" in info["bounds"]

        # Check centroid structure
        assert "longitude" in info["centroid"]
        assert "latitude" in info["centroid"]

        # Check values are reasonable
        assert info["area"] > 0
        assert -180 <= info["centroid"]["longitude"] <= 180
        assert -90 <= info["centroid"]["latitude"] <= 90

    def test_get_country_info_bounds_correctness(self, sample_country):
        """Test that bounds are calculated correctly."""
        info = get_country_info(sample_country)

        # Sample country is from (-5, -5) to (5, 5)
        assert info["bounds"]["west"] == -5
        assert info["bounds"]["south"] == -5
        assert info["bounds"]["east"] == 5
        assert info["bounds"]["north"] == 5

    def test_get_country_info_centroid_correctness(self, sample_country):
        """Test that centroid is calculated correctly."""
        info = get_country_info(sample_country)

        # Sample country should have centroid at (0, 0)
        assert abs(info["centroid"]["longitude"] - 0) < 0.001
        assert abs(info["centroid"]["latitude"] - 0) < 0.001

    def test_get_country_info_none_input(self):
        """Test with None input."""
        info = get_country_info(None)

        assert info is None

    def test_get_country_info_empty_dataframe(self):
        """Test with empty GeoDataFrame."""
        empty_gdf = gpd.GeoDataFrame()
        info = get_country_info(empty_gdf)

        assert info is None

    def test_get_country_info_complex_polygon(self):
        """Test with a more complex polygon."""
        # Create an L-shaped polygon
        l_shape = Polygon([(0, 0), (10, 0), (10, 5), (5, 5), (5, 10), (0, 10), (0, 0)])

        data = {"NAME": ["LShapedCountry"], "geometry": [l_shape]}
        gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")

        info = get_country_info(gdf)

        assert info is not None
        assert info["area"] > 0
        assert info["geometry_type"] == "Polygon"

        # Check bounds
        assert info["bounds"]["west"] == 0
        assert info["bounds"]["south"] == 0
        assert info["bounds"]["east"] == 10
        assert info["bounds"]["north"] == 10
