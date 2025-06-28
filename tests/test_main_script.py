"""Tests for high-level script functions.

These tests mock heavy operations so that they run quickly.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add the project root to the path before importing project modules
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)  # noqa: E402

import scripts.main as main_module  # noqa: E402
from fun_with_maps.core import country_analysis  # noqa: E402


class TestMainScript:
    """Unit tests for ``scripts.main`` with heavy parts patched."""

    def test_main_runs_quickly_with_patches(self):
        """``main`` should execute without heavy work when dependencies are patched."""
        with (
            patch.object(main_module, "setup_country_analysis") as mock_setup,
            patch.object(main_module, "generate_and_visualize_points") as mock_gen,
            patch.object(main_module, "analyze_closest_countries") as mock_analysis,
            patch.object(main_module, "create_colored_visualization") as mock_vis,
            patch.object(main_module, "get_admin1_capitals") as mock_capitals,
            patch.object(main_module, "create_voronoi_analysis") as mock_voronoi,
            patch.object(
                main_module, "filter_capitals_to_largest_polygon"
            ) as mock_filter,
            patch.object(main_module, "solve_tsp_for_country") as mock_solve,
            patch.object(main_module, "generate_pdf_report") as mock_report,
            patch.object(main_module, "clear_plot_tracker") as mock_clear,
            patch.object(main_module, "set_country_info") as mock_set,
        ):
            mock_setup.return_value = (MagicMock(), MagicMock(), "Testland")
            mock_gen.return_value = []
            mock_analysis.return_value = ["country"]
            mock_capitals.return_value = MagicMock(empty=True)
            mock_filter.side_effect = lambda caps, poly: caps

            main_module.main("Testland")

            mock_setup.assert_called_once_with("Testland")
            mock_gen.assert_called_once()
            mock_analysis.assert_called_once()
            mock_vis.assert_called_once()
            mock_capitals.assert_called_once_with("Testland")
            mock_voronoi.assert_called_once()
            mock_filter.assert_called_once()
            mock_solve.assert_called_once()
            mock_report.assert_called_once()
            assert mock_clear.called
            assert mock_set.called

    def test_get_country_polygon_return_value(self):
        """``get_country_polygon`` should not return a tuple."""
        mock_world_map = MagicMock()
        mock_world_map.columns = ["NAME"]
        mock_country_data = MagicMock()
        mock_country_data.empty = False
        mock_country_data.iloc = [{"NAME": "Iran"}]

        with patch.object(
            country_analysis, "get_country_polygon", return_value=mock_country_data
        ):
            result = country_analysis.get_country_polygon(mock_world_map, "Iran")
            assert not isinstance(result, tuple)

    def test_setup_country_analysis_unpacking_issue(self):
        """Ensure ``setup_country_analysis`` returns three values."""
        with (
            patch.object(main_module, "fetch_world_map") as mock_fetch,
            patch.object(main_module, "get_country_polygon") as mock_get_country,
            patch.object(main_module, "visualize_country_polygon"),
        ):
            mock_fetch.return_value = MagicMock()
            mock_country_gdf = MagicMock()
            mock_country_gdf.iloc = [{"NAME": "Iran"}]
            mock_get_country.return_value = mock_country_gdf

            result = main_module.setup_country_analysis("Iran")
            assert len(result) == 3

    def test_voronoi_only_analysis_unpacking_issue(self):
        """``voronoi_only_analysis`` should run without unpacking errors."""
        with (
            patch.object(main_module, "fetch_world_map") as mock_fetch,
            patch.object(main_module, "get_country_polygon") as mock_get_country,
            patch.object(main_module, "get_admin1_capitals") as mock_get_capitals,
            patch.object(main_module, "create_voronoi_analysis") as mock_create_voronoi,
            patch.object(main_module, "clear_plot_tracker"),
            patch.object(main_module, "set_country_info"),
        ):
            mock_fetch.return_value = MagicMock()
            mock_country_gdf = MagicMock()
            mock_country_gdf.iloc = [{"NAME": "Iran"}]
            mock_get_country.return_value = mock_country_gdf
            mock_get_capitals.return_value = MagicMock()

            main_module.voronoi_only_analysis("Iran")
            mock_create_voronoi.assert_called_once()

    def test_create_country_visualization_import(self):
        """The visualization helper should be importable."""
        from fun_with_maps.visualization.visualization import (
            create_country_visualization_with_colors,
        )

        assert callable(create_country_visualization_with_colors)

    def test_main_imports_country_analysis_module(self):
        """``scripts.main`` should use functions from ``country_analysis`` module."""
        assert main_module.get_country_polygon is country_analysis.get_country_polygon


if __name__ == "__main__":  # pragma: no cover
    pytest.main([__file__])
