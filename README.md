# Fun with Maps 🌍

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A comprehensive, modular geospatial analysis toolkit for working with world maps.
It ships with a command line interface as well as a small FastAPI backend used by
the included web game.

## Features

- 📊 **Fetch World Map Data**: Download world political maps at different resolutions
- 🗺️ **Country Analysis**: Extract and analyze specific country polygons
- 📍 **Closest Country Detection**: Find the closest countries to any geographic point
- 🎯 **Random Point Generation**: Generate random points within country polygons
- 🔍 **Voronoi Analysis**: Create Voronoi diagrams and analyze geographic regions
- 🧭 **TSP Solving**: Solve traveling salesman problems for geographic points
- 📈 **Rich Visualizations**: Create beautiful maps and charts
- 🔧 **Modular Design**: Clean, organized code structure for easy extension

## Installation

### From Source

1. Clone this repository:
```bash
git clone https://github.com/your-username/fun-with-maps.git
cd fun-with-maps
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. (Optional) Install the CLI in editable mode:
```bash
pip install -e .
```

### Development Installation

For development with additional tools:
```bash
pip install -r requirements.txt -r requirements-dev.txt
pip install -e .
pre-commit install
```

### Installing with uv

[uv](https://github.com/astral-sh/uv) is a drop-in replacement for `pip` that
speeds up dependency installation. Once `uv` itself is installed you can install
the project requirements with:

```bash
pip install uv  # one-time installation
./scripts/install_with_uv.sh
```

For development dependencies use:

```bash
./scripts/install_with_uv.sh -r requirements-dev.txt -e .
pre-commit install
```

## Quick Start

### Using the Command Line Interface

After installing with `pip install -e .`, the ``fun-with-maps-cli`` command
provides access to all features. You can still run the interactive script with
``python scripts/main.py`` if desired.

```bash
# Show available commands
fun-with-maps-cli --help

# Download the world map
fun-with-maps-cli fetch-world-map --output world.geojson

# List countries from a map file
fun-with-maps-cli list-countries world.geojson

# Retrieve admin‑1 capitals
fun-with-maps-cli get-admin1-capitals "Argentina"
```

### Running the Backend Service with Docker

The repository ships with a `Dockerfile` and a simple `docker-compose.yml`
configuration. These run the FastAPI server automatically so you don't need to
invoke `uvicorn` yourself. Start the service with:

```bash
docker-compose up --build
```

This builds the image (if necessary) and launches the web game at
<http://localhost:8000>.

If you prefer plain Docker, you can achieve the same result with:

```bash
docker build -t fun-with-maps .
docker run -p 8000:8000 fun-with-maps
```

Open the URL above to play the game.

### Using as a Python Package

```python
from fun_with_maps import fetch_world_map, get_country_polygon, generate_random_points_in_polygon

# Fetch world map data (1:10m scale by default)
world_map = fetch_world_map()

# Get a specific country
country_polygon = get_country_polygon(world_map, "France")

# Generate random points within the country
points = generate_random_points_in_polygon(country_polygon, 100)
```

## Testing

This project includes comprehensive test coverage using pytest. To run the tests:

### Install Test Dependencies

Test dependencies are listed in `requirements-dev.txt`:

```bash
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov

# Run only unit tests (excluding integration tests)
pytest -m "not integration"

# Run only integration tests
pytest -m integration
```

### Test Structure

- `tests/test_map_fetcher.py` - Tests for world map fetching functionality
- `tests/test_country_analysis.py` - Tests for country polygon extraction and analysis
- `tests/test_closest_country.py` - Tests for closest country detection
- `tests/test_point_generation.py` - Tests for random point generation
- `tests/test_visualization.py` - Tests for visualization functions
- `tests/test_examples.py` - Tests for example and demo functions
- `tests/test_integration.py` - Integration tests for complete workflows
- `tests/conftest.py` - Shared test fixtures and configuration

### Test Coverage

The tests cover:
- ✅ **Unit Tests**: Individual function testing with mocked dependencies
- ✅ **Integration Tests**: End-to-end workflow testing
- ✅ **Error Handling**: Graceful handling of edge cases and failures
- ✅ **Data Validation**: Input/output validation and type checking
- ✅ **Performance Tests**: Basic performance validation

## Project Structure

```
fun-with-maps/
├── fun_with_maps/              # Main package
│   ├── core/                   # Core functionality
│   │   ├── map_fetcher.py      # World map data fetching
│   │   ├── country_analysis.py # Country polygon extraction
│   │   ├── closest_country.py  # Find closest countries
│   │   ├── point_generation.py # Generate random points
│   │   └── country_selector.py # Country selection utilities
│   ├── analysis/               # Analysis algorithms
│   │   ├── voronoi_analysis.py # Voronoi diagram generation
│   │   ├── tsp_solver.py       # Traveling salesman solver
│   │   ├── data_processing.py  # Data processing utilities
│   │   └── parallel_processing.py # Parallel processing tools
│   ├── visualization/          # Visualization tools
│   │   ├── visualization.py    # General visualization functions
│   │   └── voronoi_visualization.py # Voronoi-specific plots
│   └── utils/                  # Utility functions
│       └── utils.py            # Helper utilities
├── scripts/                    # Entry point scripts
│   ├── main.py                 # Main interactive script
│   ├── cli.py                  # Command-line interface
│   └── diagnose_voronoi.py     # Diagnostic utilities
├── examples/                   # Example code
│   └── examples.py             # Usage examples
├── tests/                      # Test suite
├── output/                     # Generated outputs (gitignored)
│   ├── reports/                # PDF reports
│   ├── images/                 # Generated images
│   └── data/                   # Downloaded data
└── docs/                       # Documentation (future)
```

## API Reference

### Core Functions

```python
# Map fetching
from fun_with_maps.core.map_fetcher import fetch_world_map
world_map = fetch_world_map(resolution="medium")

# Country analysis
from fun_with_maps.core.country_analysis import get_country_polygon
country = get_country_polygon(world_map, "Germany")

# Point generation
from fun_with_maps.core.point_generation import generate_random_points_in_polygon
points = generate_random_points_in_polygon(country, count=1000)

# Closest country detection
from fun_with_maps.core.closest_country import find_closest_countries
closest = find_closest_countries(world_map, points)
```

### Analysis Functions

```python
# Voronoi analysis
from fun_with_maps.analysis.voronoi_analysis import get_admin1_capitals
capitals = get_admin1_capitals("France")

# TSP solving
from fun_with_maps.analysis.tsp_solver import solve_tsp
tour, cost = solve_tsp(capitals)
```

### Visualization Functions

```python
# Basic visualization
from fun_with_maps.visualization.visualization import visualize_country_polygon
visualize_country_polygon(country, "Germany")

# Voronoi visualization
from fun_with_maps.visualization.voronoi_visualization import display_voronoi_diagram
display_voronoi_diagram(country, capitals, "Germany")
```
