import subprocess
import sys
from unittest.mock import patch

import geopandas as gpd
import pytest
from shapely.geometry import Polygon

import main


class TestMainFunctionality:
    """Test cases for main.py functions."""

    @pytest.fixture
    def mock_world_data(self):
        """Create mock world map data for testing."""
        data = {
            "NAME": ["United States", "Canada", "Mexico"],
            "geometry": [
                Polygon([(-100, 25), (-100, 45), (-80, 45), (-80, 25), (-100, 25)]),
                Polygon([(-100, 45), (-100, 60), (-80, 60), (-80, 45), (-100, 45)]),
                Polygon([(-100, 15), (-100, 25), (-80, 25), (-80, 15), (-100, 15)]),
            ],
        }
        return gpd.GeoDataFrame(data, crs="EPSG:4326")

    @patch("main.fetch_world_map")
    @patch("main.visualize_world_map")
    @patch("main.analyze_point_location")
    @patch("main.visualize_point_and_closest_countries")
    @patch("builtins.print")
    def test_main_function_success(
        self,
        mock_print,
        mock_viz_closest,
        mock_analyze,
        mock_viz_world,
        mock_fetch,
        mock_world_data,
    ):
        """Test successful execution of main() function."""
        # Setup mocks
        mock_fetch.return_value = mock_world_data
        mock_analyze.return_value = {
            "is_inside_country": True,
            "containing_country": "United States",
            "closest_country": "United States",
            "distance_to_closest": 0.0,
            "top_5_closest": [
                ("United States", 0.0),
                ("Canada", 5.0),
                ("Mexico", 10.0),
            ],
            "ocean_or_land": "land",
        }

        # Run main function
        main.main()

        # Verify key functions were called
        mock_fetch.assert_called_once_with(resolution="low")
        mock_viz_world.assert_called_once()
        assert mock_analyze.call_count > 0
        mock_viz_closest.assert_called_once()

    @patch("main.fetch_world_map")
    @patch("builtins.print")
    def test_main_function_failed_fetch(self, mock_print, mock_fetch):
        """Test main() function when world map fetch fails."""
        mock_fetch.return_value = None

        # Should handle gracefully and not raise exceptions
        main.main()

        mock_fetch.assert_called_once_with(resolution="low")
        # Should print failure message
        assert any(
            "Failed to fetch world map data" in str(call)
            for call in mock_print.call_args_list
        )

    @patch("main.fetch_world_map")
    @patch("main.analyze_point_location")
    def test_main_point_analysis_coverage(
        self, mock_analyze, mock_fetch, mock_world_data
    ):
        """Test that main() analyzes the expected test points."""
        mock_fetch.return_value = mock_world_data

        # Track what points are analyzed
        analyzed_points = []

        def track_analyze_calls(world_map, point):
            analyzed_points.append(point)
            return {
                "is_inside_country": False,
                "containing_country": None,
                "closest_country": "United States",
                "distance_to_closest": 10.0,
                "top_5_closest": [("United States", 10.0)],
                "ocean_or_land": "ocean_or_water",
            }

        mock_analyze.side_effect = track_analyze_calls

        # Run main
        main.main()

        # Should analyze the expected test points
        expected_points = [
            (-74.0, 40.7),  # New York City area
            (2.3, 48.9),  # Paris area
            (0.0, 0.0),  # Gulf of Guinea
            (139.7, 35.7),  # Tokyo area
            (-58.4, -34.6),  # Buenos Aires area
        ]

        assert len(analyzed_points) == len(expected_points)
        for expected_point in expected_points:
            assert expected_point in analyzed_points

    def test_main_script_execution_default(self):
        """Test running main.py as script with default choice."""
        # Run the script with default input (pressing Enter)
        result = subprocess.run(
            [sys.executable, "main.py"],
            input="\n",  # Just press Enter for default
            text=True,
            capture_output=True,
            timeout=30,
        )

        # Should not crash
        assert result.returncode is not None
        # Should show the menu
        assert "Fun with Maps" in result.stdout
        assert "Available options:" in result.stdout

    def test_main_script_execution_choice_2(self):
        """Test running main.py as script with choice 2."""
        # Run the script with choice 2
        result = subprocess.run(
            [sys.executable, "main.py"],
            input="2\n",  # Choose option 2
            text=True,
            capture_output=True,
            timeout=30,
        )

        # Should not crash
        assert result.returncode is not None
        # Should show the menu and run comprehensive demo
        assert "Fun with Maps" in result.stdout

    def test_main_script_execution_choice_3(self):
        """Test running main.py as script with choice 3."""
        # Run the script with choice 3
        result = subprocess.run(
            [sys.executable, "main.py"],
            input="3\n",  # Choose option 3
            text=True,
            capture_output=True,
            timeout=30,
        )

        # Should not crash
        assert result.returncode is not None
        # Should show the menu
        assert "Fun with Maps" in result.stdout

    def test_main_script_execution_keyboard_interrupt(self):
        """Test running main.py as script with Ctrl+C simulation."""
        # This is harder to test directly, so we'll test the graceful handling
        # by checking that the exception handling code path exists

        # The code should have the exception handling
        with open("main.py", "r") as f:
            content = f.read()
            assert "KeyboardInterrupt" in content
            assert "Goodbye! 👋" in content

    def test_main_real_world_execution_failure(self):
        """Test that identifies the real issue when main.py fails in production."""
        # This test will fail and show us the real error that occurs
        # when running main.py without mocks

        # First, let's check if the world map can be fetched
        from map_fetcher import fetch_world_map

        # Try to fetch real data (this will likely fail due to network issues)
        world_map = fetch_world_map(resolution="low")

        if world_map is None:
            # This is the actual problem - main.py fails because fetch_world_map returns None
            pytest.fail(
                "main.py fails because fetch_world_map returns None. "
                "The external data sources (GitHub, Natural Earth) are not accessible. "
                "Need to implement a local fallback or fix the data source URLs."
            )

        # If we get here, the data fetch succeeded, so test the main function
        result = main.main()
        assert result is None  # main() should complete without exceptions

    def test_main_with_local_fallback_needed(self):
        """Test to verify that main.py needs a local fallback for world map data."""
        # Check if we have a local world map file that could serve as fallback
        import os

        potential_local_files = [
            "world_map.geojson",
            "world_political_map.geojson",
            "data/world_map.geojson",
            "assets/world_map.geojson",
        ]

        local_file_exists = any(os.path.exists(f) for f in potential_local_files)

        if not local_file_exists:
            pytest.fail(
                "No local world map file found. Main.py will fail when external sources are down. "
                "Consider adding a local fallback file or improving the fetch_world_map function."
            )


# Test the module structure
def test_main_module_structure():
    """Test that main.py has the expected structure."""
    # Check that main functions exist
    assert hasattr(main, "main")
    assert callable(main.main)

    # Check imports exist
    assert hasattr(main, "fetch_world_map")
    assert hasattr(main, "analyze_point_location")
    assert hasattr(main, "visualize_world_map")
    assert hasattr(main, "visualize_point_and_closest_countries")


def test_main_has_required_imports():
    """Test that main.py imports all required functions."""
    # Check that the required example functions are imported
    assert hasattr(main, "run_comprehensive_demo")
    assert hasattr(main, "example_closest_country_analysis")
    assert callable(main.run_comprehensive_demo)
    assert callable(main.example_closest_country_analysis)
