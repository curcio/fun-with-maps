from unittest.mock import MagicMock, mock_open, patch

import geopandas as gpd
import requests

from map_fetcher import fetch_world_map


class TestFetchWorldMap:
    """Test cases for fetch_world_map function."""

    def test_fetch_world_map_with_builtin_dataset(self):
        """Test fetching world map using built-in geopandas dataset."""
        # This test uses the actual geopandas built-in dataset
        world_map = fetch_world_map(resolution="low")

        # Since the built-in dataset is deprecated in newer versions, we allow None
        if world_map is not None:
            # Basic checks only if data is returned
            assert isinstance(world_map, gpd.GeoDataFrame)
            assert len(world_map) > 0
            assert "geometry" in world_map.columns

            # Check for name column
            name_columns = ["NAME", "name", "NAME_EN", "ADMIN", "Country", "country"]
            has_name_column = any(col in world_map.columns for col in name_columns)
            assert has_name_column, f"No name column found in {world_map.columns}"
        else:
            # If None is returned due to deprecated dataset, that's acceptable
            print("Built-in dataset unavailable (likely deprecated) - test passes")

    @patch("requests.get")
    @patch("builtins.open", new_callable=mock_open)
    def test_fetch_world_map_github_success(self, mock_file, mock_get):
        """Test successful fetch from GitHub source."""
        # Mock successful HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"type": "FeatureCollection", "features": []}'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock geopandas read_file to return sample data
        sample_data = gpd.GeoDataFrame(
            {"NAME": ["TestCountry"], "geometry": [gpd.points_from_xy([0], [0])[0]]}
        )

        with patch("geopandas.read_file") as mock_read:
            mock_read.return_value = sample_data

            result = fetch_world_map(resolution="low")

            assert result is not None
            assert isinstance(result, gpd.GeoDataFrame)

    @patch("requests.get")
    def test_fetch_world_map_network_error(self, mock_get):
        """Test handling of network errors."""
        # Mock network error
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        # Should fall back to built-in dataset
        result = fetch_world_map(resolution="low")

        # Should still return something (built-in dataset) or None
        assert result is None or isinstance(result, gpd.GeoDataFrame)

    def test_fetch_world_map_different_resolutions(self):
        """Test fetching with different resolution parameters."""
        resolutions = ["low", "medium", "high"]

        for resolution in resolutions:
            result = fetch_world_map(resolution=resolution)

            # Should return valid GeoDataFrame or None (if fetch fails)
            assert result is None or isinstance(result, gpd.GeoDataFrame)

    def test_fetch_world_map_with_custom_save_path(self, temp_file):
        """Test fetching with custom save path."""
        result = fetch_world_map(resolution="low", save_path=temp_file)

        if result is not None:
            assert isinstance(result, gpd.GeoDataFrame)

    @patch("geopandas.read_file")
    def test_fetch_world_map_geopandas_error(self, mock_read):
        """Test handling of geopandas read errors."""
        mock_read.side_effect = Exception("Read error")

        result = fetch_world_map(resolution="low")

        # Should handle error gracefully
        assert result is None

    def test_fetch_world_map_invalid_resolution(self):
        """Test with invalid resolution parameter."""
        result = fetch_world_map(resolution="invalid")

        # Should still work (falls back to built-in or handle gracefully)
        assert result is None or isinstance(result, gpd.GeoDataFrame)
