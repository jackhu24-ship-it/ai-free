# -*- coding: utf-8 -*-
"""
PHANTOM Grid Core - Type Definitions
===================================
Defines cell classification statuses and common data structures.
"""
from enum import IntEnum


class CellStatus(IntEnum):
    """
    Classification status of each cell/node in the overlapping grid.
    """
    HOLE = 0       # Blanked/hole cell (inside solid body or replaced by fine grid). Skipped in PDE.
    FIELD = 1      # Active computational domain cell. Updated by local PDE solver.
    RECEIVER = 2   # Fringe/receiver cell. Receives interpolated values from a donor grid.
