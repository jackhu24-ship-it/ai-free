# -*- coding: utf-8 -*-
"""
reorganize_cad_zones.py
將 07_📐_CAD工程圖紙 升級為標準 4 大子分區：
- 00_標準圖框與繪圖規範
- 01_車輛主電線束圖
- 02_電氣電路原理圖
- 03_機構零件與鈑件圖
"""

import os
import sys
import shutil
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

CAD_ROOT = r"G:\我的雲端硬碟\AI產出成品總庫\07_📐_CAD工程圖紙"

def reorganize():
    print("📐 正在重組 CAD 工程圖紙為【主電線束圖】與【電路原理圖】獨立分區...")
    
    # 1. 建立新結構
    output_distributor.init_output_structure()
    
    new_dirs = {
        "templates": os.path.join(CAD_ROOT, "00_標準圖框與繪圖規範"),
        "harness": os.path.join(CAD_ROOT, "01_車輛主電線束圖"),
        "schematics": os.path.join(CAD_ROOT, "02_電氣電路原理圖"),
        "parts": os.path.join(CAD_ROOT, "03_機構零件與鈑件圖")
    }
    for p in new_dirs.values():
        os.makedirs(p, exist_ok=True)
        
    # 2. 搬移舊目錄檔案
    old_harness = os.path.join(CAD_ROOT, "電氣線束圖")
    if os.path.exists(old_harness):
        for f in os.listdir(old_harness):
            src_f = os.path.join(old_harness, f)
            dst_f = os.path.join(new_dirs["harness"], f)
            shutil.move(src_f, dst_f)
            print(f"  🚚 搬移線束圖: {f} ➔ 01_車輛主電線束圖")
        shutil.rmtree(old_harness, ignore_errors=True)
        
    old_parts = os.path.join(CAD_ROOT, "機構零件圖")
    if os.path.exists(old_parts):
        for f in os.listdir(old_parts):
            src_f = os.path.join(old_parts, f)
            dst_f = os.path.join(new_dirs["parts"], f)
            shutil.move(src_f, dst_f)
            print(f"  🚚 搬移零件圖: {f} ➔ 03_機構零件與鈑件圖")
        shutil.rmtree(old_parts, ignore_errors=True)
        
    old_templates = os.path.join(CAD_ROOT, "00_標準圖框與線束模板")
    if os.path.exists(old_templates):
        for f in os.listdir(old_templates):
            src_f = os.path.join(old_templates, f)
            dst_f = os.path.join(new_dirs["templates"], f)
            shutil.move(src_f, dst_f)
            print(f"  🚚 搬移模板: {f} ➔ 00_標準圖框與繪圖規範")
        shutil.rmtree(old_templates, ignore_errors=True)
        
    # 3. 在 02_電氣電路原理圖 中產生一張標準電路原理圖 DXF
    schematic_file = os.path.join(r"G:\我的雲端硬碟\AI_master_workspace\three_memory\DATA", "cad_schematic_circuit_demo.dxf")
    doc_s = ezdxf.new("R12", setup=True)
    msp_s = doc_s.modelspace()
    for l, c in [("OUTLINE", 7), ("CIRCUIT_WIRE", 1), ("CIRCUIT_GND", 8), ("COMPONENT_BOX", 4), ("TEXT", 2), ("FUSE_SYM", 1)]:
        doc_s.layers.new(name=l, dxfattribs={"color": c})
        
    # 繪製電路原理圖符號 (電瓶 ➔ 保險絲 ➔ 點火開關 ➔ 繼電器 ➔ 負載)
    # 1. 電瓶符號 (X: 50, Y: 100)
    msp_s.add_polyline2d([(40, 80), (60, 80), (60, 120), (40, 120), (40, 80)], dxfattribs={"layer": "COMPONENT_BOX"})
    msp_s.add_text("BATTERY (12V)", dxfattribs={"layer": "TEXT", "height": 3.5}).set_placement((35, 125))
    
    # 2. 保險絲符號 (X: 120, Y: 100)
    msp_s.add_line((60, 100), (100, 100), dxfattribs={"layer": "CIRCUIT_WIRE"})
    msp_s.add_polyline2d([(100, 95), (140, 95), (140, 105), (100, 105), (100, 95)], dxfattribs={"layer": "FUSE_SYM"})
    msp_s.add_line((100, 100), (140, 100), dxfattribs={"layer": "FUSE_SYM"})
    msp_s.add_text("MAIN FUSE (15A)", dxfattribs={"layer": "TEXT", "height": 3.0}).set_placement((100, 110))
    
    # 3. 繼電器與點火開關 (X: 200, Y: 100)
    msp_s.add_line((140, 100), (180, 100), dxfattribs={"layer": "CIRCUIT_WIRE"})
    msp_s.add_polyline2d([(180, 85), (230, 85), (230, 115), (180, 115), (180, 85)], dxfattribs={"layer": "COMPONENT_BOX"})
    msp_s.add_text("IGNITION RELAY", dxfattribs={"layer": "TEXT", "height": 3.0}).set_placement((180, 120))
    
    # 4. ECU 電源輸入 (X: 300, Y: 100)
    msp_s.add_line((230, 100), (280, 100), dxfattribs={"layer": "CIRCUIT_WIRE"})
    msp_s.add_polyline2d([(280, 70), (360, 70), (360, 130), (280, 130), (280, 70)], dxfattribs={"layer": "COMPONENT_BOX"})
    msp_s.add_text("ECU CONTROLLER", dxfattribs={"layer": "TEXT", "height": 4.0}).set_placement((285, 135))
    msp_s.add_text("PIN 1: VCC (+12V)", dxfattribs={"layer": "TEXT", "height": 3.0}).set_placement((285, 115))
    msp_s.add_text("PIN 2: GND", dxfattribs={"layer": "TEXT", "height": 3.0}).set_placement((285, 85))
    
    # 接地線
    msp_s.add_line((280, 85), (200, 85), dxfattribs={"layer": "CIRCUIT_GND"})
    msp_s.add_line((200, 85), (200, 40), dxfattribs={"layer": "CIRCUIT_GND"})
    msp_s.add_line((185, 40), (215, 40), dxfattribs={"layer": "CIRCUIT_GND"})
    msp_s.add_line((190, 35), (210, 35), dxfattribs={"layer": "CIRCUIT_GND"})
    msp_s.add_line((195, 30), (205, 30), dxfattribs={"layer": "CIRCUIT_GND"})
    msp_s.add_text("SYSTEM GND", dxfattribs={"layer": "TEXT", "height": 3.0}).set_placement((180, 20))
    
    doc_s.saveas(schematic_file)
    output_distributor.publish_output(schematic_file, "cad", "schematics", custom_name="CAD_全車電源與點火控制電路原理圖", date_prefix=True)
    
    # 4. 刷新索引
    idx_p = output_distributor.generate_html_index()
    print(f"\n🎉 CAD 專區重組完成！總索引已刷新: {idx_p}")

if __name__ == "__main__":
    reorganize()
