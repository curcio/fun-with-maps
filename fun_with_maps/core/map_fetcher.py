import os

import geopandas as gpd
import requests


def fetch_world_map(
    resolution="high", save_path=os.path.join("data", "world_map.geojson")
):
    """
    Fetch a world political map with specified resolution using geopandas and requests.

    Parameters:
    resolution (str): Resolution level - 'low', 'medium', or 'high'
    save_path (str): Path to save the downloaded map data

    Returns:
    geopandas.GeoDataFrame: World map data
    """

    # Check if file already exists
    if os.path.exists(save_path):
        try:
            print(f"Map file '{save_path}' already exists. Loading existing file...")
            world = gpd.read_file(save_path)
            print(
                f"Successfully loaded existing map with {len(world)} countries/territories"
            )
            return world
        except Exception as e:
            print(f"Failed to load existing file: {e}")
            print("Proceeding to download fresh data...")

    # Alternative: Use Natural Earth directly
    # For low resolution (1:110m scale)
    if resolution == "low":
        url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
    elif resolution == "medium":
        url = (
            "https://www.naturalearthdata.com/http//www.naturalearthdata.com/"
            "download/50m/cultural/ne_50m_admin_0_countries.zip"
        )
    else:
        url = (
            "https://www.naturalearthdata.com/http//www.naturalearthdata.com/"
            "download/10m/cultural/ne_10m_admin_0_countries.zip"
        )

    try:
        print(f"Fetching {resolution} resolution world map data...")

        # Method 3: Direct download from Natural Earth (ZIP format)
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        # Save zip file temporarily
        zip_path = f"temp_world_{resolution}.zip"
        with open(zip_path, "wb") as f:
            f.write(response.content)

        # Read directly from zip
        world = gpd.read_file(f"zip://{zip_path}")

        # Clean up
        os.remove(zip_path)

        # Save the data for future use
        try:
            os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
            world.to_file(save_path, driver="GeoJSON")
            print(f"Successfully saved map data to '{save_path}'")
        except Exception as e:
            print(f"Warning: Could not save map data to '{save_path}': {e}")

        print(f"Successfully loaded map with {len(world)} countries/territories")
        return world

    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return None
    except Exception as e:
        print(f"Error loading map data: {e}")
        return None
