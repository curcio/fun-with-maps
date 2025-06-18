import geopandas as gpd
from shapely.geometry import Point

from fun_with_maps.core.closest_country import (
    analyze_point_location,
    find_closest_country_to_point,
    find_multiple_closest_countries,
)


class TestFindClosestCountryToPoint:
    """Test cases for find_closest_country_to_point function."""

    def test_find_closest_country_point_inside(self, sample_world_map):
        """Test finding closest country when point is inside a country."""
        point = (0, 0)  # Inside TestCountryA
        result = find_closest_country_to_point(sample_world_map, point)

        assert result == "TestCountryA"

    def test_find_closest_country_point_outside(self, sample_world_map):
        """Test finding closest country when point is outside all countries."""
        point = (100, 100)  # Far from all test countries
        result = find_closest_country_to_point(sample_world_map, point)

        assert result is not None
        assert isinstance(result, str)

    def test_find_closest_country_with_distance(self, sample_world_map):
        """Test finding closest country with distance return."""
        point = (0, 0)  # Inside TestCountryA
        result = find_closest_country_to_point(
            sample_world_map, point, return_distance=True
        )

        assert isinstance(result, tuple)
        assert len(result) == 2
        country, distance = result
        assert country == "TestCountryA"
        assert distance == 0.0  # Point is inside, so distance is 0

    def test_find_closest_country_with_distance_outside(self, sample_world_map):
        """Test finding closest country with distance when point is outside."""
        point = (15, 15)  # Between countries
        result = find_closest_country_to_point(
            sample_world_map, point, return_distance=True
        )

        assert isinstance(result, tuple)
        assert len(result) == 2
        country, distance = result
        assert isinstance(country, str)
        assert distance > 0  # Point is outside, so distance > 0

    def test_find_closest_country_shapely_point(self, sample_world_map):
        """Test with shapely Point object."""
        point = Point(0, 0)
        result = find_closest_country_to_point(sample_world_map, point)

        assert result == "TestCountryA"

    def test_find_closest_country_invalid_point_format(self, sample_world_map):
        """Test with invalid point format."""
        point = (0,)  # Only one coordinate
        result = find_closest_country_to_point(sample_world_map, point)

        assert result is None

    def test_find_closest_country_none_input(self):
        """Test with None world map input."""
        result = find_closest_country_to_point(None, (0, 0))

        assert result is None

    def test_find_closest_country_empty_dataframe(self):
        """Test with empty GeoDataFrame."""
        empty_gdf = gpd.GeoDataFrame()
        result = find_closest_country_to_point(empty_gdf, (0, 0))

        assert result is None

    def test_find_closest_country_max_countries_limit(self, sample_world_map):
        """Test with max_countries parameter."""
        point = (0, 0)
        result = find_closest_country_to_point(sample_world_map, point, max_countries=2)

        assert result is not None
        assert isinstance(result, str)


class TestFindMultipleClosestCountries:
    """Test cases for find_multiple_closest_countries function."""

    def test_find_multiple_closest_countries_success(self, sample_world_map):
        """Test finding multiple closest countries."""
        point = (15, 15)  # Between countries
        result = find_multiple_closest_countries(sample_world_map, point, n_countries=3)

        assert result is not None
        assert isinstance(result, list)
        assert len(result) <= 3  # Should return at most 3 countries

        # Check structure of results
        for country, distance in result:
            assert isinstance(country, str)
            assert isinstance(distance, (int, float))
            assert distance >= 0

    def test_find_multiple_closest_countries_sorted(self, sample_world_map):
        """Test that results are sorted by distance."""
        point = (15, 15)
        result = find_multiple_closest_countries(sample_world_map, point, n_countries=3)

        if len(result) > 1:
            # Check that distances are in ascending order
            distances = [distance for _, distance in result]
            assert distances == sorted(distances)

    def test_find_multiple_closest_countries_point_inside(self, sample_world_map):
        """Test when point is inside a country."""
        point = (0, 0)  # Inside TestCountryA
        result = find_multiple_closest_countries(sample_world_map, point, n_countries=3)

        assert result is not None
        assert len(result) > 0

        # First country should be the containing country with distance 0
        country, distance = result[0]
        assert country == "TestCountryA"
        assert distance == 0.0

    def test_find_multiple_closest_countries_shapely_point(self, sample_world_map):
        """Test with shapely Point object."""
        point = Point(15, 15)
        result = find_multiple_closest_countries(sample_world_map, point, n_countries=2)

        assert result is not None
        assert isinstance(result, list)

    def test_find_multiple_closest_countries_none_input(self):
        """Test with None world map input."""
        result = find_multiple_closest_countries(None, (0, 0), n_countries=3)

        assert result is None

    def test_find_multiple_closest_countries_empty_dataframe(self):
        """Test with empty GeoDataFrame."""
        empty_gdf = gpd.GeoDataFrame()
        result = find_multiple_closest_countries(empty_gdf, (0, 0), n_countries=3)

        assert result is None


