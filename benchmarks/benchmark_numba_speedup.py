# -*- coding: utf-8 -*-
"""
benchmarks/benchmark_numba_speedup.py - Numba JIT 多核心平行運算效能基準對比測試
================================================================================
量測並對比在二維偏微分方程 (Wave PDE) 200 步高負載時間推進中：
1. 純 Python / NumPy 向量化運算時間
2. Numba JIT 多核心平行 (Parallel=True, SIMD) 運算時間
3. 驗證數值等價性 (Max Absolute Difference < 1e-10)
4. 輸出評審答辯亮點柱狀對比圖: numba_acceleration_benchmark.png (同步至 generated/)
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import time
import shutil
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from solver.numba_kernels import step_wave_2d_numba


def run_numpy_wave(u: np.ndarray, v: np.ndarray, dt: float, c: float, dx: float, dy: float, active_mask: np.ndarray, n_steps: int):
    """純 NumPy 向量化求解器"""
    inv_dx2 = 1.0 / (dx * dx)
    inv_dy2 = 1.0 / (dy * dy)
    c2_dt = (c * c) * dt

    for _ in range(n_steps):
        # 笛卡爾五點差分拉普拉斯
        d2u_dx2 = (u[2:, 1:-1] - 2.0 * u[1:-1, 1:-1] + u[:-2, 1:-1]) * inv_dx2
        d2u_dy2 = (u[1:-1, 2:] - 2.0 * u[1:-1, 1:-1] + u[1:-1, :-2]) * inv_dy2
        lap = d2u_dx2 + d2u_dy2

        mask_inner = active_mask[1:-1, 1:-1]
        v_inner = v[1:-1, 1:-1]
        u_inner = u[1:-1, 1:-1]

        v_inner[mask_inner] += c2_dt * lap[mask_inner]
        u_inner[mask_inner] += dt * v_inner[mask_inner]


def benchmark_numba():
    print("==========================================================")
    print(" ⚡ [第二階段] Numba JIT 多核心平行運算基準對比測試...   ")
    print("==========================================================")

    nx, ny = 251, 251
    dx = 1.0 / (nx - 1)
    dy = 1.0 / (ny - 1)
    dt = 0.002
    c = 1.0
    n_steps = 200

    print(f"1. 測試規模: {nx} x {ny} ({nx * ny:,} 節點), 時間推進 {n_steps} 步")

    # 構造圓形孔洞遮罩
    x = np.linspace(-1, 1, nx)
    y = np.linspace(-1, 1, ny)
    X, Y = np.meshgrid(x, y, indexing="ij")
    r = np.sqrt(X**2 + Y**2)
    active_mask = (r > 0.25)  # 中間挖掉圓形孔洞

    # 初始化場量
    u_init = np.exp(-((X - 0.4)**2 + (Y - 0.4)**2) / 0.05)
    v_init = np.zeros_like(u_init)

    # --- 測試 A: 純 NumPy 基準 ---
    u_np = u_init.copy()
    v_np = v_init.copy()

    start_np = time.perf_counter()
    run_numpy_wave(u_np, v_np, dt, c, dx, dy, active_mask, n_steps)
    time_numpy = time.perf_counter() - start_np
    print(f"2. 純 NumPy 向量化總耗時: {time_numpy:.4f} 秒 ({time_numpy / n_steps * 1000:.3f} ms/步)")

    # --- 測試 B: Numba JIT (含 Warm-up) ---
    u_nb = u_init.copy()
    v_nb = v_init.copy()

    # JIT 熱身 (編譯 1 步)
    step_wave_2d_numba(u_nb, v_nb, dt, c, dx, dy, active_mask)
    u_nb = u_init.copy()
    v_nb = v_init.copy()

    start_nb = time.perf_counter()
    for _ in range(n_steps):
        step_wave_2d_numba(u_nb, v_nb, dt, c, dx, dy, active_mask)
    time_numba = time.perf_counter() - start_nb
    print(f"3. Numba JIT 平行運算總耗時: {time_numba:.4f} 秒 ({time_numba / n_steps * 1000:.3f} ms/步)")

    # 4. 加速比與數值等價性校驗
    speedup = time_numpy / time_numba
    max_diff = float(np.max(np.abs(u_np - u_nb)))
    print(f"4. 實測加速比 (Speedup): {speedup:.2f}x 🚀")
    print(f"   數值最大偏差 (NumPy vs Numba): {max_diff:.3e}")
    assert max_diff < 1e-10, f"數值偏差過大: {max_diff}"
    print("  ✓ 數值精確等價性檢驗通過！")

    # 5. 繪製評審答辯級對比柱狀圖
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))

    # 子圖 1: 總運算時間對比
    bars = ax1.bar(["NumPy Vectorized", "Numba JIT (Parallel)"], [time_numpy, time_numba],
                   color=["#e63946", "#1d3557"], width=0.55, edgecolor="black", linewidth=1.2)
    ax1.set_ylabel("Execution Time (Seconds)", fontsize=11, fontweight="bold")
    ax1.set_title("(a) Computational Wall Time (200 Steps, 63k Nodes)", fontsize=11, fontweight="bold")
    ax1.grid(True, linestyle=":", alpha=0.6, axis="y")

    for bar, val in zip(bars, [time_numpy, time_numba]):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01 * time_numpy,
                 f"{val:.3f} s", ha="center", va="bottom", fontsize=10.5, fontweight="bold")

    # 子圖 2: 效能加速比展示
    bar_speedup = ax2.bar(["Numba Parallel Speedup"], [speedup], color="#2a9d8f", width=0.45, edgecolor="black", linewidth=1.2)
    ax2.axhline(1.0, color="gray", linestyle="--", linewidth=1.2, label="Baseline (1.0x)")
    ax2.set_ylabel("Speedup Multiplier ($\times$)", fontsize=11, fontweight="bold")
    ax2.set_title(f"(b) Hardware Acceleration Factor ({speedup:.1f}x Boost)", fontsize=11, fontweight="bold")
    ax2.set_ylim(0, max(speedup * 1.25, 2.0))
    ax2.grid(True, linestyle=":", alpha=0.6, axis="y")
    ax2.legend(loc="upper left")

    ax2.text(bar_speedup[0].get_x() + bar_speedup[0].get_width() / 2, speedup + 0.1,
             f"{speedup:.2f}x", ha="center", va="bottom", fontsize=14, fontweight="bold", color="#1d3557")

    plt.suptitle("PHANTOM Grid - High-Performance Computing (HPC) Acceleration Benchmark",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()

    out_file = Path("numba_acceleration_benchmark.png")
    plt.savefig(out_file, dpi=250)
    plt.close()

    # 遵守零桌面污染原則，備份至 generated/
    gen_dir = Path("generated")
    gen_dir.mkdir(exist_ok=True)
    shutil.copy(out_file, gen_dir / out_file.name)

    print(f"5. 效能對比圖檔已輸出至: {out_file.resolve()}")
    print(f"   同步備份至: {(gen_dir / out_file.name).resolve()}")
    print("==========================================================")
    print(" ✅ [第二階段：極致運算效能升級驗證通過！]                 ")
    print("==========================================================")


if __name__ == "__main__":
    benchmark_numba()
