#!/usr/bin/env python3
"""Command line interface for :mod:`fun_with_maps`."""

from __future__ import annotations

import csv
import json
import os
import sys
from io import StringIO

import click
import geopandas as gpd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fun_with_maps.analysis.tsp_solver import TSPSolver  # noqa: E402
from fun_with_maps.analysis.voronoi_analysis import get_admin1_capitals  # noqa: E402
from fun_with_maps.core.closest_country import (  # noqa: E402
    find_closest_country_to_point,
)
from fun_with_maps.core.country_analysis import (  # noqa: E402
    get_available_countries,
    get_country_info,
    get_country_polygon,
)
from fun_with_maps.core.map_fetcher import fetch_world_map  # noqa: E402
from fun_with_maps.core.point_generation import (  # noqa: E402
    generate_random_points_in_polygon,
)


@click.group()
def cli():
    """Geographic data CLI tool."""
    pass


@cli.command("fetch-world-map")
@click.option("--resolution", default="low", show_default=True, help="Map resolution")
@click.option(
    "--output",
    default="world_map.geojson",
    show_default=True,
    help="File to save map data",
)
def fetch_world_map_cmd(resolution: str, output: str) -> None:
    """Download world map data and save it to ``OUTPUT``."""
    world = fetch_world_map(resolution=resolution, save_path=output)
    if world is None:
        click.echo("Failed to fetch world map", err=True)
        sys.exit(1)
    click.echo(f"Saved map with {len(world)} features to {output}")


@cli.command("list-countries")
@click.argument("map_file", type=click.Path(exists=True))
def list_countries_cmd(map_file: str) -> None:
    """List all countries available in ``MAP_FILE``."""
    world = gpd.read_file(map_file)
    countries = get_available_countries(world)
    for country in countries or []:
        click.echo(country)


@cli.command("country-info")
@click.argument("map_file", type=click.Path(exists=True))
@click.argument("country")
def country_info_cmd(map_file: str, country: str) -> None:
    """Show basic information about ``COUNTRY`` from ``MAP_FILE``."""
    world = gpd.read_file(map_file)
    polygon = get_country_polygon(world, country)
    info = get_country_info(polygon)
    if info is None:
        click.echo(f"Country '{country}' not found", err=True)
        sys.exit(1)
    click.echo(json.dumps(info, indent=2))


@cli.command("closest-country")
@click.argument("map_file", type=click.Path(exists=True))
@click.argument("longitude", type=float)
@click.argument("latitude", type=float)
def closest_country_cmd(map_file: str, longitude: float, latitude: float) -> None:
    """Find the closest country to the given coordinates."""
    world = gpd.read_file(map_file)
    result = find_closest_country_to_point(world, (longitude, latitude))
    if result is None:
        click.echo("Could not determine closest country", err=True)
        sys.exit(1)
    click.echo(result)


@cli.command("generate-points")
@click.argument("map_file", type=click.Path(exists=True))
@click.argument("country")
@click.option(
    "-n", "--num", type=int, default=10, show_default=True, help="Number of points"
)
def generate_points_cmd(map_file: str, country: str, num: int) -> None:
    """Generate random points within ``COUNTRY`` from ``MAP_FILE``."""
    world = gpd.read_file(map_file)
    polygon = get_country_polygon(world, country)
    if polygon is None:
        click.echo(f"Country '{country}' not found", err=True)
        sys.exit(1)
    points = generate_random_points_in_polygon(polygon, num)
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["lon", "lat"])
    for _, row in points.iterrows():
        writer.writerow([row.geometry.x, row.geometry.y])
    click.echo(output.getvalue().strip())


@cli.command("solve-tsp")
@click.argument("points_csv", type=click.Path(exists=True))
def solve_tsp_cmd(points_csv: str) -> None:
    """Solve the traveling salesman problem for coordinates in ``POINTS_CSV``."""
    with open(points_csv, "r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        next(reader, None)  # header
        points = [(float(lon), float(lat)) for lon, lat in reader]
    solver = TSPSolver()
    tour, cost = solver.solve_tsp_ortools(points)
    click.echo(json.dumps({"tour": tour, "cost": cost}, indent=2))


@cli.command("get-admin1-capitals")
@click.argument("country")
def get_admin1_capitals_cmd(country):
    """
    Get admin-1 capital cities for a given country.

    Returns CSV with name, lat, long for each capital city.

    Args:
        COUNTRY: Name of the country to get capitals for
    """
    try:
        # Get the capitals data
        capitals_gdf = get_admin1_capitals(country)

        # Check if any capitals were found
        if capitals_gdf.empty:
            click.echo(f"The country '{country}' was not found", err=True)
            sys.exit(1)

        # Create CSV output
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(["name", "lat", "long"])

        # Write data rows
        for idx, row in capitals_gdf.iterrows():
            name = row.get("NAME", "Unknown")
            lat = row.geometry.y
            long = row.geometry.x
            writer.writerow([name, lat, long])

        # Output the CSV
        click.echo(output.getvalue().strip())

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error processing request: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
