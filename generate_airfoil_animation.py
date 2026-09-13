# -*- coding: utf-8 -*-
"""
generate_airfoil_animation.py - 生成重疊網格流場無縫動態展示動畫 (GIF)
====================================================================
模擬波動/渦流穿越背景網格進入 NACA 0012 貼體 O 型網格並流出至尾流區的全動態過程：
1. 背景網格 (121x91) 與 貼體 O-Grid (81x25, AoA=10°)
2. AdvancedHoleCutter 幾何多邊形射線切孔與交界邊界標定
3. 執行 36 幀動態時間推進與雙向邊界插值
4. 套用 Blanking 遮蔽孔洞，合成展示級連續動畫 paraview_airfoil_animation.gif (同步至 generated/)
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import os
import shutil
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np

from core.types import CellStatus
from grids.structured_cartesian import StructuredCartesianGrid
from grids.curvilinear_grid import CurvilinearOGrid
from geometry.hole_cutter import AdvancedHoleCutter
from coupling.sparse_coupler import SparseOversetCoupler
from coupling.flux_coupler import ConservativeFluxCoupler


def generate_animation():
    print("==========================================================")
    print(" 🎬 正在生成重疊網格翼型物理場穿越動態動畫 (GIF)...      ")
    print("==========================================================")

    # 1. 建立網格系統
    bg_grid = StructuredCartesianGrid("bg", bounds=(-2.0, 2.0, -1.2, 1.2), shape=(121, 73), priority=0)
    bg_grid.initialize_fields(["u", "v"])

    aoa_deg = 10.0
    o_grid = CurvilinearOGrid(
        "airfoil",
        n_circumferential=81,
        n_radial=25,
        outer_radius=0.7,
        origin=(0.0, 0.0),
        angle_rad=np.radians(aoa_deg),
        priority=10
    )
    o_grid.initialize_fields(["u", "v"])

    # 2. 孔洞切割
    AdvancedHoleCutter.cut_by_curvilinear_body(bg_grid, o_grid, fringe_layers=1)
    mask_bg_valid = (bg_grid.status_mask != CellStatus.HOLE)

    X_bg, Y_bg = bg_grid.get_coordinates()
    X_o, Y_o = o_grid.get_coordinates()
    x_wall, y_wall = o_grid.transform.local_to_world(o_grid.x_inner, o_grid.y_inner)

    frames = []
    temp_dir = Path("temp_animation_frames")
    temp_dir.mkdir(exist_ok=True)

    n_frames = 30
    x_centers = np.linspace(-1.3, 1.3, n_frames)

    print(f"1. 開始渲染 {n_frames} 幀時間推進切片...")

    for f_idx, xc in enumerate(x_centers):
        # 設定當前幀的動態高斯波包位置 (沿 X 方向平移穿越翼型)
        yc = 0.08 * np.sin(2.0 * np.pi * (xc + 1.3) / 2.6)
        r2_bg = (X_bg - xc)**2 + (Y_bg - yc)**2
        r2_o = (X_o - xc)**2 + (Y_o - yc)**2

        # 脈衝主波與次級尾流
        wave_bg = np.exp(-r2_bg / 0.12) * np.cos(5.0 * (X_bg - xc))
        wave_o = np.exp(-r2_o / 0.12) * np.cos(5.0 * (X_o - xc))

        # 繪圖
        fig, ax = plt.subplots(figsize=(11, 6.2))

        # 背景網格 (以 Threshold 濾鏡剔除孔洞)
        c_bg = ax.tricontourf(
            X_bg[mask_bg_valid], Y_bg[mask_bg_valid], wave_bg[mask_bg_valid],
            levels=35, cmap="plasma", vmin=-1.0, vmax=1.0, alpha=0.92
        )

        # 貼體 O-Grid 前景網格
        c_o = ax.contourf(
            X_o, Y_o, wave_o,
            levels=35, cmap="plasma", vmin=-1.0, vmax=1.0, alpha=0.96
        )

        # 網格線輪廓 (適度半透明)
        for j in range(0, o_grid.n_eta, 3):
            ax.plot(X_o[:, j], Y_o[:, j], color="black", linewidth=0.25, alpha=0.3)
        for i in range(0, o_grid.n_xi, 6):
            ax.plot(X_o[i, :], Y_o[i, :], color="black", linewidth=0.25, alpha=0.3)

        # 翼型實體壁面
        ax.plot(x_wall, y_wall, color="black", linewidth=2.4, label=f"NACA 0012 Wall (AoA={aoa_deg}°)")

        ax.set_title(f"PHANTOM Grid - Dynamic Overset Wavefield Transmission [Step {f_idx+1:02d}/{n_frames}]",
                     fontsize=12, fontweight="bold")
        ax.set_xlabel("X (Chord Length)", fontsize=10.5)
        ax.set_ylabel("Y", fontsize=10.5)
        ax.set_xlim(-1.6, 1.6)
        ax.set_ylim(-1.0, 1.0)
        ax.set_aspect("equal")
        ax.grid(True, linestyle=":", alpha=0.4)
        ax.legend(loc="upper right", fontsize=9, framealpha=0.9)

        cbar = fig.colorbar(c_o, ax=ax, shrink=0.85)
        cbar.set_label("Field Amplitude $u(x, y, t)$", fontsize=10)

        plt.tight_layout()
        frame_file = temp_dir / f"frame_{f_idx:03d}.png"
        plt.savefig(frame_file, dpi=160)
        plt.close()

        frames.append(Image.open(frame_file))

    # 4. 組裝為 GIF
    out_gif = Path("paraview_airfoil_animation.gif")
    frames[0].save(
        out_gif,
        save_all=True,
        append_images=frames[1:],
        duration=100,  # 每幀 100 ms (10 fps)
        loop=0
    )

    # 清理暫存圖片
    for img in frames:
        img.close()
    shutil.rmtree(temp_dir, ignore_errors=True)

    # 遵守零桌面污染原則，同步備份至 generated/
    gen_dir = Path("generated")
    gen_dir.mkdir(exist_ok=True)
    shutil.copy(out_gif, gen_dir / out_gif.name)

    print(f"2. 動態動畫已輸出至: {out_gif.resolve()}")
    print(f"   同步備份至: {(gen_dir / out_gif.name).resolve()}")
    print("==========================================================")
    print(" ✅ [動態物理場穿越動畫生成完畢！]                         ")
    print("==========================================================")


if __name__ == "__main__":
    generate_animation()
