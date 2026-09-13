# -*- coding: utf-8 -*-
"""
PHANTOM Grid Core - Base Grid Interface
=======================================
Defines the abstract interface for all computational grid blocks.
"""
from abc import ABC, abstractmethod
from typing import Dict, Tuple, Optional, List
import numpy as np
from .types import CellStatus


class AbstractGrid(ABC):
    """
    Abstract Base Class for all overlapping grid components.
    Ensures numerical PDE solvers operate solely on abstract grid interfaces.
    """

    def __init__(self, grid_id: str, priority: int = 0):
        self.grid_id = grid_id
        self.priority = priority
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

    @property
    def shape(self) -> Tuple[int, int]:
        """Return grid shape (nx, ny)."""
        return self.get_shape()

    def set_field(self, name: str, data: np.ndarray) -> None:
        """Store or update physical field data with strict shape checking."""
        expected_shape = self.get_shape()
        if data.shape != expected_shape:
            raise ValueError(
                f"Grid '{self.grid_id}': field '{name}' shape {data.shape} "
                f"does not match grid shape {expected_shape}"
            )
        self.fields[name] = data.copy()

    def initialize_fields(self, field_names: List[str]) -> None:
        """Initialize specified physical fields with zeros."""
        nx, ny = self.get_shape()
        for name in field_names:
            self.fields[name] = np.zeros((nx, ny), dtype=np.float64)

    def get_field(self, name: str) -> np.ndarray:
        """Retrieve physical field data."""
        if name not in self.fields:
            raise KeyError(f"Grid '{self.grid_id}': field '{name}' not found")
        return self.fields[name]

    @abstractmethod
    def step_pde(self, dt: float) -> None:
        """
        Advance local PDE in time by step dt.
        STRICT ENFORCEMENT: Only cells with status_mask == CellStatus.FIELD are modified.
        Cells marked HOLE or RECEIVER must remain untouched by the local PDE stencil.
        """
        pass
