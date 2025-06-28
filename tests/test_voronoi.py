#!/usr/bin/env python3
"""
Test script to demonstrate the improved Voronoi diagram functionality.
This script focuses specifically on testing the infinite region handling.
"""

import matplotlib.pyplot as plt
import numpy as np

from fun_with_maps.core.country_analysis import get_country_polygon
from fun_with_maps.core.map_fetcher import fetch_world_map
from fun_with_maps.analysis.voronoi_analysis import create_voronoi_from_capitals, get_admin1_capitals
from fun_with_maps.visualization.voronoi_visualization import (
    display_voronoi_diagram,
    visualize_voronoi_with_capitals,
)


def voronoi_test_for_country(country_name: str):
    """
    Test Voronoi diagram creation for a specific country.

    Args:
        country_name: Name of the country to test
    """
    print(f"\n=== Testing Voronoi Diagram for {country_name} ===")

    try:
        # Get map and country data
        print("1. Fetching world map...")
        world_map = fetch_world_map(resolution="high")

        print(f"2. Getting {country_name} polygon...")
        country_polygon = get_country_polygon(world_map, country_name)

        print(f"3. Getting capital cities for {country_name}...")
        capitals = get_admin1_capitals(country_name)

        if capitals.empty:
            print(f"❌ No capital cities found for {country_name}")
            return False

        print(f"   Found {len(capitals)} capital cities:")
        for idx, row in capitals.iterrows():
            print(f"     - {row.get('NAME', 'Unknown')}")

        print(f"4. Creating Voronoi diagram...")
        display_voronoi_diagram(country_polygon, capitals, country_name)

        print(f"✅ Successfully created Voronoi diagram for {country_name}")
        return True

    except Exception as e:
        print(f"❌ Error testing {country_name}: {e}")
        import traceback

        traceback.print_exc()
        return False


def inspect_individual_polygons(country_name: str):
    """
    Detailed inspection of each Voronoi polygon individually.

    Args:
        country_name: Name of the country to inspect
    """
    print(f"\n=== Detailed Polygon Inspection for {country_name} ===")

    try:
        # Get map and country data
        print("1. Fetching world map...")
        world_map = fetch_world_map(resolution="high")

        print(f"2. Getting {country_name} polygon...")
        country_polygon = get_country_polygon(world_map, country_name)

        print(f"3. Getting capital cities for {country_name}...")
        capitals = get_admin1_capitals(country_name)

        if capitals.empty:
            print(f"❌ No capital cities found for {country_name}")
            return False

        print(f"   Found {len(capitals)} capital cities")

        # Create Voronoi diagram
        print(f"4. Creating Voronoi diagram...")
        vor, voronoi_polygons, capital_points = create_voronoi_from_capitals(
            capitals, country_polygon
        )

        if vor is None:
            print("❌ Could not create Voronoi diagram")
            return False

        # Get main geometry
        if hasattr(country_polygon, "geometry"):
            main_geom = country_polygon.geometry.iloc[0]
        else:
            main_geom = country_polygon

        print(
            f"\n5. Inspecting {len(voronoi_polygons)} Voronoi regions individually..."
        )
        print("   Press Enter after each polygon to continue to the next...")

        for i, (poly, capital_row) in enumerate(
            zip(voronoi_polygons, capitals.iterrows())
        ):
            idx, capital_data = capital_row
            capital_name = capital_data.get("NAME", f"Capital {i}")

            print(f"\n{'='*60}")
            print(f"POLYGON {i+1}/{len(voronoi_polygons)}: {capital_name}")
            print(f"{'='*60}")

            # Create individual plot
            fig, ax = plt.subplots(1, 1, figsize=(12, 10))

            # Plot country boundary
            if hasattr(country_polygon, "geometry"):
                country_polygon.boundary.plot(ax=ax, color="black", linewidth=2)
            else:
                x, y = country_polygon.boundary.xy
                ax.plot(x, y, color="black", linewidth=2)

            # Plot this specific polygon
            if poly is not None and not poly.is_empty:
                # Polygon analysis
                area = poly.area
                is_infinite = _touches_boundary(poly, main_geom)
                vertex_count = _count_vertices(poly)

                print(f"📊 Polygon Analysis:")
                print(f"   - Area: {area:.6f}")
                print(f"   - Vertices: {vertex_count}")
                print(f"   - Touches boundary (infinite): {is_infinite}")
                print(f"   - Polygon type: {type(poly).__name__}")
                print(f"   - Is valid: {poly.is_valid}")
                print(f"   - Is empty: {poly.is_empty}")

                # Plot the polygon
                if hasattr(poly, "geoms"):
                    # MultiPolygon
                    for j, geom in enumerate(poly.geoms):
                        x, y = geom.exterior.xy
                        ax.fill(
                            x,
                            y,
                            color=f"C{i%10}",
                            alpha=0.7,
                            edgecolor="red",
                            linewidth=3,
                            label=f"{capital_name} (Part {j+1})",
                        )
                else:
                    # Single Polygon
                    x, y = poly.exterior.xy
                    ax.fill(
                        x,
                        y,
                        color=f"C{i%10}",
                        alpha=0.7,
                        edgecolor="red",
                        linewidth=3,
                        label=capital_name,
                    )

                # Mark the capital city
                capital_x = capital_data.geometry.x
                capital_y = capital_data.geometry.y
                ax.plot(
                    capital_x,
                    capital_y,
                    "r*",
                    markersize=20,
                    markeredgecolor="darkred",
                    markeredgewidth=2,
                    label=f"{capital_name} (Capital)",
                )

                # Add label
                ax.annotate(
                    capital_name,
                    (capital_x, capital_y),
                    xytext=(10, 10),
                    textcoords="offset points",
                    fontsize=12,
                    fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.5", facecolor="yellow", alpha=0.9),
                )

            else:
                print("❌ Polygon is None or empty!")
                ax.text(
                    0.5,
                    0.5,
                    f"EMPTY POLYGON\n{capital_name}",
                    transform=ax.transAxes,
                    ha="center",
                    va="center",
                    fontsize=16,
                    color="red",
                    fontweight="bold",
                )

            # Set bounds with margin around the polygon
            if poly is not None and not poly.is_empty:
                bounds = poly.bounds
            else:
                bounds = main_geom.bounds

            margin = max(bounds[2] - bounds[0], bounds[3] - bounds[1]) * 0.1
            ax.set_xlim(bounds[0] - margin, bounds[2] + margin)
            ax.set_ylim(bounds[1] - margin, bounds[3] + margin)

            ax.set_title(
                f"{country_name} - Polygon {i+1}: {capital_name}",
                fontsize=14,
                fontweight="bold",
            )
            ax.set_xlabel("Longitude")
            ax.set_ylabel("Latitude")
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.set_aspect("equal")

            plt.tight_layout()
            plt.show()

            # Wait for user input
            user_input = input(
                f"\nPolygon {i+1} displayed. Press Enter to continue (or 'q' to quit inspection): "
            )
            if user_input.lower() == "q":
                break

            plt.close(fig)

        print(f"\n✅ Completed individual polygon inspection for {country_name}")
        return True

    except Exception as e:
        print(f"❌ Error inspecting {country_name}: {e}")
        import traceback

        traceback.print_exc()
        return False


