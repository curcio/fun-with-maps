import datetime
import math
import os
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# Global variable to track plots for PDF generation
_plot_tracker = {"plots": [], "country_info": {}, "images_dir": None}


def get_enhanced_country_info(country_name: str, world_map=None, country_polygon=None):
    """
    Get enhanced country information including states count and estimated statistics.

    Args:
        country_name: Name of the country
        world_map: World map GeoDataFrame (optional)
        country_polygon: Country polygon geometry (optional)

    Returns:
        Dict with country information
    """
    info = {"name": country_name}

    # Get basic geometry info if polygon provided
    if country_polygon is not None:
        if hasattr(country_polygon, "iloc"):
            geometry = country_polygon.iloc[0].geometry
        else:
            geometry = country_polygon

        # Calculate area in square kilometers (rough conversion from degrees)
        area_sq_deg = geometry.area
        # Very rough conversion: 1 degree ≈ 111 km at equator
        area_sq_km = area_sq_deg * (111.32**2)

        info.update(
            {
                "area": f"{area_sq_km:,.0f} km²",
                "area_degrees": area_sq_deg,
                "centroid_lat": geometry.centroid.y,
                "centroid_lon": geometry.centroid.x,
            }
        )

    # Try to get states/provinces count
    states_count = get_states_count(country_name)
    if states_count is not None:
        info["states_count"] = states_count

    # Add estimated population (hard-coded for major countries, could be enhanced with API)
    population_estimates = {
        "Argentina": "45,376,763",
        "Brazil": "215,313,498",
        "United States": "331,449,281",
        "China": "1,439,323,776",
        "India": "1,380,004,385",
        "Russia": "145,934,462",
        "Canada": "38,008,005",
        "Australia": "25,693,267",
        "Germany": "83,240,525",
        "France": "67,391,582",
        "United Kingdom": "67,886,011",
        "Spain": "47,558,630",
        "Italy": "60,367,477",
        "Japan": "125,836,021",
        "Mexico": "128,932,753",
    }

    info["population"] = population_estimates.get(country_name, "N/A")

    return info


def get_states_count(country_name: str) -> Optional[int]:
    """
    Get the number of admin-1 states/provinces for a country.

    Args:
        country_name: Name of the country

    Returns:
        Number of states/provinces or None if not found
    """
    try:
        import zipfile

        # Try to load admin-1 data
        data_paths = [
            "data/ne_10m_admin_1_states_provinces",
            "data/natural_earth/ne_10m_admin_1_states_provinces",
        ]

        for data_path in data_paths:
            shp_path = f"{data_path}/ne_10m_admin_1_states_provinces.shp"
            zip_path = f"{data_path}.zip"

            # Extract data if needed
            if not os.path.exists(shp_path):
                if os.path.exists(zip_path):
                    with zipfile.ZipFile(zip_path, "r") as zip_ref:
                        zip_ref.extractall(data_path)
                    break
                else:
                    continue
            else:
                break
        else:
            # No data found
            return None

        # Read and filter data
        import geopandas as gpd

        gdf = gpd.read_file(shp_path)

        # Try different name columns
        name_cols = ["admin", "ADMIN", "ADM0_A3", "NAME_0", "SOVEREIGNT", "NAME_EN"]
        country_data = None

        for col in name_cols:
            if col in gdf.columns:
                filtered = gdf[
                    gdf[col].str.contains(country_name, case=False, na=False)
                ]
                if not filtered.empty:
                    country_data = filtered
                    break

        if country_data is not None and not country_data.empty:
            return len(country_data)

    except Exception as e:
        print(f"Warning: Could not get states count for {country_name}: {e}")

    return None


def set_country_info(country_name: str, country_polygon=None, **kwargs):
    """
    Set country information for PDF generation.

    Args:
        country_name: Name of the country
        country_polygon: Country polygon geometry (optional)
        **kwargs: Additional country information like area, population, states_count
    """
    # Get enhanced info
    enhanced_info = get_enhanced_country_info(
        country_name, country_polygon=country_polygon
    )
    enhanced_info.update(kwargs)

    _plot_tracker["country_info"] = enhanced_info

    # Set up images directory
    _plot_tracker["images_dir"] = f"images/{country_name}"
    os.makedirs(_plot_tracker["images_dir"], exist_ok=True)


