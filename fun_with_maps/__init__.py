"""
Fun with Maps - A comprehensive geospatial analysis toolkit.

This package provides tools for working with world maps, finding closest countries
to points, analyzing polygons, and generating random geographic points.
"""

__version__ = "1.0.0"
__author__ = "Fun with Maps Team"

# Core imports
from .core.map_fetcher import fetch_world_map
from .core.country_analysis import get_country_polygon, get_available_countries
from .core.point_generation import generate_random_points_in_polygon
from .core.closest_country import find_closest_country_to_point, find_multiple_closest_countries

# Analysis imports
from .analysis.voronoi_analysis import get_admin1_capitals
from .analysis.tsp_solver import solve_tsp
from .analysis.data_processing import add_closest_countries_to_points

# Visualization imports
from .visualization.visualization import visualize_country_polygon
from .visualization.voronoi_visualization import display_voronoi_diagram

__all__ = [
    'fetch_world_map',
    'get_country_polygon', 
    'get_available_countries',
    'generate_random_points_in_polygon',
    'find_closest_country_to_point',
    'find_multiple_closest_countries',
    'get_admin1_capitals',
    'solve_tsp',
    'add_closest_countries_to_points',
    'visualize_country_polygon',
    'display_voronoi_diagram',
] 