def _touches_boundary(poly, main_geom):
    """Check if polygon touches the country boundary (indicating infinite region)."""
    try:
        return poly.touches(main_geom.boundary) or poly.intersects(main_geom.boundary)
    except:
        return False


def _count_vertices(poly):
    """Count vertices in a polygon."""
    try:
        if hasattr(poly, "geoms"):
            return sum(len(geom.exterior.coords) for geom in poly.geoms)
        else:
            return len(poly.exterior.coords)
    except:
        return 0


def main():
    """Test Voronoi diagrams for multiple countries with manual inspection."""
    print("Testing Improved Voronoi Diagram Functionality")
    print("=" * 50)
    print("Choose inspection mode:")
    print("1. Quick overview (all countries displayed sequentially)")
    print("2. Detailed polygon inspection (examine each polygon individually)")
    print("=" * 50)

    while True:
        try:
            choice = input("Enter choice (1 or 2): ").strip()
            if choice in ["1", "2"]:
                break
            print("Please enter 1 or 2")
        except KeyboardInterrupt:
            print("\nExiting...")
            return

    # Test countries with different characteristics
    test_countries = [
        "Argentina",  # Large country with many capitals (good for testing infinite regions)
        "Chile",  # Long, narrow country (challenging geometry)
        "Uruguay",  # Smaller country (fewer capitals)
        "Switzerland",  # European country (different dataset)
    ]

    if choice == "1":
        # Quick overview mode
        print("\n=== QUICK OVERVIEW MODE ===")
        print("Each country will be displayed individually for manual inspection.")
        print("Press Enter after viewing each diagram to continue to the next one.")

        results = {}

        for i, country in enumerate(test_countries, 1):
            print(f"\n{'='*20} [{i}/{len(test_countries)}] {'='*20}")
            print(f"Now displaying: {country}")
            print("=" * 50)

            success = voronoi_test_for_country(country)
            results[country] = success

            if success:
                print(f"\n✅ {country} Voronoi diagram displayed successfully.")
                print("👀 Please inspect the diagram carefully:")
                print("   - Check if all regions are properly bounded")
                print("   - Look for any missing or incorrect infinite regions")
                print("   - Verify that colors are distinct for each region")
                print("   - Ensure edges are properly clipped to country boundary")
            else:
                print(f"\n❌ Failed to create diagram for {country}")

            if i < len(test_countries):
                next_country = (
                    test_countries[i] if i < len(test_countries) else "Summary"
                )
                input(
                    f"\nPress Enter to continue to the next country ({next_country})..."
                )
            else:
                input("\nPress Enter to see the final summary...")

        # Summary
        print("\n" + "=" * 60)
        print("FINAL SUMMARY:")
        print("=" * 60)
        successful = sum(results.values())
        total = len(results)

        for country, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"  {country}: {status}")

        print(f"\nOverall: {successful}/{total} countries processed successfully")

    else:
        # Detailed inspection mode
        print("\n=== DETAILED POLYGON INSPECTION MODE ===")
        print("Each polygon will be displayed individually with analysis.")

        print("\nAvailable countries:")
        for i, country in enumerate(test_countries, 1):
            print(f"  {i}. {country}")

        while True:
            try:
                country_choice = input(
                    f"\nEnter country number (1-{len(test_countries)}) or 'q' to quit: "
                ).strip()
                if country_choice.lower() == "q":
                    print("Exiting...")
                    return

                country_idx = int(country_choice) - 1
                if 0 <= country_idx < len(test_countries):
                    selected_country = test_countries[country_idx]
                    inspect_individual_polygons(selected_country)
                    break
                else:
                    print(f"Please enter a number between 1 and {len(test_countries)}")
            except ValueError:
                print("Please enter a valid number")
            except KeyboardInterrupt:
                print("\nExiting...")
                return

    print("\n💡 If you found issues with specific polygons:")
    print("   - Note which country and which capital city region looks wrong")
    print("   - Check if it's an infinite region (at country boundary)")
    print("   - Report the specific geometric issue you observed")


if __name__ == "__main__":
    main()
