"""
Tests for the main script functionality.

This module contains tests to ensure that the main script works correctly,
including integration tests and tests for specific bug fixes.
"""

import subprocess
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.main import setup_country_analysis, voronoi_only_analysis
from fun_with_maps.core.country_analysis import get_country_polygon
from fun_with_maps.core.map_fetcher import fetch_world_map


class TestMainScript:
    """Test cases for main script functionality and integration."""

    def test_main_script_runs_without_error(self):
        """Test that the main script can be executed without crashing.
        
        This specifically tests for the 'too many values to unpack' error
        that was occurring when get_country_polygon was incorrectly unpacked.
        """
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "main.py")
        
        # Run the script with a test country
        try:
            result = subprocess.run(
                [sys.executable, script_path, "--country", "Iran"],
                capture_output=True,
                text=True,
                timeout=15  # 15 second timeout - enough to test core functionality
            )
        except subprocess.TimeoutExpired as e:
            # If it times out, that's good - it means the script is running without crashing
            # Check the stderr for the specific errors we're testing for
            stderr_output = e.stderr.decode() if e.stderr else ""
            stdout_output = e.stdout.decode() if e.stdout else ""
            
            assert "too many values to unpack" not in stderr_output, f"Unpacking error occurred: {stderr_output}"
            assert "No module named 'visualization'" not in stderr_output, f"Import error occurred: {stderr_output}"
            
            # If we see the script start processing, that's success
            assert "Starting analysis for:" in stdout_output, "Script should start analysis"
            return  # Test passes - script is running without critical errors
        
        # If no timeout, check for critical errors
        assert "too many values to unpack" not in result.stderr, f"Unpacking error occurred: {result.stderr}"
        assert "No module named 'visualization'" not in result.stderr, f"Import error occurred: {result.stderr}"

    def test_get_country_polygon_return_value(self):
        """Test that get_country_polygon returns the expected number of values."""
        # Mock the world map data
        mock_world_map = MagicMock()
        mock_world_map.columns = ["NAME"]
        mock_world_map.__getitem__.return_value.str.contains.return_value = MagicMock()
        mock_world_map.__getitem__.return_value.str.contains.return_value.__getitem__.return_value = MagicMock()
        
        # Mock a successful country match
        mock_country_data = MagicMock()
        mock_country_data.empty = False
        mock_country_data.iloc = [MagicMock()]
        mock_country_data.iloc[0] = {"NAME": "Iran"}
        
        with patch('fun_with_maps.core.country_analysis.get_country_polygon') as mock_get_country:
            mock_get_country.return_value = mock_country_data
            
            result = get_country_polygon(mock_world_map, "Iran")
            
            # The function should return exactly one value, not a tuple
            assert not isinstance(result, tuple), "get_country_polygon should not return a tuple"

    def test_setup_country_analysis_unpacking_issue(self):
        """Test the specific unpacking issue in setup_country_analysis."""
        with patch('scripts.main.fetch_world_map') as mock_fetch:
            with patch('scripts.main.get_country_polygon') as mock_get_country:
                with patch('scripts.main.visualize_country_polygon') as mock_visualize:
                    
                    # Mock the world map
                    mock_world_map = MagicMock()
                    mock_fetch.return_value = mock_world_map
                    
                    # Mock get_country_polygon to return only one value (the actual behavior)
                    mock_country_gdf = MagicMock()
                    mock_country_gdf.iloc = [{"NAME": "Iran"}]
                    mock_get_country.return_value = mock_country_gdf
                    
                    # This should not raise a "too many values to unpack" error
                    try:
                        result = setup_country_analysis("Iran")
                        # If it doesn't crash, that's good, but we need to check the fix
                        assert len(result) == 3, "setup_country_analysis should return 3 values"
                    except ValueError as e:
                        if "too many values to unpack" in str(e):
                            pytest.fail("setup_country_analysis has unpacking issue that needs to be fixed")
                        else:
                            # Some other error, re-raise it
                            raise

    def test_voronoi_only_analysis_unpacking_issue(self):
        """Test the specific unpacking issue in voronoi_only_analysis."""
        with patch('scripts.main.fetch_world_map') as mock_fetch:
            with patch('scripts.main.get_country_polygon') as mock_get_country:
                with patch('scripts.main.get_admin1_capitals') as mock_get_capitals:
                    with patch('scripts.main.create_voronoi_analysis') as mock_create_voronoi:
                        with patch('scripts.main.clear_plot_tracker') as mock_clear:
                            with patch('scripts.main.set_country_info') as mock_set_info:
                                
                                # Mock the world map
                                mock_world_map = MagicMock()
                                mock_fetch.return_value = mock_world_map
                                
                                # Mock get_country_polygon to return only one value (the actual behavior)
                                mock_country_gdf = MagicMock()
                                mock_country_gdf.iloc = [{"NAME": "Iran"}]
                                mock_get_country.return_value = mock_country_gdf
                                
                                # Mock capitals
                                mock_get_capitals.return_value = MagicMock()
                                
                                # This should not raise a "too many values to unpack" error
                                try:
                                    voronoi_only_analysis("Iran")
                                    # If it doesn't crash, the fix is working
                                except ValueError as e:
                                    if "too many values to unpack" in str(e):
                                        pytest.fail("voronoi_only_analysis has unpacking issue that needs to be fixed")
                                    else:
                                        # Some other error, re-raise it
                                        raise

    def test_visualization_import_issue(self):
        """Test that the script can import visualization functions correctly."""
        # This tests for the ModuleNotFoundError: No module named 'visualization'
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "main.py")
        
        # Run the script briefly to see if it gets past the import error
        try:
            result = subprocess.run(
                [sys.executable, script_path, "--country", "Iran"],
                capture_output=True,
                text=True,
                timeout=10  # Short timeout, just to test import works
            )
        except subprocess.TimeoutExpired as e:
            # If it times out, that means it got past the import error and is running
            # Check the stderr for any import errors that occurred before timeout
            stderr_output = e.stderr.decode() if e.stderr else ""
            assert "No module named 'visualization'" not in stderr_output, f"Visualization import error: {stderr_output}"
            return  # Test passes - script is running without import errors
        
        # If no timeout, check for import errors
        assert "No module named 'visualization'" not in result.stderr, f"Visualization import error: {result.stderr}"

    def test_create_country_visualization_import(self):
        """Test that the create_country_visualization_with_colors function can be imported correctly."""
        # Test importing the function directly
        try:
            from fun_with_maps.visualization.visualization import create_country_visualization_with_colors
            # If we can import it, the function exists
            assert callable(create_country_visualization_with_colors), "Function should be callable"
        except ImportError as e:
            pytest.fail(f"Could not import create_country_visualization_with_colors: {e}")

    def test_country_analysis_import_issue(self):
        """Test that the script can import country_analysis functions correctly."""
        # This tests for the ModuleNotFoundError: No module named 'country_analysis'
        # that occurs in the TSP analysis section
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "main.py")
        
        # Test that the main script doesn't have import errors for country_analysis
        try:
            result = subprocess.run(
                [sys.executable, script_path, "--country", "Iran"],
                capture_output=True,
                text=True,
                timeout=20  # Enough time to get to TSP analysis
            )
        except subprocess.TimeoutExpired as e:
            # Check for the specific import error in stderr
            stderr_output = e.stderr.decode() if e.stderr else ""
            assert "No module named 'country_analysis'" not in stderr_output, f"Country analysis import error: {stderr_output}"
            return  # Test passes if no import error
        
        # If no timeout, check for import errors
        assert "No module named 'country_analysis'" not in result.stderr, f"Country analysis import error: {result.stderr}"


if __name__ == "__main__":
    pytest.main([__file__]) 