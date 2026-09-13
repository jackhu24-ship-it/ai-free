# -*- coding: utf-8 -*-
"""
coupler/overlap_coupler.py - 跨網格雙向邊界通訊協調器
======================================================
負責協調背景網格與前景網格之間的數據傳遞，調用供體搜尋器完成 RECEIVER 點插值注入。
"""
from typing import Dict, Any, List
import numpy as np
from core.types import CellStatus
from core.base_grid import AbstractGrid
from interpolation.bilinear_stencil import BilinearDonorInterpolator


class OverlapCoupler:
    """跨網格通訊耦合器"""

    def __init__(self, bg_grid: AbstractGrid, comp_grid: AbstractGrid):
        self.bg_grid = bg_grid
        self.comp_grid = comp_grid

    def transfer_boundary_data(self, field_name: str) -> Dict[str, int]:
        """
        執行雙向邊界條件傳遞：
        1. BG -> FG：將背景網格場量插值寫入前景網格之 RECEIVER 外圈邊界。
        2. FG -> BG：將前景網格場量插值寫入背景網格孔洞外緣之 RECEIVER 邊界。
        """
        stats = {"bg_to_fg": 0, "fg_to_bg": 0}

        # 1. 傳遞通道 1：BG -> FG RECEIVER
        fg_rec_mask = (self.comp_grid.status_mask == CellStatus.RECEIVER)
        if np.any(fg_rec_mask):
            X_fg, Y_fg = self.comp_grid.get_coordinates()
            x_queries = X_fg[fg_rec_mask]
            y_queries = Y_fg[fg_rec_mask]

            interp_vals, valid = BilinearDonorInterpolator.interpolate_field(
                donor_grid=self.bg_grid,
                field_name=field_name,
                x_world=x_queries,
                y_world=y_queries,
                check_hole_donors=True
            )

            # 寫入前景受體邊界
            fg_field = self.comp_grid.get_field(field_name)
            fg_rec_idx = np.where(fg_rec_mask)
            valid_idx = (fg_rec_idx[0][valid], fg_rec_idx[1][valid])
            fg_field[valid_idx] = interp_vals[valid]
            self.comp_grid.set_field(field_name, fg_field)
            stats["bg_to_fg"] = int(np.sum(valid))

        # 2. 傳遞通道 2：FG -> BG RECEIVER
        bg_rec_mask = (self.bg_grid.status_mask == CellStatus.RECEIVER)
        if np.any(bg_rec_mask):
            X_bg, Y_bg = self.bg_grid.get_coordinates()
            x_queries = X_bg[bg_rec_mask]
            y_queries = Y_bg[bg_rec_mask]

            interp_vals, valid = BilinearDonorInterpolator.interpolate_field(
                donor_grid=self.comp_grid,
                field_name=field_name,
                x_world=x_queries,
                y_world=y_queries,
                check_hole_donors=True
            )

            # 寫入背景受體邊界
            bg_field = self.bg_grid.get_field(field_name)
            bg_rec_idx = np.where(bg_rec_mask)
            valid_idx = (bg_rec_idx[0][valid], bg_rec_idx[1][valid])
            bg_field[valid_idx] = interp_vals[valid]
            self.bg_grid.set_field(field_name, bg_field)
            stats["fg_to_bg"] = int(np.sum(valid))

        return stats
