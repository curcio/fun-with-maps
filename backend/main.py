import random
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from fun_with_maps.core.closest_country import find_multiple_closest_countries
from fun_with_maps.core.country_analysis import (
    get_available_countries,
    get_country_polygon,
)
from fun_with_maps.core.map_fetcher import fetch_world_map

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
# Mount images directory to serve generated visualizations
app.mount("/images", StaticFiles(directory=str(PROJECT_ROOT / "images")), name="images")

world_map = None
available_countries = []
data_loaded = False


def load_data() -> None:
    """Load world map and available countries lazily."""
    global world_map, available_countries, data_loaded
    if data_loaded:
        return
    world_map = fetch_world_map(resolution="low")
    if world_map is None:
        available_countries = []
    else:
        available_countries = get_available_countries(world_map) or []
    data_loaded = True


def generate_simple_country_visualization(country_name: str) -> str:
    """
    Generate a simple country visualization without interactive elements.

    Args:
        country_name: Name of the country

    Returns:
        Path to the generated image file relative to web root, or None if failed
    """
    try:
        # Set matplotlib to non-interactive backend
        import matplotlib

        matplotlib.use("Agg")  # Non-interactive backend
        # Suppress matplotlib warnings
        import warnings

        import matplotlib.pyplot as plt

        warnings.filterwarnings("ignore")

        from fun_with_maps.core.country_analysis import get_country_polygon
        from fun_with_maps.core.map_fetcher import fetch_world_map

        print(f"Generating simple visualization for {country_name}...")

        # Create images directory
        images_dir = PROJECT_ROOT / "images" / country_name
        images_dir.mkdir(parents=True, exist_ok=True)

        # Get world map and country polygon
        world_map_high = fetch_world_map(resolution="high")
        if world_map_high is None:
            print(f"Failed to load world map for {country_name}")
            return None

        country_polygon = get_country_polygon(world_map_high, country_name)
        if country_polygon is None or country_polygon.empty:
            print(f"Failed to get polygon for {country_name}")
            return None

        # Create a simple country visualization
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))

        # Plot the country
        country_polygon.plot(ax=ax, color="lightblue", edgecolor="navy", linewidth=2)

        # Set title and labels
        ax.set_title(f"{country_name}", fontsize=16, fontweight="bold")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.grid(True, alpha=0.3)

        # Save the plot
        filename = f"plot_01_{country_name.replace(' ', '_')}_simple_visualization.png"
        filepath = images_dir / filename

        fig.savefig(
            filepath, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none"
        )
        plt.close(fig)  # Important: close to free memory

        print(f"Successfully generated simple visualization: {filepath}")
        return f"/images/{country_name}/{filename}"

    except Exception as e:
        print(f"Error generating visualization for {country_name}: {e}")
        return None


def get_country_image_path(country_name: str) -> str:
    """
    Get the path to a country's visualization image, generating it if it doesn't exist.

    Args:
        country_name: Name of the country

    Returns:
        Path to the image file relative to the web root, or None if generation fails
    """
    if not country_name:
        return None

    # Clean country name for filesystem
    clean_name = country_name.replace(" ", "_").replace(".", "")
    images_dir = PROJECT_ROOT / "images" / country_name

    # Look for existing images (prefer colored visualization, then simple ones)
    image_patterns = [
        f"plot_02_{clean_name}_with_Points_Colored_by_Closest_Country.png",
        f"plot_02_{country_name}_with_Points_Colored_by_Closest_Country.png",
        f"plot_01_{clean_name}_with_Random_Points.png",
        f"plot_01_{country_name}_with_Random_Points.png",
        f"plot_01_{clean_name}_simple_visualization.png",
        f"plot_01_{country_name.replace(' ', '_')}_simple_visualization.png",
    ]

    # Check if any image already exists
    for pattern in image_patterns:
        image_path = images_dir / pattern
        if image_path.exists():
            return f"/images/{country_name}/{pattern}"

    # If no image exists, generate a simple one
    print(f"No image found for {country_name}, generating simple visualization...")
    return generate_simple_country_visualization(country_name)


def choose_country():
    """Select a random country and its closest neighbors."""
    load_data()
    if not available_countries:
        return None, [], None

    country = random.choice(available_countries)
    hints = []
    image_path = None

    if world_map is not None:
        polygon = get_country_polygon(world_map, country)
        if polygon is not None and not polygon.empty:
            centroid = polygon.geometry.iloc[0].centroid
            results = find_multiple_closest_countries(
                world_map, centroid, n_countries=5
            )
            hints = [n for n, _ in results if n.lower() != country.lower()]

    # Get or generate image for this country
    image_path = get_country_image_path(country)

    return country, hints[:4], image_path


@app.get("/", response_class=HTMLResponse)
async def read_index():
    """Serve the static index page."""
    index_file = BASE_DIR / "static" / "index.html"
    return FileResponse(index_file)


@app.get("/api/new-game")
async def new_game():
    """Get a new random country and hints for a fresh game."""
    country, hints, image_path = choose_country()
    load_data()  # Ensure data is loaded

    return JSONResponse(
        {
            "country": country,
            "hints": hints,
            "valid_countries": available_countries,
            "image_path": image_path,
        }
    )
