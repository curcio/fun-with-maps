#!/usr/bin/env python3
# flake8: noqa
"""
CLI application for geographic data operations.
"""

import csv
import os
import sys
from io import StringIO

import click

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)  # noqa: E402
from fun_with_maps.analysis.voronoi_analysis import get_admin1_capitals
from fun_with_maps.core.closest_country import find_multiple_closest_countries
from fun_with_maps.core.country_analysis import (
    get_available_countries,
    get_country_polygon,
)
from fun_with_maps.core.map_fetcher import fetch_world_map


@click.group()
def cli():
    """Geographic data CLI tool."""
    pass


@cli.command("list-countries")
def list_countries_cmd():
    """List all available countries."""
    world_map = fetch_world_map(resolution="low")
    if world_map is None:
        click.echo("Failed to load world map", err=True)
        sys.exit(1)

    countries = get_available_countries(world_map) or []
    for name in countries:
        click.echo(name)


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


@cli.command("closest-countries")
@click.argument("country")
@click.option("--n", default=5, help="Number of closest countries to return")
def closest_countries_cmd(country, n):
    """Return the n closest countries to the given country."""
    try:
        world_map = fetch_world_map(resolution="low")
        if world_map is None:
            click.echo("Failed to load world map", err=True)
            sys.exit(1)

        country_polygon = get_country_polygon(world_map, country)
        if country_polygon is None or country_polygon.empty:
            click.echo(f"The country '{country}' was not found", err=True)
            sys.exit(1)

        centroid = country_polygon.geometry.iloc[0].centroid
        results = find_multiple_closest_countries(
            world_map, centroid, n_countries=n + 1
        )
        if not results:
            click.echo("No closest countries found", err=True)
            sys.exit(1)

        # Skip the first result (selected country) if more than n results
        if len(results) > n:
            results = results[1:]

        filtered = [name for name, _ in results if name.lower() != country.lower()]
        for name in filtered[:n]:
            click.echo(name)

    except Exception as e:
        click.echo(f"Error processing request: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
