from unittest.mock import patch

import pytest

from fun_with_maps.core.closest_country import (
    analyze_point_location,
    find_closest_country_to_point,
)
from fun_with_maps.core.country_analysis import get_country_info, get_country_polygon
from fun_with_maps.core.point_generation import generate_random_points_in_polygon
from fun_with_maps.visualization.visualization import visualize_country_polygon


@pytest.mark.integration
class TestWorkflowIntegration:
    """Integration tests for complete workflows."""

    def test_complete_country_analysis_workflow(self, mock_world_data):
        """Test complete workflow from fetching map to analyzing countries."""
        # Step 1: Get a country polygon
        country = get_country_polygon(mock_world_data, "United States")
        assert country is not None

        # Step 2: Get country information
        info = get_country_info(country)
        assert info is not None
        assert "bounds" in info
        assert "centroid" in info

        # Step 3: Generate random points in the country
        points = generate_random_points_in_polygon(country, 5)
        assert points is not None
        assert len(points) <= 5

        # Step 4: Find closest countries for each point
        for _, row in points.iterrows():
            point = row.geometry
            closest = find_closest_country_to_point(mock_world_data, (point.x, point.y))
            assert closest is not None

    def test_point_analysis_workflow(self, mock_world_data):
        """Test workflow for analyzing random points."""
        # Test points at different locations
        test_points = [
            (-90, 35),  # Should be in United States area
            (0, 50),  # Should be in United Kingdom area
            (100, 0),  # Should be in China area
            (0, 0),  # Should be between countries
        ]

        for point in test_points:
            # Analyze the point location
            analysis = analyze_point_location(mock_world_data, point)

            assert analysis is not None
            assert "coordinates" in analysis
            assert "closest_country" in analysis
            assert "is_inside_country" in analysis

            # Check coordinate consistency
            assert analysis["coordinates"] == point

    @patch("fun_with_maps.visualization.visualization.show_plot")
    def test_visualization_workflow(self, mock_show, mock_world_data):
        """Test workflow that includes visualization."""
        # Get a country
        country = get_country_polygon(mock_world_data, "United States")
        assert country is not None

        # Visualize the country (should not raise exceptions)
        visualize_country_polygon(country, "Test Country")
        mock_show.assert_called_once()

    def test_error_handling_workflow(self, mock_world_data):
        """Test that the workflow handles errors gracefully."""
        # Test with invalid country name
        country = get_country_polygon(mock_world_data, "NonExistentCountry")
        assert country is None

        # Test downstream functions with None input
        info = get_country_info(country)
        assert info is None

        points = generate_random_points_in_polygon(country, 5)
        assert points is None

    def test_data_consistency_workflow(self, mock_world_data):
        """Test that data remains consistent throughout the workflow."""
        # Get original CRS
        original_crs = mock_world_data.crs

        # Extract a country
        country = get_country_polygon(mock_world_data, "United States")
        assert country is not None
        assert country.crs == original_crs

        # Generate points
        points = generate_random_points_in_polygon(country, 3)
        if points is not None:
            assert points.crs == original_crs

            # Verify all points are actually inside the country
            country_geom = country.iloc[0].geometry
            for _, row in points.iterrows():
                assert country_geom.contains(row.geometry)

    def test_real_world_scenario_simulation(self, mock_world_data):
        """Test a realistic scenario using the toolkit."""
        # Scenario: Find countries around a specific point and analyze them
        central_point = (0, 0)  # Point of interest

        # Step 1: Find closest countries
        analysis = analyze_point_location(mock_world_data, central_point)
        assert analysis is not None

        # Step 2: If point is inside a country, generate random points there
        if analysis["is_inside_country"]:
            country_name = analysis["containing_country"]
            country = get_country_polygon(mock_world_data, country_name)

            if country is not None:
                random_points = generate_random_points_in_polygon(country, 3)

                if random_points is not None:
                    # Step 3: Analyze each random point
                    for _, row in random_points.iterrows():
                        point_analysis = analyze_point_location(
                            mock_world_data, (row.geometry.x, row.geometry.y)
                        )

                        # All points should be in the same country
                        assert point_analysis["containing_country"] == country_name

    def test_performance_workflow(self, mock_world_data):
        """Test that the workflow performs reasonably with multiple operations."""
        import time

        start_time = time.time()

        # Perform multiple operations
        for i in range(3):  # Reduced for test performance
            # Get different countries
            countries = ["United States", "Canada", "United Kingdom"]
            if i < len(countries):
                country = get_country_polygon(mock_world_data, countries[i])
                if country is not None:
                    # Generate a few points
                    points = generate_random_points_in_polygon(country, 2)

                    if points is not None:
                        # Analyze one point
                        first_point = points.iloc[0].geometry
                        analysis = analyze_point_location(
                            mock_world_data, (first_point.x, first_point.y)
                        )
                        assert analysis is not None

        end_time = time.time()

        # Should complete within reasonable time (adjust as needed)
        assert (end_time - start_time) < 10  # 10 seconds max

    def test_module_interdependencies(self, mock_world_data):
        """Test that modules work correctly together."""
        # Test the dependency chain: map_fetcher -> country_analysis -> closest_country

        # 1. Country analysis depends on map data
        country = get_country_polygon(mock_world_data, "United States")
        assert country is not None

        # 2. Closest country analysis depends on map data and works with points
        test_point = (0, 0)
        closest = find_closest_country_to_point(mock_world_data, test_point)
        assert closest is not None

        # 3. Point generation depends on country polygon
        points = generate_random_points_in_polygon(country, 2)

        # 4. Verify generated points work with closest country analysis
        if points is not None and len(points) > 0:
            first_point = points.iloc[0].geometry
            analysis = analyze_point_location(
                mock_world_data, (first_point.x, first_point.y)
            )
            assert analysis is not None
            assert (
                analysis["is_inside_country"] is True
            )  # Should be inside original country
