# -*- coding: utf-8 -*-
"""
PHANTOM Grid Cutting - Geometric Intersection & Hole Cutting
============================================================
Implements:
1. Vectorized hole cutting based on component grids and solid geometry.
2. Morphological boundary dilation to identify Fringe / Receiver layers.
"""
from typing import Tuple, List
import numpy as np
from core.types import CellStatus
from core.base_grid import AbstractGrid
from grids.component_grid import ComponentGrid


def binary_dilate_2d(mask: np.ndarray, iterations: int = 1, connectivity: int = 8) -> np.ndarray:
    """
    Pure NumPy 2D morphological binary dilation.
    Args:
        mask: 2D boolean array.
        iterations: Number of layers to dilate (1 or 2 layers).
        connectivity: 4 or 8 neighborhood.
    """
    res = mask.copy().astype(bool)
    for _ in range(iterations):
        padded = np.pad(res, pad_width=1, mode="constant", constant_values=False)
        if connectivity == 4:
            res = (
                padded[1:-1, 1:-1] |
                padded[:-2, 1:-1] | padded[2:, 1:-1] |
                padded[1:-1, :-2] | padded[1:-1, 2:]
            )
        else:  # 8-connectivity
            res = (
                padded[1:-1, 1:-1] |
                padded[:-2, 1:-1] | padded[2:, 1:-1] |
                padded[1:-1, :-2] | padded[1:-1, 2:] |
                padded[:-2, :-2] | padded[:-2, 2:] |
                padded[2:, :-2] | padded[2:, 2:]
            )
    return res


def point_in_polygon_vectorized(
    x_pts: np.ndarray,
    y_pts: np.ndarray,
    poly_verts: List[Tuple[float, float]]
) -> np.ndarray:
    """
    Vectorized Ray-Casting algorithm for 2D Point-in-Polygon testing.
    """
    x = np.asarray(x_pts)
    y = np.asarray(y_pts)
    n_pts = x.size
    x_flat = x.ravel()
    y_flat = y.ravel()

    inside = np.zeros(n_pts, dtype=bool)
    n_verts = len(poly_verts)

    p1x, p1y = poly_verts[0]
    for i in range(n_verts + 1):
        p2x, p2y = poly_verts[i % n_verts]
        # Check if ray crosses edge (p1, p2)
        cond1 = (y_flat > min(p1y, p2y)) & (y_flat <= max(p1y, p2y))
        cond2 = (x_flat <= max(p1x, p2x))
        if np.any(cond1 & cond2):
            active = cond1 & cond2
            if p1y != p2y:
                x_inters = (y_flat[active] - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                cross = (p1x == p2x) | (x_flat[active] <= x_inters)
                inside[active] ^= cross
        p1x, p1y = p2x, p2y

    return inside.reshape(x.shape)


class HoleCutter:
    """
    Manages geometric intersection and status masking across overlapping grids.
    """

    @staticmethod
    def cut_by_component_grid(
        bg_grid: AbstractGrid,
        comp_grid: ComponentGrid,
        margin_ratio: float = 0.20,
        fringe_layers: int = 1
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Cuts a hole in the background grid underneath the component grid.
        Preserves an overlap margin (margin_ratio) along the component grid perimeter.
        Generates fringe_layers of RECEIVER nodes around the hole.
        """
        X_bg, Y_bg = bg_grid.get_coordinates()

        # Compute geometric margin in local component coordinates
        dx_span = comp_grid.local_x_max - comp_grid.local_x_min
        dy_span = comp_grid.local_y_max - comp_grid.local_y_min
        margin = margin_ratio * min(dx_span, dy_span)

        # 1. Identify HOLE cells in background grid
        in_hole = comp_grid.is_point_inside(X_bg, Y_bg, margin=margin)
        bg_grid.status_mask[in_hole] = CellStatus.HOLE

        # 2. Dilate hole boundary to create RECEIVER fringe
        dilated = binary_dilate_2d(in_hole, iterations=fringe_layers, connectivity=8)
        fringe_mask = dilated & (~in_hole)

        # Only convert active FIELD cells into RECEIVERs
        to_receiver = fringe_mask & (bg_grid.status_mask == CellStatus.FIELD)
        bg_grid.status_mask[to_receiver] = CellStatus.RECEIVER

        # 3. Mark outer boundary of component grid as RECEIVER (receives from bg)
        comp_grid.status_mask[:fringe_layers, :] = CellStatus.RECEIVER
        comp_grid.status_mask[-fringe_layers:, :] = CellStatus.RECEIVER
        comp_grid.status_mask[:, :fringe_layers] = CellStatus.RECEIVER
        comp_grid.status_mask[:, -fringe_layers:] = CellStatus.RECEIVER

        return in_hole, to_receiver

    @staticmethod
    def cut_circle_obstacle(
        grid: AbstractGrid,
        cx: float,
        cy: float,
        radius: float,
        fringe_layers: int = 1
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Cuts a circular obstacle (e.g. cylinder in flow).
        """
        X, Y = grid.get_coordinates()
        in_hole = ((X - cx) ** 2 + (Y - cy) ** 2) <= (radius ** 2)
        grid.status_mask[in_hole] = CellStatus.HOLE

        dilated = binary_dilate_2d(in_hole, iterations=fringe_layers, connectivity=8)
        to_receiver = dilated & (~in_hole) & (grid.status_mask == CellStatus.FIELD)
        grid.status_mask[to_receiver] = CellStatus.RECEIVER

        return in_hole, to_receiver

    @staticmethod
    def cut_polygon_obstacle(
        grid: AbstractGrid,
        vertices: List[Tuple[float, float]],
        fringe_layers: int = 1
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Cuts an arbitrary polygonal obstacle using vectorized ray-casting.
        """
        X, Y = grid.get_coordinates()
        in_hole = point_in_polygon_vectorized(X, Y, vertices)
        grid.status_mask[in_hole] = CellStatus.HOLE

        dilated = binary_dilate_2d(in_hole, iterations=fringe_layers, connectivity=8)
        to_receiver = dilated & (~in_hole) & (grid.status_mask == CellStatus.FIELD)
        grid.status_mask[to_receiver] = CellStatus.RECEIVER

        return in_hole, to_receiver
