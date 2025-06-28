#!/usr/bin/env python3
"""
Diagnostic script to identify Voronoi analysis issues
"""

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from map_fetcher import fetch_world_map
from voronoi_analysis import VoronoiAnalyzer


def diagnose_voronoi_issues():
    """Comprehensive diagnosis of Voronoi analysis"""

    print("=== VORONOI DIAGNOSTIC ANALYSIS ===")

    # Setup
    analyzer = VoronoiAnalyzer()
    world = fetch_world_map(resolution="high", save_path="test_world.geojson")
    argentina = world[world["NAME"].str.contains("Argentina", case=False, na=False)]
    capitals = analyzer.get_admin1_capitals("Argentina")

    print(f"Found {len(capitals)} capitals")

    # Create Voronoi diagram
    vor, voronoi_polygons, points = analyzer.create_voronoi_from_capitals(
        capitals, argentina
    )

    if vor is None:
        print("❌ CRITICAL: No Voronoi diagram created")
        return

    print(f"✅ Voronoi diagram created with {len(voronoi_polygons)} regions")

    # Diagnostic checks
    issues = []

    # Check 1: Are polygons actually polygons or circles?
    circle_count = 0
    polygon_count = 0
    for i, poly in enumerate(voronoi_polygons):
        if poly is None:
            continue

        # Check roundness (circles have roundness ≈ 0.0796)
        area = poly.area
        perimeter = poly.length
        if perimeter > 0:
            roundness = area / (perimeter**2)
            if roundness > 0.06:  # Likely a circle
                circle_count += 1
            else:
                polygon_count += 1

    if circle_count > polygon_count:
        issues.append(
            f"Too many circles: {circle_count} circles vs {polygon_count} polygons"
        )

    # Check 2: Do all capitals have regions?
    if len(voronoi_polygons) != len(capitals):
        issues.append(
            f"Mismatch: {len(capitals)} capitals but {len(voronoi_polygons)} regions"
        )

    # Check 3: Are there overlaps?
    overlap_count = 0
    for i in range(len(voronoi_polygons)):
        for j in range(i + 1, len(voronoi_polygons)):
            if voronoi_polygons[i] and voronoi_polygons[j]:
                if voronoi_polygons[i].intersects(voronoi_polygons[j]):
                    intersection = voronoi_polygons[i].intersection(voronoi_polygons[j])
                    if intersection.area > 1e-10:
                        overlap_count += 1

    if overlap_count > 0:
        issues.append(f"Found {overlap_count} overlapping region pairs")

    # Check 4: Are generating points inside their regions?
    points_outside = 0
    for i, (poly, capital_row) in enumerate(zip(voronoi_polygons, capitals.iterrows())):
        idx, capital_data = capital_row
        point = Point(capital_data.geometry.x, capital_data.geometry.y)

        if poly is None or not poly.contains(point):
            points_outside += 1

    if points_outside > 0:
        issues.append(f"{points_outside} generating points are outside their regions")

    # Check 5: Are regions properly sized?
    total_area = sum(poly.area for poly in voronoi_polygons if poly is not None)
    argentina_area = argentina.geometry.iloc[0].area
    coverage_ratio = total_area / argentina_area

    if coverage_ratio < 0.5:
        issues.append(
            f"Low coverage: Voronoi regions cover only {coverage_ratio:.1%} of country"
        )
    elif coverage_ratio > 1.2:
        issues.append(
            f"Over-coverage: Voronoi regions cover {coverage_ratio:.1%} of country"
        )

    # Check 6: Visual inspection - create diagnostic plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))

    # Left plot: Raw Voronoi regions
    argentina.plot(ax=ax1, color="lightgray", edgecolor="black", alpha=0.7)
    capitals.plot(ax=ax1, color="red", markersize=50, alpha=0.8)

    for i, poly in enumerate(voronoi_polygons):
        if poly is not None:
            gdf = gpd.GeoDataFrame([1], geometry=[poly])
            gdf.plot(ax=ax1, alpha=0.3, edgecolor="blue", linewidth=1)

    ax1.set_title("Raw Voronoi Regions")
    ax1.set_aspect("equal")

    # Right plot: Colored by type (circle vs polygon)
    argentina.plot(ax=ax2, color="lightgray", edgecolor="black", alpha=0.7)
    capitals.plot(ax=ax2, color="red", markersize=50, alpha=0.8)

    for i, poly in enumerate(voronoi_polygons):
        if poly is not None:
            # Determine if it's circle-like
            area = poly.area
            perimeter = poly.length
            if perimeter > 0:
                roundness = area / (perimeter**2)
                is_circle = roundness > 0.06
            else:
                is_circle = True

            color = "red" if is_circle else "blue"
            alpha = 0.6 if is_circle else 0.3

            gdf = gpd.GeoDataFrame([1], geometry=[poly])
            gdf.plot(ax=ax2, color=color, alpha=alpha, edgecolor="black", linewidth=1)

    ax2.set_title("Diagnostic: Red=Circles, Blue=Proper Polygons")
    ax2.set_aspect("equal")

    plt.tight_layout()
    plt.savefig("voronoi_diagnostic.png", dpi=150, bbox_inches="tight")
    print("Diagnostic plot saved as 'voronoi_diagnostic.png'")
    plt.close()

    # Report results
    print(f"\n=== DIAGNOSTIC RESULTS ===")
    if issues:
        print("❌ ISSUES FOUND:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ No major issues detected")

    print(f"\nSUMMARY:")
    print(f"   - Total regions: {len(voronoi_polygons)}")
    print(f"   - Circle-like regions: {circle_count}")
    print(f"   - Proper polygons: {polygon_count}")
    print(f"   - Coverage ratio: {coverage_ratio:.1%}")
    print(f"   - Points outside regions: {points_outside}")
    print(f"   - Overlapping pairs: {overlap_count}")

    return len(issues) == 0


if __name__ == "__main__":
    from shapely.geometry import Point

    success = diagnose_voronoi_issues()
    exit(0 if success else 1)
