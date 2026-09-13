# -*- coding: utf-8 -*-
"""
tests/test_week2.py - 第 2 週驗證：雙網格重疊與座標變換
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


def test_week2():
    # 1. 建立大尺度背景網格 (解析度較粗: dx = dy = 0.08)
    bg_grid = StructuredCartesianGrid(
        grid_id="background",
        bounds=(-3.0, 3.0, -3.0, 3.0),
        shape=(76, 76),
        priority=0
    )

    # 2. 建立局部高解析前景網格 (局部邊界 [-1, 1]x[-0.5, 0.5]，解析度高一倍: dx = dy = 0.04)
    fg_grid = ComponentGrid(
        grid_id="component_airfoil_zone",
        local_bounds=(-1.0, 1.0, -0.5, 0.5),
        shape=(51, 26),
        origin=(0.5, 0.5),           # 放置在世界座標 (0.5, 0.5)
        angle_rad=np.radians(30.0),  # 傾斜 30 度
        priority=10
    )

    # 3. 測試座標逆向映射一致性 (World -> Local -> World 往返誤差應為 0)
    X_world, Y_world = fg_grid.get_coordinates()
    X_loc_rec, Y_loc_rec = fg_grid.transform.world_to_local(X_world, Y_world)
    X_loc_orig, Y_loc_orig = fg_grid.get_local_coordinates()

    roundtrip_error = np.max(np.abs(X_loc_rec - X_loc_orig)) + np.max(np.abs(Y_loc_rec - Y_loc_orig))
    assert roundtrip_error < 1e-12, f"坐標轉換往返誤差過大: {roundtrip_error}"
    print(f"✓ 變換引擎驗證通過：SE(2) 往返誤差為 {roundtrip_error:.2e}")

    # 4. 繪製雙網格幾何拓撲分佈圖
    plt.figure(figsize=(9, 8))

    # 繪製背景網格節點 (以灰色點表示)
    X_bg, Y_bg = bg_grid.get_coordinates()
    plt.scatter(X_bg, Y_bg, s=2, c='lightgray', label='Background Mesh (Level 0)')

    # 繪製前景網格 (以狀態著色: FIELD 為藍色, RECEIVER 為橙色邊界)
    fg_field_mask = (fg_grid.status_mask == CellStatus.FIELD)
    fg_recv_mask = (fg_grid.status_mask == CellStatus.RECEIVER)

    plt.scatter(X_world[fg_field_mask], Y_world[fg_field_mask], s=8, c='royalblue', label='Component FIELD (Level 1)')
    plt.scatter(X_world[fg_recv_mask], Y_world[fg_recv_mask], s=14, c='darkorange', label='Component RECEIVER (Fringe)')

    plt.title("PHANTOM Grid - Multi-scale Overlapping Topologies", fontsize=14)
    plt.xlabel("World X")
    plt.ylabel("World Y")
    plt.axis("equal")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(loc="upper left")

    plt.savefig("week2_grid_overlap.png", dpi=200)
    print("✓ 拓撲重疊圖已輸出至 week2_grid_overlap.png")


if __name__ == "__main__":
    test_week2()
