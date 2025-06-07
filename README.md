# Fun with Maps 🌍

A comprehensive, modular geospatial analysis toolkit for working with world maps, finding closest countries to points, analyzing polygons, and generating random geographic points.

## Features

- 📊 **Fetch World Map Data**: Download world political maps at different resolutions
- 🗺️ **Country Analysis**: Extract and analyze specific country polygons
- 📍 **Closest Country Detection**: Find the closest countries to any geographic point
- 🎯 **Random Point Generation**: Generate random points within country polygons
- 📈 **Rich Visualizations**: Create beautiful maps and charts
- 🔧 **Modular Design**: Clean, organized code structure for easy extension

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Quick Start

Run the main script with an interactive menu:

```bash
python main.py
```

## Testing

This project includes comprehensive test coverage using pytest. To run the tests:

### Install Test Dependencies

Test dependencies are included in `requirements.txt`, but you can install them specifically:

```bash
pip install pytest pytest-cov
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

## Module Structure

- `map_fetcher.py` - World map data fetching functions
- `country_analysis.py` - Country polygon extraction and analysis
- `closest_country.py` - Find closest countries to points
- `point_generation.py` - Generate random points in polygons
- `visualization.py` - All visualization functions
- `examples.py` - Example and demonstration functions
