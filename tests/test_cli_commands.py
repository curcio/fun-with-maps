from unittest.mock import patch

from click.testing import CliRunner

from scripts.cli import cli


def test_list_countries_command(mock_world_data):
    runner = CliRunner()
    with patch("scripts.cli.fetch_world_map") as mock_fetch:
        mock_fetch.return_value = mock_world_data
        result = runner.invoke(cli, ["list-countries"])
        assert result.exit_code == 0
        for country in mock_world_data["NAME"]:
            assert country in result.output


def test_closest_countries_command(mock_world_data):
    runner = CliRunner()
    with patch("scripts.cli.fetch_world_map") as mock_fetch, patch(
        "scripts.cli.get_country_polygon"
    ) as mock_get_polygon, patch(
        "scripts.cli.find_multiple_closest_countries"
    ) as mock_find:
        mock_fetch.return_value = mock_world_data
        mock_polygon = mock_world_data.iloc[[0]]
        mock_get_polygon.return_value = mock_polygon
        mock_find.return_value = [("A", 0.0), ("B", 1.0), ("C", 2.0)]

        result = runner.invoke(cli, ["closest-countries", "TestCountryA", "--n", "2"])
        assert result.exit_code == 0
        assert "B" in result.output
        assert "C" in result.output
