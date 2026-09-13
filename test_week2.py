# -*- coding: utf-8 -*-
"""
Week 2 Verification Test - Component Grid & Relative Coordinate Transformation
=============================================================================
Verifies:
1. ComponentGrid initialization, pose handling, and higher spatial resolution.
2. Exact numerical precision of bidirectional affine coordinate transformations.
3. Dynamic rigid body translation, rotation, and kinematic step_motion.
4. Robust point-in-grid classification in rotated local coordinate frames.
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


def test_week2_component_grid():
    print("=" * 65)
    print("🚀 Running Week 2 Verification: Component Grid & Coordinate Mapping...")
    print("=" * 65)

    # 1. Initialize Background Grid and Foreground Component Grid
    bg = StructuredCartesianGrid("Background", (0.0, 1.0), (0.0, 1.0), (21, 21))

    # Foreground grid: local canonical frame [-0.15, 0.15] x [-0.15, 0.15], 31x31 resolution
    origin_init = (0.5, 0.5)
    theta_init = np.pi / 6  # 30 degrees rotation
    comp = ComponentGrid(
        grid_id="Foreground_CylinderPatch",
        local_x_range=(-0.15, 0.15),
        local_y_range=(-0.15, 0.15),
        dims=(31, 31),
        origin=origin_init,
        angle_rad=theta_init,
        velocity=(0.2, 0.1)
    )

    print(f"📊 Background Grid: 21x21 (dx = {bg.dx:.4f}, dy = {bg.dy:.4f})")
    print(f"🎯 Component Grid:  31x31 (dx = {comp.dx:.4f}, dy = {comp.dy:.4f}) [Higher Resolution]")
    print(f"📍 Initial Pose: Origin = {comp.origin}, Angle = {np.degrees(comp.angle_rad):.1f}°")

    # 2. Verify Bidirectional Coordinate Mapping Round-trip
    X_loc, Y_loc = comp.local_X, comp.local_Y
    X_glob, Y_glob = comp.local_to_global(X_loc, Y_loc)
    X_loc_recov, Y_loc_recov = comp.global_to_local(X_glob, Y_glob)

    round_trip_err_x = np.max(np.abs(X_loc_recov - X_loc))
    round_trip_err_y = np.max(np.abs(Y_loc_recov - Y_loc))
    max_roundtrip_err = max(round_trip_err_x, round_trip_err_y)
    print(f"🔄 Round-trip Mapping Error (Local -> Global -> Local): {max_roundtrip_err:.6e}")
    assert max_roundtrip_err < 1e-14, f"FAILED: Round-trip transformation error too large: {max_roundtrip_err}"

    # 3. Verify Point Containment (is_point_inside)
    # Origin should be strictly inside
    self_origin_inside = comp.is_point_inside(np.array([comp.origin[0]]), np.array([comp.origin[1]]))
    assert self_origin_inside[0] is True or self_origin_inside[0] == 1, "Origin must be inside component grid!"

    # Far away point outside
    far_point_inside = comp.is_point_inside(np.array([0.05]), np.array([0.05]))
    assert far_point_inside[0] is False or far_point_inside[0] == 0, "Far point must be outside component grid!"
    print("📐 Geometric Point-in-Grid Containment: Verified")

    # 4. Verify Dynamic Motion (Translation & Rotation)
    dt = 0.5
    comp.step_motion(dt=dt)  # Moves by velocity * dt = (0.1, 0.05)
    expected_new_origin = np.array([0.5 + 0.2 * 0.5, 0.5 + 0.1 * 0.5])
    origin_motion_err = np.max(np.abs(comp.origin - expected_new_origin))
    print(f"🏎️  After Motion Step (dt={dt}s): New Origin = {comp.origin}")
    assert origin_motion_err < 1e-15, f"FAILED: Motion update failed, err={origin_motion_err}"

    # Verify Global Coordinates updated
    center_idx = (comp.nx // 2, comp.ny // 2)
    center_glob_coord = np.array([comp.X[center_idx], comp.Y[center_idx]])
    assert np.allclose(center_glob_coord, comp.origin, atol=1e-14), "Center node must align with origin!"
    print("📍 Global Coordinates Auto-Synchronization: Verified")

    # Rotate by 15 degrees
    comp.rotate(np.radians(15.0))
    expected_angle = theta_init + np.radians(15.0)
    assert np.isclose(comp.angle_rad, expected_angle), "Rotation update failed!"
    print(f"🔄 Dynamic Rotation: New Angle = {np.degrees(comp.angle_rad):.1f}°: Verified")

    print("=" * 65)
    print("✅ [WEEK 2 VERIFICATION PASSED] Component Grid & Relative Mapping 100% Operational!")
    print("=" * 65)
    return True


if __name__ == "__main__":
    success = test_week2_component_grid()
    if not success:
        sys.exit(1)
