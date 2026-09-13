# -*- coding: utf-8 -*-
"""
solver/phantom_runner.py - PHANTOM Grid 協同推進與動態耦合引擎
=============================================================
負責統一調度幾何孔洞切割、局部 PDE 求解以及雙向邊界資料交換。
全面支援 Numba CPU 多核並行編譯加速與 GPU/CuPy 稀疏邊界通訊。
"""
from typing import List, Optional
import numpy as np
from core.types import CellStatus
from core.base_grid import AbstractGrid
from grids.component_grid import ComponentGrid
from geometry.hole_cutter import HoleCutter
from coupling.interpolator import OversetInterpolator
from coupling.sparse_coupler import SparseCoupler

try:
    from solver.numba_kernels import step_wave_2d_numba
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False


class PhantomRunner:
    """協調多網格間的幾何重構、PDE 局部時間步推進與邊界插值數據交換"""

    def __init__(
        self,
        bg_grid: AbstractGrid,
        comp_grid: ComponentGrid,
        use_sparse: bool = False,
        use_numba: bool = False,
        use_gpu: bool = False
    ):
        self.bg_grid = bg_grid
        self.comp_grid = comp_grid
        self.use_sparse = use_sparse or use_gpu
        self.use_numba = use_numba and HAS_NUMBA
        self.use_gpu = use_gpu
        self.sparse_coupler: Optional[SparseCoupler] = (
            SparseCoupler(bg_grid, comp_grid, use_gpu=use_gpu) if self.use_sparse else None
        )

    def _step_grid_numba(self, grid: AbstractGrid, dt: float, c: float = 1.0) -> None:
        """調用 Numba JIT 平行核心推進 2D 波動方程式"""
        if "u" in grid.fields and "v" in grid.fields:
            active_mask = (grid.status_mask == int(CellStatus.FIELD))
            dx = float(getattr(grid, "dx", 1.0))
            dy = float(getattr(grid, "dy", 1.0))
            step_wave_2d_numba(
                grid.fields["u"],
                grid.fields["v"],
                float(dt),
                float(c),
                dx,
                dy,
                active_mask
            )
        else:
            grid.step_pde(dt)

    def rebuild_topology(self) -> None:
        """當網格相對位置移動時，動態重新切割孔洞並標記邊界接收點"""
        HoleCutter.cut_holes_and_mark_fringe(
            bg_grid=self.bg_grid,
            comp_grid=self.comp_grid,
            shrink_margin=0.15,
            fringe_layers=1
        )
        if self.use_sparse and self.sparse_coupler is not None:
            self.sparse_coupler.build()

    def step(self, dt: float, field_names: List[str]) -> None:
        """
        執行單一時間步協同計算閉環:
        1. 各網格各自執行內部節點 (FIELD) 的 PDE 時間步推進 (支援 Numba CPU 平行加速)
        2. 跨網格雙向同步 RECEIVER 邊界值 (支援 CSR 稀疏矩陣與 GPU 加速)
        """
        # 1. 局部 PDE 推進 (忽略 HOLE 與 RECEIVER 點)
        if self.use_numba:
            self._step_grid_numba(self.bg_grid, dt)
            self._step_grid_numba(self.comp_grid, dt)
        else:
            self.bg_grid.step_pde(dt)
            self.comp_grid.step_pde(dt)

        # 2. 雙向邊界數據插值交換
        if self.use_sparse and self.sparse_coupler is not None:
            self.sparse_coupler.exchange_fields(field_names)
        else:
            for field in field_names:
                OversetInterpolator.exchange_all_boundaries(
                    self.bg_grid,
                    self.comp_grid,
                    field_name=field
                )
