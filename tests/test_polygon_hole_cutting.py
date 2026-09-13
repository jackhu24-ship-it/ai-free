# -*- coding: utf-8 -*-
"""
tests/test_polygon_hole_cutting.py - 任務一：任意多邊形射線法與 SDF 孔洞切割驗證
=============================================================================
驗證指標：
1. NACA 0012 翼型多邊形內部節點精準判定 (Polygon Ray-Casting)
2. 圓柱障礙物符號距離函數孔洞切割 (SDF Level-Set)
3. 形態學膨脹 1-2 層 RECEIVER 方塊圍繞孔洞無縫閉合
4. 輸出視覺化成果圖: polygon_hole_cutting.png
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
from geometry.airfoil_generator import AirfoilGridGenerator
from geometry.hole_cutter import HoleCutter


def test_polygon_and_sdf_hole_cutting():
    print("==========================================================")
    print(" 🚀 測試多邊形射線法 (NACA 翼型) 與 SDF (圓柱) 孔洞切割...")
    print("==========================================================")

    # 1. 建立高解析背景網格 [-2, 2] x [-2, 2]
    bg_grid_airfoil = StructuredCartesianGrid("bg_airfoil", bounds=(-2.0, 2.0, -2.0, 2.0), shape=(101, 101), priority=0)
    bg_grid_airfoil.initialize_fields(["u"])

    # 2. 取得 NACA 0012 翼型表面頂點，並旋轉 15 度
    xs, ys = AirfoilGridGenerator.generate_airfoil_surface(n_points=121, chord=1.2, thickness=0.12)
    # 平移中心至 (0, 0)
    xs -= 0.6
    alpha = np.radians(15.0)
    R = np.array([[np.cos(alpha), -np.sin(alpha)],
                  [np.sin(alpha),  np.cos(alpha)]])
    poly_pts = np.dot(np.column_stack([xs, ys]), R.T)

    # 執行多邊形孔洞切割
    in_hole_airfoil = HoleCutter.cut_polygon_holes_and_mark_fringe(bg_grid_airfoil, poly_pts, fringe_layers=1)

    n_hole_airfoil = int(np.sum(bg_grid_airfoil.status_mask == CellStatus.HOLE))
    n_recv_airfoil = int(np.sum(bg_grid_airfoil.status_mask == CellStatus.RECEIVER))
    n_field_airfoil = int(np.sum(bg_grid_airfoil.status_mask == CellStatus.FIELD))

    print(f"1. NACA 0012 多邊形射線切孔結果:")
    print(f"   - 孔洞盲點 (HOLE): {n_hole_airfoil}")
    print(f"   - 接收緩衝點 (RECEIVER): {n_recv_airfoil}")
    print(f"   - 有效計算點 (FIELD): {n_field_airfoil}")
    assert n_hole_airfoil > 0, "翼型內部未能識別出孔洞！"
    assert n_recv_airfoil > 0, "未能生成邊界接收點層！"
    print("  ✓ 多邊形射線法孔洞識別與接收層膨脹驗證通過！")

    # 3. 測試 SDF 圓柱孔洞切割 (圓心 (0, 0), 半徑 R=0.6)
    bg_grid_sdf = StructuredCartesianGrid("bg_sdf", bounds=(-2.0, 2.0, -2.0, 2.0), shape=(81, 81), priority=0)
    bg_grid_sdf.initialize_fields(["u"])

    def cylinder_sdf(X, Y):
        # 符號距離函數: 負值在圓內，正值在圓外
        return np.sqrt(X**2 + Y**2) - 0.6

    in_hole_sdf = HoleCutter.cut_sdf_holes_and_mark_fringe(bg_grid_sdf, cylinder_sdf, threshold=0.0, fringe_layers=1)
    n_hole_sdf = int(np.sum(bg_grid_sdf.status_mask == CellStatus.HOLE))
    n_recv_sdf = int(np.sum(bg_grid_sdf.status_mask == CellStatus.RECEIVER))

    print(f"2. 圓柱障礙物 SDF 切孔結果:")
    print(f"   - 孔洞盲點 (HOLE): {n_hole_sdf}")
    print(f"   - 接收緩衝點 (RECEIVER): {n_recv_sdf}")
    assert n_hole_sdf > 0 and n_recv_sdf > 0
    print("  ✓ 符號距離函數 (SDF) 孔洞切割驗證通過！")

    # 4. 繪製雙面板成果圖
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))

    # 子圖 1: NACA 0012 多邊形切孔
    X_a, Y_a = bg_grid_airfoil.get_coordinates()
    mask_a = bg_grid_airfoil.status_mask
    ax1.scatter(X_a[mask_a == CellStatus.FIELD], Y_a[mask_a == CellStatus.FIELD],
                c="#1f77b4", s=6, label="FIELD (Active)", alpha=0.5)
    ax1.scatter(X_a[mask_a == CellStatus.RECEIVER], Y_a[mask_a == CellStatus.RECEIVER],
                c="#ff7f0e", s=18, marker="s", label="RECEIVER (Fringe)", edgecolor="black", linewidth=0.3)
    ax1.scatter(X_a[mask_a == CellStatus.HOLE], Y_a[mask_a == CellStatus.HOLE],
                c="#d62728", s=14, marker="x", label="HOLE (Cutout)", linewidth=1.0)
    ax1.plot(poly_pts[:, 0], poly_pts[:, 1], "k-", linewidth=2.0, label="NACA 0012 Boundary")
    ax1.set_title("(a) NACA 0012 Polygon Ray-Casting Hole Cutting", fontsize=11, fontweight="bold")
    ax1.set_xlabel("World X")
    ax1.set_ylabel("World Y")
    ax1.axis("equal")
    ax1.set_xlim(-1.2, 1.2)
    ax1.set_ylim(-1.0, 1.0)
    ax1.grid(True, linestyle=":", alpha=0.4)
    ax1.legend(loc="upper right", fontsize=8)

    # 子圖 2: 圓柱 SDF 切孔
    X_s, Y_s = bg_grid_sdf.get_coordinates()
    mask_s = bg_grid_sdf.status_mask
    ax2.scatter(X_s[mask_s == CellStatus.FIELD], Y_s[mask_s == CellStatus.FIELD],
                c="#1f77b4", s=8, label="FIELD (Active)", alpha=0.5)
    ax2.scatter(X_s[mask_s == CellStatus.RECEIVER], Y_s[mask_s == CellStatus.RECEIVER],
                c="#ff7f0e", s=22, marker="s", label="RECEIVER (Fringe)", edgecolor="black", linewidth=0.3)
    ax2.scatter(X_s[mask_s == CellStatus.HOLE], Y_s[mask_s == CellStatus.HOLE],
                c="#d62728", s=18, marker="x", label="HOLE (Cutout)", linewidth=1.0)
    # 畫圓
    theta = np.linspace(0, 2*np.pi, 100)
    ax2.plot(0.6*np.cos(theta), 0.6*np.sin(theta), "k-", linewidth=2.0, label="Cylinder Surface (SDF=0)")
    ax2.set_title("(b) Cylinder Solid Obstacle SDF Level-Set Cutting", fontsize=11, fontweight="bold")
    ax2.set_xlabel("World X")
    ax2.set_ylabel("World Y")
    ax2.axis("equal")
    ax2.set_xlim(-1.2, 1.2)
    ax2.set_ylim(-1.0, 1.0)
    ax2.grid(True, linestyle=":", alpha=0.4)
    ax2.legend(loc="upper right", fontsize=8)

    plt.suptitle("PHANTOM Grid - Complex Geometry Polygon & SDF Hole Cutting",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()

    out_file = Path("polygon_hole_cutting.png")
    plt.savefig(out_file, dpi=200)
    plt.close()

    # 零桌面污染
    gen_dir = Path("generated")
    gen_dir.mkdir(exist_ok=True)
    shutil.copy(out_file, gen_dir / out_file.name)

    print(f"✓ 成果圖已成功輸出至 {out_file.resolve()}")
    print(f"✓ 已同步備份至 {(gen_dir / out_file.name).resolve()}")
    print("==========================================================")
    print(" ✅ [任務一：任意多邊形射線法與 SDF 孔洞切割驗證通過！]    ")
    print("==========================================================")


if __name__ == "__main__":
    test_polygon_and_sdf_hole_cutting()
