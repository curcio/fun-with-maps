import matplotlib.pyplot as plt
from typing import List, Optional, Tuple, Dict, Any

from ..core.closest_country import find_multiple_closest_countries
from ..utils.utils import show_plot


class Visualizer:
    """
    A class for managing all visualization operations with consistent styling and configuration.
    """
    
    def __init__(self, style: str = "default", figsize: Tuple[int, int] = (12, 10)):
        """
        Initialize the Visualizer.
        
        Args:
            style: Default matplotlib style to use
            figsize: Default figure size
        """
        self.style = style
        self.figsize = figsize
        self.color_schemes = {
            "default": {
                "country": "lightgreen",
                "country_edge": "darkgreen",
                "points": "red",
                "background": "lightblue",
                "closest_countries": ["red", "orange", "yellow", "lightgreen", "lightblue"]
            },
            "modern": {
                "country": "#3498db",
                "country_edge": "#2c3e50",
                "points": "#e74c3c",
                "background": "#ecf0f1",
                "closest_countries": ["#e74c3c", "#f39c12", "#f1c40f", "#2ecc71", "#3498db"]
            },
            "dark": {
                "country": "#34495e",
                "country_edge": "#2c3e50",
                "points": "#e67e22",
                "background": "#2c3e50",
                "closest_countries": ["#e74c3c", "#f39c12", "#f1c40f", "#27ae60", "#3498db"]
            }
        }
        self.current_colors = self.color_schemes[style] if style in self.color_schemes else self.color_schemes["default"]
        
    def set_style(self, style: str):
        """Set the visualization style."""
        if style in self.color_schemes:
            self.style = style
            self.current_colors = self.color_schemes[style]
        else:
            print(f"Unknown style '{style}'. Available styles: {list(self.color_schemes.keys())}")
    
    def visualize_country_polygon(self, country_gdf, country_name: Optional[str] = None, 
                                figsize: Optional[Tuple[int, int]] = None):
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

        figsize = figsize or self.figsize
        fig, ax = plt.subplots(1, 1, figsize=figsize)

        # Plot the country
        country_gdf.plot(
            ax=ax, 
            color=self.current_colors["country"], 
            edgecolor=self.current_colors["country_edge"], 
            linewidth=2, 
            alpha=0.7
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
        ax.set_facecolor(self.current_colors["background"])

        # Add grid
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        show_plot()

    def visualize_point_and_closest_countries(self, world_gdf, point, n_countries: int = 3, 
                                            figsize: Optional[Tuple[int, int]] = None):
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
        figsize = figsize or (15, 10)
        fig, ax = plt.subplots(1, 1, figsize=figsize)

        # Plot all countries in light gray
        world_gdf.plot(
            ax=ax, color="lightgray", edgecolor="white", linewidth=0.5, alpha=0.7
        )

        # Highlight closest countries with different colors
        colors = self.current_colors["closest_countries"]

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

    def visualize_polygon_with_points(self, polygon_gdf, points_gdf, title: Optional[str] = None, 
                                    figsize: Optional[Tuple[int, int]] = None):
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

        figsize = figsize or self.figsize
        fig, ax = plt.subplots(1, 1, figsize=figsize)

        # Plot the polygon
        polygon_gdf.plot(
            ax=ax,
            color=self.current_colors["country"],
            edgecolor=self.current_colors["country_edge"],
            linewidth=2,
            alpha=0.6,
            label="Polygon",
        )

        # Plot the random points
        points_gdf.plot(
            ax=ax,
            color=self.current_colors["points"],
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
        ax.set_facecolor(self.current_colors["background"])

        plt.tight_layout()
        show_plot(
            title=title.replace(" ", "_"),
            description=f"Visualization of {len(points_gdf)} random points within polygon boundaries"
        )

    def visualize_world_map(self, world_gdf, title: str = "World Political Map", 
                          figsize: Optional[Tuple[int, int]] = None):
        """
        Visualize the world political map.

        Parameters:
        world_gdf (geopandas.GeoDataFrame): World map data
        title (str): Plot title
        figsize (tuple): Figure size
        """
        if world_gdf is None or world_gdf.empty:
            print("No world map data to visualize")
            return

        figsize = figsize or (15, 10)
        fig, ax = plt.subplots(1, 1, figsize=figsize)

        # Plot all countries
        world_gdf.plot(
            ax=ax,
            color=self.current_colors["country"],
            edgecolor=self.current_colors["country_edge"],
            linewidth=0.5,
            alpha=0.8,
        )

        # Customize the plot
        ax.set_title(title, fontsize=16, fontweight="bold")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.grid(True, alpha=0.3)
        ax.set_facecolor(self.current_colors["background"])

        # Set world extent
        ax.set_xlim(-180, 180)
        ax.set_ylim(-90, 90)

        plt.tight_layout()
        show_plot(title="World_Map", description="Global political boundaries visualization")

    def create_country_visualization_with_colors(self, world_gdf, country_polygon, points, 
                                               unique_countries, country_name: str, 
                                               figsize: Optional[Tuple[int, int]] = None):
        """
        Create a colored visualization showing points colored by their closest countries.
        Also highlights the closest countries themselves on the map.
        """
        if points is None or points.empty:
            print("No points data to visualize")
            return

        figsize = figsize or (15, 12)
        fig, ax = plt.subplots(1, 1, figsize=figsize)

        # Find name column for world map
        name_columns = ["NAME", "name", "NAME_EN", "ADMIN", "Country", "country"]
        name_col = None
        for col in name_columns:
            if col in world_gdf.columns:
                name_col = col
                break

        # Plot world map in light gray
        world_gdf.plot(ax=ax, color="lightgray", edgecolor="white", linewidth=0.5, alpha=0.3)

        # Create color mapping for unique countries
        colors = plt.cm.Set1(range(len(unique_countries)))
        country_colors = dict(zip(unique_countries, colors))

        # Highlight the closest countries themselves on the map
        if name_col:
            for i, closest_country in enumerate(unique_countries):
                # Find and highlight the closest country
                country_mask = world_gdf[name_col].str.contains(
                    closest_country, case=False, na=False
                )
                if country_mask.any():
                    closest_country_gdf = world_gdf[country_mask]
                    closest_country_gdf.plot(
                        ax=ax,
                        color=country_colors[closest_country],
                        edgecolor="black",
                        linewidth=1.5,
                        alpha=0.6,
                        label=f"{closest_country} (neighbor)",
                    )

        # Highlight the main country with distinct styling
        if hasattr(country_polygon, "plot"):
            country_polygon.plot(
                ax=ax,
                color=self.current_colors["country"],
                edgecolor=self.current_colors["country_edge"],
                linewidth=3,
                alpha=0.8,
                label=f"{country_name} (main)",
            )

        # Plot points colored by closest country
        if 'closest_country' in points.columns:
            for country in unique_countries:
                country_points = points[points['closest_country'] == country]
                if not country_points.empty:
                    country_points.plot(
                        ax=ax,
                        color=country_colors[country],
                        markersize=25,
                        alpha=0.9,
                        label=f"Points → {country} ({len(country_points)})",
                        edgecolors="white",
                        linewidth=1,
                    )

        # Set bounds focused on the country with some margin
        if hasattr(country_polygon, "total_bounds"):
            # country_polygon is a GeoDataFrame
            bounds = country_polygon.total_bounds
        elif hasattr(country_polygon, "bounds"):
            # country_polygon is a Shapely geometry
            bounds = country_polygon.bounds
        else:
            # Fallback: get bounds from the first geometry
            bounds = country_polygon.iloc[0].geometry.bounds
        
        minx, miny, maxx, maxy = bounds
        
        # Add margin around the country (10% of the country's size)
        width = maxx - minx
        height = maxy - miny
        margin_x = width * 0.1
        margin_y = height * 0.1
        
        ax.set_xlim(minx - margin_x, maxx + margin_x)
        ax.set_ylim(miny - margin_y, maxy + margin_y)

        # Customize the plot
        ax.set_title(
            f"Points in {country_name} Colored by Closest Country",
            fontsize=14,
            fontweight="bold",
        )
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        show_plot(
            title=f"{country_name}_with_Points_Colored_by_Closest_Country",
            description=f"Points within {country_name} colored by their closest neighboring country"
        )


# Backward compatibility functions
def visualize_country_polygon(country_gdf, country_name=None, figsize=(10, 8)):
    """Backward compatibility wrapper."""
    visualizer = Visualizer()
    return visualizer.visualize_country_polygon(country_gdf, country_name, figsize)


def visualize_point_and_closest_countries(world_gdf, point, n_countries=3, figsize=(15, 10)):
    """Backward compatibility wrapper."""
    visualizer = Visualizer()
    return visualizer.visualize_point_and_closest_countries(world_gdf, point, n_countries, figsize)


def visualize_polygon_with_points(polygon_gdf, points_gdf, title=None, figsize=(12, 10)):
    """Backward compatibility wrapper."""
    visualizer = Visualizer()
    return visualizer.visualize_polygon_with_points(polygon_gdf, points_gdf, title, figsize)


def visualize_world_map(world_gdf, title="World Political Map", figsize=(15, 10)):
    """Backward compatibility wrapper."""
    visualizer = Visualizer()
    return visualizer.visualize_world_map(world_gdf, title, figsize)


def create_country_visualization_with_colors(world_gdf, country_polygon, points, unique_countries, country_name, figsize=(15, 12)):
    """Backward compatibility wrapper."""
    visualizer = Visualizer()
    return visualizer.create_country_visualization_with_colors(world_gdf, country_polygon, points, unique_countries, country_name, figsize)
