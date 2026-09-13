# -*- coding: utf-8 -*-
"""
tests/test_week4.py - 第 4 週插值精度與數值交換驗證 (V&V Benchmark)
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
from core.types import CellStatus
from grids.structured_cartesian import StructuredCartesianGrid
from grids.component_grid import ComponentGrid
from geometry.hole_cutter import HoleCutter
from coupling.interpolator import OversetInterpolator


def analytic_solution(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """已知平滑解析解：u(x, y) = sin(pi * x) * cos(pi * y)"""
    return np.sin(np.pi * x) * np.cos(np.pi * y)


def test_week4():
    # 1. 建立背景網格與帶旋轉的前景網格
    bg_grid = StructuredCartesianGrid(
        grid_id="background",
        bounds=(-2.0, 2.0, -2.0, 2.0),
        shape=(81, 81),
        priority=0
    )
    bg_grid.initialize_fields(["u"])

    fg_grid = ComponentGrid(
        grid_id="component",
        local_bounds=(-0.8, 0.8, -0.5, 0.5),
        shape=(65, 41),
        origin=(0.2, 0.1),
        angle_rad=np.radians(20.0),
        priority=10
    )
    fg_grid.initialize_fields(["u"])

    # 2. 幾何求交：在背景網格上切出孔洞並生成 RECEIVER 邊界
    HoleCutter.cut_holes_and_mark_fringe(
        bg_grid=bg_grid,
        comp_grid=fg_grid,
        shrink_margin=0.15,
        fringe_layers=1
    )

    # 3. 給予所有單元（包括計算點與潛在供體點）精確解析解初值
    X_bg, Y_bg = bg_grid.get_coordinates()
    X_fg, Y_fg = fg_grid.get_coordinates()

    bg_grid.fields["u"] = analytic_solution(X_bg, Y_bg)
    fg_grid.fields["u"] = analytic_solution(X_fg, Y_fg)

    # 4. 人為抹除兩個網格上的 RECEIVER 點數值（設為 0.0），模擬未同步狀態
    bg_recv_mask = (bg_grid.status_mask == CellStatus.RECEIVER)
    fg_recv_mask = (fg_grid.status_mask == CellStatus.RECEIVER)

    bg_grid.fields["u"][bg_recv_mask] = 0.0
    fg_grid.fields["u"][fg_recv_mask] = 0.0

    # 5. 執行雙向跨邊界雙線性插值交換
    OversetInterpolator.exchange_all_boundaries(bg_grid, fg_grid, field_name="u")

    # 6. 計算插值誤差：比較插值獲得的數值與理論真實解析解
    bg_err = np.abs(bg_grid.fields["u"][bg_recv_mask] - analytic_solution(X_bg[bg_recv_mask], Y_bg[bg_recv_mask]))
    fg_err = np.abs(fg_grid.fields["u"][fg_recv_mask] - analytic_solution(X_fg[fg_recv_mask], Y_fg[fg_recv_mask]))

    max_bg_err = np.max(bg_err)
    max_fg_err = np.max(fg_err)
    mean_bg_err = np.mean(bg_err)
    mean_fg_err = np.mean(fg_err)

    print(f"背景網格接收點 (BG RECEIVER) 誤差: 最大 = {max_bg_err:.3e}, 平均 = {mean_bg_err:.3e}")
    print(f"前景網格接收點 (FG RECEIVER) 誤差: 最大 = {max_fg_err:.3e}, 平均 = {mean_fg_err:.3e}")

    # 7. 斷言驗證：雙線性插值在平滑解析解下應嚴格滿足局部二次收斂精度容許值 (< 2e-2)
    assert max_bg_err < 0.02, f"背景網格接收邊界插值誤差超出預期: {max_bg_err}"
    assert max_fg_err < 0.02, f"前景網格接收邊界插值誤差超出預期: {max_fg_err}"

    print("✓ 驗證通過：雙向雙線性跨邊界數據通訊完全打通，精度符合 V&V 規範！")


if __name__ == "__main__":
    test_week4()
