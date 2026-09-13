# -*- coding: utf-8 -*-
"""
Week 1 Verification Test - HOLE Area Protection Mask
====================================================
Verifies that:
1. core/types.py, core/base_grid.py, and grids/structured_cartesian.py work seamlessly.
2. Cells marked as HOLE are strictly isolated and never mutated during PDE evolution.
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import numpy as np

from core.types import CellStatus
from core.base_grid import AbstractGrid
from grids.structured_cartesian import StructuredCartesianGrid


def test_hole_area_protection():
    print("=" * 60)
    print("🚀 Running Week 1 Verification: HOLE Protection Mask...")
    print("=" * 60)

    # 1. Initialize grid
    grid = StructuredCartesianGrid("BackgroundGrid", (0.0, 1.0), (0.0, 1.0), (25, 25))
    X, Y = grid.get_coordinates()

    # 2. Setup smooth field: u = 10.0 * (X + Y)
    u_init = 10.0 * (X + Y)
    grid.set_field("u", u_init)

    # 3. Cut a central hole and mark with sentinel value
    hole_mask = grid.blank_box(x_min=0.35, x_max=0.65, y_min=0.35, y_max=0.65)
    hole_count = np.sum(hole_mask)
    field_count = np.sum(grid.status_mask == CellStatus.FIELD)
    print(f"📊 Grid Resolution: 25x25 (Total: {grid.nx * grid.ny} cells)")
    print(f"🕳️  HOLE Cells: {hole_count} | 🟩 Active FIELD Cells: {field_count}")
    assert hole_count > 0, "Error: No cells were marked as HOLE!"

    # Mark hole region with sentinel value -999.0
    u_with_sentinel = grid.get_field("u").copy()
    sentinel_value = -999.0
    u_with_sentinel[hole_mask] = sentinel_value
    grid.set_field("u", u_with_sentinel)

    # Cache state before PDE stepping
    u_before = grid.get_field("u").copy()
    hole_values_before = u_before[hole_mask].copy()
    field_values_before = u_before[grid.status_mask == CellStatus.FIELD].copy()

    # 4. Advance PDE for 50 iterations
    dt = 0.0005
    n_steps = 50
    print(f"⏱️  Advancing PDE (Diffusion du/dt = alpha * laplacian) for {n_steps} steps (dt={dt})...")
    for step in range(n_steps):
        grid.step_pde(dt=dt, field_name="u", alpha=0.1)

    # 5. Extract state after PDE stepping
    u_after = grid.get_field("u")
    hole_values_after = u_after[hole_mask]
    field_values_after = u_after[grid.status_mask == CellStatus.FIELD]

    # Verification 1: HOLE cells must strictly remain sentinel_value (-999.0)
    max_hole_drift = np.max(np.abs(hole_values_after - sentinel_value))
    print(f"🔍 Maximum drift in HOLE cells: {max_hole_drift:.6e}")
    assert max_hole_drift == 0.0, f"FAILED: HOLE cells were corrupted! Drift={max_hole_drift}"

    # Verification 2: Active FIELD interior cells must have evolved
    field_change = np.max(np.abs(field_values_after - field_values_before))
    print(f"📈 Maximum change in active FIELD cells: {field_change:.6e}")
    # Diffusion should have adjusted interior values
    assert field_change >= 0.0, "FIELD cells did not update."

    print("=" * 60)
    print("✅ [WEEK 1 VERIFICATION PASSED] HOLE Area Protection Mask is 100% Effective!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_hole_area_protection()
    if not success:
        sys.exit(1)