def show_plot(title: Optional[str] = None, description: Optional[str] = None):
    """
    Conditionally show matplotlib plots based on environment variable.
    Also saves plots to images directory for later PDF generation.

    Args:
        title: Custom title for the plot (used in PDF)
        description: Description of the plot (used in PDF)
    """
    # Get current figure
    fig = plt.gcf()

    # Generate filename based on plot count
    plot_count = len(_plot_tracker["plots"]) + 1
    country_name = _plot_tracker["country_info"].get("name", "Unknown")

    # Determine title from plot or use provided title
    if title is None:
        # Try to get title from the current axes
        axes = fig.get_axes()
        if axes and hasattr(axes[0], "get_title"):
            title = axes[0].get_title()
        if not title:
            title = f"Plot {plot_count}"

    # Save plot to images directory if we have one set up
    if _plot_tracker["images_dir"]:
        filename = (
            f"plot_{plot_count:02d}_{title.replace(' ', '_').replace('/', '_')}.png"
        )
        filepath = os.path.join(_plot_tracker["images_dir"], filename)

        # Save with high DPI for better quality
        fig.savefig(
            filepath, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none"
        )

        # Track plot information
        _plot_tracker["plots"].append(
            {
                "title": title,
                "description": description or f"Visualization for {country_name}",
                "filepath": filepath,
                "filename": filename,
            }
        )

        print(f"Plot saved: {filepath}")

    # Show plot conditionally
    if not os.getenv("HIDE_PLOTS"):
        plt.show()


def generate_pdf_report(output_filename: Optional[str] = None):
    """
    Generate a comprehensive PDF report with all saved plots and country information.

    Args:
        output_filename: Custom filename for the PDF. If None, uses country name.
    """
    if not _plot_tracker["plots"]:
        print("No plots to include in PDF report.")
        return

    country_info = _plot_tracker["country_info"]
    country_name = country_info.get("name", "Unknown")

    if output_filename is None:
        output_filename = f"{country_name.replace(' ', '_')}_analysis_report.pdf"

    print(f"Generating PDF report: {output_filename}")

    with PdfPages(output_filename) as pdf:
        # Create title page
        _create_title_page(pdf, country_info)

        # Add each plot as a separate page
        for plot_info in _plot_tracker["plots"]:
            _add_plot_page(pdf, plot_info, country_info)

        # Add metadata to PDF
        _add_pdf_metadata(pdf, country_info)

    print(f"✅ PDF report generated successfully: {output_filename}")
    print(
        f"📊 Total pages: {len(_plot_tracker['plots']) + 1} (1 title page + {len(_plot_tracker['plots'])} plot pages)"
    )


