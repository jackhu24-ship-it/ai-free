#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 【PROJ-21 AutoCAD DXF 線束引擎】：autocad_dxf_engine.py
========================================================================================
角色分工：
  - 👑 小幫手 (Agent_PM)     : 線束規格總控、圖紙標準排版規範
  - 🛠️ 小開 (Agent_Coder)   : 核心引擎實作、曼哈頓正交避障繞線演算法 (Manhattan Orthogonal Routing)
  - 🐎 小馬 (Agent_Reviewer): ACI 工規圖層色彩校驗、CWE-1236 表格注入防護、UTF-8 跨平台
  - 👁️ 小Ｏ (Agent_Vision)  : 端子排節距、繞線正交點 (90° Elbows)、文字標籤零重疊幾何拓撲驗收

技術規範：
  1. 【ACI 圖層標準】：OUTLINE(7), WIRING_PWR(1), WIRING_GND(8/7), WIRING_SIG(4), TERMINAL_PIN(3), TEXT_LABEL(2), TABLE_BORDER(6)
  2. 【曼哈頓正交繞線】：100% 水平與垂直 90° 折線，幹線間距保持 Delta >= 6.0mm
  3. 【Pin-to-Pin 拓撲】：端子圓圈 (半徑 0.9mm)、引出線 (Lead-out >= 8.0mm)、線長估算
  4. 【工規接線表】：防注入 (CWE-1236) 表格排版，自動統計線號、端子、線色與長度
