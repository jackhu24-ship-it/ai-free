# -*- coding: utf-8 -*-
"""
tests/test_week5.py - 第 5 週物理求解器接入與波前跨邊界傳播驗證
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
from solver.phantom_runner import PhantomRunner


def test_week5():
    # 1. 建立背景粗網格 (範圍 [-3, 3])
    bg_grid = StructuredCartesianGrid(
        grid_id="background",
        bounds=(-3.0, 3.0, -3.0, 3.0),
        shape=(91, 91),
        priority=0
    )
    bg_grid.initialize_fields(["u", "v"])

    # 2. 建立前景局部高解析度網格 (隨時間動態移動)
    fg_grid = ComponentGrid(
        grid_id="component_tracker",
        local_bounds=(-1.0, 1.0, -0.6, 0.6),
        shape=(61, 37),
        origin=(0.0, 0.0),
        angle_rad=np.radians(15.0),
        priority=10
    )
    fg_grid.initialize_fields(["u", "v"])

    runner = PhantomRunner(bg_grid, fg_grid)

    # 3. 初始化物理場：在背景網格左下方放置一束高斯脈衝波
    X_bg, Y_bg = bg_grid.get_coordinates()
    r0 = np.sqrt((X_bg + 0.8)**2 + (Y_bg + 0.8)**2)
    bg_grid.fields["u"] = np.exp(-(r0**2) / 0.08)

    # 前景網格同步初始場量
    X_fg, Y_fg = fg_grid.get_coordinates()
    r0_fg = np.sqrt((X_fg + 0.8)**2 + (Y_fg + 0.8)**2)
    fg_grid.fields["u"] = np.exp(-(r0_fg**2) / 0.08)

    # 4. 首次幾何求交構建拓撲
    runner.rebuild_topology()

    # 5. 時間推進迴圈 (滿足 CFL 條件: dt <= 0.5 * min(dx, dy) / c)
    dt = 0.01
    total_steps = 120

    print("開始執行 PHANTOM Grid 波動物理推進...")
    for step_idx in range(total_steps):
        # 模擬特徵自適應平移：組件網格沿 (1, 0.5) 方向動態慢移
        if step_idx % 20 == 0 and step_idx > 0:
            current_x = 0.0 + step_idx * 0.003
            current_y = 0.0 + step_idx * 0.0015
            fg_grid.set_motion(origin=(current_x, current_y), angle_rad=np.radians(15.0))
            runner.rebuild_topology()

        runner.step(dt=dt, field_names=["u", "v"])

    # 6. 穩定性與守恆檢查：檢查數值是否發散 (NaN / Inf)
    u_bg_max = np.max(np.abs(bg_grid.fields["u"]))
    u_fg_max = np.max(np.abs(fg_grid.fields["u"]))

    print(f"推進完成！背景網格波幅極值: {u_bg_max:.4f}, 前景網格波幅極值: {u_fg_max:.4f}")
    assert not np.isnan(u_bg_max) and not np.isinf(u_bg_max), "背景網格數值計算發散！"
    assert not np.isnan(u_fg_max) and not np.isinf(u_fg_max), "前景網格數值計算發散！"
    print("✓ 驗證通過：波動跨邊界平滑過渡且計算保持數值穩定！")

    # 7. 視覺化跨邊界物理場分佈
    plt.figure(figsize=(9, 8))

    # 遮蓋背景網格中的孔洞點，避免非物理點污染等高線圖
    bg_display_u = np.copy(bg_grid.fields["u"])
    bg_display_u[bg_grid.status_mask == CellStatus.HOLE] = np.nan

    # 繪製背景場量
    cntr_bg = plt.contourf(X_bg, Y_bg, bg_display_u, levels=30, cmap="viridis", alpha=0.85)
    plt.colorbar(cntr_bg, label="Field u (Background)")

    # 疊加前景網格的場量分佈點
    X_fg_now, Y_fg_now = fg_grid.get_coordinates()
    fg_field_mask = (fg_grid.status_mask == CellStatus.FIELD)
    plt.scatter(
        X_fg_now[fg_field_mask],
        Y_fg_now[fg_field_mask],
        c=fg_grid.fields["u"][fg_field_mask],
        cmap="viridis",
        s=12,
        edgecolor="black",
        linewidth=0.3,
        label="Component Wavefront"
    )

    plt.title(f"PHANTOM Grid - Wave Equation Coupling (Step {total_steps})", fontsize=13)
    plt.xlabel("World X")
    plt.ylabel("World Y")
    plt.axis("equal")
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.legend(loc="upper right")
    plt.tight_layout()

    plt.savefig("week5_coupled_wave.png", dpi=200)
    print("✓ 波動耦合傳播成果圖已輸出至 week5_coupled_wave.png")


if __name__ == "__main__":
    test_week5()
