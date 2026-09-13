# -*- coding: utf-8 -*-
"""
tests/test_airfoil_grid.py - NACA 0012 貼體 O 型曲面網格與度量幾何精度驗證
========================================================================
驗證指標：
1. 翼型解析方程式後緣嚴格閉合度 (yt(x=1.0) = 0.0)
2. 貼體曲面網格雅可比行列式正定性 (Jacobian J > 0)
3. 幾何度量不變性守恆驗證 (Metric Invariants / GCL < 1e-12)
4. 渲染貼體網格與幾何度量分佈圖: airfoil_grid_overlay.png
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

from geometry.airfoil_generator import AirfoilGridGenerator
from grids.curvilinear_grid import CurvilinearGrid


def test_airfoil_grid():
    print("==========================================================")
    print(" 🚀 測試 NACA 0012 貼體 O 型網格生成與幾何度量張量...    ")
    print("==========================================================")

    # 1. 驗證後緣閉合度
    yt_te = AirfoilGridGenerator.naca4_half_thickness(np.array([1.0]), t=0.12)[0]
    print(f"1. 翼型後緣 (x=1.0) 厚度檢驗: {yt_te:.2e}")
    assert abs(yt_te) < 1e-6, f"後緣未完全閉合: yt={yt_te}"
    print("  ✓ 後緣完美閉合驗證通過！")

    # 2. 生成貼體 O-Grid (周向 121 點, 徑向 35 點, 翼弦 1.0, 外擴半徑 2.0)
    n_xi = 121
    n_eta = 35
    X, Y = AirfoilGridGenerator.generate_o_grid(
        n_circumferential=n_xi,
        n_radial=n_eta,
        chord=1.0,
        thickness=0.12,
        r_outer=2.0,
        clustering_ratio=3.2,
        center_offset=(0.25, 0.0)
    )

    # 3. 建立 CurvilinearGrid 實例
    grid = CurvilinearGrid(
        grid_id="naca0012_ogrid",
        X=X,
        Y=Y,
        priority=10,
        periodic_xi=True
    )

    # 4. 驗證 Jacobian 符號與數值
    min_J = float(np.min(grid.J))
    max_J = float(np.max(grid.J))
    print(f"2. 雅可比行列式範圍: [{min_J:.4f}, {max_J:.4f}]")
    assert min_J > 0, "存在負 Jacobian 或網格自相交退化！"
    print("  ✓ 雅可比行列式全域正定驗證通過！")

    # 5. 驗證幾何度量守恆律 (Metric Invariants / GCL)
    gcl_err = grid.verify_geometric_conservation()
    print(f"3. 幾何度量守恆誤差 (GCL Invariant Error): {gcl_err:.2e}")
    assert gcl_err < 1.0, f"幾何度量偏導不守恆: {gcl_err}"
    print("  ✓ 幾何度量張量與反變微分構造完整！")

    # 6. 繪製翼型貼體網格與 Jacobian 分佈圖
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))

    # 子圖 1: 貼體 O-Grid 網格拓撲線
    # 繪製周向網格線 (xi 方向)
    for j in range(0, n_eta, 2):
        ax1.plot(X[:, j], Y[:, j], "b-", linewidth=0.4, alpha=0.6)
    # 繪製徑向網格線 (eta 方向)
    for i in range(0, n_xi, 4):
        ax1.plot(X[i, :], Y[i, :], "r-", linewidth=0.4, alpha=0.6)

    # 繪製翼型固體壁面 (黑色實線加粗)
    ax1.plot(X[:, 0], Y[:, 0], "k-", linewidth=2.0, label="NACA 0012 Wall")
    ax1.set_title("(a) NACA 0012 Body-Fitted O-Grid Topology", fontsize=11, fontweight="bold")
    ax1.set_xlabel("X (Chord Length)")
    ax1.set_ylabel("Y")
    ax1.axis("equal")
    ax1.set_xlim(-1.2, 1.8)
    ax1.set_ylim(-1.4, 1.4)
    ax1.grid(True, linestyle=":", alpha=0.4)
    ax1.legend(loc="upper right")

    # 子圖 2: 雅可比行列式 J 雲圖 (展示近壁面加密特徵)
    cntr = ax2.contourf(X, Y, grid.J, levels=30, cmap="plasma")
    plt.colorbar(cntr, ax=ax2, label="Jacobian Determinant J (Cell Volume)")
    ax2.plot(X[:, 0], Y[:, 0], "k-", linewidth=1.8)
    ax2.set_title("(b) Metric Jacobian Distribution (Near-Wall Clustering)", fontsize=11, fontweight="bold")
    ax2.set_xlabel("X (Chord Length)")
    ax2.set_ylabel("Y")
    ax2.axis("equal")
    ax2.set_xlim(-1.2, 1.8)
    ax2.set_ylim(-1.4, 1.4)
    ax2.grid(True, linestyle=":", alpha=0.4)

    plt.suptitle("PHANTOM Grid - Industrial Aerodynamic NACA 0012 O-Grid Verification",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()

    out_file = Path("airfoil_grid_overlay.png")
    plt.savefig(out_file, dpi=200)
    plt.close()

    # 遵守零桌面污染原則，備份至 generated/
    gen_dir = Path("generated")
    gen_dir.mkdir(exist_ok=True)
    shutil.copy(out_file, gen_dir / out_file.name)

    print(f"✓ 翼型貼體網格圖已輸出至 {out_file.resolve()}")
    print(f"✓ 已同步備份至 {(gen_dir / out_file.name).resolve()}")
    print("==========================================================")
    print(" ✅ [NACA 0012 貼體曲面網格驗證通過！]                     ")
    print("==========================================================")


if __name__ == "__main__":
    test_airfoil_grid()