class TestAnalyzePointLocation:
    """Test cases for analyze_point_location function."""

    def test_analyze_point_location_inside_country(self, sample_world_map):
        """Test analysis when point is inside a country."""
        point = (0, 0)  # Inside TestCountryA
        result = analyze_point_location(sample_world_map, point)

        assert result is not None
        assert isinstance(result, dict)

        # Check required fields
        required_fields = [
            "coordinates",
            "closest_country",
            "distance_to_closest",
            "is_inside_country",
            "containing_country",
            "top_5_closest",
            "ocean_or_land",
        ]
        for field in required_fields:
            assert field in result

        # Check values for point inside country
        assert result["coordinates"] == (0, 0)
        assert result["is_inside_country"] is True
        assert result["containing_country"] == "TestCountryA"
        assert result["closest_country"] == "TestCountryA"
        assert result["distance_to_closest"] == 0.0
        assert result["ocean_or_land"] == "land"

    def test_analyze_point_location_outside_country(self, sample_world_map):
        """Test analysis when point is outside all countries."""
        point = (100, 100)  # Far from all countries
        result = analyze_point_location(sample_world_map, point)

        assert result is not None
        assert isinstance(result, dict)

        # Check values for point outside countries
        assert result["coordinates"] == (100, 100)
        assert result["is_inside_country"] is False
        assert result["containing_country"] is None
        assert result["distance_to_closest"] > 0
        assert result["ocean_or_land"] == "ocean_or_water"

    def test_analyze_point_location_shapely_point(self, sample_world_map):
        """Test with shapely Point object."""
        point = Point(0, 0)
        result = analyze_point_location(sample_world_map, point)

        assert result is not None
        assert result["coordinates"] == (0, 0)

    def test_analyze_point_location_top_5_closest(self, sample_world_map):
        """Test that top_5_closest is populated."""
        point = (15, 15)  # Between countries
        result = analyze_point_location(sample_world_map, point)

        assert "top_5_closest" in result
        if result["top_5_closest"]:
            assert isinstance(result["top_5_closest"], list)
            assert len(result["top_5_closest"]) <= 5

            # Check structure
            for country, distance in result["top_5_closest"]:
                assert isinstance(country, str)
                assert isinstance(distance, (int, float))

    def test_analyze_point_location_comprehensive_fields(self, sample_world_map):
        """Test that all analysis fields are present and have correct types."""
        point = (25, 25)  # Inside TestCountryB
        result = analyze_point_location(sample_world_map, point)

        # Check coordinates
        assert isinstance(result["coordinates"], tuple)
        assert len(result["coordinates"]) == 2

        # Check boolean fields
        assert isinstance(result["is_inside_country"], bool)

        # Check string fields (can be None)
        if result["closest_country"] is not None:
            assert isinstance(result["closest_country"], str)
        if result["containing_country"] is not None:
            assert isinstance(result["containing_country"], str)

        # Check numeric fields (can be None)
        if result["distance_to_closest"] is not None:
            assert isinstance(result["distance_to_closest"], (int, float))

        # Check list field
        assert isinstance(result["top_5_closest"], list)

        # Check ocean_or_land field
        assert result["ocean_or_land"] in ["land", "ocean_or_water", "unknown"]
