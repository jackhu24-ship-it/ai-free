# -*- coding: utf-8 -*-
"""
PHANTOM Grid - Abstract Grid Interface
======================================
Defines the base contract for overlapping/chimera grid blocks and cell classification.
"""
from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Dict, Tuple, Optional
import numpy as np


class CellStatus(IntEnum):
    """Classification status for each grid cell in an overlapping mesh."""
    HOLE = 0       # Blanked cell: covered by solid body or finer mesh, skipped in PDE update
    FIELD = 1      # Active fluid / physical domain cell evaluated by PDE solver
    RECEIVER = 2   # Fringe / Receiver boundary cell updated by interpolation from a donor grid


class AbstractGrid(ABC):
    """
    Abstract Base Class for all grid blocks in the PHANTOM overlapping mesh system.
    Decouples topology and coordinates from PDE numerical solvers.
    """

    def __init__(self, grid_id: str):
        self.grid_id = grid_id
        self.status_mask: Optional[np.ndarray] = None
        self.fields: Dict[str, np.ndarray] = {}

    @abstractmethod
    def get_coordinates(self) -> Tuple[np.ndarray, np.ndarray]:
        """Return coordinate meshgrids (X, Y)."""
        pass

    @abstractmethod
    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        """Return (x_min, x_max, y_min, y_max) bounding box."""
        pass

    @abstractmethod
    def get_shape(self) -> Tuple[int, int]:
        """Return grid shape (nx, ny)."""
        pass

    def set_field(self, name: str, data: np.ndarray) -> None:
        """Store or update a physical field array."""
        expected_shape = self.get_shape()
        if data.shape != expected_shape:
            raise ValueError(
                f"Grid '{self.grid_id}': field '{name}' shape {data.shape} "
                f"does not match grid shape {expected_shape}"
            )
        self.fields[name] = data.copy()

    def get_field(self, name: str) -> np.ndarray:
        """Retrieve a physical field array."""
        if name not in self.fields:
            raise KeyError(f"Grid '{self.grid_id}': field '{name}' not found")
        return self.fields[name]

    @abstractmethod
    def step_pde(self, dt: float) -> None:
        """
        Advance PDE by time step dt locally.
        Only updates nodes where status_mask == CellStatus.FIELD.
        """
        pass
