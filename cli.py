#!/usr/bin/env python3
"""
CLI application for geographic data operations.
"""

import csv
import sys
from io import StringIO

import click

from voronoi_analysis import get_admin1_capitals


@click.group()
def cli():
    """Geographic data CLI tool."""
    pass


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
