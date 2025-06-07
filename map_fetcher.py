import os

import geopandas as gpd
import requests


def fetch_world_map(resolution="low", save_path="world_map.geojson"):
    """
    Fetch a world political map with specified resolution using geopandas and requests.

    Parameters:
    resolution (str): Resolution level - 'low', 'medium', or 'high'
    save_path (str): Path to save the downloaded map data

    Returns:
    geopandas.GeoDataFrame: World map data
    """

    # Natural Earth data URLs for different resolutions
    urls = {
        "low": (
            "https://raw.githubusercontent.com/holtzy/The-Python-Graph-Gallery/"
            "master/static/data/world-110m.geojson"
        ),
        "medium": (
            "https://raw.githubusercontent.com/holtzy/The-Python-Graph-Gallery/"
            "master/static/data/world-50m.geojson"
        ),
        "high": (
            "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
            "master/geojson/ne_10m_admin_0_countries.geojson"
        ),
    }

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

        # Method 1: Try to fetch from GitHub (GeoJSON format)
        if resolution in urls:
            try:
                response = requests.get(urls[resolution], timeout=30)
                response.raise_for_status()

                # Save the data
                with open(save_path, "w") as f:
                    f.write(response.text)

                # Load with geopandas
                world = gpd.read_file(save_path)
                print(
                    f"Successfully loaded map with {len(world)} countries/territories"
                )
                return world

            except Exception as e:
                print(f"GitHub source failed: {e}")
                print("Trying alternative method...")

        # Method 2: Use geopandas built-in datasets
        try:
            print("Using geopandas built-in world dataset...")
            world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
            print(
                f"Successfully loaded built-in dataset with "
                f"{len(world)} countries/territories"
            )
            return world

        except Exception as e:
            print(f"Built-in dataset failed: {e}")
            print("Trying direct Natural Earth download...")

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

        print(f"Successfully loaded map with {len(world)} countries/territories")
        return world

    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return None
    except Exception as e:
        print(f"Error loading map data: {e}")
        return None
