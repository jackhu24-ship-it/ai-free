# -*- coding: utf-8 -*-
"""
tests/test_task1_airfoil.py - NACA 0012 貼體 O 型網格生成與多邊形孔洞切割驗證
========================================================================
任務一驗證標的：
1. 建立背景笛卡爾網格 ([-1.5, 1.5] x [-1.0, 1.0], 121 x 81)
2. 建立攻角 12 度之 NACA 0012 貼體 O-Grid (81 x 25, 外半徑 0.6)
3. 執行 AdvancedHoleCutter.cut_by_curvilinear_body 進行多邊形射線孔洞切割
4. 斷言背景網格成功挖出 HOLE 節點並在外圍標定 RECEIVER 接收層
5. 輸出視覺化圖表 task1_airfoil_ogrid.png 並同步至 generated/
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
from grids.curvilinear_grid import CurvilinearOGrid
from geometry.hole_cutter import AdvancedHoleCutter


def test_task1_airfoil_ogrid():
    print("==========================================================")
    print(" 🚀 [任務一] NACA 0012 貼體 O 型網格生成與孔洞切割驗證...   ")
    print("==========================================================")

    # 1. 建立背景直角笛卡爾網格
    bg_grid = StructuredCartesianGrid(
        grid_id="background_grid",
        bounds=(-1.5, 1.5, -1.0, 1.0),
        shape=(121, 81),
        priority=1
    )
    X_bg, Y_bg = bg_grid.get_coordinates()
    print(f"1. 背景笛卡爾網格初始化完成: 形狀 {bg_grid.get_shape()}, 邊界 {bg_grid.get_bounding_box()}")

    # 2. 建立帶有 12 度攻角 (AoA = 12 deg) 的 NACA 0012 貼體 O 型網格
    aoa_deg = 12.0
    aoa_rad = np.radians(aoa_deg)
    curv_grid = CurvilinearOGrid(
        grid_id="naca0012_ogrid",
        n_circumferential=81,
        n_radial=25,
        outer_radius=0.6,
        origin=(0.0, 0.0),
        angle_rad=aoa_rad,
        priority=10
    )
    X_curv, Y_curv = curv_grid.get_coordinates()
    print(f"2. 貼體 O-Grid 初始化完成: 形狀 {curv_grid.get_shape()}, 攻角 {aoa_deg} 度")
    print(f"   幾何度量 Jacobian J 均值: {np.mean(curv_grid.J):.4e}")

    # 3. 執行基於翼型實體輪廓的幾何孔洞切割與邊界層標定
    AdvancedHoleCutter.cut_by_curvilinear_body(bg_grid, curv_grid, fringe_layers=1)

    # 4. 統計狀態並進行嚴格斷言
    n_field = np.sum(bg_grid.status_mask == CellStatus.FIELD)
    n_holes = np.sum(bg_grid.status_mask == CellStatus.HOLE)
    n_recvs = np.sum(bg_grid.status_mask == CellStatus.RECEIVER)
    n_curv_recvs = np.sum(curv_grid.status_mask == CellStatus.RECEIVER)

    print(f"3. 背景網格切割統計:")
    print(f"   - FIELD (計算節點):   {n_field} 個")
    print(f"   - HOLE (被挖除節點):  {n_holes} 個")
    print(f"   - RECEIVER (接收節點): {n_recvs} 個")
    print(f"   貼體 O-Grid 外層接收節點: {n_curv_recvs} 個")

    assert n_holes > 0, f"錯誤: 孔洞節點數必須大於 0, 當前為 {n_holes}"
    assert n_recvs > 0, f"錯誤: 背景接收節點數必須大於 0, 當前為 {n_recvs}"
    assert n_curv_recvs > 0, f"錯誤: 貼體網格外圍接收節點數必須大於 0"
    print("  ✓ 幾何拓撲標記與孔洞切割斷言全部通過！")

    # 5. 繪製精緻的重疊網格拓撲與孔洞邊界視覺化圖
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.5))

    # ---- 子圖 1: 全域重疊網格拓撲 ----
    # 繪製背景 FIELD 節點
    mask_field = (bg_grid.status_mask == CellStatus.FIELD)
    ax1.scatter(X_bg[mask_field], Y_bg[mask_field], s=6, c="#c5cdd9", alpha=0.6, label="BG: Field")

    # 繪製背景 HOLE 節點
    mask_hole = (bg_grid.status_mask == CellStatus.HOLE)
    ax1.scatter(X_bg[mask_hole], Y_bg[mask_hole], s=14, c="#1e1e24", marker="x", label="BG: Hole (Excavated)")

    # 繪製背景 RECEIVER 節點
    mask_recv = (bg_grid.status_mask == CellStatus.RECEIVER)
    ax1.scatter(X_bg[mask_recv], Y_bg[mask_recv], s=25, c="#e63946", marker="s", edgecolors="black", linewidths=0.5, label="BG: Receiver Fringe")

    # 繪製 O-Grid 網格線
    for j in range(0, curv_grid.n_eta, 2):
        ax1.plot(X_curv[:, j], Y_curv[:, j], color="#3a86ff", linewidth=0.5, alpha=0.5)
    for i in range(0, curv_grid.n_xi, 4):
        ax1.plot(X_curv[i, :], Y_curv[i, :], color="#3a86ff", linewidth=0.5, alpha=0.5)

    # 繪製 O-Grid 最外層 RECEIVER
    mask_curv_recv = (curv_grid.status_mask == CellStatus.RECEIVER)
    ax1.scatter(X_curv[mask_curv_recv], Y_curv[mask_curv_recv], s=20, c="#fb8500", marker="^", edgecolors="black", linewidths=0.5, label="O-Grid: Outer Receiver")

    # 繪製翼型表面實體輪廓 (世界座標)
    x_wall_w, y_wall_w = curv_grid.transform.local_to_world(curv_grid.x_inner, curv_grid.y_inner)
    ax1.plot(x_wall_w, y_wall_w, color="#800000", linewidth=2.2, label=f"NACA 0012 Wall (AoA={aoa_deg}°)")

    ax1.set_title("(a) Overset Mesh Assembly: Background + Body-Fitted O-Grid", fontsize=11, fontweight="bold")
    ax1.set_xlabel("X")
    ax1.set_ylabel("Y")
    ax1.set_xlim(-1.5, 1.5)
    ax1.set_ylim(-1.0, 1.0)
    ax1.set_aspect("equal")
    ax1.grid(True, linestyle=":", alpha=0.4)
    ax1.legend(loc="upper right", fontsize=8.5, framealpha=0.9)

    # ---- 子圖 2: 翼型近壁區孔洞切割與 Fringe 接收層特寫 ----
    ax2.scatter(X_bg[mask_field], Y_bg[mask_field], s=12, c="#d3d3d3", alpha=0.7)
    ax2.scatter(X_bg[mask_hole], Y_bg[mask_hole], s=32, c="#1e1e24", marker="x", label=f"Hole Nodes ({n_holes})")
    ax2.scatter(X_bg[mask_recv], Y_bg[mask_recv], s=45, c="#e63946", marker="s", edgecolors="black", linewidths=0.6, label=f"Fringe Receivers ({n_recvs})")

    # O-Grid 網格線 (局部特寫)
    for j in range(0, curv_grid.n_eta, 1):
        ax2.plot(X_curv[:, j], Y_curv[:, j], color="#3a86ff", linewidth=0.6, alpha=0.6)
    for i in range(0, curv_grid.n_xi, 2):
        ax2.plot(X_curv[i, :], Y_curv[i, :], color="#3a86ff", linewidth=0.6, alpha=0.6)

    ax2.scatter(X_curv[mask_curv_recv], Y_curv[mask_curv_recv], s=35, c="#fb8500", marker="^", edgecolors="black", linewidths=0.6, label="O-Grid Outer Fringe")
    ax2.plot(x_wall_w, y_wall_w, color="#800000", linewidth=2.5, label="Airfoil Body Wall")

    ax2.set_title(f"(b) Zoom-in: Polygon Ray-Casting Hole Cut & Fringe Layer", fontsize=11, fontweight="bold")
    ax2.set_xlabel("X")
    ax2.set_ylabel("Y")
    ax2.set_xlim(-0.6, 0.9)
    ax2.set_ylim(-0.5, 0.5)
    ax2.set_aspect("equal")
    ax2.grid(True, linestyle=":", alpha=0.5)
    ax2.legend(loc="upper right", fontsize=8.5, framealpha=0.9)

    plt.suptitle("PHANTOM Grid - Task 1: Body-Fitted O-Grid & Polygon Hole Cutting Verification",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()

    out_file = Path("task1_airfoil_ogrid.png")
    plt.savefig(out_file, dpi=200)
    plt.close()

    # 遵守零桌面污染原則，備份至 generated/
    gen_dir = Path("generated")
    gen_dir.mkdir(exist_ok=True)
    shutil.copy(out_file, gen_dir / out_file.name)

    print(f"4. 驗證圖檔已輸出至: {out_file.resolve()}")
    print(f"   同步備份至: {(gen_dir / out_file.name).resolve()}")
    print("==========================================================")
    print(" ✅ [任務一驗證成功: NACA 0012 貼體網格與孔洞切割全數通過]  ")
    print("==========================================================")


if __name__ == "__main__":
    test_task1_airfoil_ogrid()
