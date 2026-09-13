# -*- coding: utf-8 -*-
"""
PHANTOM Grid - Hole Cutting & Fringe Dilation
=============================================
Performs geometric intersection, hole blanking, and boundary dilation for receiver cells.
"""
from typing import Tuple
import numpy as np
from .base_grid import AbstractGrid, CellStatus


def binary_dilate_2d(mask: np.ndarray, iterations: int = 1) -> np.ndarray:
    """
    Pure NumPy morphological 2D binary dilation with 8-neighborhood kernel.
    Guarantees zero dependency on heavy C-extensions while delivering high speed.
    """
    res = mask.copy().astype(bool)
    for _ in range(iterations):
        padded = np.pad(res, pad_width=1, mode="constant", constant_values=False)
        # 8-neighbor or 4-neighbor OR operation
        res = (
            padded[1:-1, 1:-1] |
            padded[:-2, 1:-1] | padded[2:, 1:-1] |
            padded[1:-1, :-2] | padded[1:-1, 2:] |
            padded[:-2, :-2] | padded[:-2, 2:] |
            padded[2:, :-2] | padded[2:, 2:]
        )
    return res


class HoleCutter:
    """
    Orchestrates geometric hole cutting and fringe generation on grid blocks.
    """

    @staticmethod
    def cut_box(
        grid: AbstractGrid,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
        fringe_width: int = 1
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Cuts a rectangular hole in the target grid.
        Cells strictly inside [x_min, x_max] x [y_min, y_max] become HOLE.
        Cells immediately surrounding the hole (dilated by fringe_width) become RECEIVER.
        """
        X, Y = grid.get_coordinates()
        in_hole = (X >= x_min) & (X <= x_max) & (Y >= y_min) & (Y <= y_max)

        # Mark hole cells
        grid.status_mask[in_hole] = CellStatus.HOLE

        # Dilate hole to identify fringe receiver cells
        dilated = binary_dilate_2d(in_hole, iterations=fringe_width)
        fringe = dilated & (~in_hole)

        # Only convert active FIELD cells into RECEIVERs
        to_receiver = fringe & (grid.status_mask == CellStatus.FIELD)
        grid.status_mask[to_receiver] = CellStatus.RECEIVER

        return in_hole, to_receiver

    @staticmethod
    def cut_circle(
        grid: AbstractGrid,
        cx: float,
        cy: float,
        radius: float,
        fringe_width: int = 1
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Cuts a circular hole (e.g. cylinder in cross-flow).
        """
        X, Y = grid.get_coordinates()
        dist_sq = (X - cx) ** 2 + (Y - cy) ** 2
        in_hole = dist_sq <= (radius ** 2)

        grid.status_mask[in_hole] = CellStatus.HOLE

        dilated = binary_dilate_2d(in_hole, iterations=fringe_width)
        fringe = dilated & (~in_hole)

        to_receiver = fringe & (grid.status_mask == CellStatus.FIELD)
        grid.status_mask[to_receiver] = CellStatus.RECEIVER

        return in_hole, to_receiver

    @classmethod
    def cut_for_component_grid(
        cls,
        background_grid: AbstractGrid,
        component_grid: AbstractGrid,
        overlap_margin_ratio: float = 0.20,
        fringe_width: int = 1
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Automatically cuts a hole in background_grid inside the component_grid's domain.
        A safety margin (overlap_margin_ratio) ensures the hole is strictly smaller than the
        component grid, leaving an overlap region for two-way interpolation.
        """
        cx_min, cx_max, cy_min, cy_max = component_grid.get_bounding_box()
        dx_span = cx_max - cx_min
        dy_span = cy_max - cy_min

        hx_min = cx_min + overlap_margin_ratio * dx_span
        hx_max = cx_max - overlap_margin_ratio * dx_span
        hy_min = cy_min + overlap_margin_ratio * dy_span
        hy_max = cy_max - overlap_margin_ratio * dy_span

        return cls.cut_box(background_grid, hx_min, hx_max, hy_min, hy_max, fringe_width)
