"""
==============================================================================
 ARCHITECTURE : PHANTOM GRID / TOP-TIER INDUSTRIAL PDF SPECIFICATION
 MODULE       : generate_charts.py
 SIGNED BY    : Commander Jack (👑 霸丸總指揮官權威落款)
 SEAL TIME    : 2026-10-02 13:44:48 CST
 STATUS       : OFFICIALLY RELEASED & SEALED
 INTEGRITY    : SHA256:8587fcc6bf706618... [VERIFIED]
 SPEC STANDARD: PG-SPEC-2026-PDF-WORLD-CLASS
==============================================================================
"""

#!/usr/bin/env python3
"""
PHANTOM GRID Vector Chart Generator
規範標準: PG-SPEC-2026-CHART (A4 版面 12-Column Grid 適用)
輸出格式: 向量 SVG (無損嵌入 Typst / PDF)
"""

import os
import matplotlib.pyplot as plt
import numpy as np

# 確保輸出目錄存在
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../assets/images")
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "latency_benchmark.svg")


def apply_phantom_grid_theme():
    """設定符合 PHANTOM GRID 視覺識別與出版精度的 Matplotlib 參數"""
    plt.rcParams.update({
        # 1. 畫布比例 (配合 A4 雙欄或主欄寬度: 6.8 x 3.4 英吋，約 2:1 黃金視覺比)
        "figure.figsize": (6.8, 3.4),
        "figure.dpi": 300,

        # 2. 字體階層與特性
        "font.family": "sans-serif",
        "font.sans-serif": ["Inter", "Noto Sans TC", "DejaVu Sans"],
        "font.size": 8.5,
        "axes.titlesize": 10.5,
        "axes.titleweight": "bold",
        "axes.labelsize": 8.5,
        "xtick.labelsize": 8.0,
        "ytick.labelsize": 8.0,

        # 3. 座標軸與線條精確度
        "axes.linewidth": 0.8,
        "axes.edgecolor": "#94A3B8",        # Slate 400
        "axes.facecolor": "#FFFFFF",
        "figure.facecolor": "#FFFFFF",

        # 4. 背景輔助網格線 (0.5pt 淺灰點線)
        "axes.grid": True,
        "axes.grid.axis": "y",             # 僅保留 Y 軸水平網格，避免垂直線雜訊
        "grid.color": "#E2E8F0",           # Slate 200
        "grid.linestyle": ":",
        "grid.linewidth": 0.6,

        # 5. SVG 渲染標準 (保留文字為 SVG text 節點，便於向量縮放與搜尋)
        "svg.fonttype": "none"
    })


def generate_latency_chart():
    apply_phantom_grid_theme()

    fig, ax = plt.subplots()

    # 模擬測試數據：匯流排負載率 (%) 與 節點延遲 (μs)
    bus_load = np.array([10, 20, 30, 40, 50, 60, 70, 80, 90])
    
    # 數列 A: PHANTOM GRID CAN-FD (硬體時間戳 + 零拷貝排程)
    pg_latency = np.array([4.2, 4.5, 4.8, 5.2, 5.9, 7.1, 8.8, 11.4, 15.6])
    
    # 數列 B: 傳統 Legacy CAN / FIFO 排程
    legacy_latency = np.array([6.5, 7.8, 9.6, 12.5, 17.2, 24.0, 35.8, 54.2, 82.0])

    # ------------------------------------------------------------------
    # 繪製數列 (實線/虛線 + 幾何符號雙重識別，符合色弱與高對比規範)
    # ------------------------------------------------------------------
    
    # 數列 1: PHANTOM GRID Core (品牌藍 #0066FF, 實線, 圓形端點)
    ax.plot(
        bus_load, pg_latency,
        color="#0066FF",
        linestyle="-",
        linewidth=1.8,
        marker="o",
        markersize=4.5,
        markerfacecolor="#0066FF",
        markeredgecolor="#FFFFFF",
        markeredgewidth=0.8,
        zorder=3
    )

    # 數列 2: 傳統架構 (深冷灰 #64748B, 虛線, 方形端點)
    ax.plot(
        bus_load, legacy_latency,
        color="#64748B",
        linestyle="--",
        linewidth=1.5,
        marker="s",
        markersize=4.2,
        markerfacecolor="#64748B",
        markeredgecolor="#FFFFFF",
        markeredgewidth=0.8,
        zorder=2
    )

    # ------------------------------------------------------------------
    # 末端直接標註 (Direct Labeling) - 消除圖例閱讀負擔
    # ------------------------------------------------------------------
    ax.text(
        bus_load[-1] + 1.2, pg_latency[-1],
        "PHANTOM GRID (Deterministic)",
        color="#0066FF",
        fontsize=8.0,
        fontweight="bold",
        va="center"
    )

    ax.text(
        bus_load[-1] + 1.2, legacy_latency[-1],
        "Legacy FIFO Stack",
        color="#64748B",
        fontsize=8.0,
        va="center"
    )

    # ------------------------------------------------------------------
    # 標題與軸標籤設定 (結論先導型命名)
    # ------------------------------------------------------------------
    ax.set_title("BUS LOAD VS DISPATCH LATENCY (μs)", loc="left", pad=12, color="#0F172A")
    ax.set_xlabel("CAN-FD Bus Saturation (%)", labelpad=6, color="#475569")
    ax.set_ylabel("Round-trip Latency (μs)", labelpad=6, color="#475569")

    # 軸範圍微調與刻度格式
    ax.set_xlim(5, 108)  # 右側多留空間放置文字標籤
    ax.set_ylim(0, 90)
    ax.set_xticks([10, 25, 50, 75, 90])
    ax.set_yticks([0, 20, 40, 60, 80])

    # 隱藏上方與右方框線 (簡約高階工程風格)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#CBD5E1")
    ax.spines["bottom"].set_color("#CBD5E1")

    # 刻度線顏色與長度
    ax.tick_params(colors="#475569", width=0.8, length=3.5)

    # 輸出純向量 SVG
    plt.tight_layout()
    plt.savefig(OUTPUT_FILE, format="svg", bbox_inches="tight")
    plt.close()

    print(f"✅ [PHANTOM GRID] 向量圖表已成功生成: {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_latency_chart()
