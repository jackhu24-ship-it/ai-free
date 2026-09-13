# -*- coding: utf-8 -*-
"""
PHANTOM Grid - Structured Cartesian Grid
========================================
Implements a 2D structured Cartesian grid with HOLE protection mask enforcement.
"""
from typing import Tuple, Optional
import numpy as np
from core.base_grid import AbstractGrid
from core.types import CellStatus


class StructuredCartesianGrid(AbstractGrid):
    """
    2D Structured Cartesian grid block with uniform spatial resolution.
    Strictly isolates HOLE and RECEIVER cells during PDE time steps.
    """

    def __init__(
        self,
        grid_id: str,
        bounds: Optional[Tuple[float, ...]] = None,
        shape: Optional[Tuple[int, int]] = None,
        x_range: Optional[Tuple[float, float]] = None,
        y_range: Optional[Tuple[float, float]] = None,
        dims: Optional[Tuple[int, int]] = None,
        priority: int = 0
    ):
        super().__init__(grid_id, priority)
        # Support Case A: bounds=(-3, 3, -3, 3), shape=(76, 76)
        # Support Case B: positional (grid_id, (0, 1), (0, 1), (21, 21))
        if bounds is not None and len(bounds) == 4:
            self.x_min, self.x_max = float(bounds[0]), float(bounds[1])
            self.y_min, self.y_max = float(bounds[2]), float(bounds[3])
            nx, ny = shape if shape is not None else dims
        elif bounds is not None and len(bounds) == 2:
            self.x_min, self.x_max = float(bounds[0]), float(bounds[1])
            self.y_min, self.y_max = float(shape[0]), float(shape[1])
            nx, ny = x_range if x_range is not None else dims
        elif x_range is not None and y_range is not None:
            self.x_min, self.x_max = float(x_range[0]), float(x_range[1])
            self.y_min, self.y_max = float(y_range[0]), float(y_range[1])
            nx, ny = dims if dims is not None else shape
        else:
            raise ValueError("Invalid grid bounds/shape specification")

        self.nx, self.ny = int(nx), int(ny)
        self.xmin, self.xmax, self.ymin, self.ymax = self.x_min, self.x_max, self.y_min, self.y_max

        if self.nx < 3 or self.ny < 3:
            raise ValueError(f"Grid dims must be at least 3x3, got ({self.nx}, {self.ny})")

        self.dx = (self.x_max - self.x_min) / (self.nx - 1)
        self.dy = (self.y_max - self.y_min) / (self.ny - 1)

        x_coords = np.linspace(self.x_min, self.x_max, self.nx)
        y_coords = np.linspace(self.y_min, self.y_max, self.ny)
        self.X, self.Y = np.meshgrid(x_coords, y_coords, indexing="ij")

        # Initial status: all cells active
        self.status_mask = np.full((self.nx, self.ny), CellStatus.FIELD, dtype=int)

    def get_coordinates(self) -> Tuple[np.ndarray, np.ndarray]:
        """Return coordinate meshgrids (X, Y)."""
        return self.X, self.Y

    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        """Return (x_min, x_max, y_min, y_max)."""
        return self.x_min, self.x_max, self.y_min, self.y_max

    def get_shape(self) -> Tuple[int, int]:
        """Return (nx, ny)."""
        return (self.nx, self.ny)

    def blank_box(self, x_min: float, x_max: float, y_min: float, y_max: float) -> np.ndarray:
        """
        Mark cells inside [x_min, x_max] x [y_min, y_max] as HOLE.
        Returns boolean mask of modified cells.
        """
        mask = (self.X >= x_min) & (self.X <= x_max) & (self.Y >= y_min) & (self.Y <= y_max)
        self.status_mask[mask] = CellStatus.HOLE
        return mask

    def blank_circle(self, cx: float, cy: float, radius: float) -> np.ndarray:
        """
        Mark cells within radius of (cx, cy) as HOLE.
        """
        dist_sq = (self.X - cx) ** 2 + (self.Y - cy) ** 2
        mask = dist_sq <= (radius ** 2)
        self.status_mask[mask] = CellStatus.HOLE
        return mask

    def compute_laplacian(self, field_name: str) -> np.ndarray:
        """
        Compute standard 2nd-order 5-point Laplacian stencil on interior cells.
        """
        u = self.get_field(field_name)
        lap = np.zeros_like(u)

        d2u_dx2 = (u[2:, 1:-1] - 2.0 * u[1:-1, 1:-1] + u[:-2, 1:-1]) / (self.dx ** 2)
        d2u_dy2 = (u[1:-1, 2:] - 2.0 * u[1:-1, 1:-1] + u[1:-1, :-2]) / (self.dy ** 2)

        lap[1:-1, 1:-1] = d2u_dx2 + d2u_dy2
        return lap

    def step_pde(self, dt: float, field_name: str = "u", alpha: float = 0.1) -> None:
        """2D 偏微分方程向量化中心差分推進 (支援 2D 波動方程式與擴散方程，嚴格保護非 FIELD 節點)"""
        if "u" not in self.fields:
            return

        u = self.fields["u"]
        laplacian = np.zeros_like(u)
        laplacian[1:-1, 1:-1] = (
            (u[2:, 1:-1] - 2.0 * u[1:-1, 1:-1] + u[:-2, 1:-1]) / (self.dx ** 2) +
            (u[1:-1, 2:] - 2.0 * u[1:-1, 1:-1] + u[1:-1, :-2]) / (self.dy ** 2)
        )

        # 僅更新計算節點 (FIELD)，HOLE 與 RECEIVER 不參與內部差分推進
        compute_mask = np.zeros_like(u, dtype=bool)
        compute_mask[1:-1, 1:-1] = (self.status_mask[1:-1, 1:-1] == int(CellStatus.FIELD))

        if "v" in self.fields:
            # 2D 波動方程式 (辛 Euler / Symplectic Euler 推進以維持能量守恆)
            v = self.fields["v"]
            c = 1.0  # 波速
            v[compute_mask] += dt * (c ** 2) * laplacian[compute_mask]
            u[compute_mask] += dt * v[compute_mask]
        else:
            # 2D 擴散方程式 (維持相容性)
            u[compute_mask] += dt * alpha * laplacian[compute_mask]
