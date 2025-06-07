import os
import tempfile

import geopandas as gpd
import pytest
from shapely.geometry import Polygon

# Set environment variable to hide plots during testing
os.environ["HIDE_PLOTS"] = "1"


@pytest.fixture
def sample_world_map():
    """Create a simple sample world map for testing."""
    # Create a simple world map with a few test countries
    data = {
        "NAME": ["TestCountryA", "TestCountryB", "TestCountryC"],
        "geometry": [
            Polygon(
                [(-10, -10), (-10, 10), (10, 10), (10, -10), (-10, -10)]
            ),  # Large square
            Polygon([(20, 20), (20, 30), (30, 30), (30, 20), (20, 20)]),  # Small square
            Polygon([(-50, -5), (-40, -5), (-40, 5), (-50, 5), (-50, -5)]),  # Rectangle
        ],
    }
    return gpd.GeoDataFrame(data, crs="EPSG:4326")


@pytest.fixture
def sample_country():
    """Create a sample country polygon for testing."""
    data = {
        "NAME": ["SampleCountry"],
        "geometry": [Polygon([(-5, -5), (-5, 5), (5, 5), (5, -5), (-5, -5)])],
    }
    return gpd.GeoDataFrame(data, crs="EPSG:4326")


@pytest.fixture
def test_points():
    """Create test points for closest country analysis."""
    return [
        (0, 0),  # Inside TestCountryA
        (25, 25),  # Inside TestCountryB
        (-45, 0),  # Inside TestCountryC
        (100, 100),  # Far from all countries
        (15, 15),  # Between countries
    ]


@pytest.fixture
def temp_file():
    """Create a temporary file for testing file operations."""
    fd, path = tempfile.mkstemp(suffix=".geojson")
    os.close(fd)
    yield path
    # Cleanup
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def mock_world_data():
    """Create mock world map data matching realistic structure."""
    countries = [
        "United States",
        "Canada",
        "Mexico",
        "Brazil",
        "Argentina",
        "United Kingdom",
        "France",
        "Germany",
        "Spain",
        "Italy",
        "Russia",
        "China",
        "Japan",
        "India",
        "Australia",
    ]

    geometries = []
    for i, country in enumerate(countries):
        # Create simple rectangular polygons at different locations
        x_offset = (i % 5) * 40 - 100  # Spread across longitude
        y_offset = (i // 5) * 30 - 45  # Spread across latitude

        poly = Polygon(
            [
                (x_offset, y_offset),
                (x_offset + 20, y_offset),
                (x_offset + 20, y_offset + 20),
                (x_offset, y_offset + 20),
                (x_offset, y_offset),
            ]
        )
        geometries.append(poly)

    data = {"NAME": countries, "geometry": geometries}
    return gpd.GeoDataFrame(data, crs="EPSG:4326")
