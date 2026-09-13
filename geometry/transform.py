# -*- coding: utf-8 -*-
"""
geometry/transform.py - 2D 剛體座標變換引擎 (SE(2))
===================================================
基於齊次座標 (Homogeneous Coordinates) 的 SE(2) 二維剛體變換引擎。
提供局部座標系 (Local) 與世界全域座標系 (World) 之間的平移與旋轉變換。
"""
import numpy as np
from typing import Tuple


class RigidTransform2D:
    """處理局部座標系 (Local) 與世界全域座標系 (World) 之間的平移與旋轉變換"""

    def __init__(self, origin: Tuple[float, float] = (0.0, 0.0), angle_rad: float = 0.0):
        self.x0, self.y0 = float(origin[0]), float(origin[1])
        self.theta = float(angle_rad)
        self._update_matrices()

    def _update_matrices(self) -> None:
        """更新齊次變換矩陣及其逆矩陣"""
        c, s = np.cos(self.theta), np.sin(self.theta)
        # 局部 -> 世界 矩陣
        self.T_local_to_world = np.array([
            [c, -s, self.x0],
            [s,  c, self.y0],
            [0,  0,     1.0]
        ], dtype=np.float64)

        # 世界 -> 局部 矩陣 (透過代數逆運算解析求解，避免數值逆矩陣誤差)
        self.T_world_to_local = np.array([
            [ c, s, -(self.x0 * c + self.y0 * s)],
            [-s, c,  (self.x0 * s - self.y0 * c)],
            [ 0, 0,                          1.0]
        ], dtype=np.float64)

    def set_pose(self, origin: Tuple[float, float], angle_rad: float) -> None:
        """更新位姿 (Pose)"""
        self.x0, self.y0 = float(origin[0]), float(origin[1])
        self.theta = float(angle_rad)
        self._update_matrices()

    def local_to_world(self, x_loc: np.ndarray, y_loc: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """將局部座標矩陣向量化映射至世界座標"""
        orig_shape = x_loc.shape
        coords = np.vstack([x_loc.ravel(), y_loc.ravel(), np.ones(x_loc.size)])
        world_coords = self.T_local_to_world @ coords
        return world_coords[0].reshape(orig_shape), world_coords[1].reshape(orig_shape)

    def world_to_local(self, x_w: np.ndarray, y_w: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """將世界座標矩陣映射回局部座標 (供後續供體搜尋與孔洞判定使用)"""
        orig_shape = x_w.shape
        coords = np.vstack([x_w.ravel(), y_w.ravel(), np.ones(x_w.size)])
        loc_coords = self.T_world_to_local @ coords
        return loc_coords[0].reshape(orig_shape), loc_coords[1].reshape(orig_shape)
