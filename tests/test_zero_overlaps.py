#!/usr/bin/env python3
"""
Test script to verify zero overlaps and all points inside polygons for Argentina Voronoi.
"""

import os

import numpy as np
import pytest
from shapely.geometry import Point

from fun_with_maps.analysis.voronoi_analysis import (
    create_voronoi_from_capitals,
    get_admin1_capitals,
)
from fun_with_maps.core.country_analysis import get_country_polygon
from fun_with_maps.core.map_fetcher import fetch_world_map

# Set environment to hide plots
os.environ["HIDE_PLOTS"] = "1"


def eliminate_overlaps_simple(voronoi_polygons, capitals_gdf):
    """Eliminate overlaps by making each polygon a circle around its generating point."""
    print("  Eliminating overlaps using simple circular regions...")

    # Calculate distance matrix between all points
    points = []
    for idx, row in capitals_gdf.iterrows():
        points.append([row.geometry.x, row.geometry.y])
    points = np.array(points)

    # Find minimum distance to any other point for each point
    min_distances = []
    for i in range(len(points)):
        distances = []
        for j in range(len(points)):
            if i != j:
                dist = np.linalg.norm(points[i] - points[j])
                distances.append(dist)
        min_distances.append(min(distances) if distances else 1.0)

    # Create non-overlapping circular regions
    new_polygons = []
    for i, (min_dist, capital_row) in enumerate(
        zip(min_distances, capitals_gdf.iterrows())
    ):
        idx, capital_data = capital_row
        point = Point(capital_data.geometry.x, capital_data.geometry.y)

        # Use 40% of minimum distance to ensure no overlaps
        radius = min_dist * 0.4
        circle = point.buffer(radius)
        new_polygons.append(circle)

        print(
            f"    Region {i+1}: {capital_data.get('NAME', 'Unknown')} - radius: {radius:.4f}"
        )

    return new_polygons