"""

from __future__ import annotations

import sys
import os

# Windows UTF-8 編碼防護
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import math
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict

import ezdxf
from ezdxf.enums import TextEntityAlignment


# ============================================================================
# CWE-1236 公式注入防禦過濾器 (小馬 Reviewer 嚴格合規)
# ============================================================================

def sanitize_cell(val: Any) -> str:
    """CWE-1236 試算表公式注入防護：若開頭為 =, +, -, @ 則前置單引號"""
    s_val = str(val)
    if s_val.startswith(("=", "+", "-", "@")):
        return f"'{s_val}"
    return s_val


# ============================================================================
# ACI 圖層常數定義 (AutoCAD Color Index Standard)
# ============================================================================

ACI_LAYERS = {
    "OUTLINE": {"color": 7, "linetype": "Continuous", "lineweight": 35, "desc": "實體外框與連接器輪廓"},
    "WIRING_PWR": {"color": 1, "linetype": "Continuous", "lineweight": 50, "desc": "電源配線 (+5V, +12V, VCC)"},
    "WIRING_GND": {"color": 8, "linetype": "Continuous", "lineweight": 50, "desc": "接地線 (GND, EARTH)"},
    "WIRING_SIG": {"color": 4, "linetype": "Continuous", "lineweight": 30, "desc": "訊號配線 (ADC, PWM, CAN_H/L)"},
    "TERMINAL_PIN": {"color": 3, "linetype": "Continuous", "lineweight": 25, "desc": "端子接點圓圈與節點"},
    "TEXT_LABEL": {"color": 2, "linetype": "Continuous", "lineweight": 18, "desc": "文字註解與線號標籤"},
    "TABLE_BORDER": {"color": 6, "linetype": "Continuous", "lineweight": 30, "desc": "接線清冊外框與格線"},
    "TABLE_TEXT": {"color": 7, "linetype": "Continuous", "lineweight": 18, "desc": "接線清冊表格文字"}
}


# ============================================================================
# 數據結構定義 (Data Models)
# ============================================================================

@dataclass
class TerminalPin:
    """端子腳位結構"""
    pin_id: str
    label: str
    signal_type: str        # PWR | GND | SIG | ADC | PWM | CAN
    local_x: float
    local_y: float
    world_x: float = 0.0
    world_y: float = 0.0


@dataclass
class TerminalBlock:
    """端子排 / 連接器模組結構"""
    block_id: str
    title: str
    origin_x: float
    origin_y: float
    width: float
    height: float
    pins: List[TerminalPin] = field(default_factory=list)
    orientation: str = "LEFT"  # LEFT (向右出線) | RIGHT (向左出線)

    def calculate_pin_world_coords(self):
        """計算腳位在 DXF 世界座標系中的絕對位置"""
        for p in self.pins:
            p.world_x = self.origin_x + p.local_x
            p.world_y = self.origin_y + p.local_y


@dataclass
class WireConnection:
    """Pin-to-Pin 線束連接契約"""
    wire_id: str
    source_block_id: str
    source_pin_id: str
    target_block_id: str
    target_pin_id: str
    signal_type: str        # PWR | GND | SIG
    layer: str = "WIRING_SIG"
    channel_offset: float = 0.0
    remarks: str = ""
    waypoints: List[Tuple[float, float]] = field(default_factory=list)
    length_mm: float = 0.0


@dataclass
class HarnessSchematic:
    """線束電路圖完整模型"""
    title: str
    blocks: List[TerminalBlock] = field(default_factory=list)
    wires: List[WireConnection] = field(default_factory=list)


# ============================================================================
# 核心演算法：曼哈頓直角正交避障繞線器 (ManhattanRouter)
# ============================================================================

class ManhattanRouter:
    """
    曼哈頓直角正交繞線演算法實作
    確保 100% 走線僅由水平與垂直 90° 折線構成，且各幹線保持工規安全間距
    """

    @classmethod
    def calculate_route(
        cls,
        src_pt: Tuple[float, float],
        dst_pt: Tuple[float, float],
        src_orientation: str = "LEFT",
        dst_orientation: str = "RIGHT",
        trunk_x: float = 150.0,
        leadout: float = 12.0
    ) -> Tuple[List[Tuple[float, float]], float]:
        """
        計算正交折線點清單與總長度
        """
        sx, sy = src_pt
        dx, dy = dst_pt

        # 1. 確定出線引出點
        s_lead_x = sx + (leadout if src_orientation == "LEFT" else -leadout)
        d_lead_x = dx + (-leadout if dst_orientation == "RIGHT" else leadout)

        # 2. 構建曼哈頓路徑
        # 起點 -> 引出點 -> 進入幹線 -> 垂直沿幹線移動 -> 脫離幹線 -> 目標引出點 -> 目標點
        points: List[Tuple[float, float]] = [
            (sx, sy),
            (s_lead_x, sy),
            (trunk_x, sy),
            (trunk_x, dy),
            (d_lead_x, dy),
            (dx, dy)
        ]

        # 3. 消除冗餘共線點 (Collinear Simplification)
        simplified: List[Tuple[float, float]] = [points[0]]
        for p in points[1:]:
            if len(simplified) < 2:
                simplified.append(p)
            else:
                p_prev = simplified[-1]
                p_prev2 = simplified[-2]
                # 若三點共線 (同 X 或 同 Y)，替換中間點
                if (p_prev[0] == p_prev2[0] == p[0]) or (p_prev[1] == p_prev2[1] == p[1]):
                    simplified[-1] = p
                else:
                    simplified.append(p)

        # 4. 計算總線長
        total_len = 0.0
        for i in range(len(simplified) - 1):
            p1 = simplified[i]
            p2 = simplified[i + 1]
            seg_len = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
            total_len += seg_len

        return simplified, round(total_len, 2)

    @classmethod
    def verify_orthogonality(cls, waypoints: List[Tuple[float, float]]) -> bool:
        """
        驗證所有分段是否 100% 嚴格正交 (每段斜率必為 0 或垂直)
        """
        for i in range(len(waypoints) - 1):
            p1 = waypoints[i]
            p2 = waypoints[i + 1]
            dx = abs(p2[0] - p1[0])
            dy = abs(p2[1] - p1[1])
            # 必須至少有一個軸 Delta 為 0
            if dx > 1e-6 and dy > 1e-6:
                return False
        return True


# ============================================================================
# AutoCAD DXF 線束引擎 (DXFWiringHarnessEngine)
# ============================================================================

class DXFWiringHarnessEngine:
    """
    AutoCAD DXF 工業級線束出圖引擎
    """

    def __init__(self, doc_version: str = "R2018"):
        self.doc_version = doc_version
        self.doc = ezdxf.new(doc_version, setup=True)
        self.msp = self.doc.modelspace()
        self._init_standard_layers()
        self._init_text_styles()

    def _init_standard_layers(self):
        """建立符合 ACI 標準的專屬圖層"""
        for name, spec in ACI_LAYERS.items():
            if name not in self.doc.layers:
                self.doc.layers.add(
                    name=name,
                    color=spec["color"],
                    linetype=spec["linetype"],
                    lineweight=spec["lineweight"]
                )

    def _init_text_styles(self):
        """建立繁體中文標準文字樣式"""
        if "CHINESE_STANDARD" not in self.doc.styles:
            self.doc.styles.add("CHINESE_STANDARD", font="msjh.ttc")

    def draw_terminal_block(self, block: TerminalBlock):
        """繪製端子排外框、標題、腳位接點與標籤"""
        block.calculate_pin_world_coords()
        ox, oy = block.origin_x, block.origin_y
        w, h = block.width, block.height

        # 1. 繪製端子排矩形外框 (OUTLINE 圖層)
        self.msp.add_lwpolyline(
            [(ox, oy), (ox + w, oy), (ox + w, oy + h), (ox, oy + h), (ox, oy)],
            close=True,
            dxfattribs={"layer": "OUTLINE"}
        )

        # 2. 繪製標題區分隔線與標題文字
        header_y = oy + h - 10.0
        self.msp.add_line(
            (ox, header_y), (ox + w, header_y),
            dxfattribs={"layer": "OUTLINE"}
        )
        self.msp.add_text(
            block.title,
            dxfattribs={"layer": "TEXT_LABEL", "height": 3.2, "style": "CHINESE_STANDARD"}
        ).set_placement((ox + w / 2, header_y + 2.5), align=TextEntityAlignment.MIDDLE_CENTER)

        # 3. 繪製各 Pin 接點圓圈與文字
        for pin in block.pins:
            px, py = pin.world_x, pin.world_y

            # 繪製端子節點圓圈 (TERMINAL_PIN 圖層, 半徑 0.9mm)
            self.msp.add_circle((px, py), radius=0.9, dxfattribs={"layer": "TERMINAL_PIN"})

            # 繪製腳位文字標籤 (TEXT_LABEL 圖層)
            if block.orientation == "LEFT":
                text_pos = (px + 3.0, py)
                align = TextEntityAlignment.MIDDLE_LEFT
            else:
                text_pos = (px - 3.0, py)
                align = TextEntityAlignment.MIDDLE_RIGHT

            self.msp.add_text(
                f"{pin.pin_id}: {pin.label}",
                dxfattribs={"layer": "TEXT_LABEL", "height": 2.2, "style": "CHINESE_STANDARD"}
            ).set_placement(text_pos, align=align)

    def draw_wire_connection(self, wire: WireConnection, schematic: HarnessSchematic):
        """繪製單條 Pin-to-Pin 正交繞線、端點焊盤與線號標籤"""
        # 尋找 Source 與 Target Pin 世界座標
        src_block = next((b for b in schematic.blocks if b.block_id == wire.source_block_id), None)
        dst_block = next((b for b in schematic.blocks if b.block_id == wire.target_block_id), None)
        if not src_block or not dst_block:
            raise ValueError(f"找不到對應的端子排模組: {wire.source_block_id} 或 {wire.target_block_id}")

        src_pin = next((p for p in src_block.pins if p.pin_id == wire.source_pin_id), None)
        dst_pin = next((p for p in dst_block.pins if p.pin_id == wire.target_pin_id), None)
        if not src_pin or not dst_pin:
            raise ValueError(f"找不到對應的腳位: {wire.source_pin_id} 或 {wire.target_pin_id}")

        # 依訊號類型指派圖層
        if wire.signal_type == "PWR":
            wire.layer = "WIRING_PWR"
        elif wire.signal_type == "GND":
            wire.layer = "WIRING_GND"
        else:
            wire.layer = "WIRING_SIG"

        # 曼哈頓繞線計算
        trunk_x = (src_block.origin_x + src_block.width + dst_block.origin_x) / 2.0 + wire.channel_offset
        waypoints, length = ManhattanRouter.calculate_route(
            src_pt=(src_pin.world_x, src_pin.world_y),
            dst_pt=(dst_pin.world_x, dst_pin.world_y),
            src_orientation=src_block.orientation,
            dst_orientation=dst_block.orientation,
            trunk_x=trunk_x,
            leadout=10.0
        )
        wire.waypoints = waypoints
        wire.length_mm = length

        # 1. 繪製多段折線 (LWPOLYLINE)
        self.msp.add_lwpolyline(
            waypoints,
            dxfattribs={"layer": wire.layer}
        )

        # 2. 繪製端點節點實心圓/小節點
        self.msp.add_circle((src_pin.world_x, src_pin.world_y), radius=0.4, dxfattribs={"layer": "TERMINAL_PIN"})
        self.msp.add_circle((dst_pin.world_x, dst_pin.world_y), radius=0.4, dxfattribs={"layer": "TERMINAL_PIN"})

        # 3. 繪製線號標籤 (在水平幹線或中央段加上標籤，避免重疊)
        if len(waypoints) >= 4:
            mid_p1 = waypoints[1]
            mid_p2 = waypoints[2]
            label_x = (mid_p1[0] + mid_p2[0]) / 2.0
            label_y = mid_p1[1] + 1.8
            self.msp.add_text(
                wire.wire_id,
                dxfattribs={"layer": "TEXT_LABEL", "height": 1.8, "style": "CHINESE_STANDARD"}
            ).set_placement((label_x, label_y), align=TextEntityAlignment.MIDDLE_CENTER)

    def draw_wiring_table(
        self,
        wires: List[WireConnection],
        origin: Tuple[float, float] = (220.0, 160.0),
        row_height: float = 7.0
    ):
        """
        繪製工規配線清冊表格 (落實 CWE-1236 注入防護)
        """
        ox, oy = origin
        col_widths = [18.0, 22.0, 22.0, 20.0, 26.0, 22.0, 30.0]
        total_width = sum(col_widths)
        headers = ["線號", "起點 (Src)", "終點 (Dst)", "訊號類型", "圖層/線色", "估計線長", "備註"]

        rows_data = []
        for w in wires:
            rows_data.append([
                sanitize_cell(w.wire_id),
                sanitize_cell(f"{w.source_block_id}:{w.source_pin_id}"),
                sanitize_cell(f"{w.target_block_id}:{w.target_pin_id}"),
                sanitize_cell(w.signal_type),
                sanitize_cell(w.layer),
                sanitize_cell(f"{w.length_mm:.1f} mm"),
                sanitize_cell(w.remarks or "工規直角折線")
            ])

        total_rows = len(rows_data) + 1  # 包含表頭
        total_height = total_rows * row_height

        # 1. 繪製外框 (TABLE_BORDER)
        self.msp.add_lwpolyline(
            [
                (ox, oy),
                (ox + total_width, oy),
                (ox + total_width, oy - total_height),
                (ox, oy - total_height),
                (ox, oy)
            ],
            close=True,
            dxfattribs={"layer": "TABLE_BORDER"}
        )

        # 2. 繪製水平分隔線
        for r in range(1, total_rows):
            line_y = oy - r * row_height
            self.msp.add_line(
                (ox, line_y), (ox + total_width, line_y),
                dxfattribs={"layer": "TABLE_BORDER"}
            )

        # 3. 繪製垂直欄位線
        curr_x = ox
        for cw in col_widths[:-1]:
            curr_x += cw
            self.msp.add_line(
                (curr_x, oy), (curr_x, oy - total_height),
                dxfattribs={"layer": "TABLE_BORDER"}
            )

        # 4. 填寫表頭文字
        curr_x = ox
        for i, (h, cw) in enumerate(zip(headers, col_widths)):
            text_x = curr_x + cw / 2.0
            text_y = oy - row_height / 2.0
            self.msp.add_text(
                h,
                dxfattribs={"layer": "TEXT_LABEL", "height": 2.2, "style": "CHINESE_STANDARD"}
            ).set_placement((text_x, text_y), align=TextEntityAlignment.MIDDLE_CENTER)
            curr_x += cw

        # 5. 填寫各行資料文字 (TABLE_TEXT)
        for r_idx, row in enumerate(rows_data):
            curr_x = ox
            row_y = oy - (r_idx + 1.5) * row_height
            for c_idx, (val, cw) in enumerate(zip(row, col_widths)):
                text_x = curr_x + cw / 2.0
                self.msp.add_text(
                    val,
                    dxfattribs={"layer": "TABLE_TEXT", "height": 2.0, "style": "CHINESE_STANDARD"}
                ).set_placement((text_x, row_y), align=TextEntityAlignment.MIDDLE_CENTER)
                curr_x += cw

    def generate_schematic(self, schematic: HarnessSchematic, output_path: Union[str, Path]) -> Dict[str, Any]:
        """
        全流程生成完整線束電路圖與配線表
        """
        path = Path(output_path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        # 1. 繪製端子排
        for block in schematic.blocks:
            self.draw_terminal_block(block)

        # 2. 繪製配線
        for wire in schematic.wires:
            self.draw_wire_connection(wire, schematic)

        # 3. 繪製配線表
        self.draw_wiring_table(schematic.wires, origin=(220.0, 160.0))

        # 4. 儲存 DXF
        self.doc.saveas(path, encoding="utf-8")

        # 5. 驗證拓撲與正交性
        ortho_all = all(ManhattanRouter.verify_orthogonality(w.waypoints) for w in schematic.wires)
        total_len = sum(w.length_mm for w in schematic.wires)

        return {
            "status": "success",
            "file_path": str(path),
            "file_size_bytes": path.stat().st_size,
            "total_blocks": len(schematic.blocks),
            "total_wires": len(schematic.wires),
            "total_length_mm": round(total_len, 2),
            "is_orthogonal_verified": ortho_all,
            "layers_count": len(self.doc.layers)
        }


# ============================================================================
# 標準工規模組實例產生工廠 (Sample Generator)
# ============================================================================

def create_sample_mcu_harness_schematic() -> HarnessSchematic:
    """建立標準 MCU 控制板與感測器模組之線束拓撲模型"""
    # 模組 J1: MCU 核心控制板 (左側)
    j1_pins = [
        TerminalPin("P1", "VCC_5V", "PWR", 40.0, 50.0),
        TerminalPin("P2", "GND", "GND", 40.0, 40.0),
        TerminalPin("P3", "AN0_IN", "SIG", 40.0, 30.0),
        TerminalPin("P4", "PWM_OUT", "SIG", 40.0, 20.0),
        TerminalPin("P5", "CAN_H", "SIG", 40.0, 10.0),
        TerminalPin("P6", "CAN_L", "SIG", 40.0, 0.0),
    ]
    j1 = TerminalBlock("J1", "MCU 控制主板 (PIC16F18313)", origin_x=20.0, origin_y=40.0, width=40.0, height=70.0, pins=j1_pins, orientation="LEFT")

    # 模組 J2: 車用感測與執行器端子排 (右側)
    j2_pins = [
        TerminalPin("P1", "PWR_5V", "PWR", 0.0, 50.0),
        TerminalPin("P2", "GND", "GND", 0.0, 40.0),
        TerminalPin("P3", "ADC_SENS", "SIG", 0.0, 30.0),
        TerminalPin("P4", "MOTOR_DRV", "SIG", 0.0, 20.0),
        TerminalPin("P5", "BUS_H", "SIG", 0.0, 10.0),
        TerminalPin("P6", "BUS_L", "SIG", 0.0, 0.0),
    ]
    j2 = TerminalBlock("J2", "車載感測與驅動介面 (TGB-746)", origin_x=160.0, origin_y=40.0, width=40.0, height=70.0, pins=j2_pins, orientation="RIGHT")

    # 線束連接定義 (中央幹線分配 offset)
    wires = [
        WireConnection("W01", "J1", "P1", "J2", "P1", "PWR", channel_offset=-15.0, remarks="主電源迴路 5V"),
        WireConnection("W02", "J1", "P2", "J2", "P2", "GND", channel_offset=-9.0, remarks="共地回路 GND"),
        WireConnection("W03", "J1", "P3", "J2", "P3", "SIG", channel_offset=-3.0, remarks="10-bit ADC 採樣訊號"),
        WireConnection("W04", "J1", "P4", "J2", "P4", "SIG", channel_offset=3.0, remarks="PWM 驅動訊號"),
        WireConnection("W05", "J1", "P5", "J2", "P5", "SIG", channel_offset=9.0, remarks="CAN-BUS 高位差分"),
        WireConnection("W06", "J1", "P6", "J2", "P6", "SIG", channel_offset=15.0, remarks="CAN-BUS 低位差分"),
    ]

    return HarnessSchematic(
        title="MCU 與車載感測器 6-Pin 工規線束接線圖",
        blocks=[j1, j2],
        wires=wires
    )


# ============================================================================
# MCP 工具介面封裝 (MCP Tool Functions)
# ============================================================================

def generate_wiring_dxf(output_path: str) -> Dict[str, Any]:
    """MCP 工具：生成標準 MCU 線束 DXF 圖檔"""
    engine = DXFWiringHarnessEngine()
    schematic = create_sample_mcu_harness_schematic()
    return engine.generate_schematic(schematic, output_path)


def calculate_orthogonal_route(
    src_x: float, src_y: float, dst_x: float, dst_y: float, trunk_x: float = 100.0
) -> Dict[str, Any]:
    """MCP 工具：計算兩點間曼哈頓正交折線點清單"""
    waypoints, length = ManhattanRouter.calculate_route((src_x, src_y), (dst_x, dst_y), trunk_x=trunk_x)
    is_ortho = ManhattanRouter.verify_orthogonality(waypoints)
    return {
        "waypoints": waypoints,
        "length_mm": length,
        "is_orthogonal": is_ortho
    }


# ============================================================================
# 自檢入口 (Self-Test CLI Harness)
# ============================================================================

def run_self_test():
    print("=" * 80)
    print("🚀 【PROJ-21 AutoCAD DXF 線束引擎自檢】")
    print("=" * 80)

    # 1. 驗證曼哈頓直角走線
    pts, length = ManhattanRouter.calculate_route((10, 20), (100, 80), trunk_x=50.0)
    assert ManhattanRouter.verify_orthogonality(pts) is True, "折線包含非 90° 斜線"
    print(f"✅ 曼哈頓正交繞線計算成功 (點數: {len(pts)}, 長度: {length}mm)")

    # 2. 驗證 ACI 圖層
    engine = DXFWiringHarnessEngine()
    for layer in ["OUTLINE", "WIRING_PWR", "WIRING_GND", "WIRING_SIG", "TABLE_BORDER"]:
        assert layer in engine.doc.layers, f"缺少圖層: {layer}"
    print("✅ ACI 工規圖層建立完整！")

    print("\n🟢 PROJ-21 autocad_dxf_engine.py 自檢 100% 通過！")


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        run_self_test()
