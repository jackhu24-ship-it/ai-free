# -*- coding: utf-8 -*-
"""
interpolation/bilinear_stencil.py - 供體搜尋與雙線性插值權重組裝器
===================================================================
實現 O(1) 向量化供體單元搜尋與四點雙線性插值權重組裝。
自動處理剛體座標變換與 HOLE 供體單元排除。
"""
from typing import Tuple, Optional, Any
import numpy as np
from core.types import CellStatus
from core.base_grid import AbstractGrid


class BilinearDonorInterpolator:
    """
    供體單元定位器與雙線性插值權重組裝引擎。
    """

    @staticmethod
    def locate_and_weight(
        donor_grid: AbstractGrid,
        x_world: np.ndarray,
        y_world: np.ndarray,
        check_hole_donors: bool = True
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        在供體網格中搜尋包圍查詢點 (x_world, y_world) 的供體單元，並計算雙線性權重。

        回傳:
            weights: (4, N) 權重陣列 [w00, w10, w01, w11]，各列嚴格滿足 sum(w_i) = 1.0
            corner_indices: (4, 2, N) 四個頂點在供體網格中的 (i, j) 索引
            valid_mask: (N,) 布林陣列，指示供體是否合法 (在凸包範圍內且非 HOLE)
        """
        xw = np.asarray(x_world, dtype=np.float64)
        yw = np.asarray(y_world, dtype=np.float64)
        orig_shape = xw.shape
        xw_flat = xw.ravel()
        yw_flat = yw.ravel()
        n_pts = xw_flat.size

        # 1. 座標轉換：若供體網格具備 transform (如 ComponentGrid)，將世界座標轉為其局部座標
        if hasattr(donor_grid, "transform"):
            x_loc, y_loc = donor_grid.transform.world_to_local(xw_flat, yw_flat)
            xmin, xmax = donor_grid.xmin, donor_grid.xmax
            ymin, ymax = donor_grid.ymin, donor_grid.ymax
        else:
            x_loc, y_loc = xw_flat, yw_flat
            xmin, xmax = donor_grid.x_min, donor_grid.x_max
            ymin, ymax = donor_grid.y_min, donor_grid.y_max

        dx, dy = donor_grid.dx, donor_grid.dy
        nx, ny = donor_grid.nx, donor_grid.ny

        # 2. 邊界與幾何包含檢定
        in_bounds = (
            (x_loc >= xmin) & (x_loc <= xmax) &
            (y_loc >= ymin) & (y_loc <= ymax)
        )

        # 3. 計算連續單元座標與整數網格索引 (O(1) 直接映射)
        xi_continuous = (x_loc - xmin) / dx
        eta_continuous = (y_loc - ymin) / dy

        i0 = np.clip(np.floor(xi_continuous).astype(np.int32), 0, nx - 2)
        j0 = np.clip(np.floor(eta_continuous).astype(np.int32), 0, ny - 2)
        i1 = i0 + 1
        j1 = j0 + 1

        # 局部正規化單元座標 [0, 1]
        xi = np.clip(xi_continuous - i0, 0.0, 1.0)
        eta = np.clip(eta_continuous - j0, 0.0, 1.0)

        # 4. 雙線性插值基底函數權重
        w00 = (1.0 - xi) * (1.0 - eta)
        w10 = xi * (1.0 - eta)
        w01 = (1.0 - xi) * eta
        w11 = xi * eta

        weights = np.vstack([w00, w10, w01, w11])  # (4, N)

        # 四頂點索引組合: (0,0), (1,0), (0,1), (1,1)
        # shape: (4, 2, N)
        corners = np.array([
            [i0, j0],
            [i1, j0],
            [i0, j1],
            [i1, j1]
        ], dtype=np.int32)

        # 5. 供體單元品質檢驗：檢查四個頂點是否包含 HOLE 盲點
        valid = in_bounds.copy()
        if check_hole_donors and donor_grid.status_mask is not None:
            mask = donor_grid.status_mask
            no_holes = (
                (mask[i0, j0] != CellStatus.HOLE) &
                (mask[i1, j0] != CellStatus.HOLE) &
                (mask[i0, j1] != CellStatus.HOLE) &
                (mask[i1, j1] != CellStatus.HOLE)
            )
            valid = valid & no_holes

        return weights, corners, valid

    @classmethod
    def interpolate_field(
        cls,
        donor_grid: AbstractGrid,
        field_name: str,
        x_world: np.ndarray,
        y_world: np.ndarray,
        check_hole_donors: bool = True
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        從供體網格插值提取指定物理量 field_name。

        回傳:
            interpolated_values: 與輸入座標相同形狀的插值結果陣列
            valid_mask: 有效插值點遮罩
        """
        xw = np.asarray(x_world)
        yw = np.asarray(y_world)
        orig_shape = xw.shape

        weights, corners, valid = cls.locate_and_weight(
            donor_grid, xw, yw, check_hole_donors=check_hole_donors
        )

        u = donor_grid.get_field(field_name)

        # 提取四個頂點的數值 (4, N)
        # corners[k, 0] 為 i 索引, corners[k, 1] 為 j 索引
        u00 = u[corners[0, 0], corners[0, 1]]
        u10 = u[corners[1, 0], corners[1, 1]]
        u01 = u[corners[2, 0], corners[2, 1]]
        u11 = u[corners[3, 0], corners[3, 1]]

        # 向量化加權乘積 (sum over 4 points)
        interp_flat = (
            weights[0] * u00 +
            weights[1] * u10 +
            weights[2] * u01 +
            weights[3] * u11
        )

        interp_flat[~valid] = np.nan
        return interp_flat.reshape(orig_shape), valid.reshape(orig_shape)
