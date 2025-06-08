import os
from typing import List, Optional, Tuple

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from shapely.geometry import LineString, Polygon

from utils import show_plot
from voronoi_analysis import create_voronoi_from_capitals


def get_color_palette(num_colors: int) -> List:
    """Get appropriate color palette based on number of colors needed."""
    if num_colors <= 12:
        return plt.cm.Set3(np.linspace(0, 1, num_colors))
    elif num_colors <= 20:
        return plt.cm.tab20(np.linspace(0, 1, num_colors))
    else:
        # Combine multiple palettes for many regions
        colors1 = plt.cm.Set3(np.linspace(0, 1, 12))
        colors2 = plt.cm.Pastel1(np.linspace(0, 1, 9))
        colors3 = plt.cm.Set2(np.linspace(0, 1, 8))
        colors = np.vstack([colors1, colors2, colors3])
        return [colors[i % len(colors)] for i in range(num_colors)]


def plot_country_boundary(ax, country_polygon, country_name: str):
    """Plot country boundary on the given axes."""
    if hasattr(country_polygon, "geometry"):
        country_polygon.boundary.plot(
            ax=ax, color="black", linewidth=2, label=f"{country_name} Boundary"
        )
        return country_polygon.geometry.iloc[0]
    else:
        x, y = country_polygon.boundary.xy
        ax.plot(x, y, color="black", linewidth=2, label=f"{country_name} Boundary")
        return country_polygon


def plot_voronoi_regions(ax, voronoi_polygons: List, colors: List, alpha: float = 0.7):
    """Plot Voronoi regions with given colors."""
    for i, (poly, color) in enumerate(zip(voronoi_polygons, colors)):
        if poly is not None and not poly.is_empty:
            _plot_single_region(ax, poly, color, alpha)


def _plot_single_region(ax, poly, color, alpha: float):
    """Helper function to plot a single Voronoi region."""
    if hasattr(poly, "geoms"):
        # Handle MultiPolygon
        for geom in poly.geoms:
            if isinstance(geom, Polygon):
                x, y = geom.exterior.xy
                ax.fill(x, y, color=color, alpha=alpha, edgecolor="white", linewidth=2)
    else:
        # Handle single Polygon
        if isinstance(poly, Polygon):
            x, y = poly.exterior.xy
            ax.fill(x, y, color=color, alpha=alpha, edgecolor="white", linewidth=2)


def plot_voronoi_edges(ax, vor, main_geom):
    """Plot Voronoi diagram edges clipped to country boundary."""
    from shapely.geometry import LineString

    # Plot finite edges
    for edge in vor.ridge_vertices:
        if -1 not in edge:  # Only finite edges
            points_on_edge = vor.vertices[edge]
            line = LineString(
                [
                    (points_on_edge[0, 0], points_on_edge[0, 1]),
                    (points_on_edge[1, 0], points_on_edge[1, 1]),
                ]
            )
            _plot_clipped_line(ax, line, main_geom)


def _plot_clipped_line(ax, line: LineString, main_geom, style: str = "-"):
    """Helper function to plot a line clipped to geometry boundary."""
    try:
        clipped_line = line.intersection(main_geom)
        if not clipped_line.is_empty:
            if hasattr(clipped_line, "geoms"):
                for geom in clipped_line.geoms:
                    _plot_line_coords(ax, geom, style)
            else:
                _plot_line_coords(ax, clipped_line, style)
    except Exception:
        # Fallback: draw original line if it intersects
        if main_geom.intersects(line):
            coords = list(line.coords)
            if len(coords) >= 2:
                x_coords, y_coords = zip(*coords)
                ax.plot(
                    x_coords,
                    y_coords,
                    color="darkslategray",
                    linewidth=2,
                    alpha=0.9,
                    linestyle=style,
                )


def _plot_line_coords(ax, geom, style: str):
    """Helper function to plot line coordinates."""
    if hasattr(geom, "coords"):
        coords = list(geom.coords)
        if len(coords) >= 2:
            x_coords, y_coords = zip(*coords)
            ax.plot(
                x_coords,
                y_coords,
                color="darkslategray",
                linewidth=2,
                alpha=0.9,
                linestyle=style,
            )