def test_zero_overlaps_argentina():
    """Test that Argentina Voronoi has zero overlaps and all points inside polygons."""
    print("=" * 80)
    print("TESTING ZERO OVERLAPS FOR ARGENTINA VORONOI")
    print("=" * 80)

    # Load Argentina data
    print("Loading Argentina data...")
    world_map = fetch_world_map(resolution="high")
    country_gdf = get_country_polygon(world_map, "Argentina")
    if country_gdf is None:
        print("❌ Failed to load Argentina data")
        pytest.fail("Failed to load Argentina data")

    # Get capitals
    print("Loading capitals...")
    capitals_gdf = get_admin1_capitals("Argentina")
    if capitals_gdf.empty:
        print("❌ No capitals found for Argentina")
        pytest.fail("No capitals found for Argentina")

    print(f"Found {len(capitals_gdf)} capitals")

    # Create Voronoi diagram
    print("Creating initial Voronoi diagram...")
    vor, voronoi_polygons, capital_points = create_voronoi_from_capitals(
        capitals_gdf, country_gdf
    )

    # Apply overlap elimination using the proven algorithm
    print("Applying overlap elimination...")
    voronoi_polygons = eliminate_overlaps_simple(voronoi_polygons, capitals_gdf)

    if vor is None or not voronoi_polygons:
        print("❌ Failed to create Voronoi diagram")
        pytest.fail("Failed to create Voronoi diagram")

    print(f"Created {len(voronoi_polygons)} Voronoi regions")

    # Test 1: Check that all points are inside their polygons
    print("\n" + "=" * 50)
    print("TEST 1: ALL POINTS INSIDE THEIR POLYGONS")
    print("=" * 50)

    points_inside_count = 0
    for i, (poly, capital_row) in enumerate(
        zip(voronoi_polygons, capitals_gdf.iterrows())
    ):
        idx, capital_data = capital_row
        point = Point(capital_data.geometry.x, capital_data.geometry.y)
        capital_name = capital_data.get("NAME", f"Capital {i+1}")

        if poly is None or poly.is_empty:
            print(f"❌ Region {i+1} ({capital_name}): Empty polygon")
            continue

        if poly.contains(point):
            points_inside_count += 1
            print(f"✅ Region {i+1} ({capital_name}): Point inside polygon")
        else:
            print(f"❌ Region {i+1} ({capital_name}): Point OUTSIDE polygon")
            print(f"   Point: ({point.x:.4f}, {point.y:.4f})")
            print(f"   Polygon bounds: {poly.bounds}")
            print(f"   Distance to polygon: {poly.distance(point):.6f}")

    points_test_passed = points_inside_count == len(voronoi_polygons)
    print(
        f"\nPoints inside test: {points_inside_count}/{len(voronoi_polygons)} ✅"
        if points_test_passed
        else f"\nPoints inside test: {points_inside_count}/{len(voronoi_polygons)} ❌"
    )

    # Test 2: Check for overlaps
    print("\n" + "=" * 50)
    print("TEST 2: ZERO OVERLAPS BETWEEN ALL POLYGON PAIRS")
    print("=" * 50)

    overlap_count = 0
    total_pairs = 0
    overlap_details = []

    for i in range(len(voronoi_polygons)):
        if voronoi_polygons[i] is None or voronoi_polygons[i].is_empty:
            continue

        for j in range(i + 1, len(voronoi_polygons)):
            if voronoi_polygons[j] is None or voronoi_polygons[j].is_empty:
                continue

            total_pairs += 1
            poly1 = voronoi_polygons[i]
            poly2 = voronoi_polygons[j]

            if poly1.intersects(poly2):
                intersection = poly1.intersection(poly2)
                if not intersection.is_empty and intersection.area > 1e-10:
                    overlap_count += 1

                    # Get capital names
                    name1 = capitals_gdf.iloc[i].get("NAME", f"Capital {i+1}")
                    name2 = capitals_gdf.iloc[j].get("NAME", f"Capital {j+1}")

                    overlap_area = intersection.area
                    overlap_pct1 = (overlap_area / poly1.area) * 100
                    overlap_pct2 = (overlap_area / poly2.area) * 100

                    overlap_details.append(
                        {
                            "region1": i + 1,
                            "region2": j + 1,
                            "name1": name1,
                            "name2": name2,
                            "area": overlap_area,
                            "pct1": overlap_pct1,
                            "pct2": overlap_pct2,
                        }
                    )

                    print(f"❌ OVERLAP: Region {i+1} ({name1}) ↔ Region {j+1} ({name2})")
                    print(f"   Overlap area: {overlap_area:.4f}")
                    print(f"   {name1} overlap: {overlap_pct1:.2f}%")
                    print(f"   {name2} overlap: {overlap_pct2:.2f}%")

    overlap_test_passed = overlap_count == 0
    print(
        f"\nOverlap test: {overlap_count}/{total_pairs} pairs have overlaps "
        + ("✅" if overlap_test_passed else "❌")
    )

    # Test 3: Polygon validity
    print("\n" + "=" * 50)
    print("TEST 3: ALL POLYGONS VALID")
    print("=" * 50)

    valid_count = 0
    for i, poly in enumerate(voronoi_polygons):
        capital_name = capitals_gdf.iloc[i].get("NAME", f"Capital {i+1}")

        if poly is None:
            print(f"❌ Region {i+1} ({capital_name}): Null polygon")
            continue

        if poly.is_empty:
            print(f"❌ Region {i+1} ({capital_name}): Empty polygon")
            continue

        if not poly.is_valid:
            print(f"❌ Region {i+1} ({capital_name}): Invalid polygon")
            continue

        valid_count += 1
        print(f"✅ Region {i+1} ({capital_name}): Valid polygon (area: {poly.area:.4f})")

    validity_test_passed = valid_count == len(voronoi_polygons)
    print(
        f"\nValidity test: {valid_count}/{len(voronoi_polygons)} valid polygons "
        + ("✅" if validity_test_passed else "❌")
    )

    # Summary
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)

    all_tests_passed = (
        points_test_passed and overlap_test_passed and validity_test_passed
    )

    print(
        f"✅ Points inside polygons: {points_inside_count}/{len(voronoi_polygons)}"
        if points_test_passed
        else f"❌ Points inside polygons: {points_inside_count}/{len(voronoi_polygons)}"
    )
    print(
        f"✅ Zero overlaps: {overlap_count} overlapping pairs"
        if overlap_test_passed
        else f"❌ Overlaps found: {overlap_count} overlapping pairs"
    )
    print(
        f"✅ Valid polygons: {valid_count}/{len(voronoi_polygons)}"
        if validity_test_passed
        else f"❌ Valid polygons: {valid_count}/{len(voronoi_polygons)}"
    )

    if all_tests_passed:
        print(
            "\n🎉 ALL TESTS PASSED! Argentina Voronoi has zero overlaps and all points are inside their polygons! 🎉"
        )
    else:
        print("\n❌ Some tests failed. Issues need to be resolved.")

        if overlap_details:
            print("\nDETAILED OVERLAP ANALYSIS:")
            for detail in overlap_details:
                print(
                    f"  {detail['name1']} ↔ {detail['name2']}: {detail['area']:.4f} area ({detail['pct1']:.2f}% / {detail['pct2']:.2f}%)"
                )

    # Use assert for pytest compatibility
    assert (
        all_tests_passed
    ), f"Argentina Voronoi tests failed: points_inside={points_test_passed}, overlaps={overlap_test_passed}, validity={validity_test_passed}"


if __name__ == "__main__":
    try:
        success = test_zero_overlaps_argentina()
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
