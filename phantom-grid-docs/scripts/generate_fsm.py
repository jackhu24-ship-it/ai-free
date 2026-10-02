"""
==============================================================================
 ARCHITECTURE : PHANTOM GRID / TOP-TIER INDUSTRIAL PDF SPECIFICATION
 MODULE       : generate_fsm.py
 SIGNED BY    : Commander Jack (👑 霸丸總指揮官權威落款)
 SEAL TIME    : 2026-10-02 13:47:24 CST
 STATUS       : OFFICIALLY RELEASED & SEALED
 INTEGRITY    : SHA256:f0f6a7a28ff8f80f... [VERIFIED]
 SPEC STANDARD: PG-SPEC-2026-PDF-WORLD-CLASS
==============================================================================
"""

import os
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# 強制 UTF-8 輸出
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = BASE_DIR / "assets" / "images" / "safety_fsm.svg"

def draw_fsm():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # 設置高清晰向量畫布
    fig = plt.figure(figsize=(7.6, 2.6), dpi=300)
    ax = fig.add_subplot(111)
    ax.set_axis_off()

    # 狀態定義 (名稱, X 座標, 框線顏色, 底色)
    states = [
        ("POWER_ON\nINIT", 0.12, "#64748B", "#F8FAFC"),
        ("NORMAL_RUN\n(ASIL-D Active)", 0.42, "#0066FF", "#EFF6FF"),
        ("DEGRADED_LIMP\n(Safe State)", 0.72, "#D97706", "#FFFBEB"),
        ("EMERGENCY_STOP\n(Power Cut)", 0.94, "#DC2626", "#FEF2F2"),
    ]

    # 繪製圓角狀態框
    for name, x, border, bg in states:
        box = patches.FancyBboxPatch(
            (x - 0.08, 0.35), 0.16, 0.4,
            boxstyle="round,pad=0.03,rounding_size=0.04",
            linewidth=1.2, edgecolor=border, facecolor=bg
        )
        ax.add_patch(box)
        ax.text(x, 0.55, name, ha="center", va="center", fontsize=7.5, fontweight="bold", color="#0F172A", fontfamily="sans-serif")

    # 繪製跳轉箭頭與轉換條件
    transitions = [
        (0.20, 0.34, 0.65, "BIST Passed (CRC Ok)", "#0066FF"),
        (0.50, 0.64, 0.65, "DTC Severity >= 3", "#D97706"),
        (0.80, 0.86, 0.65, "Heartbeat Timeout", "#DC2626")
    ]

    for x1, x2, y, label, color in transitions:
        ax.annotate(
            "", xy=(x2, y), xytext=(x1, y),
            arrowprops=dict(arrowstyle="->", color=color, lw=1.4)
        )
        ax.text((x1 + x2) / 2, y + 0.12, label, ha="center", va="bottom", fontsize=6.5, color="#475569", fontfamily="sans-serif")

    # 座標限制
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0.1, 0.9)

    plt.tight_layout()
    plt.savefig(str(OUTPUT_FILE), format="svg", bbox_inches="tight")
    plt.close()
    print(f"✅ [FSM Generator] 安全狀態機向量圖已生成: {OUTPUT_FILE} ({OUTPUT_FILE.stat().st_size} bytes)")

if __name__ == "__main__":
    draw_fsm()