def plot_capitals(ax, capitals_gdf: gpd.GeoDataFrame, colors: List) -> List[Patch]:
    """Plot capital cities and return legend elements."""
    # Plot capitals
    capitals_gdf.plot(
        ax=ax,
        color="red",
        marker="*",
        markersize=200,
        label=f"Capitals ({len(capitals_gdf)})",
        edgecolors="darkred",
        linewidth=2,
        alpha=0.9,
    )

    # Create legend elements and add labels
    legend_elements = []
    for idx, row in capitals_gdf.iterrows():
        if idx < len(colors):
            legend_elements.append(
                Patch(
                    facecolor=colors[idx],
                    alpha=0.7,
                    label=row.get("NAME", f"Capital {idx}"),
                )
            )

        # Add capital city labels
        ax.annotate(
            row.get("NAME", f"Capital {idx}"),
            (row.geometry.x, row.geometry.y),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=9,
            ha="left",
            va="bottom",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.9),
        )

    return legend_elements


def setup_plot_layout(ax, main_geom, country_name: str, margin_factor: float = 0.05):
    """Setup plot title, bounds, and styling."""
    # Set title and labels
    ax.set_title(
        f"{country_name} - Voronoi Diagram from Capital Cities",
        fontsize=16,
        fontweight="bold",
        pad=20,
    )
    ax.set_xlabel("Longitude", fontsize=12)
    ax.set_ylabel("Latitude", fontsize=12)

    # Set bounds with margin
    bounds = main_geom.bounds
    margin = max(bounds[2] - bounds[0], bounds[3] - bounds[1]) * margin_factor
    ax.set_xlim(bounds[0] - margin, bounds[2] + margin)
    ax.set_ylim(bounds[1] - margin, bounds[3] + margin)

    # Style
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    ax.set_facecolor("aliceblue")


def setup_legends(ax, legend_elements: List[Patch], max_legend_items: int = 15):
    """Setup both main and Voronoi region legends."""
    main_legend = ax.legend(loc="upper right", bbox_to_anchor=(1, 1))

    # Add Voronoi legend if not too many items
    if legend_elements and len(legend_elements) <= max_legend_items:
        voronoi_legend = ax.legend(  # noqa: F841
            handles=legend_elements,
            title="Voronoi Regions (Capitals)",
            loc="upper left",
            bbox_to_anchor=(0, 1),
            fontsize=8,
            title_fontsize=9,
        )
        ax.add_artist(main_legend)  # Keep both legends


def visualize_voronoi_with_capitals(
    country_polygon, capitals_gdf: gpd.GeoDataFrame, country_name: str
) -> Tuple[Optional[plt.Figure], Optional[plt.Axes]]:
    """
    Visualize country with Voronoi diagram based on capital cities.

    Args:
        country_polygon: Country boundary (GeoDataFrame or Shapely geometry)
        capitals_gdf: GeoDataFrame containing capital cities
        country_name: Name of the country for the title

    Returns:
        tuple: (figure, axes) or (None, None) if failed
    """
    print(f"Creating Voronoi visualization for {country_name}...")

    # Create Voronoi diagram
    vor, voronoi_polygons, capital_points = create_voronoi_from_capitals(
        capitals_gdf, country_polygon
    )

    if vor is None:
        print("Could not create Voronoi diagram")
        return None, None

    # Setup plot
    fig, ax = plt.subplots(1, 1, figsize=(15, 12))

    # Plot country boundary
    main_geom = plot_country_boundary(ax, country_polygon, country_name)

    # Get colors and plot regions
    colors = get_color_palette(len(voronoi_polygons))
    plot_voronoi_regions(ax, voronoi_polygons, colors)

    # Plot Voronoi edges
    plot_voronoi_edges(ax, vor, main_geom)

    # Plot capitals and get legend elements
    legend_elements = plot_capitals(ax, capitals_gdf, colors)

    # Setup layout and legends
    setup_plot_layout(ax, main_geom, country_name)
    setup_legends(ax, legend_elements)

    plt.tight_layout()
    return fig, ax


def display_voronoi_diagram(
    country_polygon, capitals_gdf: gpd.GeoDataFrame, country_name: str
):
    """Create and display Voronoi diagram visualization."""
    fig, ax = visualize_voronoi_with_capitals(
        country_polygon, capitals_gdf, country_name
    )
    if fig is not None:
        # Check if plots should be hidden
        if not os.environ.get("HIDE_PLOTS", "").lower() in ["1", "true", "yes"]:
            show_plot()
        else:
            print(
                f"Plot created for {country_name} but display is hidden (HIDE_PLOTS=1)"
            )
            plt.close(fig)  # Close to free memory
    else:
        print("Failed to create Voronoi visualization")
