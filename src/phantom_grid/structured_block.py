# -*- coding: utf-8 -*-
"""
PHANTOM Grid - Structured Cartesian 2D Block
============================================
Implements a 2D structured Cartesian grid block with NumPy vectorization.
"""
from typing import Tuple, Optional
import numpy as np
from .base_grid import AbstractGrid, CellStatus


class StructuredBlock2D(AbstractGrid):
    """
    2D Structured Cartesian grid block with uniform spacing (dx, dy).
    Coordinates are indexed as (i, j) matching (nx, ny).
    """

    def __init__(
        self,
        grid_id: str,
        x_bounds: Tuple[float, float],
        y_bounds: Tuple[float, float],
        dims: Tuple[int, int]
    ):
        super().__init__(grid_id)
        self.x_min, self.x_max = float(x_bounds[0]), float(x_bounds[1])
        self.y_min, self.y_max = float(y_bounds[0]), float(y_bounds[1])
        self.nx, self.ny = int(dims[0]), int(dims[1])

        if self.nx < 3 or self.ny < 3:
            raise ValueError(f"Grid dimensions must be at least 3x3, got ({self.nx}, {self.ny})")

        self.dx = (self.x_max - self.x_min) / (self.nx - 1)
        self.dy = (self.y_max - self.y_min) / (self.ny - 1)

        x_coords = np.linspace(self.x_min, self.x_max, self.nx)
        y_coords = np.linspace(self.y_min, self.y_max, self.ny)
        self.X, self.Y = np.meshgrid(x_coords, y_coords, indexing="ij")

        # Initial status: all active field
        self.status_mask = np.full((self.nx, self.ny), CellStatus.FIELD, dtype=int)

    def get_coordinates(self) -> Tuple[np.ndarray, np.ndarray]:
        """Return coordinate meshgrids (X, Y) of shape (nx, ny)."""
        return self.X, self.Y

    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        """Return (x_min, x_max, y_min, y_max)."""
        return self.x_min, self.x_max, self.y_min, self.y_max

    def get_shape(self) -> Tuple[int, int]:
        """Return grid shape (nx, ny)."""
        return (self.nx, self.ny)

    def mark_perimeter_as_receiver(self, width: int = 1) -> None:
        """
        Mark outer boundary cells of this block as RECEIVER points.
        Useful for embedded component grids that take boundary conditions from background.
        """
        w = max(1, width)
        self.status_mask[:w, :] = CellStatus.RECEIVER
        self.status_mask[-w:, :] = CellStatus.RECEIVER
        self.status_mask[:, :w] = CellStatus.RECEIVER
        self.status_mask[:, -w:] = CellStatus.RECEIVER

    def compute_laplacian(self, field_name: str) -> np.ndarray:
        """
        Compute 2nd-order central difference Laplacian: d2/dx2 + d2/dy2.
        Boundary points and masked nodes maintain zero derivative.
        """
        u = self.get_field(field_name)
        lap = np.zeros_like(u)

        # Vectorized 5-point stencil on interior
        d2u_dx2 = (u[2:, 1:-1] - 2.0 * u[1:-1, 1:-1] + u[:-2, 1:-1]) / (self.dx ** 2)
        d2u_dy2 = (u[1:-1, 2:] - 2.0 * u[1:-1, 1:-1] + u[1:-1, :-2]) / (self.dy ** 2)

        lap[1:-1, 1:-1] = d2u_dx2 + d2u_dy2
        return lap

    def step_pde(self, dt: float, field_name: str = "u", alpha: float = 0.1) -> None:
        """
        Advance 2D diffusion equation: du/dt = alpha * Laplacian(u)
        Strictly updates only nodes where status_mask == CellStatus.FIELD.
        """
        if field_name not in self.fields:
            return

        u = self.get_field(field_name)
        lap = self.compute_laplacian(field_name)

        # Update interior FIELD cells
        update_mask = (self.status_mask == CellStatus.FIELD)
        # Exclude physical boundary if needed, but stencil is naturally 0 on outer border
        u[update_mask] += dt * alpha * lap[update_mask]
        self.set_field(field_name, u)
