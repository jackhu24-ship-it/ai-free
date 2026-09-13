# -*- coding: utf-8 -*-
"""
solver/conservation_monitor.py - 全域物理守恆性即時積分監控器
============================================================
精確計算多網格系統（含貼體曲面與笛卡爾背景網格）的總質量、總動量與能量積分，
實時跟蹤長時間數值模擬過程中的物理守恆漂移，供競賽答辯與驗收審計。
"""
from typing import List, Dict, Tuple
import numpy as np

from core.types import CellStatus
from core.base_grid import AbstractGrid
from grids.curvilinear_grid import CurvilinearGrid
from grids.structured_cartesian import StructuredCartesianGrid


class ConservationMonitor:
    """全域物理守恆量監控器"""

    def __init__(self, grids: List[AbstractGrid]):
        self.grids = grids
        self.initial_mass: Dict[str, float] = {}
        self.mass_history: Dict[str, List[float]] = {}
        self.relative_drift_history: Dict[str, List[float]] = {}

    def compute_grid_integral(self, grid: AbstractGrid, field_name: str) -> float:
        """計算單一網格上有效區域 (FIELD 節點) 的微分體素面積分"""
        if field_name not in grid.fields:
            return 0.0

        field = grid.fields[field_name]
        # 僅統計真實計算點 (FIELD)，排除 HOLE 與交界 RECEIVER 以防重疊重複計算
        active_mask = (grid.status_mask == CellStatus.FIELD)

        if isinstance(grid, CurvilinearGrid):
            # 貼體曲面微元: dOmega = |J| * d_xi * d_eta
            cell_areas = np.abs(grid.J)
        elif isinstance(grid, StructuredCartesianGrid):
            cell_areas = np.full((grid.nx, grid.ny), grid.dx * grid.dy, dtype=np.float64)
        else:
            dx = getattr(grid, "dx", 1.0)
            dy = getattr(grid, "dy", 1.0)
            nx, ny = grid.get_shape()
            cell_areas = np.full((nx, ny), dx * dy, dtype=np.float64)

        integral = float(np.sum(field[active_mask] * cell_areas[active_mask]))
        return integral

    def compute_total_mass(self, field_name: str) -> float:
        """計算所有網格在全域空間的物理量總積分"""
        total = sum(self.compute_grid_integral(g, field_name) for g in self.grids)
        return total

    def record_step(self, step_idx: int, field_names: List[str]) -> Dict[str, float]:
        """記錄當前時間步的守恆量並計算相對漂移"""
        current_drifts = {}
        for f in field_names:
            total_m = self.compute_total_mass(f)

            if f not in self.initial_mass:
                self.initial_mass[f] = total_m
                self.mass_history[f] = []
                self.relative_drift_history[f] = []

            m0 = self.initial_mass[f]
            # 計算相對漂移 (漂移誤差)
            denom = abs(m0) if abs(m0) > 1e-12 else 1.0
            drift = abs(total_m - m0) / denom

            self.mass_history[f].append(total_m)
            self.relative_drift_history[f].append(drift)
            current_drifts[f] = drift

        return current_drifts
