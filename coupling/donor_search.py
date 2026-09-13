# -*- coding: utf-8 -*-
"""
coupling/donor_search.py - 供體單元搜尋與雙線性插值權重組裝器
===================================================================
第 4 週核心模組：
1. 供體單元搜尋 (Donor Cell Hunting)：O(1) 逆向定位包圍 RECEIVER 點的 4 個有效供體節點 (嚴格排除 HOLE 點)。
2. 插值權重組裝 (Weight Assembler)：組裝雙線性權重 (sum(w_i) = 1.0) 並建立跨網格數據傳遞通道。
"""
from typing import Tuple, Dict, Any, Optional
import numpy as np
from core.types import CellStatus
from core.base_grid import AbstractGrid


class DonorSearcher:
    """供體單元搜尋引擎：定位供體單元並計算雙線性權重"""

    @staticmethod
    def locate_donors_and_weights(
        donor_grid: AbstractGrid,
        x_world: np.ndarray,
        y_world: np.ndarray,
        check_hole_donors: bool = True
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        在 donor_grid 中逆向定位查詢點 (x_world, y_world) 的 4 個供體節點與雙線性權重。

        回傳:
            weights: (4, N) 雙線性權重矩陣，保證 sum(w_i) = 1.0
            corner_indices: (4, 2, N) 四個供體節點在供體網格中的 (i, j) 座標
            valid_mask: (N,) 布林陣列，標識供體是否合法 (在凸包範圍內且非 HOLE)
        """
        xw = np.asarray(x_world, dtype=np.float64)
        yw = np.asarray(y_world, dtype=np.float64)
        orig_shape = xw.shape
        xw_flat = xw.ravel()
        yw_flat = yw.ravel()
        n_pts = xw_flat.size

        # 1. 座標轉換：若供體網格具備 transform 則轉換至局部軸對齊參考系
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

        # 2. 幾何凸包邊界檢定
        in_bounds = (
            (x_loc >= xmin) & (x_loc <= xmax) &
            (y_loc >= ymin) & (y_loc <= ymax)
        )

        # 3. O(1) 局部解析連續單元索引
        xi_continuous = (x_loc - xmin) / dx
        eta_continuous = (y_loc - ymin) / dy

        i0 = np.clip(np.floor(xi_continuous).astype(np.int32), 0, nx - 2)
        j0 = np.clip(np.floor(eta_continuous).astype(np.int32), 0, ny - 2)
        i1 = i0 + 1
        j1 = j0 + 1

        # 局部正規化單元座標 [0, 1]
        xi = np.clip(xi_continuous - i0, 0.0, 1.0)
        eta = np.clip(eta_continuous - j0, 0.0, 1.0)

        # 4. 雙線性插值權重組裝 (∑ w_i = 1)
        w00 = (1.0 - xi) * (1.0 - eta)
        w10 = xi * (1.0 - eta)
        w01 = (1.0 - xi) * eta
        w11 = xi * eta

        weights = np.vstack([w00, w10, w01, w11])  # (4, N)

        corners = np.array([
            [i0, j0],
            [i1, j0],
            [i0, j1],
            [i1, j1]
        ], dtype=np.int32)  # (4, 2, N)

        # 5. 排除依賴 HOLE 盲點的非法供體單元
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


class WeightAssembler:
    """跨網格雙線性數據傳遞與權重組裝協調器"""

    @staticmethod
    def interpolate_field(
        donor_grid: AbstractGrid,
        field_name: str,
        x_world: np.ndarray,
        y_world: np.ndarray,
        check_hole_donors: bool = True
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        利用組裝之雙線性權重，從供體網格提取數值並注入查詢點。
        """
        xw = np.asarray(x_world)
        yw = np.asarray(y_world)
        orig_shape = xw.shape

        weights, corners, valid = DonorSearcher.locate_donors_and_weights(
            donor_grid, xw, yw, check_hole_donors=check_hole_donors
        )

        u = donor_grid.get_field(field_name)

        # 提取四頂點物理量 (4, N)
        u00 = u[corners[0, 0], corners[0, 1]]
        u10 = u[corners[1, 0], corners[1, 1]]
        u01 = u[corners[2, 0], corners[2, 1]]
        u11 = u[corners[3, 0], corners[3, 1]]

        # 向量化加權求和: u_interp = sum_i (w_i * u_i)
        interp_flat = (
            weights[0] * u00 +
            weights[1] * u10 +
            weights[2] * u01 +
            weights[3] * u11
        )

        interp_flat[~valid] = np.nan
        return interp_flat.reshape(orig_shape), valid.reshape(orig_shape)

    @classmethod
    def transfer_two_way(
        cls,
        bg_grid: AbstractGrid,
        comp_grid: AbstractGrid,
        field_name: str
    ) -> Dict[str, int]:
        """
        執行雙向數據傳遞閉環：
        1. BG -> FG RECEIVER (外邊界)
        2. FG -> BG RECEIVER (孔洞外緣)
        """
        stats = {"bg_to_fg": 0, "fg_to_bg": 0}

        # 1. BG -> FG RECEIVER
        fg_rec_mask = (comp_grid.status_mask == CellStatus.RECEIVER)
        if np.any(fg_rec_mask):
            X_fg, Y_fg = comp_grid.get_coordinates()
            xq = X_fg[fg_rec_mask]
            yq = Y_fg[fg_rec_mask]

            interp_vals, valid = cls.interpolate_field(
                donor_grid=bg_grid,
                field_name=field_name,
                x_world=xq,
                y_world=yq,
                check_hole_donors=True
            )

            fg_field = comp_grid.get_field(field_name)
            fg_rec_idx = np.where(fg_rec_mask)
            valid_idx = (fg_rec_idx[0][valid], fg_rec_idx[1][valid])
            fg_field[valid_idx] = interp_vals[valid]
            comp_grid.set_field(field_name, fg_field)
            stats["bg_to_fg"] = int(np.sum(valid))

        # 2. FG -> BG RECEIVER
        bg_rec_mask = (bg_grid.status_mask == CellStatus.RECEIVER)
        if np.any(bg_rec_mask):
            X_bg, Y_bg = bg_grid.get_coordinates()
            xq = X_bg[bg_rec_mask]
            yq = Y_bg[bg_rec_mask]

            interp_vals, valid = cls.interpolate_field(
                donor_grid=comp_grid,
                field_name=field_name,
                x_world=xq,
                y_world=yq,
                check_hole_donors=True
            )

            bg_field = bg_grid.get_field(field_name)
            bg_rec_idx = np.where(bg_rec_mask)
            valid_idx = (bg_rec_idx[0][valid], bg_rec_idx[1][valid])
            bg_field[valid_idx] = interp_vals[valid]
            bg_grid.set_field(field_name, bg_field)
            stats["fg_to_bg"] = int(np.sum(valid))

        return stats
