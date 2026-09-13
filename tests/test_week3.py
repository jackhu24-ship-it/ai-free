# -*- coding: utf-8 -*-
"""
tests/test_week3.py - 第 3 週孔洞切割與邊界標定驗證
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from core.types import CellStatus
from grids.structured_cartesian import StructuredCartesianGrid
from grids.component_grid import ComponentGrid
from geometry.hole_cutter import HoleCutter


def test_week3():
    # 1. 建立背景網格與傾斜的前景網格
    bg_grid = StructuredCartesianGrid(
        grid_id="background",
        bounds=(-3.0, 3.0, -3.0, 3.0),
        shape=(91, 91),
        priority=0
    )

    fg_grid = ComponentGrid(
        grid_id="component_patch",
        local_bounds=(-1.2, 1.2, -0.6, 0.6),
        shape=(61, 31),
        origin=(0.4, 0.3),
        angle_rad=np.radians(25.0),
        priority=10
    )

    # 2. 執行孔洞切割
    HoleCutter.cut_holes_and_mark_fringe(
        bg_grid=bg_grid,
        comp_grid=fg_grid,
        shrink_margin=0.15,
        fringe_layers=1
    )

    # 3. 斷言檢查：確保三個狀態的節點皆已正常生成
    n_hole = np.sum(bg_grid.status_mask == CellStatus.HOLE)
    n_recv = np.sum(bg_grid.status_mask == CellStatus.RECEIVER)
    n_field = np.sum(bg_grid.status_mask == CellStatus.FIELD)

    print(f"背景網格節點總數: {bg_grid.nx * bg_grid.ny}")
    print(f"  - FIELD (計算點): {n_field}")
    print(f"  - HOLE (孔洞盲點): {n_hole}")
    print(f"  - RECEIVER (接收插值點): {n_recv}")

    assert n_hole > 0, "錯誤：未能識別任何 HOLE 盲點！"
    assert n_recv > 0, "錯誤：未能生成孔洞外圈 RECEIVER 邊界！"
    print("✓ 拓撲狀態斷言檢查全數通過！")

    # 4. 繪製全域拓撲視覺化圖表
    X_bg, Y_bg = bg_grid.get_coordinates()
    X_fg, Y_fg = fg_grid.get_coordinates()

    plt.figure(figsize=(10, 8))

    # 背景網格：分別繪製 FIELD、RECEIVER、HOLE
    bg_field = (bg_grid.status_mask == CellStatus.FIELD)
    bg_recv = (bg_grid.status_mask == CellStatus.RECEIVER)
    bg_hole = (bg_grid.status_mask == CellStatus.HOLE)

    plt.scatter(X_bg[bg_field], Y_bg[bg_field], s=6, c='lightgray', label='BG: FIELD')
    plt.scatter(X_bg[bg_recv], Y_bg[bg_recv], s=25, c='red', marker='s', label='BG: RECEIVER (Fringe)')
    plt.scatter(X_bg[bg_hole], Y_bg[bg_hole], s=8, c='black', alpha=0.3, label='BG: HOLE (Cutout)')

    # 前景網格：繪製 FIELD 與 外圈邊界 RECEIVER
    fg_field = (fg_grid.status_mask == CellStatus.FIELD)
    fg_recv = (fg_grid.status_mask == CellStatus.RECEIVER)

    plt.scatter(X_fg[fg_field], Y_fg[fg_field], s=10, c='royalblue', label='FG: FIELD')
    plt.scatter(X_fg[fg_recv], Y_fg[fg_recv], s=20, c='darkorange', marker='^', label='FG: RECEIVER')

    plt.title("PHANTOM Grid - Hole Cutting & Receiver Topology", fontsize=14)
    plt.xlabel("World X")
    plt.ylabel("World Y")
    plt.axis("equal")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0))
    plt.tight_layout()

    plt.savefig("week3_hole_cutting.png", dpi=200)
    print("✓ 幾何切割成果圖已輸出至 week3_hole_cutting.png")


if __name__ == "__main__":
    test_week3()
