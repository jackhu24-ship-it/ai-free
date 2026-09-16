#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cad_smart_pdu_dxf_generator.py (v2.0 Pinout Extended Edition)
-------------------------------------------------------------------------
模組功能：
1. 繪製 AutoCAD A3 標準圖框 (420 x 297 mm) 與工程標題欄。
2. 繪製 8 通道 Smart PDU 三段式電力拓撲圖（KL30/KL15 -> 智慧核心 -> 負載端）。
3. [全新擴充] 自動生成各通道車規防水接插件端子排列 (Pinout) 視圖：
   - 支援 2-Pin、4-Pin、8-Pin、12-Pin (如 Deutsch DT, TE MCP, Amphenol AT)
   - 繪製外殼輪廓 (Housing)、防呆鍵 (Keying Notch)、密封膠圈 (Gasket)
   - 標記 Pin 編號 (1..N)、對應通道 (CH1..CH8)、額定載流、線徑與國際車規線色
4. 生成底部 Pin-to-Pin 配線 BOM 表。
-------------------------------------------------------------------------
"""

import math
import os
import sys
from typing import Dict, List, Any

# Windows UTF-8 編碼防護
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


class SmartPDUDXFGenerator:
    """智慧配電盒 AutoCAD DXF (R12 相容 ASCII 格式) 向量圖形產生器"""

    def __init__(self, filename: str = "smart_pdu_wiring_with_pinouts.dxf"):
        self.filename = filename
        self.entities: List[str] = []
        self.layers = {
            "0": 7,              # 預設白色
            "BORDER": 7,         # 白色 (A3 外框)
            "TITLE_BLOCK": 4,     # 青色 (標題欄)
            "POWER_KL30": 1,     # 紅色 (KL30 常電)
            "POWER_KL15": 2,     # 黃色 (KL15 ACC/IGN 電源)
            "GND_KL31": 0,       # 黑色/白底 (KL31 搭鐵接地)
            "LOGIC_CORE": 3,     # 綠色 (MCU & E-Fuse 核心)
            "LOAD_MODULES": 4,   # 青色 (8 大負載模組)
            "SIGNAL_LINE": 6,    # 洋紅 (CAN/LIN 訊號)
            "TEXT_DIM": 7,       # 白色 (文字與工程尺寸標註)
            "CON_HOUSING": 5,    # 藍色 (接插件外殼與結構線)
            "CON_PINS": 2,       # 黃色 (接插件端子金屬接觸面)
        }



    # ==========================================
    # DXF 基礎圖元繪製函式
    # ==========================================

    def add_line(self, x1: float, y1: float, x2: float, y2: float, layer: str = "0"):
        self.entities.append(
            f"0\nLINE\n8\n{layer}\n10\n{x1:.3f}\n20\n{y1:.3f}\n30\n0.0\n11\n{x2:.3f}\n21\n{y2:.3f}\n31\n0.0\n"
        )

    def add_rect(self, x: float, y: float, w: float, h: float, layer: str = "0"):
        self.add_line(x, y, x + w, y, layer)
        self.add_line(x + w, y, x + w, y + h, layer)
        self.add_line(x + w, y + h, x, y + h, layer)
        self.add_line(x, y + h, x, y, layer)

    def add_circle(self, cx: float, cy: float, r: float, layer: str = "0"):
        self.entities.append(
            f"0\nCIRCLE\n8\n{layer}\n10\n{cx:.3f}\n20\n{cy:.3f}\n30\n0.0\n40\n{r:.3f}\n"
        )

    def add_arc(self, cx: float, cy: float, r: float, start_deg: float, end_deg: float, layer: str = "0"):
        self.entities.append(
            f"0\nARC\n8\n{layer}\n10\n{cx:.3f}\n20\n{cy:.3f}\n30\n0.0\n40\n{r:.3f}\n50\n{start_deg:.1f}\n51\n{end_deg:.1f}\n"
        )

    def add_text(self, text: str, x: float, y: float, height: float = 2.5, layer: str = "TEXT_DIM", align: str = "LEFT"):
        """繪製文字 (支援 LEFT, CENTER, RIGHT 對齊)"""
        # CWE-1236 防禦：清理控制字元
        clean_text = str(text).replace("\n", " ").replace("\r", "")
        
        align_code = 0
        h_flag = 0
        if align == "CENTER":
            align_code = 1
            h_flag = 1
        elif align == "RIGHT":
            align_code = 2
            h_flag = 2

        if align_code == 0:
            self.entities.append(
                f"0\nTEXT\n8\n{layer}\n10\n{x:.3f}\n20\n{y:.3f}\n30\n0.0\n40\n{height:.3f}\n1\n{clean_text}\n"
            )
        else:
            self.entities.append(
                f"0\nTEXT\n8\n{layer}\n10\n{x:.3f}\n20\n{y:.3f}\n30\n0.0\n40\n{height:.3f}\n1\n{clean_text}\n"
                f"72\n{h_flag}\n11\n{x:.3f}\n21\n{y:.3f}\n31\n0.0\n"
            )

    # ==========================================
    # 專屬：防水接插件 Pinout 視圖繪製引擎
    # ==========================================

    def draw_waterproof_connector_pinout(
        self,
        center_x: float,
        center_y: float,
        connector_id: str,
        connector_model: str,
        pin_defs: List[Dict[str, Any]],
        cols: int = 4,
        rows: int = 2,
        pin_pitch: float = 8.0,
    ):
        """
        繪製單個車規防水接頭的 Pinout 排布圖：
        - 外殼 Housing 與圓角倒角
        - 頂部防呆定位鍵槽 (Keying Notch)
        - 雙圈防水矽膠密封墊圈 (Sealing Lip)
        - 金屬端子插孔 (含實體圓形與中心十字標記)
        - 端子編號、線色與通道映射
        """
        margin_x = 10.0
        margin_y = 9.0
        housing_w = (cols - 1) * pin_pitch + 2 * margin_x
        housing_h = (rows - 1) * pin_pitch + 2 * margin_y

        left = center_x - housing_w / 2.0
        bottom = center_y - housing_h / 2.0

        # 1. 繪製外殼外框 (CON_HOUSING 圖層)
        self.add_rect(left, bottom, housing_w, housing_h, layer="CON_HOUSING")

        # 2. 繪製頂部防呆卡扣 (Keying Notch: 寬 8mm, 高 3mm)
        notch_w = 8.0
        notch_h = 2.5
        notch_left = center_x - notch_w / 2.0
        notch_top = bottom + housing_h
        self.add_rect(notch_left, notch_top, notch_w, notch_h, layer="CON_HOUSING")

        # 3. 繪製防水密封膠條輪廓 (雙層圓角同心方框)
        gasket_offset = 1.5
        self.add_rect(
            left + gasket_offset,
            bottom + gasket_offset,
            housing_w - 2 * gasket_offset,
            housing_h - 2 * gasket_offset,
            layer="CON_HOUSING",
        )

        # 4. 接頭標題 (如 "J2: 8-Pin Deutsch DT06-8S (IP67)")
        header_text = f"[{connector_id}] {connector_model}"
        self.add_text(
            header_text,
            center_x,
            bottom + housing_h + notch_h + 3.0,
            height=2.2,
            layer="TEXT_DIM",
            align="CENTER",
        )

        # 5. 排列並繪製 Pin 端子
        # 計算 Pin (1,1) 的左上起點 (車規視圖常以左上角為 Pin 1)
        start_pin_x = center_x - ((cols - 1) * pin_pitch) / 2.0
        start_pin_y = center_y + ((rows - 1) * pin_pitch) / 2.0

        pin_radius = 2.0

        for idx, pdef in enumerate(pin_defs):
            row_idx = idx // cols
            col_idx = idx % cols
            if row_idx >= rows:
                break

            px = start_pin_x + col_idx * pin_pitch
            py = start_pin_y - row_idx * pin_pitch

            pin_num = pdef.get("pin", idx + 1)
            ch_name = pdef.get("ch", f"P{pin_num}")
            wire_color = pdef.get("color", "BLK")
            wire_size = pdef.get("size", "1.0")

            # 繪製端子孔圓 (CON_PINS)
            self.add_circle(px, py, pin_radius, layer="CON_PINS")
            # 繪製中心十字微標
            cross_r = 0.8
            self.add_line(px - cross_r, py, px + cross_r, py, layer="CON_PINS")
            self.add_line(px, py - cross_r, px, py + cross_r, layer="CON_PINS")

            # 標註 Pin 編號 (置中在圓心上方)
            self.add_text(f"#{pin_num}", px, py + pin_radius + 0.6, height=1.4, layer="TEXT_DIM", align="CENTER")

            # 標註通道與線色 (置中在圓心下方)
            self.add_text(f"{ch_name}", px, py - pin_radius - 1.8, height=1.3, layer="TEXT_DIM", align="CENTER")
            self.add_text(f"{wire_color} {wire_size}mm²", px, py - pin_radius - 3.2, height=1.1, layer="TEXT_DIM", align="CENTER")

    # ==========================================
    # A3 綜合圖面組裝
    # ==========================================

    def build_complete_diagram(self, channels_data: List[Dict[str, Any]]):
        """組裝整張 A3 智慧配電盒拓撲與 Pinout 接線圖"""
        # 1. A3 圖框 (420 x 297 mm)
        self.add_rect(0, 0, 420, 297, layer="BORDER")
        self.add_rect(5, 5, 410, 287, layer="BORDER")

        # 2. 標題欄 (右下角 140 x 30 mm)
        tb_x, tb_y, tb_w, tb_h = 275, 5, 140, 30
        self.add_rect(tb_x, tb_y, tb_w, tb_h, layer="TITLE_BLOCK")
        self.add_text("SMART PDU WIRING & PINOUT DIAGRAM", tb_x + 70, tb_y + 22, height=3.5, layer="TITLE_BLOCK", align="CENTER")
        self.add_text("ISO 8820 / SAE J1128 / IP67 COMPLIANT", tb_x + 70, tb_y + 15, height=2.0, layer="TEXT_DIM", align="CENTER")
        self.add_text("SCALE: 1:1  |  SIZE: A3 (420x297)  |  REV: V2.1", tb_x + 70, tb_y + 8, height=1.8, layer="TEXT_DIM", align="CENTER")

        # 3. 繪製左側電源進線 (KL30 / KL15 / KL31)
        self.add_rect(15, 180, 50, 95, layer="LOGIC_CORE")
        self.add_text("POWER INLET", 40, 265, height=2.8, layer="TEXT_DIM", align="CENTER")
        self.add_text("KL30 Battery (12V/100A)", 40, 245, height=2.0, layer="POWER_KL30", align="CENTER")
        self.add_text("KL15 Ignition (ACC 10A)", 40, 220, height=2.0, layer="POWER_KL15", align="CENTER")
        self.add_text("KL31 Ground Return", 40, 195, height=2.0, layer="GND_KL31", align="CENTER")

        # 4. 繪製中央智慧配電盒本體 (Smart E-Fuse Array)
        self.add_rect(80, 165, 85, 120, layer="LOGIC_CORE")
        self.add_text("SMART PDU CORE (8-CH E-FUSE)", 122.5, 275, height=3.0, layer="LOGIC_CORE", align="CENTER")
        self.add_text("ARM Cortex-M4 + High-Side MOSFETs", 122.5, 268, height=1.8, layer="TEXT_DIM", align="CENTER")

        # 5. 繪製 8 迴路負載輸出方框 (中右側)
        load_start_x = 190
        load_start_y = 265
        for i, ch in enumerate(channels_data):
            ly = load_start_y - i * 14
            self.add_rect(load_start_x, ly, 65, 11, layer="LOAD_MODULES")
            self.add_text(f"{ch['ch_id']}: {ch['name']}", load_start_x + 3, ly + 6.5, height=1.8, layer="LOAD_MODULES")
            self.add_text(f"({ch['curr']}A | Fuse:{ch['fuse']}A | {ch['size']}mm²)", load_start_x + 3, ly + 2.5, height=1.5, layer="TEXT_DIM")
            # 走線連接配電盒至負載
            self.add_line(165, ly + 5.5, load_start_x, ly + 5.5, layer="POWER_KL30" if ch['power'] == "KL30" else "POWER_KL15")

        # ==========================================
        # 6. [核心新功能] 繪製防水接插件 Pinout 專區
        # ==========================================
        # 分區標題
        self.add_line(265, 160, 410, 160, layer="TITLE_BLOCK")
        self.add_text("HARNESS CONNECTOR PINOUT VIEWS (端子視圖)", 337.5, 163, height=2.5, layer="TITLE_BLOCK", align="CENTER")

        # 接頭 J1: 4-Pin Deutsch DT06-4S (高負載電源輸出組: 散熱風扇 / 霧燈 / 泵浦 / 雨刷)
        j1_pins = [
            {"pin": 1, "ch": "CH1:FAN", "color": "RED/BLK", "size": "4.0"},
            {"pin": 2, "ch": "CH2:FOG", "color": "YEL/RED", "size": "2.5"},
            {"pin": 3, "ch": "CH3:PUMP", "color": "BLU/WHT", "size": "2.5"},
            {"pin": 4, "ch": "CH4:WIPER", "color": "GRN/BLK", "size": "2.5"},
        ]
        self.draw_waterproof_connector_pinout(
            center_x=305,
            center_y=115,
            connector_id="J1",
            connector_model="Deutsch DT06-4S (2x2)",
            pin_defs=j1_pins,
            cols=2,
            rows=2,
            pin_pitch=10.0,
        )

        # 接頭 J2: 4-Pin TE MCP 2.8 (信號與小功率負載組: 喇叭 / 遠光 / 近光 / 行車紀錄器)
        j2_pins = [
            {"pin": 1, "ch": "CH5:HORN", "color": "ORG/BLK", "size": "1.5"},
            {"pin": 2, "ch": "CH6:HI-BEAM", "color": "WHT/BLU", "size": "1.5"},
            {"pin": 3, "ch": "CH7:LO-BEAM", "color": "YEL/GRN", "size": "1.5"},
            {"pin": 4, "ch": "CH8:DVR", "color": "RED/WHT", "size": "0.75"},
        ]
        self.draw_waterproof_connector_pinout(
            center_x=370,
            center_y=115,
            connector_id="J2",
            connector_model="TE MCP2.8 (2x2)",
            pin_defs=j2_pins,
            cols=2,
            rows=2,
            pin_pitch=10.0,
        )

        # 接頭 J3: 主電源進線 2-Pin Amphenol AT (KL30 / KL31)
        j3_pins = [
            {"pin": 1, "ch": "KL30 IN", "color": "RED", "size": "16.0"},
            {"pin": 2, "ch": "KL31 GND", "color": "BLK", "size": "16.0"},
        ]
        self.draw_waterproof_connector_pinout(
            center_x=337.5,
            center_y=55,
            connector_id="J0_PWR",
            connector_model="Amphenol AT06-2S (1x2 High-Current)",
            pin_defs=j3_pins,
            cols=2,
            rows=1,
            pin_pitch=14.0,
        )

        # 7. 繪製底部 Pin-to-Pin BOM 配線清單
        self.draw_bom_table(15, 10, channels_data)

    def draw_bom_table(self, start_x: float, start_y: float, channels_data: List[Dict[str, Any]]):
        """繪製 A3 底部配線與接插件對應 BOM 表"""
        table_w = 250.0
        row_h = 6.0
        self.add_rect(start_x, start_y, table_w, 40, layer="TITLE_BLOCK")
        self.add_text("PIN-TO-PIN HARNESS WIRING & CONNECTOR SCHEDULE", start_x + 125, start_y + 35, height=2.2, layer="TITLE_BLOCK", align="CENTER")

        cols_x = [start_x, start_x + 20, start_x + 65, start_x + 90, start_x + 120, start_x + 155, start_x + 195, start_x + table_w]
        headers = ["CH", "Load Name", "Con/Pin", "Current", "Wire Gauge", "Color Code", "E-Fuse Spec"]
        
        # 繪製表頭
        for i, h in enumerate(headers):
            self.add_text(h, cols_x[i] + 2, start_y + 28, height=1.8, layer="TITLE_BLOCK")
        self.add_line(start_x, start_y + 26, start_x + table_w, start_y + 26, layer="TITLE_BLOCK")

        # 繪製資料行 (選列 4 筆代表展示，維持版面俐落)
        for idx, ch in enumerate(channels_data[:4]):
            ry = start_y + 20 - idx * row_h
            con_pin = f"J1-P{idx+1}" if idx < 4 else f"J2-P{idx-3}"
            self.add_text(ch["ch_id"], cols_x[0] + 2, ry, height=1.6, layer="TEXT_DIM")
            self.add_text(ch["name"][:12], cols_x[1] + 2, ry, height=1.6, layer="TEXT_DIM")
            self.add_text(con_pin, cols_x[2] + 2, ry, height=1.6, layer="CON_PINS")
            self.add_text(f"{ch['curr']} A", cols_x[3] + 2, ry, height=1.6, layer="TEXT_DIM")
            self.add_text(f"{ch['size']} mm²", cols_x[4] + 2, ry, height=1.6, layer="TEXT_DIM")
            self.add_text(ch["color"], cols_x[5] + 2, ry, height=1.6, layer="TEXT_DIM")
            self.add_text(f"{ch['fuse']}A (<5ms)", cols_x[6] + 2, ry, height=1.6, layer="TEXT_DIM")

    # ==========================================
    # 輸出 DXF 檔案
    # ==========================================

    def export_dxf(self) -> str:
        """組裝 DXF 檔頭 (Header)、圖層表 (Tables) 與實體區 (Entities)"""
        dxf_lines = [
            "0\nSECTION\n2\nHEADER\n9\n$ACADVER\n1\nAC1009\n0\nENDSEC\n",
            "0\nSECTION\n2\nTABLES\n0\nTABLE\n2\nLAYER\n70\n" + str(len(self.layers)) + "\n",
        ]
        for name, color in self.layers.items():
            dxf_lines.append(f"0\nLAYER\n2\n{name}\n70\n0\n62\n{color}\n6\nCONTINUOUS\n")
        dxf_lines.append("0\nENDTAB\n0\nENDSEC\n")

        # ENTITIES
        dxf_lines.append("0\nSECTION\n2\nENTITIES\n")
        dxf_lines.extend(self.entities)
        dxf_lines.append("0\nENDSEC\n0\nEOF\n")

        content = "".join(dxf_lines)
        os.makedirs(os.path.dirname(os.path.abspath(self.filename)), exist_ok=True)
        with open(self.filename, "w", encoding="utf-8") as f:
            f.write(content)
        return self.filename


# ==========================================
# 測試與自動化主程式
# ==========================================
if __name__ == "__main__":
    sample_channels = [
        {"ch_id": "CH1", "name": "Cooling Fan", "power": "KL30", "curr": 20.0, "fuse": 30, "size": 4.0, "color": "RED/BLK"},
        {"ch_id": "CH2", "name": "Fog Lamp", "power": "KL15", "curr": 10.0, "fuse": 15, "size": 2.5, "color": "YEL/RED"},
        {"ch_id": "CH3", "name": "Fuel Pump", "power": "KL15", "curr": 8.0, "fuse": 15, "size": 2.5, "color": "BLU/WHT"},
        {"ch_id": "CH4", "name": "Windshield Wiper", "power": "KL15", "curr": 8.0, "fuse": 15, "size": 2.5, "color": "GRN/BLK"},
        {"ch_id": "CH5", "name": "Horn Circuit", "power": "KL30", "curr": 6.0, "fuse": 10, "size": 1.5, "color": "ORG/BLK"},
        {"ch_id": "CH6", "name": "High Beam Headlight", "power": "KL15", "curr": 4.5, "fuse": 7.5, "size": 1.5, "color": "WHT/BLU"},
        {"ch_id": "CH7", "name": "Low Beam Headlight", "power": "KL15", "curr": 4.5, "fuse": 7.5, "size": 1.5, "color": "YEL/GRN"},
        {"ch_id": "CH8", "name": "Dashcam & Telematics", "power": "KL30", "curr": 1.0, "fuse": 3.0, "size": 0.75, "color": "RED/WHT"},
    ]

    out_file = "G:/我的雲端硬碟/AI_master_workspace/three_memory/DATA/sample_smart_pdu_with_pinouts.dxf"
    gen = SmartPDUDXFGenerator(out_file)
    gen.build_complete_diagram(sample_channels)
    saved_path = gen.export_dxf()
    print(f"✅ DXF 接線圖與 Pinout 視圖已成功生成: {saved_path}")
