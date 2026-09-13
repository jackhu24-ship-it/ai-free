# -*- coding: utf-8 -*-
"""
Week 3 Verification Test - Geometric Intersection & Hole Cutting
================================================================
Verifies:
1. Dynamic hole cutting beneath rotated component grid.
2. Robust morphological boundary dilation (fringe/receiver layers).
3. Circular and polygonal obstacle hole cutting via ray-casting.
4. Clean partitioning into FIELD, HOLE, and RECEIVER cells.
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import numpy as np

from core.types import CellStatus
from grids.structured_cartesian import StructuredCartesianGrid
from grids.component_grid import ComponentGrid
from cutting.hole_cutter import HoleCutter, binary_dilate_2d


def test_week3_hole_cutting():
    print("=" * 65)
    print("🚀 Running Week 3 Verification: Hole Cutting & Fringe Dilation...")
    print("=" * 65)

    # 1. Test Hole Cutting by Rotated Component Grid
    bg = StructuredCartesianGrid("Background", (0.0, 1.0), (0.0, 1.0), (41, 41))
    comp = ComponentGrid(
        grid_id="RotatedFineGrid",
        local_x_range=(-0.15, 0.15),
        local_y_range=(-0.15, 0.15),
        dims=(31, 31),
        origin=(0.5, 0.5),
        angle_rad=np.radians(30.0)
    )

    in_hole, fringe = HoleCutter.cut_by_component_grid(
        bg_grid=bg,
        comp_grid=comp,
        margin_ratio=0.15,
        fringe_layers=1
    )

    bg_holes = np.sum(bg.status_mask == CellStatus.HOLE)
    bg_receivers = np.sum(bg.status_mask == CellStatus.RECEIVER)
    bg_fields = np.sum(bg.status_mask == CellStatus.FIELD)
    comp_receivers = np.sum(comp.status_mask == CellStatus.RECEIVER)

    print(f"📊 Background Grid Cells: {bg.nx * bg.ny}")
    print(f"🕳️  Background HOLE Cells:      {bg_holes}")
    print(f"🔴 Background RECEIVER Fringe: {bg_receivers}")
    print(f"🟩 Background Active FIELD:    {bg_fields}")
    print(f"🟡 Component Perimeter RECEIVERS: {comp_receivers}")

    assert bg_holes > 0, "FAILED: No holes cut in background!"
    assert bg_receivers > 0, "FAILED: No receiver fringe generated around hole!"
    assert comp_receivers == (2 * (comp.nx + comp.ny) - 4), "FAILED: Component perimeter receivers mismatch!"
    assert (bg_holes + bg_receivers + bg_fields) == (bg.nx * bg.ny), "FAILED: Status cell conservation violated!"

    # 2. Test Circular Obstacle Hole Cutting
    flow_grid = StructuredCartesianGrid("FlowGrid", (0.0, 2.0), (0.0, 1.0), (41, 21))
    HoleCutter.cut_circle_obstacle(flow_grid, cx=0.5, cy=0.5, radius=0.15, fringe_layers=1)
    circle_holes = np.sum(flow_grid.status_mask == CellStatus.HOLE)
    circle_rec = np.sum(flow_grid.status_mask == CellStatus.RECEIVER)
    print(f"⭕ Circular Cylinder Obstacle: {circle_holes} HOLE cells, {circle_rec} RECEIVER fringe cells")
    assert circle_holes > 0 and circle_rec > 0, "FAILED: Circular obstacle hole cutting failed!"

    # 3. Test Polygonal Obstacle Hole Cutting (Diamond / Wing profile)
    poly_grid = StructuredCartesianGrid("PolyGrid", (0.0, 1.0), (0.0, 1.0), (31, 31))
    diamond_verts = [(0.5, 0.3), (0.7, 0.5), (0.5, 0.7), (0.3, 0.5)]
    HoleCutter.cut_polygon_obstacle(poly_grid, diamond_verts, fringe_layers=1)
    poly_holes = np.sum(poly_grid.status_mask == CellStatus.HOLE)
    poly_rec = np.sum(poly_grid.status_mask == CellStatus.RECEIVER)
    print(f"🔷 Diamond Polygon Obstacle:   {poly_holes} HOLE cells, {poly_rec} RECEIVER fringe cells")
    assert poly_holes > 0 and poly_rec > 0, "FAILED: Polygon obstacle ray-casting failed!"

    print("=" * 65)
    print("✅ [WEEK 3 VERIFICATION PASSED] Hole Cutting & Fringe Dilation 100% Operational!")
    print("=" * 65)
    return True


if __name__ == "__main__":
    success = test_week3_hole_cutting()
    if not success:
        sys.exit(1)
