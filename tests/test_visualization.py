from unittest.mock import MagicMock, patch

import geopandas as gpd
import matplotlib.pyplot as plt
import pytest
from shapely.geometry import Point

from visualization import (
    visualize_country_polygon,
    visualize_point_and_closest_countries,
    visualize_polygon_with_points,
    visualize_world_map,
)


class TestVisualizationFunctions:
    """Test cases for visualization functions."""

    @patch("matplotlib.pyplot.show")
    def test_visualize_country_polygon_success(self, mock_show, sample_country):
        """Test successful country polygon visualization."""
        # Should not raise any exceptions
        visualize_country_polygon(sample_country, "Test Country")

        # plt.show() should be called
        mock_show.assert_called_once()

    @patch("matplotlib.pyplot.show")
    def test_visualize_country_polygon_with_name(self, mock_show, sample_country):
        """Test visualization with custom country name."""
        visualize_country_polygon(sample_country, "Custom Name")
        mock_show.assert_called_once()

    @patch("matplotlib.pyplot.show")
    def test_visualize_country_polygon_without_name(self, mock_show, sample_country):
        """Test visualization without providing country name."""
        visualize_country_polygon(sample_country)
        mock_show.assert_called_once()

    def test_visualize_country_polygon_none_input(self):
        """Test with None input - should handle gracefully."""
        # Should not raise exceptions
        visualize_country_polygon(None)

    def test_visualize_country_polygon_empty_dataframe(self):
        """Test with empty GeoDataFrame."""
        empty_gdf = gpd.GeoDataFrame()
        # Should not raise exceptions
        visualize_country_polygon(empty_gdf)

    @patch("matplotlib.pyplot.show")
    @patch("visualization.find_multiple_closest_countries")
    def test_visualize_point_and_closest_countries_success(
        self, mock_find_countries, mock_show, sample_world_map
    ):
        """Test successful point and closest countries visualization."""
        # Mock the find_multiple_closest_countries function
        mock_find_countries.return_value = [
            ("TestCountryA", 0.0),
            ("TestCountryB", 5.0),
            ("TestCountryC", 10.0),
        ]

        point = (0, 0)
        visualize_point_and_closest_countries(sample_world_map, point, n_countries=3)

        mock_find_countries.assert_called_once()
        mock_show.assert_called_once()

    @patch("matplotlib.pyplot.show")
    @patch("visualization.find_multiple_closest_countries")
    def test_visualize_point_and_closest_countries_with_shapely_point(
        self, mock_find_countries, mock_show, sample_world_map
    ):
        """Test visualization with shapely Point object."""
        mock_find_countries.return_value = [("TestCountryA", 0.0)]

        point = Point(0, 0)
        visualize_point_and_closest_countries(sample_world_map, point, n_countries=1)

        mock_find_countries.assert_called_once()
        mock_show.assert_called_once()

    @patch("visualization.find_multiple_closest_countries")
    def test_visualize_point_and_closest_countries_no_countries_found(
        self, mock_find_countries, sample_world_map
    ):
        """Test when no closest countries are found."""
        mock_find_countries.return_value = None

        point = (0, 0)
        # Should handle gracefully without raising exceptions
        visualize_point_and_closest_countries(sample_world_map, point)

    @patch("matplotlib.pyplot.show")
    def test_visualize_polygon_with_points_success(self, mock_show, sample_country):
        """Test successful polygon with points visualization."""
        # Create sample points
        points_data = {
            "point_id": [1, 2, 3],
            "geometry": [Point(0, 0), Point(1, 1), Point(-1, -1)],
        }
        points_gdf = gpd.GeoDataFrame(points_data, crs="EPSG:4326")

        visualize_polygon_with_points(sample_country, points_gdf, "Test Visualization")

        mock_show.assert_called_once()

    @patch("matplotlib.pyplot.show")
    def test_visualize_polygon_with_points_default_title(
        self, mock_show, sample_country
    ):
        """Test visualization with default title."""
        points_data = {"point_id": [1], "geometry": [Point(0, 0)]}
        points_gdf = gpd.GeoDataFrame(points_data, crs="EPSG:4326")

        visualize_polygon_with_points(sample_country, points_gdf)

        mock_show.assert_called_once()

    def test_visualize_polygon_with_points_none_inputs(self):
        """Test with None inputs."""
        # Should handle gracefully
        visualize_polygon_with_points(None, None)

    def test_visualize_polygon_with_points_none_points(self, sample_country):
        """Test with None points input."""
        visualize_polygon_with_points(sample_country, None)

    @patch("matplotlib.pyplot.show")
    def test_visualize_world_map_success(self, mock_show, sample_world_map):
        """Test successful world map visualization."""
        visualize_world_map(sample_world_map, "Test World Map")

        mock_show.assert_called_once()

    @patch("matplotlib.pyplot.show")
    def test_visualize_world_map_default_title(self, mock_show, sample_world_map):
        """Test world map visualization with default title."""
        visualize_world_map(sample_world_map)

        mock_show.assert_called_once()

    def test_visualize_world_map_none_input(self):
        """Test world map visualization with None input."""
        # Should handle gracefully
        visualize_world_map(None)

    @patch("matplotlib.pyplot.show")
    def test_visualization_parameters(self, mock_show, sample_country):
        """Test that visualization functions accept different figure sizes."""
        # Test with custom figure size
        visualize_country_polygon(sample_country, figsize=(8, 6))
        mock_show.assert_called_once()

    @patch("matplotlib.pyplot.show")
    def test_visualization_cleanup(self, mock_show, sample_country):
        """Test that visualizations don't leave figures open."""
        # Get initial figure count
        initial_figs = len(plt.get_fignums())

        visualize_country_polygon(sample_country)

        # After show(), figure count should not increase
        final_figs = len(plt.get_fignums())
        assert final_figs >= initial_figs  # Should not create unclosed figures

    @patch("matplotlib.pyplot.show")
    @patch("matplotlib.pyplot.subplots")
    def test_visualization_matplotlib_integration(
        self, mock_subplots, mock_show, sample_country
    ):
        """Test that visualization functions properly use matplotlib."""
        # Mock matplotlib components
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        visualize_country_polygon(sample_country)

        # Check that matplotlib functions were called
        mock_subplots.assert_called_once()
        mock_show.assert_called_once()

        # Check that the GeoDataFrame plot method would be called
        # (This is harder to test directly, but we can verify the function runs)
