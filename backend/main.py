import random
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
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
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

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


def choose_country():
    """Select a random country and its closest neighbors."""
    load_data()
    if not available_countries:
        return None, []

    country = random.choice(available_countries)
    hints = []
    if world_map is not None:
        polygon = get_country_polygon(world_map, country)
        if polygon is not None and not polygon.empty:
            centroid = polygon.geometry.iloc[0].centroid
            results = find_multiple_closest_countries(
                world_map, centroid, n_countries=5
            )
            hints = [n for n, _ in results if n.lower() != country.lower()]
    return country, hints[:4]


@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    country, hints = choose_country()
    game_data = {"country": country, "valid_countries": available_countries}
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "country": country,
            "hints": hints,
            "valid_countries": available_countries,
            "game_data": game_data,
            "image_path": None,
        },
    )
