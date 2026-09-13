# -*- coding: utf-8 -*-
"""
Unit Tests for PHANTOM Overlapping Grid Package
===============================================
"""
import unittest
import numpy as np

from src.phantom_grid.base_grid import CellStatus
from src.phantom_grid.structured_block import StructuredBlock2D
from src.phantom_grid.hole_cutter import HoleCutter, binary_dilate_2d
from src.phantom_grid.interpolator import BilinearInterpolator
from src.phantom_grid.coupler import OverlapCoupler


class TestPhantomGrid(unittest.TestCase):
    """Test suite covering data abstraction, hole cutting, interpolation and coupling."""

    def test_grid_initialization_and_fields(self):
        """Test 2D structured block initialization and physical field storage."""
        block = StructuredBlock2D("bg", (0.0, 1.0), (0.0, 2.0), (11, 21))
        self.assertEqual(block.get_shape(), (11, 21))
        self.assertEqual(block.get_bounding_box(), (0.0, 1.0, 0.0, 2.0))
        self.assertAlmostEqual(block.dx, 0.1)
        self.assertAlmostEqual(block.dy, 0.1)

        X, Y = block.get_coordinates()
        self.assertEqual(X.shape, (11, 21))
        self.assertEqual(Y.shape, (11, 21))
        self.assertAlmostEqual(X[0, 0], 0.0)
        self.assertAlmostEqual(X[-1, -1], 1.0)
        self.assertAlmostEqual(Y[-1, -1], 2.0)

        # Field management
        data = np.zeros((11, 21))
        block.set_field("pressure", data)
        self.assertTrue(np.array_equal(block.get_field("pressure"), data))

        # Invalid shape check
        with self.assertRaises(ValueError):
            block.set_field("invalid", np.zeros((5, 5)))

    def test_hole_cutter_box_and_dilation(self):
        """Test rectangular hole cutting and fringe receiver generation."""
        block = StructuredBlock2D("bg", (0.0, 1.0), (0.0, 1.0), (21, 21))
        in_hole, fringe = HoleCutter.cut_box(
            block, x_min=0.35, x_max=0.65, y_min=0.35, y_max=0.65, fringe_width=1
        )

        # Check hole cells
        hole_count = np.sum(block.status_mask == CellStatus.HOLE)
        rec_count = np.sum(block.status_mask == CellStatus.RECEIVER)
        field_count = np.sum(block.status_mask == CellStatus.FIELD)

        self.assertGreater(hole_count, 0)
        self.assertGreater(rec_count, 0)
        self.assertEqual(hole_count + rec_count + field_count, 21 * 21)

        # Confirm hole nodes are marked HOLE
        X, Y = block.get_coordinates()
        center_node = (np.abs(X - 0.5) < 0.01) & (np.abs(Y - 0.5) < 0.01)
        self.assertTrue(block.status_mask[center_node][0] == CellStatus.HOLE)

    def test_hole_cutter_circle(self):
        """Test circular hole cutting (cylinder obstacle)."""
        block = StructuredBlock2D("flow", (0.0, 2.0), (0.0, 2.0), (21, 21))
        in_hole, fringe = HoleCutter.cut_circle(block, cx=1.0, cy=1.0, radius=0.3, fringe_width=1)

        hole_count = np.sum(block.status_mask == CellStatus.HOLE)
        rec_count = np.sum(block.status_mask == CellStatus.RECEIVER)
        self.assertGreater(hole_count, 0)
        self.assertGreater(rec_count, 0)

    def test_bilinear_interpolation_accuracy(self):
        """Verify 2nd-order accuracy of bilinear interpolation with analytical function."""
        # Smooth test field: f(x, y) = sin(pi * x) * cos(pi * y)
        block = StructuredBlock2D("donor", (0.0, 1.0), (0.0, 1.0), (51, 51))
        X, Y = block.get_coordinates()
        exact_field = np.sin(np.pi * X) * np.cos(np.pi * Y)
        block.set_field("phi", exact_field)

        # Query points located strictly off-grid
        xq = np.array([0.234, 0.456, 0.789, 0.500])
        yq = np.array([0.654, 0.321, 0.123, 0.500])
        exact_query = np.sin(np.pi * xq) * np.cos(np.pi * yq)

        interp_vals, valid = BilinearInterpolator.interpolate(
            donor=block, field_name="phi", xq=xq, yq=yq
        )

        self.assertTrue(np.all(valid))
        max_err = np.max(np.abs(interp_vals - exact_query))
        # Bilinear interpolation error on 51x51 (dx=0.02) should be < 1e-3
        self.assertLess(max_err, 1e-3)

    def test_bilinear_donor_validation(self):
        """Ensure interpolation rejects donor cells marked as HOLE."""
        block = StructuredBlock2D("donor", (0.0, 1.0), (0.0, 1.0), (11, 11))
        block.set_field("phi", np.ones((11, 11)))
        # Cut a hole at the center
        HoleCutter.cut_box(block, 0.4, 0.6, 0.4, 0.6, fringe_width=1)

        # Query inside the hole
        xq = np.array([0.5])
        yq = np.array([0.5])
        interp_vals, valid = BilinearInterpolator.interpolate(
            donor=block, field_name="phi", xq=xq, yq=yq, check_donor_status=True
        )
        self.assertFalse(valid[0])
        self.assertTrue(np.isnan(interp_vals[0]))

    def test_static_nesting_and_two_way_coupling(self):
        """Verify static patch setup and two-way boundary exchange."""
        # Background coarse grid
        bg = StructuredBlock2D("bg", (0.0, 1.0), (0.0, 1.0), (21, 21))
        # Component fine grid
        comp = StructuredBlock2D("comp", (0.3, 0.7), (0.3, 0.7), (25, 25))

        coupler = OverlapCoupler(bg, [comp])
        coupler.setup_static_nesting(overlap_margin_ratio=0.20, fringe_width=1)

        # Analytical function: quadratic polynomial f(x, y) = x**2 + y**2
        # (Bilinear interpolation is exact for linear, small error for quadratic)
        bg.set_field("u", bg.X**2 + bg.Y**2)
        comp.set_field("u", comp.X**2 + comp.Y**2)

        stats = coupler.transfer_boundary_data("u")
        self.assertGreater(stats["bg_to_comp"], 0)
        self.assertGreater(stats["comp_to_bg"], 0)

        # Verify component receiver boundaries match exact analytical values closely
        comp_rec = (comp.status_mask == CellStatus.RECEIVER)
        comp_u = comp.get_field("u")[comp_rec]
        comp_exact = (comp.X**2 + comp.Y**2)[comp_rec]
        comp_err = np.max(np.abs(comp_u - comp_exact))
        self.assertLess(comp_err, 0.01)

    def test_step_system_pde(self):
        """Verify coupled time-stepping executes smoothly without error."""
        bg = StructuredBlock2D("bg", (0.0, 1.0), (0.0, 1.0), (21, 21))
        comp = StructuredBlock2D("comp", (0.3, 0.7), (0.3, 0.7), (25, 25))

        coupler = OverlapCoupler(bg, [comp])
        coupler.setup_static_nesting(overlap_margin_ratio=0.20, fringe_width=1)

        # Initial Gaussian pulse
        bg.set_field("u", np.exp(-((bg.X - 0.5)**2 + (bg.Y - 0.5)**2) / 0.05))
        comp.set_field("u", np.exp(-((comp.X - 0.5)**2 + (comp.Y - 0.5)**2) / 0.05))

        # Advance 5 coupled time steps
        for _ in range(5):
            stats = coupler.step_system(dt=0.001, field_name="u", alpha=0.05)
            self.assertGreater(stats["bg_to_comp"], 0)


if __name__ == "__main__":
    unittest.main()
