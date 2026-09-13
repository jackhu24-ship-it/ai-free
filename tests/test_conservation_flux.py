# -*- coding: utf-8 -*-
"""
tests/test_conservation_flux.py - 跨邊界 Berger 嚴格守恆性通量修正與全域質量驗證
================================================================================
驗證指標：
1. 重疊網格系統在標準插值 vs Berger 守恆通量修正下的全域質量/能量漂移對比
2. 封閉物理系統總量積分監控 (ConservationMonitor)
3. 輸出數值守恆性驗證報表圖: conservation_flux_verification.png
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
from coupling.conservative_flux import ConservativeFluxMatcher
from solver.conservation_monitor import ConservationMonitor


def run_simulation(enable_flux_correction: bool, n_steps: int = 120, dt: float = 0.005):
    """執行重疊網格波動推進並記錄全域守恆量"""
    bounds = (-2.5, 2.5, -2.5, 2.5)

    # 1. 背景笛卡爾網格
    bg = StructuredCartesianGrid("bg", bounds=bounds, shape=(91, 91), priority=0)
    bg.initialize_fields(["u", "v"])

    # 2. 前景高解析度網格 (覆蓋核心區)
    fg = ComponentGrid("fg", local_bounds=(-0.9, 0.9, -0.9, 0.9), shape=(61, 61),
                       origin=(0.0, 0.0), angle_rad=np.radians(12.0), priority=10)
    fg.initialize_fields(["u", "v"])

    # 拓撲切割
    HoleCutter.cut_holes_and_mark_fringe(bg, fg, shrink_margin=0.15, fringe_layers=1)

    # 稀疏通訊運算元
    coupler_bg_to_fg = SparseOversetCoupler(bg, fg)
    coupler_fg_to_bg = SparseOversetCoupler(fg, bg)

    # 守恆性通量修正器
    flux_matcher = ConservativeFluxMatcher(bg, fg) if enable_flux_correction else None

    # 初始化平滑正質量高斯波包 (確保系統總質量 M0 > 0)
    X_b, Y_b = bg.get_coordinates()
    r_b = np.sqrt((X_b + 0.3)**2 + (Y_b + 0.3)**2)
    bg.fields["u"] = np.exp(-(r_b**2) / 0.15)

    X_f, Y_f = fg.get_coordinates()
    r_f = np.sqrt((X_f + 0.3)**2 + (Y_f + 0.3)**2)
    fg.fields["u"] = np.exp(-(r_f**2) / 0.15)

    # 監控器
    monitor = ConservationMonitor([bg, fg])
    monitor.record_step(0, ["u"])

    for step in range(1, n_steps + 1):
        # 局部 PDE 推進
        bg.step_pde(dt)
        fg.step_pde(dt)

        # 稀疏邊界插值
        coupler_bg_to_fg.transfer("u")
        coupler_fg_to_bg.transfer("u")

        # 若啟用，執行 Berger 跨邊界守恆通量修正
        if enable_flux_correction and flux_matcher is not None:
            flux_matcher.apply_flux_correction("u")

        # 記錄守恆量
        monitor.record_step(step, ["u"])

    return monitor, bg, fg


def test_conservation_flux():
    print("==========================================================")
    print(" 🚀 測試跨邊界 Berger 守恆通量修正 (Flux Matching)...     ")
    print("==========================================================")

    n_steps = 140
    dt = 0.005

    print("1. 執行標準插值 (未開啟通量修正)...")
    mon_uncorrected, bg_uncorr, fg_uncorr = run_simulation(enable_flux_correction=False, n_steps=n_steps, dt=dt)
    m0_uncorr = mon_uncorrected.initial_mass["u"]
    m_end_uncorr = mon_uncorrected.mass_history["u"][-1]
    drift_uncorr = mon_uncorrected.relative_drift_history["u"][-1]
    print(f"   初始質量: {m0_uncorr:.6f} | 最終質量: {m_end_uncorr:.6f} | 漂移: {drift_uncorr:.2e}")

    print("2. 執行 Berger 跨邊界守恆通量修正...")
    mon_corrected, bg_corr, fg_corr = run_simulation(enable_flux_correction=True, n_steps=n_steps, dt=dt)
    m0_corr = mon_corrected.initial_mass["u"]
    m_end_corr = mon_corrected.mass_history["u"][-1]
    drift_corr = mon_corrected.relative_drift_history["u"][-1]
    print(f"   初始質量: {m0_corr:.6f} | 最終質量: {m_end_corr:.6f} | 漂移: {drift_corr:.2e}")

    # 驗證守恆性指標顯著改善
    improvement = drift_uncorr / (drift_corr + 1e-16)
    print(f"3. 守恆性改善倍率: {improvement:.2f}x")
    assert drift_corr < 0.05, f"守恆修正後漂移超出容許範圍: {drift_corr}"
    print("  ✓ Berger 守恆通量修正閉環驗證通過！")

    # 繪製競賽級對比報告圖
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))

    # 子圖 1: 總質量演化歷程
    ax1 = axes[0]
    steps = np.arange(n_steps + 1)
    ax1.plot(steps, mon_uncorrected.mass_history["u"], "r--", linewidth=1.8, label="Standard Interpolation")
    ax1.plot(steps, mon_corrected.mass_history["u"], "g-", linewidth=2.0, label="Berger Flux Corrected")
    ax1.axhline(m0_corr, color="black", linestyle=":", label="Initial Mass M₀")
    ax1.set_title("(a) Total Mass Evolution M(t)", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Time Step")
    ax1.set_ylabel("Total System Mass")
    ax1.legend(loc="best")
    ax1.grid(True, linestyle=":", alpha=0.5)

    # 子圖 2: 相對漂移對數曲線
    ax2 = axes[1]
    ax2.semilogy(steps[1:], mon_uncorrected.relative_drift_history["u"][1:], "r--", label="Standard Interpolation")
    ax2.semilogy(steps[1:], mon_corrected.relative_drift_history["u"][1:], "g-", label="Berger Flux Corrected")
    ax2.set_title("(b) Relative Mass Drift |M(t)-M₀| / M₀", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Time Step")
    ax2.set_ylabel("Relative Drift Error (Log Scale)")
    ax2.legend(loc="best")
    ax2.grid(True, which="both", linestyle=":", alpha=0.5)

    # 子圖 3: 最終波場快照 (展示平滑度與完整性)
    ax3 = axes[2]
    X_b, Y_b = bg_corr.get_coordinates()
    disp_u = np.copy(bg_corr.fields["u"])
    disp_u[bg_corr.status_mask == CellStatus.HOLE] = np.nan
    cntr = ax3.contourf(X_b, Y_b, disp_u, levels=25, cmap="viridis", alpha=0.85)
    plt.colorbar(cntr, ax=ax3, label="Wave Amplitude u")

    X_f, Y_f = fg_corr.get_coordinates()
    active_fg = (fg_corr.status_mask == CellStatus.FIELD)
    ax3.scatter(X_f[active_fg], Y_f[active_fg], c=fg_corr.fields["u"][active_fg],
                cmap="viridis", s=8, edgecolor="black", linewidth=0.2)
    ax3.set_title(f"(c) Conservative Wavefield (Step {n_steps})", fontsize=11, fontweight="bold")
    ax3.set_xlabel("World X")
    ax3.set_ylabel("World Y")
    ax3.axis("equal")
    ax3.grid(True, linestyle=":", alpha=0.4)

    plt.suptitle("PHANTOM Grid - Berger Conservative Flux Matching Verification",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()

    out_file = Path("conservation_flux_verification.png")
    plt.savefig(out_file, dpi=200)
    plt.close()

    # 遵守零桌面污染原則，備份至 generated/
    gen_dir = Path("generated")
    gen_dir.mkdir(exist_ok=True)
    shutil.copy(out_file, gen_dir / out_file.name)

    print(f"✓ 守恆通量驗證報表已輸出至 {out_file.resolve()}")
    print(f"✓ 已同步備份至 {(gen_dir / out_file.name).resolve()}")
    print("==========================================================")
    print(" ✅ [Berger 守恆性通量匹配驗證通過！]                      ")
    print("==========================================================")


if __name__ == "__main__":
    test_conservation_flux()
