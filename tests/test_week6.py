# -*- coding: utf-8 -*-
"""
tests/test_week6.py - 第 6 週稀疏矩陣 CSR 邊界插值加速與國際競賽基準評測報告
===========================================================================
驗證內容：
1. 稀疏矩陣 SpMV 插值與傳統逐點雙線性插值之數學等價性 (誤差 < 1e-13)
2. 稀疏矩陣列和歸一性 (Row sum = 1.0) 與極致稀疏度 (> 99.9%)
3. 全域單一細網格 vs PHANTOM 重疊自適應網格之波動求解與資源消耗評測
4. 輸出競賽發表等級評測圖表: week6_benchmark_report.png
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import shutil
import time
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from core.types import CellStatus
from grids.structured_cartesian import StructuredCartesianGrid
from grids.component_grid import ComponentGrid
from geometry.hole_cutter import HoleCutter
from coupling.interpolator import OversetInterpolator
from coupling.sparse_coupler import SparseCoupler
from solver.phantom_runner import PhantomRunner
from benchmarks.benchmark_week6 import run_boundary_exchange_benchmark, run_solver_comparison_benchmark


def test_sparse_coupler_equivalence():
    """驗證 1: 稀疏矩陣插值與傳統插值數值完全等價"""
    print("[測試 1] 驗證 CSR 稀疏矩陣與傳統雙線性插值等價性...")
    bg = StructuredCartesianGrid("bg", bounds=(-3.0, 3.0, -3.0, 3.0), shape=(91, 91), priority=0)
    bg.initialize_fields(["u", "v"])
    fg = ComponentGrid("fg", local_bounds=(-1.0, 1.0, -0.6, 0.6), shape=(61, 37),
                       origin=(0.1, -0.05), angle_rad=np.radians(20.0), priority=10)
    fg.initialize_fields(["u", "v"])

    HoleCutter.cut_holes_and_mark_fringe(bg, fg, shrink_margin=0.15, fringe_layers=1)

    # 填入隨機測試場
    rng = np.random.default_rng(12345)
    bg.fields["u"] = rng.standard_normal(bg.shape)
    fg.fields["u"] = rng.standard_normal(fg.shape)

    # 傳統插值預期值
    bg_trad = np.copy(bg.fields["u"])
    fg_trad = np.copy(fg.fields["u"])
    OversetInterpolator.exchange_all_boundaries(bg, fg, "u")
    expected_fg_recv = np.copy(fg.fields["u"][fg.status_mask == CellStatus.RECEIVER])
    expected_bg_recv = np.copy(bg.fields["u"][bg.status_mask == CellStatus.RECEIVER])

    # 重置並使用 CSR 稀疏矩陣插值
    bg.fields["u"] = bg_trad
    fg.fields["u"] = fg_trad
    coupler = SparseCoupler(bg, fg)
    coupler.build()
    coupler.exchange_fields(["u"])

    actual_fg_recv = fg.fields["u"][fg.status_mask == CellStatus.RECEIVER]
    actual_bg_recv = bg.fields["u"][bg.status_mask == CellStatus.RECEIVER]

    diff_fg = np.max(np.abs(actual_fg_recv - expected_fg_recv))
    diff_bg = np.max(np.abs(actual_bg_recv - expected_bg_recv))

    print(f"  - 前景接收點最大絕對偏差: {diff_fg:.2e}")
    print(f"  - 背景接收點最大絕對偏差: {diff_bg:.2e}")
    assert diff_fg < 1e-13, f"前景插值等價性驗證失敗: diff={diff_fg}"
    assert diff_bg < 1e-13, f"背景插值等價性驗證失敗: diff={diff_bg}"
    print("  ✓ CSR 稀疏插值器通過機器精度等價性檢驗！")


def test_sparse_matrix_properties():
    """驗證 2: 檢驗稀疏矩陣之行和歸一性與極致稀疏度"""
    print("\n[測試 2] 驗證 CSR 稀疏矩陣數學特性與稀疏度...")
    bg = StructuredCartesianGrid("bg", bounds=(-3.0, 3.0, -3.0, 3.0), shape=(91, 91), priority=0)
    bg.initialize_fields(["u"])
    fg = ComponentGrid("fg", local_bounds=(-1.0, 1.0, -0.6, 0.6), shape=(61, 37),
                       origin=(0.0, 0.0), angle_rad=np.radians(15.0), priority=10)
    fg.initialize_fields(["u"])

    HoleCutter.cut_holes_and_mark_fringe(bg, fg, shrink_margin=0.15, fringe_layers=1)

    coupler = SparseCoupler(bg, fg)
    coupler.build()

    info = coupler.get_sparsity_info()
    sparsity_fg = info["bg_to_comp"]["sparsity"]
    sparsity_bg = info["comp_to_bg"]["sparsity"]

    # 檢查列和 (Row sum of weights = 1.0)
    row_sum_fg = np.array(coupler.W_bg_to_comp.sum(axis=1)).ravel()
    row_sum_bg = np.array(coupler.W_comp_to_bg.sum(axis=1)).ravel()

    assert np.allclose(row_sum_fg, 1.0, atol=1e-12), "前景傳輸矩陣權重和不為 1.0！"
    assert np.allclose(row_sum_bg, 1.0, atol=1e-12), "背景傳輸矩陣權重和不為 1.0！"
    assert sparsity_fg > 0.999, f"稀疏度不足: {sparsity_fg:.4f}"
    assert sparsity_bg > 0.998, f"稀疏度不足: {sparsity_bg:.4f}"

    print(f"  - 背景->前景傳輸矩陣維度: {info['bg_to_comp']['shape']}, 稀疏度: {sparsity_fg*100:.2f}%")
    print(f"  - 前景->背景傳輸矩陣維度: {info['comp_to_bg']['shape']}, 稀疏度: {sparsity_bg*100:.2f}%")
    print("  ✓ 稀疏矩陣歸一性與超高稀疏度驗證通過！")


def test_week6_benchmark_and_visualization():
    """驗證 3: 執行全域單一網格 vs PHANTOM 基準評測並輸出多維視覺化報告"""
    print("\n[測試 3] 執行國際競賽級基準評測與儀表板渲染...")
    b_exch = run_boundary_exchange_benchmark(n_iterations=300)
    b_solver = run_solver_comparison_benchmark(total_steps=120, dt=0.01)

    # 繪製 4 面板高解析度報告圖
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    plt.subplots_adjust(hspace=0.28, wspace=0.24)

    # -------------------------------------------------------------
    # 子圖 1: 物理波動場分佈 (PHANTOM 稀疏重疊網格成果)
    # -------------------------------------------------------------
    ax1 = axes[0, 0]
    bg = StructuredCartesianGrid("bg", bounds=(-3.0, 3.0, -3.0, 3.0), shape=(91, 91), priority=0)
    bg.initialize_fields(["u", "v"])
    fg = ComponentGrid("fg", local_bounds=(-1.0, 1.0, -0.6, 0.6), shape=(61, 37),
                       origin=(0.0, 0.0), angle_rad=np.radians(15.0), priority=10)
    fg.initialize_fields(["u", "v"])

    X_bg, Y_bg = bg.get_coordinates()
    r0_bg = np.sqrt((X_bg + 0.8)**2 + (Y_bg + 0.8)**2)
    bg.fields["u"] = np.exp(-(r0_bg**2) / 0.08)

    X_fg, Y_fg = fg.get_coordinates()
    r0_fg = np.sqrt((X_fg + 0.8)**2 + (Y_fg + 0.8)**2)
    fg.fields["u"] = np.exp(-(r0_fg**2) / 0.08)

    runner = PhantomRunner(bg, fg, use_sparse=True)
    runner.rebuild_topology()
    for _ in range(120):
        runner.step(0.01, ["u", "v"])

    bg_disp = np.copy(bg.fields["u"])
    bg_disp[bg.status_mask == CellStatus.HOLE] = np.nan

    c1 = ax1.contourf(X_bg, Y_bg, bg_disp, levels=30, cmap="viridis", alpha=0.88)
    fg_mask = (fg.status_mask == CellStatus.FIELD)
    X_fg_now, Y_fg_now = fg.get_coordinates()
    ax1.scatter(X_fg_now[fg_mask], Y_fg_now[fg_mask], c=fg.fields["u"][fg_mask],
                cmap="viridis", s=10, edgecolor="black", linewidth=0.25, label="Component Fine")
    plt.colorbar(c1, ax=ax1, label="Wave Amplitude u")
    ax1.set_title("(a) PHANTOM Overlapping Grid: Wavefield (t=1.2s)", fontsize=11, fontweight="bold")
    ax1.set_xlabel("World X")
    ax1.set_ylabel("World Y")
    ax1.axis("equal")
    ax1.legend(loc="upper right", fontsize=8)
    ax1.grid(True, linestyle=":", alpha=0.4)

    # -------------------------------------------------------------
    # 子圖 2: 稀疏矩陣結構可視化 (Sparsity Spy Pattern)
    # -------------------------------------------------------------
    ax2 = axes[0, 1]
    W = runner.sparse_coupler.W_bg_to_comp
    min_c = int(np.min(W.indices)) if W.nnz > 0 else 0
    max_c = int(np.max(W.indices)) if W.nnz > 0 else W.shape[1]
    pad = 50
    c_start = max(0, min_c - pad)
    c_end = min(W.shape[1], max_c + pad)

    sub_W = W[:min(80, W.shape[0]), c_start:c_end]
    ax2.spy(sub_W, markersize=3.5, color="#1f77b4", aspect="auto")
    ax2.set_title(f"(b) CSR Transfer Matrix Structure: W_bg_to_comp\n(Sparsity: {100*(1.0-W.nnz/(W.shape[0]*W.shape[1])):.2f}%, nnz={W.nnz})",
                  fontsize=11, fontweight="bold")
    ax2.set_xlabel(f"Donor Flattened Index (Offset: {c_start} ~ {c_end})")
    ax2.set_ylabel("Receiver Index (Component Fringe)")

    # -------------------------------------------------------------
    # 子圖 3: 效能指標對比柱狀圖 (記憶體與通訊加速)
    # -------------------------------------------------------------
    ax3 = axes[1, 0]
    metrics = ["Grid Cells", "Memory (KB)", "Exchange (ms/step)"]
    fine_vals = [b_solver["fine"]["total_cells"] / 1000.0,
                 b_solver["fine"]["memory_kb"],
                 b_exch["t_interp_per_call_ms"]]
    phantom_vals = [b_solver["phantom"]["total_cells"] / 1000.0,
                    b_solver["phantom"]["memory_kb"],
                    b_exch["t_sparse_per_call_ms"]]

    x_idx = np.arange(len(metrics))
    width = 0.32

    rects1 = ax3.bar(x_idx - width/2, fine_vals, width, label="Uniform Fine", color="#d62728", alpha=0.85)
    rects2 = ax3.bar(x_idx + width/2, phantom_vals, width, label="PHANTOM Sparse", color="#2ca02c", alpha=0.85)

    ax3.set_ylabel("Value (Normalized Units)")
    ax3.set_title("(c) Resource & Latency Comparison", fontsize=11, fontweight="bold")
    ax3.set_xticks(x_idx)
    ax3.set_xticklabels(["Cells (x10³)", "RAM (KB)", "Coupling (ms)"])
    ax3.legend(loc="upper right")
    ax3.grid(True, axis="y", linestyle=":", alpha=0.4)

    # 標記改善數據
    ax3.text(0, max(fine_vals[0], phantom_vals[0]) * 0.7,
             f"-{b_solver['comparison']['cell_reduction_pct']:.1f}%",
             ha="center", fontweight="bold", color="#1b5e20", fontsize=9)
    ax3.text(1, max(fine_vals[1], phantom_vals[1]) * 0.7,
             f"-{b_solver['comparison']['mem_saving_pct']:.1f}%",
             ha="center", fontweight="bold", color="#1b5e20", fontsize=9)
    ax3.text(2, max(fine_vals[2], phantom_vals[2]) * 0.7,
             f"{b_exch['speedup']:.1f}x FAST",
             ha="center", fontweight="bold", color="#1b5e20", fontsize=9)

    # -------------------------------------------------------------
    # 子圖 4: 穿越重疊交界面的 1D 波動截面連續性檢驗
    # -------------------------------------------------------------
    ax4 = axes[1, 1]
    # 取 y = 0 切線剖面
    j_bg = np.argmin(np.abs(Y_bg[0, :] - 0.0))
    x_slice_bg = X_bg[:, j_bg]
    u_slice_bg = np.copy(bg.fields["u"][:, j_bg])
    u_slice_bg[bg.status_mask[:, j_bg] == CellStatus.HOLE] = np.nan

    ax4.plot(x_slice_bg, u_slice_bg, "b-o", markersize=3, label="Background Mesh (y=0)", alpha=0.85)

    # 前景組件網格對應點
    comp_pts_x = []
    comp_pts_u = []
    for ii in range(fg.nx):
        for jj in range(fg.ny):
            wx = X_fg_now[ii, jj]
            wy = Y_fg_now[ii, jj]
            if abs(wy - 0.0) < 0.04 and fg.status_mask[ii, jj] == CellStatus.FIELD:
                comp_pts_x.append(wx)
                comp_pts_u.append(fg.fields["u"][ii, jj])

    if comp_pts_x:
        sort_idx = np.argsort(comp_pts_x)
        ax4.plot(np.array(comp_pts_x)[sort_idx], np.array(comp_pts_u)[sort_idx],
                 "r--s", markersize=4, label="Component Fine Mesh", alpha=0.9)

    ax4.set_title("(d) Cross-Boundary Wavefront Continuity (y ≈ 0.0)", fontsize=11, fontweight="bold")
    ax4.set_xlabel("World Coordinate X")
    ax4.set_ylabel("Wave Amplitude u")
    ax4.axvspan(-0.8, 0.8, color="gray", alpha=0.15, label="Overlap Zone")
    ax4.grid(True, linestyle=":", alpha=0.4)
    ax4.legend(loc="upper left", fontsize=8)

    plt.suptitle("PHANTOM Overlapping Grid - Week 6 Comprehensive Benchmark",
                 fontsize=14, fontweight="bold", y=0.98)
    plt.tight_layout()

    out_file = Path("week6_benchmark_report.png")
    plt.savefig(out_file, dpi=200)
    plt.close()

    # 嚴格遵守零桌面污染原則，備份至 generated/
    gen_dir = Path("generated")
    gen_dir.mkdir(exist_ok=True)
    shutil.copy(out_file, gen_dir / out_file.name)

    print(f"  ✓ 基準評測圖表已成功輸出: {out_file.resolve()}")
    print(f"  ✓ 已同步備份至: {(gen_dir / out_file.name).resolve()}")


def test_week6():
    """執行第 6 週全套測試案例"""
    test_sparse_coupler_equivalence()
    test_sparse_matrix_properties()
    test_week6_benchmark_and_visualization()
    print("\n=================================================================")
    print(" ✓✓✓ 第 6 週稀疏矩陣加速與競賽基準評測全項通過！ ✓✓✓")
    print("=================================================================")


if __name__ == "__main__":
    test_week6()
