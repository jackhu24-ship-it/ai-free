# -*- coding: utf-8 -*-
"""
grids/curvilinear_grid.py - 貼體曲面結構網格 (Curvilinear Grid)
==============================================================
支援任意曲線座標變換 (x(xi, eta), y(xi, eta))，
精確計算度量張量 (Metric Tensor)、逆度量微分與雅可比行列式 (Jacobian J)，
並在強守恆幾何形式下執行曲線空間中的物理偏微分方程 (PDE) 數值推進。
"""
from typing import Tuple, List, Optional
import numpy as np

from core.base_grid import AbstractGrid
from core.types import CellStatus


class CurvilinearGrid(AbstractGrid):
    """
    貼體曲面網格區塊。
    支援非正交曲線座標系，並內建幾何度量守恆律 (GCL) 與物理通量差分算子。
    """

    def __init__(
        self,
        grid_id: str,
        X: np.ndarray,
        Y: np.ndarray,
        priority: int = 10,
        periodic_xi: bool = False
    ):
        super().__init__(grid_id, priority)
        assert X.shape == Y.shape, "X 與 Y 網格維度必須完全一致"
        self.X = X.astype(np.float64)
        self.Y = Y.astype(np.float64)
        self.nx, self.ny = self.X.shape
        self.periodic_xi = periodic_xi

        # 計算度量張量與 Jacobian
        self._compute_metrics()

        # 狀態掩碼初始化
        self.status_mask = np.full((self.nx, self.ny), CellStatus.FIELD, dtype=np.int32)

        # 物理推進參數
        self.c = 1.0       # 波速
        self.alpha = 0.01  # 擴散係數

    def _compute_metrics(self) -> None:
        """計算座標變換度量張量與雅可比行列式"""
        # 1. 數值微商 (偏導算子)
        self.x_xi = np.gradient(self.X, axis=0)
        self.x_eta = np.gradient(self.X, axis=1)
        self.y_xi = np.gradient(self.Y, axis=0)
        self.y_eta = np.gradient(self.Y, axis=1)

        # 若周向週期性閉合，對 xi 邊界修正微商
        if self.periodic_xi and self.nx > 2:
            dx_per = 0.5 * (self.X[1, :] - self.X[-2, :])
            dy_per = 0.5 * (self.Y[1, :] - self.Y[-2, :])
            self.x_xi[0, :] = dx_per
            self.x_xi[-1, :] = dx_per
            self.y_xi[0, :] = dy_per
            self.y_xi[-1, :] = dy_per

        # 2. 雅可比行列式 J = x_xi * y_eta - x_eta * y_xi
        self.J = self.x_xi * self.y_eta - self.x_eta * self.y_xi

        # 確保 Jacobian 方向為正 (正向定向)
        if np.mean(self.J) < 0:
            self.J = -self.J
            self.x_xi = -self.x_xi
            self.y_xi = -self.y_xi

        # 防止除零奇異點
        self.J_safe = np.where(np.abs(self.J) < 1e-12, 1e-12, self.J)

        # 3. 逆變換度量導數 (Contravariant Metric Derivatives)
        self.xi_x = self.y_eta / self.J_safe
        self.xi_y = -self.x_eta / self.J_safe
        self.eta_x = -self.y_xi / self.J_safe
        self.eta_y = self.x_xi / self.J_safe

        # 4. 反變度量張量分量 (Contravariant Metric Tensor g^ij)
        self.g11 = self.xi_x**2 + self.xi_y**2
        self.g12 = self.xi_x * self.eta_x + self.xi_y * self.eta_y
        self.g22 = self.eta_x**2 + self.eta_y**2

    def get_coordinates(self) -> Tuple[np.ndarray, np.ndarray]:
        return self.X, self.Y

    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        return float(np.min(self.X)), float(np.max(self.X)), float(np.min(self.Y)), float(np.max(self.Y))

    def get_shape(self) -> Tuple[int, int]:
        return (self.nx, self.ny)

    def verify_geometric_conservation(self) -> float:
        """
        驗證幾何度量守恆律 (Metric Invariants / GCL):
        (y_eta)_xi - (y_xi)_eta 應在機器精度下嚴格為 0。
        """
        d_y_eta_d_xi = np.gradient(self.y_eta, axis=0)
        d_y_xi_d_eta = np.gradient(self.y_xi, axis=1)
        gcl_error = float(np.max(np.abs(d_y_eta_d_xi - d_y_xi_d_eta)))
        return gcl_error

    def compute_curvilinear_laplacian(self, field: np.ndarray) -> np.ndarray:
        """
        計算曲線座標下的強守恆型拉普拉斯運算元:
        div(grad u) = 1/J [ d/d_xi (J (g11 u_xi + g12 u_eta)) + d/d_eta (J (g12 u_xi + g22 u_eta)) ]
        """
        u_xi = np.gradient(field, axis=0)
        u_eta = np.gradient(field, axis=1)

        if self.periodic_xi and self.nx > 2:
            du_per = 0.5 * (field[1, :] - field[-2, :])
            u_xi[0, :] = du_per
            u_xi[-1, :] = du_per

        # 計算反變方向的幾何通量
        flux_xi = self.J * (self.g11 * u_xi + self.g12 * u_eta)
        flux_eta = self.J * (self.g12 * u_xi + self.g22 * u_eta)

        d_flux_xi = np.gradient(flux_xi, axis=0)
        d_flux_eta = np.gradient(flux_eta, axis=1)

        if self.periodic_xi and self.nx > 2:
            dflux_per = 0.5 * (flux_xi[1, :] - flux_xi[-2, :])
            d_flux_xi[0, :] = dflux_per
            d_flux_xi[-1, :] = dflux_per

        lap = (d_flux_xi + d_flux_eta) / self.J_safe
        return lap

    def step_pde(self, dt: float) -> None:
        """
        在貼體曲面空間推進 PDE 時間步。
        僅計算 FIELD 節點，HOLE 與 RECEIVER 嚴格隔離保護。
        """
        active_mask = (self.status_mask == CellStatus.FIELD)

        if "v" in self.fields and "u" in self.fields:
            # 2D 二階波動方程式 (Symplectic Euler)
            u = self.fields["u"]
            v = self.fields["v"]

            lap_u = self.compute_curvilinear_laplacian(u)

            # 更新速度場 v
            v[active_mask] += (self.c**2) * lap_u[active_mask] * dt
            # 更新位移場 u
            u[active_mask] += v[active_mask] * dt

        elif "u" in self.fields:
            # 2D 擴散方程
            u = self.fields["u"]
            lap_u = self.compute_curvilinear_laplacian(u)
            u[active_mask] += self.alpha * lap_u[active_mask] * dt


