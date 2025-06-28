from unittest.mock import patch

import geopandas as gpd
from click.testing import CliRunner

from fun_with_maps.cli import cli


def run_cli(args):
    runner = CliRunner()
    return runner.invoke(cli, args)


def test_cli_help_runs():
    result = run_cli(["--help"])
    assert result.exit_code == 0
    assert "Geographic data CLI tool" in result.output


@patch("fun_with_maps.cli.fetch_world_map")
def test_fetch_world_map_command(mock_fetch, tmp_path):
    mock_fetch.return_value = gpd.GeoDataFrame({"geometry": []})
    output = tmp_path / "map.geojson"
    result = run_cli(["fetch-world-map", "--output", str(output)])
    assert result.exit_code == 0
    mock_fetch.assert_called_once()
    assert output.exists() or "Failed" not in result.output
