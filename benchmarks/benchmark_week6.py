# -*- coding: utf-8 -*-
"""
benchmarks/benchmark_week6.py - 國際競賽級效能與精度基準測試報告
================================================================
比對兩套方案：
1. 全域單一密集網格 (Global Fine Grid)
2. PHANTOM 重疊自適應網格 (Overlapping Adaptive Grid) + 稀疏矩陣通訊運算元
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import shutil
from pathlib import Path
import time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from core.types import CellStatus
from grids.structured_cartesian import StructuredCartesianGrid
from grids.component_grid import ComponentGrid
from geometry.hole_cutter import HoleCutter
from coupling.sparse_coupler import SparseOversetCoupler, SparseCoupler
from coupling.interpolator import OversetInterpolator


def run_boundary_exchange_benchmark(n_iterations: int = 300):
    """微觀評測：純邊界交換耗時對比 (逐點雙線性 vs CSR 稀疏矩陣 SpMV)"""
    bg = StructuredCartesianGrid("bg", bounds=(-3.0, 3.0, -3.0, 3.0), shape=(91, 91), priority=0)
    bg.initialize_fields(["u", "v"])
    fg = ComponentGrid("fg", local_bounds=(-1.0, 1.0, -0.6, 0.6), shape=(61, 37),
                       origin=(0.0, 0.0), angle_rad=np.radians(15.0), priority=10)
    fg.initialize_fields(["u", "v"])

    HoleCutter.cut_holes_and_mark_fringe(bg, fg, shrink_margin=0.15, fringe_layers=1)

    rng = np.random.default_rng(42)
    bg.fields["u"] = rng.standard_normal(bg.shape)
    bg.fields["v"] = rng.standard_normal(bg.shape)
    fg.fields["u"] = rng.standard_normal(fg.shape)
    fg.fields["v"] = rng.standard_normal(fg.shape)

    t0 = time.perf_counter()
    for _ in range(n_iterations):
        OversetInterpolator.exchange_all_boundaries(bg, fg, "u")
        OversetInterpolator.exchange_all_boundaries(bg, fg, "v")
    t_interp = time.perf_counter() - t0

    coupler = SparseCoupler(bg, fg)
    coupler.build()

    t0 = time.perf_counter()
    for _ in range(n_iterations):
        coupler.exchange_fields(["u", "v"])
    t_sparse = time.perf_counter() - t0

    speedup = t_interp / t_sparse if t_sparse > 0 else 1.0
    return {
        "n_iterations": n_iterations,
        "t_interp_total_sec": t_interp,
        "t_interp_per_call_ms": (t_interp / n_iterations) * 1000.0,
        "t_sparse_total_sec": t_sparse,
        "t_sparse_per_call_ms": (t_sparse / n_iterations) * 1000.0,
        "speedup": speedup,
        "sparsity_info": coupler.get_sparsity_info()
    }


def run_solver_comparison_benchmark(total_steps: int = 120, dt: float = 0.01):
    """微觀評測：求解器全流程對比"""
    res = run_benchmark()
    return {
        "fine": {
            "total_cells": res["dofs_fine"],
            "memory_kb": (res["dofs_fine"] * 20) / 1024.0,
            "elapsed_sec": res["time_fine"],
            "ms_per_step": (res["time_fine"] / 150) * 1000.0
        },
        "phantom": {
            "total_cells": res["dofs_phantom"],
            "memory_kb": (res["dofs_phantom"] * 20) / 1024.0,
            "elapsed_sec": res["time_phantom"],
            "ms_per_step": (res["time_phantom"] / 150) * 1000.0
        },
        "comparison": {
            "cell_reduction_pct": res["memory_saving"],
            "mem_saving_pct": res["memory_saving"],
            "speedup_solver": res["speedup"]
        }
    }


def run_benchmark():
    bounds = (-2.0, 2.0, -2.0, 2.0)
    dt = 0.005
    n_steps = 150

    print("==========================================================")
    print("      PHANTOM Grid vs Global Fine Grid Benchmark          ")
    print("==========================================================")

    # -------------------------------------------------------------
    # Case A: 全域單一超細網格 (基準組: 解析度與前景組件看齊)
    # -------------------------------------------------------------
    fine_shape = (201, 201)
    fine_grid = StructuredCartesianGrid("global_fine", bounds, shape=fine_shape)
    fine_grid.initialize_fields(["u", "v"])

    # 初始化波動
    X_f, Y_f = fine_grid.get_coordinates()
    fine_grid.fields["u"] = np.exp(-((X_f + 0.5)**2 + (Y_f + 0.5)**2) / 0.05)

    start_time = time.perf_counter()
    for _ in range(n_steps):
        fine_grid.step_pde(dt)
    time_fine = time.perf_counter() - start_time
    dofs_fine = fine_grid.nx * fine_grid.ny

    # -------------------------------------------------------------
    # Case B: PHANTOM 重疊稀疏矩陣自適應架構
    # -------------------------------------------------------------
    # 背景粗網格 (解析度減半)
    bg_grid = StructuredCartesianGrid("bg", bounds, shape=(101, 101), priority=0)
    bg_grid.initialize_fields(["u", "v"])

    # 前景高解析網格 (僅覆蓋感興趣的核心特徵區)
    fg_grid = ComponentGrid(
        "comp",
        local_bounds=(-0.8, 0.8, -0.8, 0.8),
        shape=(81, 81),
        origin=(0.0, 0.0),
        angle_rad=np.radians(10.0),
        priority=10
    )
    fg_grid.initialize_fields(["u", "v"])

    # 拓撲切割
    HoleCutter.cut_holes_and_mark_fringe(bg_grid, fg_grid, shrink_margin=0.12, fringe_layers=1)

    # 構建稀疏通訊運算元
    coupler_bg_to_fg = SparseOversetCoupler(donor_grid=bg_grid, receiver_grid=fg_grid)
    coupler_fg_to_bg = SparseOversetCoupler(donor_grid=fg_grid, receiver_grid=bg_grid)

    # 初始化場量
    X_b, Y_b = bg_grid.get_coordinates()
    bg_grid.fields["u"] = np.exp(-((X_b + 0.5)**2 + (Y_b + 0.5)**2) / 0.05)
    X_c, Y_c = fg_grid.get_coordinates()
    fg_grid.fields["u"] = np.exp(-((X_c + 0.5)**2 + (Y_c + 0.5)**2) / 0.05)

    start_time = time.perf_counter()
    for _ in range(n_steps):
        # 1. 局部推進
        bg_grid.step_pde(dt)
        fg_grid.step_pde(dt)
        # 2. 稀疏矩陣高效通訊
        coupler_bg_to_fg.transfer("u")
        coupler_fg_to_bg.transfer("u")
    time_phantom = time.perf_counter() - start_time

    # 計算有效自由度 (排除 HOLE 點)
    active_bg = np.sum(bg_grid.status_mask != CellStatus.HOLE)
    active_fg = fg_grid.nx * fg_grid.ny
    dofs_phantom = active_bg + active_fg

    # -------------------------------------------------------------
    # 數據輸出與對比
    # -------------------------------------------------------------
    speedup = time_fine / time_phantom
    memory_saving = (1.0 - dofs_phantom / dofs_fine) * 100.0

    print(f"全域密集網格: 自由度 = {dofs_fine:7d} | 計算耗時 = {time_fine:.3f} s")
    print(f"PHANTOM 網格: 自由度 = {dofs_phantom:7d} | 計算耗時 = {time_phantom:.3f} s")
    print(f">> 計算加速比 (Speedup) : {speedup:.2f} x")
    print(f">> 自由度節省率 (Memory/DOFs Saving) : {memory_saving:.1f} %")
    print("==========================================================")

    # 繪製競賽基準評估圖表
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))

    categories = ['Global Fine Grid', 'PHANTOM Grid']
    dofs = [dofs_fine, dofs_phantom]
    times = [time_fine, time_phantom]

    # 自由度/記憶體對比
    ax1.bar(categories, dofs, color=['#7f7f7f', '#1f77b4'], width=0.5)
    ax1.set_ylabel("Total Active Degrees of Freedom (DOFs)")
    ax1.set_title(f"DOFs Reduction: -{memory_saving:.1f}%", fontsize=12, fontweight='bold')
    ax1.grid(axis='y', linestyle='--', alpha=0.5)

    # 耗時對比
    ax2.bar(categories, times, color=['#7f7f7f', '#2ca02c'], width=0.5)
    ax2.set_ylabel("Wall-clock Execution Time (seconds)")
    ax2.set_title(f"Performance Speedup: {speedup:.2f}x", fontsize=12, fontweight='bold')
    ax2.grid(axis='y', linestyle='--', alpha=0.5)

    plt.tight_layout()
    out_file = Path("week6_benchmark_report.png")
    plt.savefig(out_file, dpi=200)
    plt.close()

    # 遵守零桌面污染原則，備份至 generated/
    gen_dir = Path("generated")
    gen_dir.mkdir(exist_ok=True)
    shutil.copy(out_file, gen_dir / out_file.name)

    print("✓ 基準對比報表圖已儲存至 week6_benchmark_report.png")
    print("✓ 已同步備份至 generated/week6_benchmark_report.png")

    return {
        "dofs_fine": dofs_fine,
        "dofs_phantom": dofs_phantom,
        "time_fine": time_fine,
        "time_phantom": time_phantom,
        "speedup": speedup,
        "memory_saving": memory_saving
    }


if __name__ == "__main__":
    run_benchmark()
