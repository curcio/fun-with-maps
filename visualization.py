import matplotlib.pyplot as plt

from closest_country import find_multiple_closest_countries
from utils import show_plot


def visualize_country_polygon(country_gdf, country_name=None, figsize=(10, 8)):
    """
    Visualize a specific country's polygon.

    Parameters:
    country_gdf (geopandas.GeoDataFrame): Country polygon data
    country_name (str): Name for the title (optional)
    figsize (tuple): Figure size
    """
    if country_gdf is None or country_gdf.empty:
        print("No country data to visualize")
        return

    fig, ax = plt.subplots(1, 1, figsize=figsize)

    # Plot the country
    country_gdf.plot(
        ax=ax, color="lightgreen", edgecolor="darkgreen", linewidth=2, alpha=0.7
    )

    # Get country name for title
    if country_name is None:
        name_columns = ["NAME", "name", "NAME_EN", "ADMIN", "Country", "country"]
        for col in name_columns:
            if col in country_gdf.columns:
                country_name = country_gdf.iloc[0][col]
                break

    # Customize the plot
    title = f"Polygon of {country_name}" if country_name else "Country Polygon"
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    # Set background color
    ax.set_facecolor("lightblue")

    # Add grid
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    show_plot()


def visualize_point_and_closest_countries(
    world_gdf, point, n_countries=3, figsize=(15, 10)
):
    """
    Visualize a point and its closest countries on the world map.

    Parameters:
    world_gdf (geopandas.GeoDataFrame): World map data
    point (tuple or shapely.geometry.Point): Point coordinates
    n_countries (int): Number of closest countries to highlight
    figsize (tuple): Figure size
    """
    if isinstance(point, (tuple, list)):
        lon, lat = point[0], point[1]
    else:
        lon, lat = point.x, point.y

    # Get closest countries
    closest_countries = find_multiple_closest_countries(world_gdf, point, n_countries)

    if not closest_countries:
        print("No closest countries found")
        return

    # Find name column
    name_columns = ["NAME", "name", "NAME_EN", "ADMIN", "Country", "country"]
    name_col = None
    for col in name_columns:
        if col in world_gdf.columns:
            name_col = col
            break

    # Create the plot
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    # Plot all countries in light gray
    world_gdf.plot(
        ax=ax, color="lightgray", edgecolor="white", linewidth=0.5, alpha=0.7
    )

    # Highlight closest countries with different colors
    colors = ["red", "orange", "yellow", "lightgreen", "lightblue"]

    for i, (country_name, distance) in enumerate(closest_countries):
        if i < len(colors):
            # Find and highlight the country
            country_mask = world_gdf[name_col].str.contains(
                country_name, case=False, na=False
            )
            if country_mask.any():
                world_gdf[country_mask].plot(
                    ax=ax,
                    color=colors[i],
                    edgecolor="black",
                    linewidth=1,
                    alpha=0.8,
                    label=f"{i+1}. {country_name}",
                )

    # Plot the point
    ax.scatter(
        lon,
        lat,
        c="darkblue",
        s=200,
        marker="*",
        edgecolor="white",
        linewidth=2,
        zorder=5,
        label="Query Point",
    )

    # Add point coordinates as text
    ax.annotate(
        f"({lon:.2f}, {lat:.2f})",
        xy=(lon, lat),
        xytext=(10, 10),
        textcoords="offset points",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8),
        fontsize=10,
        ha="left",
    )

    # Customize the plot
    ax.set_title(
        f"Point Location and {n_countries} Closest Countries",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
    ax.grid(True, alpha=0.3)

    # Set reasonable bounds around the point
    buffer = 20  # degrees
    ax.set_xlim(lon - buffer, lon + buffer)
    ax.set_ylim(lat - buffer, lat + buffer)

    plt.tight_layout()
    show_plot()


def visualize_polygon_with_points(
    polygon_gdf, points_gdf, title=None, figsize=(12, 10)
):
    """
    Visualize a polygon with random points inside it.

    Parameters:
    polygon_gdf (geopandas.GeoDataFrame): Polygon data
    points_gdf (geopandas.GeoDataFrame): Random points data
    title (str): Plot title
    figsize (tuple): Figure size
    """
    if polygon_gdf is None or points_gdf is None:
        print("Missing polygon or points data")
        return

    fig, ax = plt.subplots(1, 1, figsize=figsize)

    # Plot the polygon
    polygon_gdf.plot(
        ax=ax,
        color="lightblue",
        edgecolor="navy",
        linewidth=2,
        alpha=0.6,
        label="Polygon",
    )

    # Plot the random points
    points_gdf.plot(
        ax=ax,
        color="red",
        markersize=20,
        alpha=0.7,
        label=f"Random Points (n={len(points_gdf)})",
    )

    # Customize the plot
    if title is None:
        title = f"Polygon with {len(points_gdf)} Random Points"

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_facecolor("lightcyan")

    plt.tight_layout()
    show_plot()


def visualize_world_map(world_gdf, title="World Political Map", figsize=(15, 10)):
    """
    Visualize the world political map.

    Parameters:
    world_gdf (geopandas.GeoDataFrame): World map data
    title (str): Plot title
    figsize (tuple): Figure size
    """
    if world_gdf is None:
        print("No map data to visualize")
        return

    fig, ax = plt.subplots(1, 1, figsize=figsize)

    # Plot the map
    world_gdf.plot(
        ax=ax, color="lightblue", edgecolor="black", linewidth=0.5, alpha=0.7
    )

    # Customize the plot
    ax.set_title(title, fontsize=16, fontweight="bold")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    # Remove axis ticks for cleaner look
    ax.set_xticks([])
    ax.set_yticks([])

    # Set background color
    ax.set_facecolor("lightcyan")

    plt.tight_layout()
    show_plot()
