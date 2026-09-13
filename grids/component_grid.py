# -*- coding: utf-8 -*-
"""
grids/component_grid.py - 具備剛體運動能力的局部高解析度前景網格
============================================================
局部自適應前景組件網格，封裝 RigidTransform2D 剛體運動引擎。
"""
from typing import Tuple, List, Optional
import numpy as np
from core.base_grid import AbstractGrid
from core.types import CellStatus
from geometry.transform import RigidTransform2D


class ComponentGrid(AbstractGrid):
    """局部自適應前景組件網格"""

    def __init__(
        self,
        grid_id: str,
        local_bounds: Optional[Tuple[float, ...]] = None,
        shape: Optional[Tuple[int, int]] = None,
        local_x_range: Optional[Tuple[float, float]] = None,
        local_y_range: Optional[Tuple[float, float]] = None,
        origin: Tuple[float, float] = (0.0, 0.0),
        angle_rad: float = 0.0,
        priority: int = 10,  # 預設高於背景網格 (Priority 0)
        velocity: Tuple[float, float] = (0.0, 0.0),
        dims: Optional[Tuple[int, int]] = None
    ):
        super().__init__(grid_id, priority)

        if local_bounds is not None and len(local_bounds) == 4:
            self.xmin, self.xmax, self.ymin, self.ymax = (
                float(local_bounds[0]), float(local_bounds[1]),
                float(local_bounds[2]), float(local_bounds[3])
            )
        elif local_x_range is not None and local_y_range is not None:
            self.xmin, self.xmax = float(local_x_range[0]), float(local_x_range[1])
            self.ymin, self.ymax = float(local_y_range[0]), float(local_y_range[1])
        elif local_bounds is not None and len(local_bounds) == 2 and local_y_range is not None:
            self.xmin, self.xmax = float(local_bounds[0]), float(local_bounds[1])
            self.ymin, self.ymax = float(local_y_range[0]), float(local_y_range[1])
        else:
            raise ValueError("Invalid local_bounds/range specification")

        actual_shape = shape if shape is not None else dims
        self.nx, self.ny = int(actual_shape[0]), int(actual_shape[1])
        self.transform = RigidTransform2D(origin, angle_rad)
        self.velocity = np.array([float(velocity[0]), float(velocity[1])], dtype=np.float64)

        # 1. 構建局部的標準正規網格
        x_loc = np.linspace(self.xmin, self.xmax, self.nx)
        y_loc = np.linspace(self.ymin, self.ymax, self.ny)
        self.X_local, self.Y_local = np.meshgrid(x_loc, y_loc, indexing='ij')

        self.dx = (self.xmax - self.xmin) / (self.nx - 1)
        self.dy = (self.ymax - self.ymin) / (self.ny - 1)

        # 本地座標別名
        self.local_X = self.X_local
        self.local_Y = self.Y_local
        self.local_x_min = self.xmin
        self.local_x_max = self.xmax
        self.local_y_min = self.ymin
        self.local_y_max = self.ymax

        # 2. 初始化單元狀態 (周圍最外圈 1 層預設標記為 RECEIVER 接收層)
        self.status_mask = np.full((self.nx, self.ny), CellStatus.FIELD, dtype=np.int32)
        self._mark_outer_boundary_as_receiver()

    def _mark_outer_boundary_as_receiver(self) -> None:
        """前景網格的外邊界必須依賴背景網格插值輸入，因此設為 RECEIVER"""
        self.status_mask[0, :] = CellStatus.RECEIVER
        self.status_mask[-1, :] = CellStatus.RECEIVER
        self.status_mask[:, 0] = CellStatus.RECEIVER
        self.status_mask[:, -1] = CellStatus.RECEIVER

    def get_coordinates(self) -> Tuple[np.ndarray, np.ndarray]:
        """回傳當前時間步映射到全域世界坐標的 (X, Y) 矩陣"""
        return self.transform.local_to_world(self.X_local, self.Y_local)

    @property
    def X(self) -> np.ndarray:
        return self.get_coordinates()[0]

    @property
    def Y(self) -> np.ndarray:
        return self.get_coordinates()[1]

    @property
    def origin(self) -> np.ndarray:
        return np.array([self.transform.x0, self.transform.y0], dtype=np.float64)

    @property
    def angle_rad(self) -> float:
        return self.transform.theta

    def get_local_coordinates(self) -> Tuple[np.ndarray, np.ndarray]:
        """回傳本體局部座標"""
        return self.X_local, self.Y_local

    def set_motion(self, origin: Tuple[float, float], angle_rad: float) -> None:
        """更新前景網格的世界位姿 (模擬運動/自適應特徵追蹤)"""
        self.transform.set_pose(origin, angle_rad)

    def set_pose(self, origin: Tuple[float, float], angle_rad: Optional[float] = None) -> None:
        theta = angle_rad if angle_rad is not None else self.transform.theta
        self.transform.set_pose(origin, theta)

    def translate(self, dx: float, dy: float) -> None:
        self.transform.set_pose((self.transform.x0 + dx, self.transform.y0 + dy), self.transform.theta)

    def rotate(self, dtheta: float) -> None:
        self.transform.set_pose((self.transform.x0, self.transform.y0), self.transform.theta + dtheta)

    def step_motion(self, dt: float) -> None:
        self.translate(self.velocity[0] * dt, self.velocity[1] * dt)

    def local_to_global(self, x_loc: np.ndarray, y_loc: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        return self.transform.local_to_world(x_loc, y_loc)

    def global_to_local(self, x_w: np.ndarray, y_w: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        return self.transform.world_to_local(x_w, y_w)

    def is_point_inside(self, x_w: np.ndarray, y_w: np.ndarray, margin: float = 0.0) -> np.ndarray:
        x_loc, y_loc = self.transform.world_to_local(x_w, y_w)
        inside = (
            (x_loc >= (self.xmin + margin)) &
            (x_loc <= (self.xmax - margin)) &
            (y_loc >= (self.ymin + margin)) &
            (y_loc <= (self.ymax - margin))
        )
        return inside

    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        X_w, Y_w = self.get_coordinates()
        return float(np.min(X_w)), float(np.max(X_w)), float(np.min(Y_w)), float(np.max(Y_w))

    def get_shape(self) -> Tuple[int, int]:
        return (self.nx, self.ny)

    def initialize_fields(self, field_names: List[str]) -> None:
        for name in field_names:
            self.fields[name] = np.zeros((self.nx, self.ny), dtype=np.float64)

    def step_pde(self, dt: float) -> None:
        """2D 偏微分方程向量化中心差分推進 (支援 2D 波動方程式與擴散方程，嚴格保護非 FIELD 節點)"""
        if "u" not in self.fields:
            return

        u = self.fields["u"]
        laplacian = np.zeros_like(u)

        laplacian[1:-1, 1:-1] = (
            (u[2:, 1:-1] - 2 * u[1:-1, 1:-1] + u[:-2, 1:-1]) / (self.dx ** 2) +
            (u[1:-1, 2:] - 2 * u[1:-1, 1:-1] + u[1:-1, :-2]) / (self.dy ** 2)
        )

        compute_mask = np.zeros_like(u, dtype=bool)
        compute_mask[1:-1, 1:-1] = (self.status_mask[1:-1, 1:-1] == int(CellStatus.FIELD))

        if "v" in self.fields:
            # 2D 波動方程式 (辛 Euler / Symplectic Euler 推進以維持能量守恆)
            v = self.fields["v"]
            c = 1.0  # 波速
            v[compute_mask] += dt * (c ** 2) * laplacian[compute_mask]
            u[compute_mask] += dt * v[compute_mask]
        else:
            alpha = 0.1
            u[compute_mask] += dt * alpha * laplacian[compute_mask]
