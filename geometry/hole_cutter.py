# -*- coding: utf-8 -*-
"""
geometry/hole_cutter.py - 向量化孔洞切割與 Fringe 接收層標定模組
============================================================
支援三種孔洞切割模式：
1. 剛體變換局部包圍盒切割 (SE(2) Box Hole Cutting)
2. 任意閉合多邊形射線法 (Polygon Ray-Casting Hole Cutting - 如 NACA 0012 翼型)
3. 符號距離函數切割 (SDF / Level-Set Hole Cutting - 如圓柱/球體)
"""
from typing import Tuple, List, Callable, Optional, TYPE_CHECKING
import numpy as np
from scipy.ndimage import binary_dilation
from matplotlib.path import Path as MplPath

from core.types import CellStatus
from core.base_grid import AbstractGrid

if TYPE_CHECKING:
    from grids.component_grid import ComponentGrid


class HoleCutter:
    """負責在背景網格中辨識覆蓋區域並標定 HOLE 與 RECEIVER 邊界"""

    # 4-Connectivity 十字結構元素
    CROSS_STRUCTURE = np.array([[0, 1, 0],
                                [1, 1, 1],
                                [0, 1, 0]], dtype=bool)

    @staticmethod
    def cut_holes_and_mark_fringe(
        bg_grid: AbstractGrid,
        comp_grid: 'ComponentGrid',
        shrink_margin: float = 0.15,
        fringe_layers: int = 1
    ) -> None:
        """
        模式 1: 基於剛體變換局部包圍盒之幾何孔洞切割
        """
        X_bg, Y_bg = bg_grid.get_coordinates()
        X_loc, Y_loc = comp_grid.transform.world_to_local(X_bg, Y_bg)

        xmin, xmax = comp_grid.xmin, comp_grid.xmax
        ymin, ymax = comp_grid.ymin, comp_grid.ymax

        dx_box = xmax - xmin
        dy_box = ymax - ymin
        hole_xmin = xmin + shrink_margin * dx_box
        hole_xmax = xmax - shrink_margin * dx_box
        hole_ymin = ymin + shrink_margin * dy_box
        hole_ymax = ymax - shrink_margin * dy_box

        in_hole = (
            (X_loc >= hole_xmin) & (X_loc <= hole_xmax) &
            (Y_loc >= hole_ymin) & (Y_loc <= hole_ymax)
        )

        dilated_hole = binary_dilation(in_hole, structure=HoleCutter.CROSS_STRUCTURE, iterations=fringe_layers)
        fringe_mask = dilated_hole & (~in_hole)

        bg_grid.status_mask[in_hole] = CellStatus.HOLE
        bg_grid.status_mask[fringe_mask] = CellStatus.RECEIVER

    @staticmethod
    def cut_polygon_holes_and_mark_fringe(
        bg_grid: AbstractGrid,
        polygon_vertices: np.ndarray,
        fringe_layers: int = 1
    ) -> np.ndarray:
        """
        模式 2: 任意閉合多邊形光線投射法 (Polygon Ray-Casting Hole Cutting)
        精確挖除任意複雜幾何（如 NACA 翼型、葉片、機身外形）內部網格點。

        參數:
            bg_grid: 背景網格
            polygon_vertices: 頂點座標陣列，shape (N, 2)，依序閉合
            fringe_layers: 邊界接收層厚度
        回傳:
            in_hole: 布林遮罩
        """
        X_bg, Y_bg = bg_grid.get_coordinates()
        nx, ny = X_bg.shape
        points = np.column_stack([X_bg.ravel(), Y_bg.ravel()])

        # 建立多邊形路徑並向量化光線投射檢驗 (Ray-Casting)
        path = MplPath(polygon_vertices)
        in_hole_flat = path.contains_points(points)
        in_hole = in_hole_flat.reshape((nx, ny))

        dilated_hole = binary_dilation(in_hole, structure=HoleCutter.CROSS_STRUCTURE, iterations=fringe_layers)
        fringe_mask = dilated_hole & (~in_hole)

        bg_grid.status_mask[in_hole] = CellStatus.HOLE
        bg_grid.status_mask[fringe_mask] = CellStatus.RECEIVER
        return in_hole

    @staticmethod
    def cut_sdf_holes_and_mark_fringe(
        bg_grid: AbstractGrid,
        sdf_func: Callable[[np.ndarray, np.ndarray], np.ndarray],
        threshold: float = 0.0,
        fringe_layers: int = 1
    ) -> np.ndarray:
        """
        模式 3: 符號距離函數孔洞切割 (SDF / Level-Set Hole Cutting)
        以幾何曲面距離場 phi(x, y) <= threshold 定義固體實體孔洞區。
        """
        X_bg, Y_bg = bg_grid.get_coordinates()
        sdf_vals = sdf_func(X_bg, Y_bg)
        in_hole = (sdf_vals <= threshold)

        dilated_hole = binary_dilation(in_hole, structure=HoleCutter.CROSS_STRUCTURE, iterations=fringe_layers)
        fringe_mask = dilated_hole & (~in_hole)

        bg_grid.status_mask[in_hole] = CellStatus.HOLE
        bg_grid.status_mask[fringe_mask] = CellStatus.RECEIVER
        return in_hole

    @staticmethod
    def mark_outer_boundary_receivers(grid: AbstractGrid, n_layers: int = 1) -> None:
        """將組件網格最外層邊緣網格標記為 RECEIVER"""
        nx, ny = grid.get_shape()
        grid.status_mask[:n_layers, :] = CellStatus.RECEIVER
        grid.status_mask[-n_layers:, :] = CellStatus.RECEIVER
        grid.status_mask[:, :n_layers] = CellStatus.RECEIVER
        grid.status_mask[:, -n_layers:] = CellStatus.RECEIVER


class AdvancedHoleCutter:
    """支援任意封閉曲面障礙物的向量化幾何求交器"""

    @staticmethod
    def cut_by_curvilinear_body(
        bg_grid: AbstractGrid,
        curv_grid: 'CurvilinearOGrid',
        fringe_layers: int = 1
    ) -> None:
        """
        將落在貼體網格物體內部 (如翼型實體內) 的背景節點標記為 HOLE，
        並在孔洞外緣膨脹生成 RECEIVER 邊界層。
        """
        # 1. 取得翼型內邊界在世界座標下的頂點
        x_body_w, y_body_w = curv_grid.transform.local_to_world(
            curv_grid.x_inner, curv_grid.y_inner
        )
        polygon_vertices = np.column_stack([x_body_w, y_body_w])
        poly_path = MplPath(polygon_vertices)

        # 2. 背景網格世界節點求交判定 (Point-in-Polygon)
        X_bg, Y_bg = bg_grid.get_coordinates()
        flat_points = np.column_stack([X_bg.ravel(), Y_bg.ravel()])

        # 向量化包含測試
        inside_hole_flat = poly_path.contains_points(flat_points)
        inside_hole = inside_hole_flat.reshape(X_bg.shape)

        # 3. 邊界膨脹：生成孔洞外側的 RECEIVER 邊界
        structure = np.array([[0, 1, 0],
                              [1, 1, 1],
                              [0, 1, 0]], dtype=bool)
        dilated_hole = binary_dilation(inside_hole, structure=structure, iterations=fringe_layers)
        fringe_mask = dilated_hole & (~inside_hole)

        # 4. 更新狀態遮罩
        bg_grid.status_mask[inside_hole] = CellStatus.HOLE
        bg_grid.status_mask[fringe_mask] = CellStatus.RECEIVER
