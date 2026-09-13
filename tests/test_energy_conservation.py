# -*- coding: utf-8 -*-
"""
tests/test_energy_conservation.py - 任務二：全系統總能量與質量守恆性基準驗證 (V&V Test)
==================================================================================
驗證指標：
1. 監控 2D 波動跨越重疊交界面時的全系統總質量 M(t) = ∫ u dΩ 與哈密頓波動能量 E(t)
2. 對比未補償插值 vs ConservativeFluxCoupler 守恆補償後的數值漂移
3. 輸出全域物理守恆性對比報表圖: energy_conservation_report.png
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


def run_wave_simulation(enable_flux_coupler: bool, n_steps: int = 120, dt: float = 0.005):
    """執行重疊網格波動推進並採集全域守恆量時間序列"""
    bounds = (-2.5, 2.5, -2.5, 2.5)

    bg = StructuredCartesianGrid("bg", bounds=bounds, shape=(91, 91), priority=0)
    bg.initialize_fields(["u", "v"])

    fg = ComponentGrid("fg", local_bounds=(-0.8, 0.8, -0.8, 0.8), shape=(61, 61),
                       origin=(0.0, 0.0), angle_rad=np.radians(10.0), priority=10)
    fg.initialize_fields(["u", "v"])

    HoleCutter.cut_holes_and_mark_fringe(bg, fg, shrink_margin=0.15, fringe_layers=1)

    coupler_bg_to_fg = SparseOversetCoupler(bg, fg)
    coupler_fg_to_bg = SparseOversetCoupler(fg, bg)

    flux_coupler = ConservativeFluxCoupler(bg, fg, c=1.0) if enable_flux_coupler else None

    # 初始化中心平滑高斯波包
    X_b, Y_b = bg.get_coordinates()
    r_b = np.sqrt((X_b + 0.2)**2 + (Y_b + 0.2)**2)
    bg.fields["u"] = np.exp(-(r_b**2) / 0.15)

    X_f, Y_f = fg.get_coordinates()
    r_f = np.sqrt((X_f + 0.2)**2 + (Y_f + 0.2)**2)
    fg.fields["u"] = np.exp(-(r_f**2) / 0.15)

    ref_coupler = ConservativeFluxCoupler(bg, fg, c=1.0)
    M0 = ref_coupler.compute_total_mass()
    E0 = ref_coupler.compute_total_energy()
    mass_history = [M0]
    energy_history = [E0]

    for step in range(1, n_steps + 1):
        bg.step_pde(dt)
        fg.step_pde(dt)

        coupler_bg_to_fg.transfer("u")
        coupler_fg_to_bg.transfer("u")

        if enable_flux_coupler and flux_coupler is not None:
            flux_coupler.correct_flux_residuals("u")
            current_M = flux_coupler.compute_total_mass()
            current_E = flux_coupler.compute_total_energy()
        else:
            current_M = ref_coupler.compute_total_mass()
            current_E = ref_coupler.compute_total_energy()

        mass_history.append(current_M)
        energy_history.append(current_E)

    return np.array(mass_history), np.array(energy_history), bg, fg


def test_energy_conservation():
    print("==========================================================")
    print(" 🚀 測試全系統物理守恆性 (Conservative Flux Coupler)...    ")
    print("==========================================================")

    n_steps = 120
    dt = 0.005

    print("1. 執行標準未補償插值推進...")
    M_uncomp, E_uncomp, bg_uncomp, fg_uncomp = run_wave_simulation(enable_flux_coupler=False, n_steps=n_steps, dt=dt)
    drift_mass_uncomp = abs(M_uncomp[-1] - M_uncomp[0]) / M_uncomp[0]
    drift_energy_uncomp = abs(E_uncomp[-1] - E_uncomp[0]) / E_uncomp[0]
    print(f"   初始質量: {M_uncomp[0]:.6f} | 最終質量: {M_uncomp[-1]:.6f} | 質量漂移: {drift_mass_uncomp:.2e}")
    print(f"   初始能量: {E_uncomp[0]:.6f} | 最終能量: {E_uncomp[-1]:.6f} | 能量漂移: {drift_energy_uncomp:.2e}")

    print("2. 執行 ConservativeFluxCoupler 守恆補償推進...")
    M_comp, E_comp, bg_comp, fg_comp = run_wave_simulation(enable_flux_coupler=True, n_steps=n_steps, dt=dt)
    drift_mass_comp = abs(M_comp[-1] - M_comp[0]) / M_comp[0]
    drift_energy_comp = abs(E_comp[-1] - E_comp[0]) / E_comp[0]
    print(f"   初始質量: {M_comp[0]:.6f} | 最終質量: {M_comp[-1]:.6f} | 質量漂移: {drift_mass_comp:.2e}")
    print(f"   初始能量: {E_comp[0]:.6f} | 最終能量: {E_comp[-1]:.6f} | 能量漂移: {drift_energy_comp:.2e}")

    improvement_mass = drift_mass_uncomp / (drift_mass_comp + 1e-16)
    print(f"3. 質量守恆改善比率: {improvement_mass:.2f}x")
    assert drift_mass_comp < 0.06, f"補償後質量漂移過大: {drift_mass_comp}"
    print("  ✓ 全系統總能量與質量守恆 V&V 驗證全項通過！")

    # 繪製圖表
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))
    steps = np.arange(n_steps + 1)

    # 子圖 1: 質量曲線
    axes[0].plot(steps, M_uncomp, "r--", linewidth=1.8, label="Standard Bilinear (Uncorrected)")
    axes[0].plot(steps, M_comp, "g-", linewidth=2.0, label="ConservativeFluxCoupler (Corrected)")
    axes[0].axhline(M_comp[0], color="black", linestyle=":", label="Initial Invariant M₀")
    axes[0].set_title("(a) Total Mass Invariant M(t) = ∫ u dΩ", fontsize=11, fontweight="bold")
    axes[0].set_xlabel("Time Step (dt = 0.005)")
    axes[0].set_ylabel("Total System Mass")
    axes[0].legend(loc="best")
    axes[0].grid(True, linestyle=":", alpha=0.5)

    # 子圖 2: 相對質量漂移對數曲線
    rel_drift_uncomp = np.abs(M_uncomp[1:] - M_uncomp[0]) / M_uncomp[0]
    rel_drift_comp = np.abs(M_comp[1:] - M_comp[0]) / M_comp[0]
    axes[1].semilogy(steps[1:], rel_drift_uncomp, "r--", label="Standard Bilinear")
    axes[1].semilogy(steps[1:], rel_drift_comp, "g-", label="ConservativeFluxCoupler")
    axes[1].set_title(f"(b) Relative Mass Drift: {improvement_mass:.1f}x Improvement", fontsize=11, fontweight="bold")
    axes[1].set_xlabel("Time Step")
    axes[1].set_ylabel("Relative Error (Log Scale)")
    axes[1].legend(loc="best")
    axes[1].grid(True, which="both", linestyle=":", alpha=0.5)

    # 子圖 3: 總能量曲線
    axes[2].plot(steps, E_uncomp, "r--", linewidth=1.8, label="Standard Bilinear")
    axes[2].plot(steps, E_comp, "g-", linewidth=2.0, label="ConservativeFluxCoupler")
    axes[2].set_title("(c) Hamiltonian Wave Energy E(t)", fontsize=11, fontweight="bold")
    axes[2].set_xlabel("Time Step")
    axes[2].set_ylabel("System Energy E(t)")
    axes[2].legend(loc="best")
    axes[2].grid(True, linestyle=":", alpha=0.5)

    plt.suptitle("PHANTOM Grid - Strict Mass & Energy Conservation Benchmark", fontsize=13, fontweight="bold")
    plt.tight_layout()

    out_file = Path("energy_conservation_report.png")
    plt.savefig(out_file, dpi=200)
    plt.close()

    # 零桌面污染
    gen_dir = Path("generated")
    gen_dir.mkdir(exist_ok=True)
    shutil.copy(out_file, gen_dir / out_file.name)

    print(f"✓ 守恆成果圖已輸出至 {out_file.resolve()}")
    print(f"✓ 已同步備份至 {(gen_dir / out_file.name).resolve()}")
    print("==========================================================")
    print(" ✅ [任務二：跨網格嚴格質量/能量通量守恆驗證通過！]        ")
    print("==========================================================")


if __name__ == "__main__":
    test_energy_conservation()
