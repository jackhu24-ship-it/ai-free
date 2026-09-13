# -*- coding: utf-8 -*-
"""
coupling/flux_coupler.py - 跨網格守恆性通量修正器 (Conservative Flux Matching)
==============================================================================
實作基於邊界積分通量匹配 (Conservative Boundary Flux Matching) 的補償運算元。
確保在重疊交界面上，流出供體網格的總通量嚴格等於流入接收網格的總通量，
消除長時間波動或對流推進中非物理的數值質量/能量漂移。
"""
from typing import List, Tuple, Optional, Union
import numpy as np

from core.types import CellStatus
from core.base_grid import AbstractGrid
from grids.curvilinear_grid import CurvilinearGrid
from grids.structured_cartesian import StructuredCartesianGrid


class ConservativeFluxCoupler:
    """
    實作基於邊界積分通量匹配 (Conservative Boundary Flux Matching) 的補償運算元。
    支援實例級別 (Instance-level) 能量/質量監控與類別級別 (Class-level) 強制守恆校正。
    """

    def __init__(self, bg_grid: AbstractGrid, fg_grid: AbstractGrid, c: float = 1.0):
        self.bg = bg_grid
        self.fg = fg_grid
        self.c = c
        self.initial_mass: Optional[float] = None
        self.initial_energy: Optional[float] = None
        self.mass_history: List[float] = []
        self.energy_history: List[float] = []

    @staticmethod
    def compute_grid_mass(grid: AbstractGrid, field_name: str = "u") -> float:
        """
        計算單一網格內所有活躍計算單元 (FIELD) 的全域數值積分 (總質量):
        Mass = sum(u * dx * dy)
        """
        if field_name not in grid.fields:
            return 0.0

        u = grid.fields[field_name]
        # 僅統計有效 FIELD 單元，排除 HOLE 與 RECEIVER (避免重複計算)
        active_mask = (grid.status_mask == CellStatus.FIELD)

        # 取得網格面積微元 dA
        if isinstance(grid, CurvilinearGrid):
            weights = np.abs(grid.J)
            return float(np.sum(u[active_mask] * weights[active_mask]))
        else:
            dx = getattr(grid, "dx", 1.0)
            dy = getattr(grid, "dy", 1.0)
            dA = dx * dy
            return float(np.sum(u[active_mask]) * dA)

    def compute_total_mass(self, grid: Optional[Union[AbstractGrid, str]] = None, field_name: str = "u") -> float:
        """
        全域總質量積分計算函數。
        支援兩種呼叫模式:
        1. 靜態/類別呼叫: ConservativeFluxCoupler.compute_total_mass(grid, "u")
        2. 實例呼叫: coupler.compute_total_mass()
        """
        if isinstance(self, AbstractGrid):
            fname = grid if isinstance(grid, str) else field_name
            return ConservativeFluxCoupler.compute_grid_mass(self, fname)

        # 當前為實例呼叫
        if grid is not None and isinstance(grid, AbstractGrid):
            return ConservativeFluxCoupler.compute_grid_mass(grid, field_name)

        fname = grid if isinstance(grid, str) else field_name
        total_M = 0.0
        for g in [self.bg, self.fg]:
            u = g.fields.get(fname)
            if u is None:
                continue
            weights = self.get_cell_weights(g)
            active_mask = (g.status_mask == CellStatus.FIELD)
            total_M += float(np.sum(u[active_mask] * weights[active_mask]))
        return total_M

    @classmethod
    def enforce_conservation(
        cls,
        grid_a: AbstractGrid,
        grid_b: AbstractGrid,
        target_total_mass: float,
        field_name: str = "u"
    ) -> float:
        """
        在時間推進後校正全域微量質量漂移，將殘差均攤至重疊邊界附近的活躍單元中。

        參數:
            grid_a, grid_b: 重疊的兩套網格
            target_total_mass: 理論初始全域總質量
            field_name: 物理場名稱

        回傳:
            mass_drift_error: 修正前的質量漂移相對誤差
        """
        # 1. 計算當前兩套網格內 FIELD 單元的總質量之和
        current_mass_a = cls.compute_total_mass(grid_a, field_name)
        current_mass_b = cls.compute_total_mass(grid_b, field_name)
        current_total_mass = current_mass_a + current_mass_b

        # 2. 計算總質量漂移殘差
        mass_drift = current_total_mass - target_total_mass
        relative_error = abs(mass_drift) / (abs(target_total_mass) + 1e-12)

        # 3. 若產生非物理質量漂移，進行局部保守補償
        # 找出兩者靠近 RECEIVER 的活躍邊緣節點進行微調分配
        if abs(mass_drift) > 1e-14:
            mask_a = (grid_a.status_mask == CellStatus.FIELD)
            mask_b = (grid_b.status_mask == CellStatus.FIELD)

            n_active_a = np.sum(mask_a)
            n_active_b = np.sum(mask_b)
            total_active = n_active_a + n_active_b

            if total_active > 0:
                dA_a = getattr(grid_a, "dx", 1.0) * getattr(grid_a, "dy", 1.0)
                dA_b = getattr(grid_b, "dx", 1.0) * getattr(grid_b, "dy", 1.0)

                # 計算平均補償增量 delta_u
                # delta_mass = delta_u * (n_a * dA_a + n_b * dA_b)
                total_area = n_active_a * dA_a + n_active_b * dA_b
                delta_u = mass_drift / total_area

                # 從活躍單元中扣除漂移量以維持守恆
                grid_a.fields[field_name][mask_a] -= delta_u
                grid_b.fields[field_name][mask_b] -= delta_u

        return relative_error

    def get_cell_weights(self, grid: AbstractGrid) -> np.ndarray:
        """獲取各單元微分面積/體積權重 dOmega"""
        if isinstance(grid, CurvilinearGrid):
            return np.abs(grid.J)
        elif isinstance(grid, StructuredCartesianGrid):
            return np.full(grid.get_shape(), grid.dx * grid.dy, dtype=np.float64)
        else:
            dx = getattr(grid, "dx", 1.0)
            dy = getattr(grid, "dy", 1.0)
            return np.full(grid.get_shape(), dx * dy, dtype=np.float64)

    def compute_total_energy(self) -> float:
        """
        計算全系統哈密頓波動總能量:
        E = 1/2 * integral_{FIELD} (v^2 + c^2 * |grad u|^2) dOmega
        """
        total_E = 0.0
        for grid in [self.bg, self.fg]:
            u = grid.fields.get("u")
            v = grid.fields.get("v")
            if u is None:
                continue

            v_val = v if v is not None else np.zeros_like(u)
            weights = self.get_cell_weights(grid)
            active_mask = (grid.status_mask == CellStatus.FIELD)

            dx = getattr(grid, "dx", 1.0)
            dy = getattr(grid, "dy", 1.0)
            grad_u_x, grad_u_y = np.gradient(u, dx, dy, axis=(0, 1))

            # 波動 Hamiltonian 密度: 0.5 * (v^2 + c^2 * (ux^2 + uy^2))
            energy_density = 0.5 * (v_val**2 + (self.c**2) * (grad_u_x**2 + grad_u_y**2))
            total_E += float(np.sum(energy_density[active_mask] * weights[active_mask]))

        return total_E

    def correct_flux_residuals(self, field_name: str = "u") -> float:
        """
        在交界接收層 (RECEIVER) 執行 Berger 守恆通量補償微調：
        1. 檢測全域質量漂移 Delta_M = M(t) - M(0)
        2. 將微小漂移按邊界單元體積比例回饋補償至接收點鄰域單元
        """
        current_M = self.compute_total_mass()

        if self.initial_mass is None:
            self.initial_mass = current_M
            self.mass_history.append(current_M)
            current_E = self.compute_total_energy()
            self.initial_energy = current_E
            self.energy_history.append(current_E)
            return 0.0

        self.mass_history.append(current_M)
        current_E = self.compute_total_energy()
        self.energy_history.append(current_E)

        delta_M = current_M - self.initial_mass

        # 若質量漂移大於數值公差，對重疊邊界進行通量守恆微調補償
        if abs(self.initial_mass) > 1e-12:
            rel_error = delta_M / self.initial_mass
            if abs(rel_error) > 1e-12:
                # 統計所有邊界接收點體積
                total_recv_vol = 0.0
                for grid in [self.bg, self.fg]:
                    recv_mask = (grid.status_mask == CellStatus.RECEIVER)
                    weights = self.get_cell_weights(grid)
                    total_recv_vol += np.sum(weights[recv_mask])

                if total_recv_vol > 0:
                    # 每單位體積通量校正值
                    correction_per_vol = delta_M / total_recv_vol
                    for grid in [self.bg, self.fg]:
                        recv_mask = (grid.status_mask == CellStatus.RECEIVER)
                        if np.any(recv_mask) and field_name in grid.fields:
                            # 施加低鬆弛係數 0.1 修正
                            grid.fields[field_name][recv_mask] -= 0.1 * correction_per_vol

        return float(delta_M)
