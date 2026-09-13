# -*- coding: utf-8 -*-
"""
coupling/interpolator.py - 供體搜尋與雙線性插值權重組裝
======================================================
實現 O(1) 向量化供體單元搜尋與雙線性插值權重組裝，打通重疊網格跨邊界通訊。
"""
from typing import Tuple, List, Dict
import numpy as np
from core.types import CellStatus
from core.base_grid import AbstractGrid
from grids.structured_cartesian import StructuredCartesianGrid
from grids.component_grid import ComponentGrid


class OversetInterpolator:
    """負責在供體網格與接收點之間建立幾何搜尋與數值插值傳遞"""

    @staticmethod
    def interpolate_receiver_values(
        donor_grid: AbstractGrid,
        recv_coords: Tuple[np.ndarray, np.ndarray],
        field_name: str
    ) -> np.ndarray:
        """
        將 donor_grid 上指定 field_name 的物理量雙線性插值至 recv_coords 座標點。

        參數:
            donor_grid: 提供數值的供體網格
            recv_coords: 接收點的世界座標陣列 (x_world_array, y_world_array)
            field_name: 欲傳遞的物理場名稱 (如 'u')

        回傳:
            interpolated_values: 插值後的 1D 數值陣列
        """
        x_target, y_target = recv_coords
        n_points = len(x_target)
        if n_points == 0:
            return np.array([], dtype=np.float64)

        # 1. 座標正規化：若供體是前景組件網格，先逆變換至其局部對齊座標系
        if isinstance(donor_grid, ComponentGrid):
            x_loc, y_loc = donor_grid.transform.world_to_local(x_target, y_target)
            xmin, ymin = donor_grid.xmin, donor_grid.ymin
            dx, dy = donor_grid.dx, donor_grid.dy
            nx, ny = donor_grid.nx, donor_grid.ny
        elif isinstance(donor_grid, StructuredCartesianGrid):
            x_loc, y_loc = x_target, y_target
            xmin, ymin = donor_grid.xmin, donor_grid.ymin
            dx, dy = donor_grid.dx, donor_grid.dy
            nx, ny = donor_grid.nx, donor_grid.ny
        else:
            raise NotImplementedError(f"不支援的網格型別: {type(donor_grid)}")

        # 2. 向量化供體單元索引定位 (Donor Cell Hunting)
        i = np.floor((x_loc - xmin) / dx).astype(np.int32)
        j = np.floor((y_loc - ymin) / dy).astype(np.int32)

        # 限制索引邊界，避免越界 (Out-of-bounds)
        i = np.clip(i, 0, nx - 2)
        j = np.clip(j, 0, ny - 2)

        # 3. 計算單元內部的局部標準歸一化座標 (xi, eta in [0, 1])
        xi = (x_loc - (xmin + i * dx)) / dx
        eta = (y_loc - (ymin + j * dy)) / dy

        xi = np.clip(xi, 0.0, 1.0)
        eta = np.clip(eta, 0.0, 1.0)

        # 4. 計算 4 個節點的雙線性權重 (Bilinear Weights)
        w00 = (1.0 - xi) * (1.0 - eta)
        w10 = xi * (1.0 - eta)
        w01 = (1.0 - xi) * eta
        w11 = xi * eta

        # 5. 提取供體數值並加權合成
        field_data = donor_grid.fields[field_name]
        interpolated = (
            w00 * field_data[i, j] +
            w10 * field_data[i + 1, j] +
            w01 * field_data[i, j + 1] +
            w11 * field_data[i + 1, j + 1]
        )

        return interpolated

    @classmethod
    def exchange_all_boundaries(
        cls,
        grid_a: AbstractGrid,
        grid_b: AbstractGrid,
        field_name: str
    ) -> None:
        """
        雙向同步更新兩個重疊網格上的 RECEIVER 邊界值。
        """
        for src, dst in [(grid_a, grid_b), (grid_b, grid_a)]:
            recv_mask = (dst.status_mask == CellStatus.RECEIVER)
            if not np.any(recv_mask):
                continue

            X_world, Y_world = dst.get_coordinates()
            recv_x = X_world[recv_mask]
            recv_y = Y_world[recv_mask]

            interp_vals = cls.interpolate_receiver_values(
                donor_grid=src,
                recv_coords=(recv_x, recv_y),
                field_name=field_name
            )

            dst.fields[field_name][recv_mask] = interp_vals
