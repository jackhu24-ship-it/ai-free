# -*- coding: utf-8 -*-
"""
tests/test_task2_conservation.py - 任務二驗證：跨網格嚴格質量守恆性基準測試
========================================================================
驗證指標：
1. 建立背景笛卡爾網格 ([-2.0, 2.0]^2, 81x81) 與旋轉 15° 前景網格 ([-0.7, 0.7]^2, 51x51)
2. 注入偏心高斯波包脈衝，模擬 150 個時間步的波前跨界傳播
3. 對比「標準雙線性插值 (Uncorrected)」vs「PHANTOM 守恆通量匹配 (Conservative Flux Matching)」
4. 斷言啟用守恆修正後的相對質量誤差被壓制至機器精度極限 (< 1e-12)
5. 繪製並輸出歷史質量誤差收斂對比曲線圖 task2_conservation_benchmark.png (同步至 generated/)
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import shutil
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from core.types import CellStatus
from grids.structured_cartesian import StructuredCartesianGrid
from grids.component_grid import ComponentGrid
from geometry.hole_cutter import HoleCutter
from coupling.sparse_coupler import SparseOversetCoupler
from coupling.flux_coupler import ConservativeFluxCoupler


def run_conservation_experiment(use_conservation_fix: bool = True):
    # 建立雙網格環境
    bounds = (-2.0, 2.0, -2.0, 2.0)
    bg_grid = StructuredCartesianGrid("bg", bounds, shape=(81, 81), priority=0)
    bg_grid.initialize_fields(["u", "v"])

    fg_grid = ComponentGrid(
        "comp",
        local_bounds=(-0.7, 0.7, -0.7, 0.7),
        shape=(51, 51),
        origin=(0.0, 0.0),
        angle_rad=np.radians(15.0),
        priority=10
    )
    fg_grid.initialize_fields(["u", "v"])

    # 孔洞切割
    HoleCutter.cut_holes_and_mark_fringe(bg_grid, fg_grid, shrink_margin=0.15, fringe_layers=1)

    # 建立稀疏通訊
    coupler_bg_to_fg = SparseOversetCoupler(bg_grid, fg_grid)
    coupler_fg_to_bg = SparseOversetCoupler(fg_grid, bg_grid)

    # 初值設定：在交界處生成高斯脈衝
    X_b, Y_b = bg_grid.get_coordinates()
    X_c, Y_c = fg_grid.get_coordinates()
    bg_grid.fields["u"] = np.exp(-((X_b + 0.3)**2 + (Y_b + 0.3)**2) / 0.08)
    fg_grid.fields["u"] = np.exp(-((X_c + 0.3)**2 + (Y_c + 0.3)**2) / 0.08)

    # 計算初始目標總質量
    init_mass = (
        ConservativeFluxCoupler.compute_total_mass(bg_grid, "u") +
        ConservativeFluxCoupler.compute_total_mass(fg_grid, "u")
    )

    dt = 0.005
    n_steps = 150
    mass_history = []

    for step in range(n_steps):
        # 1. 局部 PDE 推進
        bg_grid.step_pde(dt)
        fg_grid.step_pde(dt)

        # 2. 邊界數據插值交換
        coupler_bg_to_fg.transfer("u")
        coupler_fg_to_bg.transfer("u")

        # 3. 是否啟用守恆修正
        if use_conservation_fix:
            ConservativeFluxCoupler.enforce_conservation(
                bg_grid, fg_grid, target_total_mass=init_mass, field_name="u"
            )

        # 記錄當前全域總質量相對誤差
        current_mass = (
            ConservativeFluxCoupler.compute_total_mass(bg_grid, "u") +
            ConservativeFluxCoupler.compute_total_mass(fg_grid, "u")
        )
        err = abs(current_mass - init_mass) / init_mass
        mass_history.append(err)

    return mass_history


def test_task2():
    print("==========================================================")
    print(" 🚀 [任務二] 正在執行質量守恆性對比測試 (150 步迭代)...   ")
    print("==========================================================")

    # 對比兩組實驗
    err_without_fix = run_conservation_experiment(use_conservation_fix=False)
    err_with_fix = run_conservation_experiment(use_conservation_fix=True)

    max_err_unfixed = float(np.max(err_without_fix))
    max_err_fixed = float(np.max(err_with_fix))

    print(f"1. 無修正插值之最大質量累積誤差: {max_err_unfixed:.3e}")
    print(f"2. 啟用守恆修正之最大質量累積誤差: {max_err_fixed:.3e}")
    print(f"   守恆精確度改善幅度: {max_err_unfixed / (max_err_fixed + 1e-18):.2e}x")

    # 斷言：啟用修正後的漂移必須被壓制在極微小範圍 (< 1e-12)
    assert max_err_fixed < 1e-12, f"守恆修正未能壓制質量漂移！max_err={max_err_fixed}"
    print("  ✓ 驗證通過：跨網格數值守恆性達到機器精度極限！")

    # 繪製對比圖表
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.plot(err_without_fix, label="Standard Bilinear Transfer (Uncorrected)", color="#d90429", linestyle="--", linewidth=2.2)
    ax.plot(err_with_fix, label="PHANTOM Conservative Flux Matching", color="#1d3557", linewidth=2.2)

    ax.set_yscale("log")
    ax.set_title("PHANTOM Grid - Mass Conservation Drift Over Time (150 Steps)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Simulation Time Steps ($N$)", fontsize=11)
    ax.set_ylabel("Relative Mass Error $|M(t) - M(0)| / M(0)$", fontsize=11)
    ax.grid(True, which="both", linestyle="--", alpha=0.5)
    ax.legend(loc="upper left", fontsize=10.5, framealpha=0.95)
    plt.tight_layout()

    out_file = Path("task2_conservation_benchmark.png")
    plt.savefig(out_file, dpi=250)
    plt.close()

    # 遵守零桌面污染原則，備份至 generated/
    gen_dir = Path("generated")
    gen_dir.mkdir(exist_ok=True)
    shutil.copy(out_file, gen_dir / out_file.name)

    print(f"3. 質量守恆基準圖表已輸出至: {out_file.resolve()}")
    print(f"   同步備份至: {(gen_dir / out_file.name).resolve()}")
    print("==========================================================")
    print(" ✅ [任務二驗證成功: 跨網格守恆通量修正全項通過]            ")
    print("==========================================================")


if __name__ == "__main__":
    test_task2()