class CurvilinearOGrid(AbstractGrid):
    """環繞物體的 O 型貼體曲線網格"""

    def __init__(
        self,
        grid_id: str,
        n_circumferential: int = 81,  # 環向點數 (xi)
        n_radial: int = 31,           # 徑向點數 (eta)
        outer_radius: float = 1.5,
        origin: Tuple[float, float] = (0.0, 0.0),
        angle_rad: float = 0.0,
        priority: int = 10
    ):
        super().__init__(grid_id, priority)
        from geometry.transform import RigidTransform2D
        from geometry.airfoil import NACA4Airfoil

        self.n_xi = n_circumferential
        self.n_eta = n_radial
        self.nx = n_circumferential
        self.ny = n_radial
        self.transform = RigidTransform2D(origin, angle_rad)

        # 1. 取得物體表面輪廓線 (內邊界 eta=0)
        x_body, y_body = NACA4Airfoil.generate_contour(
            n_points=(n_circumferential // 2) + 1,
            thickness=0.12,
            chord=1.0
        )
        # 對齊環向點數
        idx_resample = np.linspace(0, len(x_body) - 1, self.n_xi).astype(int)
        self.x_inner = x_body[idx_resample] - 0.25  # 將重心移至 1/4 弦長處
        self.y_inner = y_body[idx_resample]

        # 2. 構建圓形外邊界 (eta=1)
        theta = np.linspace(0.0, 2.0 * np.pi, self.n_xi)
        x_outer = outer_radius * np.cos(theta)
        y_outer = outer_radius * np.sin(theta)

        # 3. 跨徑向採用幾何級數分佈生成 2D 貼體座標
        # s in [0, 1]，靠近翼面 (s=0) 處網格更密
        s = np.linspace(0.0, 1.0, self.n_eta)
        stretch = (np.exp(2.5 * s) - 1.0) / (np.exp(2.5) - 1.0)

        self.X_local = np.zeros((self.n_xi, self.n_eta), dtype=np.float64)
        self.Y_local = np.zeros((self.n_xi, self.n_eta), dtype=np.float64)

        for j in range(self.n_eta):
            w = stretch[j]
            self.X_local[:, j] = (1.0 - w) * self.x_inner + w * x_outer
            self.Y_local[:, j] = (1.0 - w) * self.y_inner + w * y_outer

        # 4. 計算幾何度量張量 (Metrics) 與 Jacobian
        self._compute_metrics()

        # 5. 初始化拓撲遮罩：最外層外邊界設為 RECEIVER
        self.status_mask = np.full((self.n_xi, self.n_eta), CellStatus.FIELD, dtype=np.int32)
        self.status_mask[:, -1] = CellStatus.RECEIVER  # 徑向最外層需從背景網格插值

    def _compute_metrics(self) -> None:
        """利用二階中心差分計算度量係數 x_xi, x_eta, y_xi, y_eta 與 Jacobian J"""
        d_xi = 1.0 / (self.n_xi - 1)
        d_eta = 1.0 / (self.n_eta - 1)

        # 環向微商
        self.x_xi = np.gradient(self.X_local, d_xi, axis=0)
        self.y_xi = np.gradient(self.Y_local, d_xi, axis=0)
        self.x_eta = np.gradient(self.X_local, d_eta, axis=1)
        self.y_eta = np.gradient(self.Y_local, d_eta, axis=1)

        # Jacobian 矩陣行列式: J = x_xi * y_eta - x_eta * y_xi
        self.J = self.x_xi * self.y_eta - self.x_eta * self.y_xi

    def get_coordinates(self) -> Tuple[np.ndarray, np.ndarray]:
        return self.transform.local_to_world(self.X_local, self.Y_local)

    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        X_w, Y_w = self.get_coordinates()
        return float(np.min(X_w)), float(np.max(X_w)), float(np.min(Y_w)), float(np.max(Y_w))

    def get_shape(self) -> Tuple[int, int]:
        return (self.n_xi, self.n_eta)

    def initialize_fields(self, field_names: List[str]) -> None:
        for name in field_names:
            self.fields[name] = np.zeros((self.n_xi, self.n_eta), dtype=np.float64)

    def step_pde(self, dt: float) -> None:
        """曲線座標系下的簡諧擴散推進"""
        if "u" not in self.fields:
            return
        u = self.fields["u"]
        compute_mask = (self.status_mask == CellStatus.FIELD)
        u_xi = np.gradient(u, axis=0)
        u_eta = np.gradient(u, axis=1)
        laplacian = (np.gradient(u_xi, axis=0) + np.gradient(u_eta, axis=1)) / (np.abs(self.J) + 1e-8)
        u[compute_mask] += dt * 0.05 * laplacian[compute_mask]
