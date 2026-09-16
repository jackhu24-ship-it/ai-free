# -*- coding: utf-8 -*-
"""
init_cad_templates.py
為 07_📐_CAD工程圖紙 建立 00_標準圖框與線束模板 專用子目錄與母版標準 DXF。
"""

import os
import sys
import ezdxf

# 強制 Windows 繁中 UTF-8
if sys.platform.startswith("win"):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "SRC"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import output_distributor

def build_cad_templates():
    print("📐 正在為 CAD 專區建立標準母版與線束模板...")
    
    # 1. 產生 CAD 繪圖與線束規範書
    spec_content = """# AutoCAD (DXF) 標準工程圖框與電氣線束繪圖規範書

## 1. 圖紙尺寸與圖框標準
- 標準圖紙：A3 橫式 (420.0 x 297.0 mm)
- 雙層圖框：外框 (420x297), 內框 (400x277, 留邊 10mm/20mm 裝訂邊)
- 右下角 Title Block：包含專案名稱、圖號、比例、設計者、日期與版本。

## 2. ACI 8 大工規圖層色彩標準
| 圖層名稱 | 色彩編號 | 顏色名稱 | 用途說明 |
| :--- | :---: | :--- | :--- |
| `0` | 7 | White/Black | 預設底層 (不作主要繪圖) |
| `OUTLINE` | 7 | White | 零件外框、車體邊界與圖框 |
| `WIRING_PWR` | 1 | Red (紅) | 12V / 5V 電源與高壓主幹線 |
| `WIRING_GND` | 8 | Dark Gray (深灰/黑) | 系統接地與迴路保護線 |
| `WIRING_CAN` | 3 | Green (綠) | CAN-H / CAN-L 通訊雙絞線 |
| `WIRING_SIG` | 4 | Cyan (青藍) | 感測器微電壓訊號線 (ADC/Switch) |
| `TEXT` | 2 | Yellow (黃) | 線路標註、長度標籤、端子 Pin 號 |
| `TABLE` | 7 | White | 右側 BOM 接線清冊與表格框線 |

## 3. 電氣線束曼哈頓 90° 正交避障原則
- 線路一律採正交 90° 折線，嚴禁非 90° 斜切穿過零件實體。
- 大電流電源線走最外圈，CAN 訊號線走中心抗干擾隔離槽。
- 自動預留端子壓接餘裕 (+15mm Margin)。
"""
    spec_path = os.path.join(r"G:\我的雲端硬碟\AI_master_workspace\three_memory\02_Knowledge\Specs", "CAD_標準圖框與線束繪圖規範指南.md")
    with open(spec_path, "w", encoding="utf-8") as f:
        f.write(spec_content)
    output_distributor.publish_output(spec_path, "cad", "templates", custom_name="CAD_標準圖框與電氣線束繪圖規範指南", date_prefix=False)

    # 2. 產生 A3 橫式標準工程圖框母版 DXF
    a3_path = os.path.join(r"G:\我的雲端硬碟\AI_master_workspace\three_memory\DATA", "cad_a3_template_master.dxf")
    doc = ezdxf.new("R12", setup=True)
    msp = doc.modelspace()
    doc.layers.new(name="FRAME_BORDER", dxfattribs={"color": 7})
    doc.layers.new(name="TITLE_BLOCK", dxfattribs={"color": 7})
    doc.layers.new(name="TEXT", dxfattribs={"color": 2})

    # 外框 420x297
    msp.add_polyline2d([(0, 0), (420, 0), (420, 297), (0, 297), (0, 0)], dxfattribs={"layer": "FRAME_BORDER"})
    # 內框 400x277
    msp.add_polyline2d([(10, 10), (410, 10), (410, 287), (10, 287), (10, 10)], dxfattribs={"layer": "FRAME_BORDER"})
    # Title Block 右下角 (300, 10) -> (410, 60)
    msp.add_polyline2d([(300, 10), (410, 10), (410, 60), (300, 60), (300, 10)], dxfattribs={"layer": "TITLE_BLOCK"})
    msp.add_line((300, 35), (410, 35), dxfattribs={"layer": "TITLE_BLOCK"})
    msp.add_line((355, 10), (355, 60), dxfattribs={"layer": "TITLE_BLOCK"})
    msp.add_text("Five-Agent AI OS", dxfattribs={"layer": "TEXT", "height": 5.0}).set_placement((305, 45))
    msp.add_text("DWG: HARNESS-A3-MASTER", dxfattribs={"layer": "TEXT", "height": 3.5}).set_placement((305, 20))
    msp.add_text("SCALE: 1:1", dxfattribs={"layer": "TEXT", "height": 3.5}).set_placement((360, 20))

    doc.saveas(a3_path)
    output_distributor.publish_output(a3_path, "cad", "templates", custom_name="CAD_A3橫式標準工程圖框母版", date_prefix=True)

    # 3. 產生全車主電線正交拓撲標準模板 DXF
    harness_master = os.path.join(r"G:\我的雲端硬碟\AI_master_workspace\three_memory\DATA", "cad_main_harness_template_master.dxf")
    doc_h = ezdxf.new("R12", setup=True)
    msp_h = doc_h.modelspace()
    for l, c in [("OUTLINE", 7), ("WIRING_PWR", 1), ("WIRING_GND", 8), ("WIRING_CAN", 3), ("WIRING_SIG", 4), ("TEXT", 2)]:
        doc_h.layers.new(name=l, dxfattribs={"color": c})

    # 主脊椎線 (X: 100~350, Y: 150)
    msp_h.add_line((100, 150), (350, 150), dxfattribs={"layer": "WIRING_PWR"})
    msp_h.add_line((100, 148), (350, 148), dxfattribs={"layer": "WIRING_GND"})
    msp_h.add_line((100, 146), (350, 146), dxfattribs={"layer": "WIRING_CAN"})

    # 車頭分支 (X: 100, Y: 150 -> Y: 220 速度錶 / Y: 80 大燈)
    msp_h.add_line((100, 150), (100, 220), dxfattribs={"layer": "WIRING_PWR"})
    msp_h.add_line((100, 146), (100, 220), dxfattribs={"layer": "WIRING_CAN"})
    msp_h.add_text("SPEEDOMETER (Zone A)", dxfattribs={"layer": "TEXT", "height": 4.0}).set_placement((70, 225))

    # 中段電源分支 (X: 200, Y: 150 -> Y: 80 電瓶 / 保險絲)
    msp_h.add_line((200, 150), (200, 80), dxfattribs={"layer": "WIRING_PWR"})
    msp_h.add_line((200, 148), (200, 80), dxfattribs={"layer": "WIRING_GND"})
    msp_h.add_text("BATTERY / FUSE (Zone B)", dxfattribs={"layer": "TEXT", "height": 4.0}).set_placement((170, 65))

    # 車尾分支 (X: 350, Y: 150 -> Y: 220 尾燈 / 馬達)
    msp_h.add_line((350, 150), (350, 220), dxfattribs={"layer": "WIRING_PWR"})
    msp_h.add_line((350, 148), (350, 220), dxfattribs={"layer": "WIRING_GND"})
    msp_h.add_text("TAIL_LIGHT (Zone D)", dxfattribs={"layer": "TEXT", "height": 4.0}).set_placement((320, 225))

    doc_h.saveas(harness_master)
    output_distributor.publish_output(harness_master, "cad", "templates", custom_name="CAD_全車主電線正交拓撲標準模板", date_prefix=True)

    # 刷新索引
    idx = output_distributor.generate_html_index()
    print("✅ CAD 模板區建立並同步完成！總索引已刷新:", idx)

if __name__ == "__main__":
    build_cad_templates()