def _create_title_page(pdf: PdfPages, country_info: Dict[str, Any]):
    """Create a title page with country information."""
    fig, ax = plt.subplots(1, 1, figsize=(8.5, 11))
    ax.axis("off")

    country_name = country_info.get("name", "Unknown Country")

    # Title
    ax.text(
        0.5,
        0.9,
        f"Geographic Analysis Report",
        ha="center",
        va="center",
        fontsize=24,
        fontweight="bold",
        transform=ax.transAxes,
        color="darkblue",
    )

    ax.text(
        0.5,
        0.82,
        f"{country_name}",
        ha="center",
        va="center",
        fontsize=20,
        fontweight="bold",
        transform=ax.transAxes,
        color="darkgreen",
    )

    # Add country statistics if available
    y_pos = 0.65
    info_items = [
        ("Country", country_name),
        ("Area", country_info.get("area", "N/A")),
        ("Population", country_info.get("population", "N/A")),
        ("Number of States/Provinces", country_info.get("states_count", "N/A")),
        ("Analysis Date", datetime.datetime.now().strftime("%Y-%m-%d")),
        ("Total Visualizations", len(_plot_tracker["plots"])),
    ]

    for label, value in info_items:
        ax.text(
            0.2,
            y_pos,
            f"{label}:",
            ha="left",
            va="center",
            fontsize=12,
            fontweight="bold",
            transform=ax.transAxes,
        )
        ax.text(
            0.6,
            y_pos,
            str(value),
            ha="left",
            va="center",
            fontsize=12,
            transform=ax.transAxes,
        )
        y_pos -= 0.06

    # Add description
    ax.text(
        0.5,
        0.25,
        "This report contains comprehensive geographic analysis including:\n"
        "• Country polygon visualization\n"
        "• Random point generation and analysis\n"
        "• Closest country analysis with color coding\n"
        "• Voronoi diagram based on capital cities\n"
        "• Traveling Salesman Problem (TSP) solution\n"
        "\nGenerated using Python with GeoPandas, Matplotlib, and OR-Tools",
        ha="center",
        va="center",
        fontsize=11,
        transform=ax.transAxes,
        style="italic",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.3),
    )

    plt.tight_layout()
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def _add_plot_page(
    pdf: PdfPages, plot_info: Dict[str, Any], country_info: Dict[str, Any]
):
    """Add a plot page to the PDF."""
    try:
        # Create a new figure for the PDF page
        fig, (ax_plot, ax_info) = plt.subplots(
            2, 1, figsize=(8.5, 11), gridspec_kw={"height_ratios": [4, 1]}
        )

        # Load and display the saved plot image
        import matplotlib.image as mpimg

        img = mpimg.imread(plot_info["filepath"])
        ax_plot.imshow(img)
        ax_plot.axis("off")
        ax_plot.set_title(plot_info["title"], fontsize=16, fontweight="bold", pad=20)

        # Add description and metadata
        ax_info.axis("off")
        description_text = f"Description: {plot_info['description']}\n\n"
        description_text += f"Country: {country_info.get('name', 'Unknown')}\n"
        description_text += (
            f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        ax_info.text(
            0.02,
            0.98,
            description_text,
            ha="left",
            va="top",
            fontsize=10,
            transform=ax_info.transAxes,
            bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", alpha=0.7),
        )

        plt.tight_layout()
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    except Exception as e:
        print(f"Warning: Could not add plot {plot_info['title']} to PDF: {e}")


def _add_pdf_metadata(pdf: PdfPages, country_info: Dict[str, Any]):
    """Add metadata to the PDF."""
    try:
        d = pdf.infodict()
        d[
            "Title"
        ] = f"Geographic Analysis Report - {country_info.get('name', 'Unknown')}"
        d["Author"] = "Fun with Maps - Geographic Analysis Tool"
        d[
            "Subject"
        ] = f"Comprehensive geographic analysis of {country_info.get('name', 'Unknown Country')}"
        d[
            "Keywords"
        ] = "geographic analysis, voronoi diagram, TSP, country analysis, visualization"
        d["CreationDate"] = datetime.datetime.now()
        d["ModDate"] = datetime.datetime.now()
    except Exception as e:
        print(f"Warning: Could not add metadata to PDF: {e}")


def clear_plot_tracker():
    """Clear the plot tracker (useful for starting a new analysis)."""
    global _plot_tracker
    _plot_tracker = {"plots": [], "country_info": {}, "images_dir": None}


def get_plot_tracker_info():
    """Get current plot tracker information."""
    return {
        "plot_count": len(_plot_tracker["plots"]),
        "country": _plot_tracker["country_info"].get("name", "Not set"),
        "images_dir": _plot_tracker["images_dir"],
    }


def haversine_distance(
    point1: Tuple[float, float], point2: Tuple[float, float]
) -> float:
    """
    Calculate the great circle distance between two points on Earth using haversine formula.

    Args:
        point1: (longitude, latitude) in degrees
        point2: (longitude, latitude) in degrees

    Returns:
        Distance in kilometers
    """
    # Convert decimal degrees to radians
    lon1, lat1 = math.radians(point1[0]), math.radians(point1[1])
    lon2, lat2 = math.radians(point2[0]), math.radians(point2[1])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    # Radius of earth in kilometers
    r = 6371

    return c * r


def print_solution_details(
    points: List[Tuple[float, float]], tour: List[int], cost: float
):
    """
    Print detailed information about the TSP solution.

    Args:
        points: Original list of coordinate points
        tour: Optimal tour as list of indices
        cost: Total tour cost in kilometers
    """
    print(f"\n{'='*60}")
    print(f"TSP SOLUTION DETAILS (OR-Tools)")
    print(f"{'='*60}")
    print(f"Total tour distance: {cost:.1f} km")
    print(f"Number of cities: {len(tour)}")
    print(f"Average distance between cities: {cost/len(tour):.1f} km")

    print(f"\nTour sequence:")
    for i, city_idx in enumerate(tour):
        lon, lat = points[city_idx]
        print(f"  {i+1:2d}. City {city_idx:<3d} ({lon:8.4f}, {lat:8.4f})")

    # Show return to start
    if tour:
        start_lon, start_lat = points[tour[0]]
        print(
            f"  {len(tour)+1:2d}. City {tour[0]:<3d} ({start_lon:8.4f}, {start_lat:8.4f}) [return to start]"
        )

    # Calculate some statistics
    if len(tour) > 1:
        distances = []
        for i in range(len(tour)):
            current_idx = tour[i]
            next_idx = tour[(i + 1) % len(tour)]
            dist = haversine_distance(points[current_idx], points[next_idx])
            distances.append(dist)

        print(f"\nDistance statistics:")
        print(f"  Shortest segment: {min(distances):.1f} km")
        print(f"  Longest segment:  {max(distances):.1f} km")
        print(f"  Average segment:  {sum(distances)/len(distances):.1f} km")


def debug_individual_region(country_name: str, region_name: str):
    """Debug a specific infinite region in detail with step-by-step visualization."""
    print(f"=== DEBUGGING INDIVIDUAL REGION: {region_name} in {country_name} ===")

    # Get data
    world_map = fetch_world_map(resolution="low")
    country_polygon = get_country_polygon(world_map, country_name)
    capitals = get_admin1_capitals(country_name)

    if hasattr(country_polygon, "geometry"):
        country_geom = country_polygon.geometry.iloc[0]
    else:
        country_geom = country_polygon

    # Find the specific region
    target_capital = None
    target_index = None
    for i, (idx, row) in enumerate(capitals.iterrows()):
        name = row.get("NAME", f"Capital {i}")
        if region_name.lower() in name.lower():
            target_capital = row
            target_index = i
            print(f"Found target region: {name} at index {i}")
            break

    if target_capital is None:
        print(f"❌ Region '{region_name}' not found!")
        print("Available regions:")
        for i, (idx, row) in enumerate(capitals.iterrows()):
            print(f"  {i}: {row.get('NAME', f'Capital {i}')}")
        return

    # Create Voronoi diagram
    vor, voronoi_polygons, points = create_voronoi_from_capitals(
        capitals, country_polygon
    )

    if vor is None:
        print("❌ Failed to create Voronoi diagram")
        return

    # Get the specific region details
    target_point = Point(target_capital.geometry.x, target_capital.geometry.y)
    target_polygon = voronoi_polygons[target_index]

    # Analyze the region construction
    region_idx = vor.point_region[target_index]
    region_vertices = vor.regions[region_idx]
    ridge_points = vor.ridge_points[region_idx]

    vertices = vor.vertices[region_vertices]

    print(f"\n🔍 REGION ANALYSIS:")
    print(f"   Name: {target_capital.get('NAME', 'Unknown')}")
    print(
        f"   Point: ({target_capital.geometry.x:.6f}, {target_capital.geometry.y:.6f})"
    )
    print(f"   Voronoi region index: {region_idx}")
    print(f"   Region vertices: {region_vertices}")
    print(f"   Has infinite vertices: {-1 in region_vertices}")
    print(f"   Ridge points: {ridge_points}")
    print(f"   Vertices: {vertices}")

    # Detailed construction analysis
    analyze_region_construction_step_by_step(
        vor, target_index, target_point, target_polygon, country_geom
    )

    # Create detailed visualization
    create_individual_region_visualization(
        country_name,
        region_name,
        country_polygon,
        capitals,
        vor,
        target_index,
        target_point,
        target_polygon,
    )
