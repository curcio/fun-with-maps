def get_country_polygon(world_gdf, country_name):
    """
    Extract a specific country's polygon from the world map data.

    Parameters:
    world_gdf (geopandas.GeoDataFrame): World map data
    country_name (str): Name of the country to extract

    Returns:
    geopandas.GeoDataFrame: GeoDataFrame containing only the specified country
    None: If country not found
    """
    if world_gdf is None:
        print("No world map data provided")
        return None

    # Try to find the name column (can vary between datasets)
    name_columns = ["NAME", "name", "NAME_EN", "ADMIN", "Country", "country"]
    name_col = None

    for col in name_columns:
        if col in world_gdf.columns:
            name_col = col
            break

    if name_col is None:
        print("No name column found in the dataset")
        print(f"Available columns: {list(world_gdf.columns)}")
        return None

    # Search for the country (case-insensitive partial match)
    country_mask = world_gdf[name_col].str.contains(country_name, case=False, na=False)
    country_data = world_gdf[country_mask]

    if country_data.empty:
        # Try exact match
        country_mask = world_gdf[name_col].str.lower() == country_name.lower()
        country_data = world_gdf[country_mask]

    if country_data.empty:
        print(f"Country '{country_name}' not found.")
        print("Available countries (first 10):")
        print(world_gdf[name_col].head(10).tolist())

        # Suggest similar countries
        similar_countries = world_gdf[
            world_gdf[name_col].str.contains(country_name[:3], case=False, na=False)
        ][name_col].tolist()
        if similar_countries:
            print(f"Did you mean one of these? {similar_countries[:5]}")

        return None

    if len(country_data) > 1:
        print(f"Multiple matches found for '{country_name}':")
        print(country_data[name_col].tolist())
        print("Returning the first match.")
        # Return only the first match
        country_data = country_data.iloc[:1]

    print(f"Found country: {country_data.iloc[0][name_col]}")
    return country_data, country_data.iloc[0][name_col]


def get_country_info(country_gdf):
    """
    Get basic information about a country's polygon.

    Parameters:
    country_gdf (geopandas.GeoDataFrame): Country polygon data

    Returns:
    dict: Dictionary with country information
    """
    if country_gdf is None or country_gdf.empty:
        return None

    country_row = country_gdf.iloc[0]
    geometry = country_row.geometry

    # Calculate bounds
    bounds = geometry.bounds  # (minx, miny, maxx, maxy)

    # Calculate area (in the CRS units, typically square degrees for geographic CRS)
    area = geometry.area

    info = {
        "geometry_type": geometry.geom_type,
        "bounds": {
            "west": bounds[0],
            "south": bounds[1],
            "east": bounds[2],
            "north": bounds[3],
        },
        "area": area,
        "centroid": {"longitude": geometry.centroid.x, "latitude": geometry.centroid.y},
        "crs": str(country_gdf.crs),
    }

    return info


def get_available_countries(world_gdf):
    """
    Get a list of all available countries from the world map data.

    Parameters:
    world_gdf (geopandas.GeoDataFrame): World map data

    Returns:
    list: Sorted list of country names
    None: If no countries found or error occurred
    """
    if world_gdf is None or world_gdf.empty:
        print("No world map data provided")
        return None

    # Find the name column
    name_columns = ["NAME", "name", "NAME_EN", "ADMIN", "Country", "country"]
    name_col = None

    for col in name_columns:
        if col in world_gdf.columns:
            name_col = col
            break

    if name_col is None:
        print("No name column found in the dataset")
        return None

    # Get all unique country names and sort them
    countries = world_gdf[name_col].dropna().unique().tolist()
    countries.sort()

    return countries
