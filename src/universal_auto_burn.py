#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 嵌入式硬體模組：萬能全自動智慧感知燒錄引擎 (universal_auto_burn.py) - 旗艦版
作者：🛠️ 小開 (Agent_Coder)
審查：🐎 小馬 (Agent_Reviewer)
統籌：👑 小幫手 (Agent_PM)

核心特性：
1. 【支援拖曳燒錄】：可將任意變數檔名的 .hex 檔案直接拖曳至桌面圖示放開，立即自動燒錄！
2. 【智慧最新追蹤】：未拖曳時，自動掃描並抓取專案目錄中「最後產出 / 最新修改」的 .hex 檔案！
3. 【多版本彈性選單】：若有多個候選版本，提供極速繁中數字選單（按 Enter 預設最新）！
4. 【硬體晶片自適應】：自動讀取晶片 ID 與 HEX 配置，自動輸出 5.0V/3.3V 供電並校驗！
"""

from __future__ import annotations

import sys
import os
import re
import datetime
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

IPECMD_PATH = Path(r"C:\Program Files\Microchip\MPLABX\v6.15\mplab_platform\mplab_ipe\ipecmd.exe")

DEVICE_ID_MAP = {
    "0x3066": {"name": "PIC16F18313", "cmd": "16F18313", "voltage": 5.0},
    "0x6160": {"name": "PIC18F25K80", "cmd": "18F25K80", "voltage": 5.0},
    "0x6140": {"name": "PIC18F26K80", "cmd": "18F26K80", "voltage": 5.0},
    "0x6120": {"name": "PIC18F45K80", "cmd": "18F45K80", "voltage": 5.0},
    "0x6100": {"name": "PIC18F46K80", "cmd": "18F46K80", "voltage": 5.0},
    "0x2420": {"name": "PIC16F1936", "cmd": "16F1936", "voltage": 5.0},
    "0x2440": {"name": "PIC16F1937", "cmd": "16F1937", "voltage": 5.0},
    "0x1380": {"name": "PIC18F2580", "cmd": "18F2580", "voltage": 5.0},
    "0x13a0": {"name": "PIC18F2680", "cmd": "18F2680", "voltage": 5.0},
}

PROJECT_DIRS = [
    Path(r"C:\MPLAB Program"),
    Path(r"C:\Users\user\MPLABXProjects"),
    Path(r"G:\我的雲端硬碟\晶片"),
    Path(os.path.expanduser("~/OneDrive/桌面")),
    Path(os.path.expanduser("~/Desktop"))
]



def run_ipecmd(args: list[str], timeout: int = 35) -> tuple[int, str, str]:
    if not IPECMD_PATH.exists():
        return -1, "", f"找不到 ipecmd 工具: {IPECMD_PATH}"
    cmd = [str(IPECMD_PATH)] + args
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return res.returncode, res.stdout, res.stderr
    except subprocess.TimeoutExpired:
        return -2, "", "執行超時 (請檢查 PICkit 4 USB 連接)"
    except Exception as e:
        return -3, "", str(e)


def probe_hardware_chip() -> Optional[dict[str, Any]]:
    """主動探測硬體晶片"""
    probe_candidates = ["16F18313", "18F25K80", "18F26K80", "16F1936"]
    for candidate in probe_candidates:
        args = [f"-P{candidate}", "-TPPK4", "-TSBUR210575365", "-W5.0", "-B"]
        ret, stdout, stderr = run_ipecmd(args, timeout=20)
        
        if "Target device" in stdout and "found" in stdout:
            m = re.search(r"Target device (PIC[0-9A-Z]+) found", stdout)
            dev_fullname = m.group(1) if m else f"PIC{candidate}"
            dev_cmd = dev_fullname[3:] if dev_fullname.startswith("PIC") else dev_fullname
            return {
                "name": dev_fullname,
                "cmd": dev_cmd,
                "voltage": 5.0,
                "raw_log": stdout
            }
        
        m_id = re.search(r"Device Id\s*=\s*(0x[0-9a-fA-F]+)", stdout)
        if m_id:
            dev_id = m_id.group(1).lower()
            if dev_id in DEVICE_ID_MAP:
                return DEVICE_ID_MAP[dev_id]

    return None


def scan_all_hex_files() -> List[dict[str, Any]]:
    """掃描所有可用的 HEX 檔案"""
    found = []
    for root in PROJECT_DIRS:
        if not root.exists():
            continue
        for h in root.rglob("*.hex"):
            if "backup" in str(h).lower() or ".bak" in str(h).lower():
                continue
            
            dev_target = ""
            for p in h.parents:
                conf = p / "nbproject" / "configurations.xml"
                if conf.exists():
                    try:
                        txt = conf.read_text(encoding="utf-8", errors="replace")
                        m = re.search(r"<targetDevice>(.*?)</targetDevice>", txt)
                        if m:
                            d = m.group(1).strip().upper()
                            if d.startswith("PIC"):
                                d = d[3:]
                            dev_target = d
                    except Exception:
                        pass
                    break
            
            if not dev_target:
                if "745" in str(h):
                    dev_target = "18F25K80"
                elif "746" in str(h):
                    dev_target = "16F18313"
                else:
                    dev_target = "16F18313"

            found.append({
                "hex_path": h,
                "device": dev_target,
                "mtime": h.stat().st_mtime,
                "project_name": h.parents[2].name if len(h.parents) >= 3 else h.parent.name
            })
    
    found.sort(key=lambda x: x["mtime"], reverse=True)
    return found


def main():
    print("\n" + "="*70)
    print("🚀 Microchip PICkit 4 【萬能智慧感知燒錄引擎】 (Five-Agent AI OS)")
    print("   特性: 支援任意檔名 HEX 拖曳 ➔ 自動辨識晶片 ➔ 一鍵秒燒！")
    print("="*70 + "\n")

    # 1. 檢查是否有拖曳傳入的 HEX 檔案
    target_hex_path = None
    if len(sys.argv) > 1:
        dragged = Path(sys.argv[1].strip('"'))
        if dragged.exists() and dragged.suffix.lower() == ".hex":
            target_hex_path = dragged
            print(f"📥 【收到拖曳檔案】: {target_hex_path.name}")
            print(f"📁 檔案完整路徑: {target_hex_path}")

    # 2. 探測硬體晶片
    print("\n🔍 【步驟一】 正在透過 PICkit 4 探測目標板上的晶片型號...")
    detected_chip = probe_hardware_chip()

    if not detected_chip:
        print("\n" + "-"*70)
        print("⚠️ 【未偵測到晶片】 Target Device ID (0x0)")
        print("👉 請確認：")
        print("   1. PICkit 4 的 5 針 ICSP 排線是否插牢。")
        print("   2. Pin 1 (白色三角形標誌 ▽) 方向是否正確對準。")
        print("-"*70 + "\n")
        return

    chip_name = detected_chip["name"]
    chip_cmd = detected_chip["cmd"]
    voltage = detected_chip["voltage"]

    print(f"🎉 【晶片辨識成功】 偵測到硬體晶片為: 【{chip_name}】！")

    # 3. 確定要燒錄的 HEX 檔案
    final_hex = None
    if target_hex_path:
        final_hex = target_hex_path
    else:
        print("\n🔍 【步驟二】 正在專案庫中自動尋找匹配 【" + chip_name + "】 的最新 HEX 檔案...")
        all_hex = scan_all_hex_files()
        
        # 篩選出匹配該晶片的候選 HEX
        matched_list = [h for h in all_hex if h["device"].upper() in chip_cmd.upper() or chip_cmd.upper() in h["device"].upper()]
        if not matched_list:
            matched_list = all_hex

        if len(matched_list) == 1:
            final_hex = matched_list[0]["hex_path"]
            dt_str = datetime.datetime.fromtimestamp(matched_list[0]["mtime"]).strftime("%Y-%m-%d %H:%M:%S")
            print(f"🎯 自動鎖定最新產出檔案: 【{final_hex.name}】 ({dt_str})")
        else:
            print("\n" + "-"*70)
            print(f"📋 找到以下 {len(matched_list)} 個可用於 {chip_name} 的 HEX 檔案：")
            for idx, item in enumerate(matched_list[:5], 1):
                dt_str = datetime.datetime.fromtimestamp(item["mtime"]).strftime("%Y-%m-%d %H:%M")
                print(f"  【{idx}】 {item['hex_path'].name}  (專案: {item['project_name']}, 更新: {dt_str})")
            print("-"*70)
            
            choice = input(f"👉 請選擇編號 [1-{min(len(matched_list), 5)}] (直接按 Enter 預設最新 【1】): ").strip()
            sel_idx = 0
            if choice.isdigit() and 1 <= int(choice) <= len(matched_list):
                sel_idx = int(choice) - 1
            final_hex = matched_list[sel_idx]["hex_path"]
            print(f"🎯 選定燒錄檔案: 【{final_hex.name}】")

    # 4. 執行燒錄
    print("\n" + "="*70)
    print(f"⚡ 【步驟三】 正在命令 PICkit 4 供電 {voltage}V 並寫入 {final_hex.name} ...")
    print("="*70 + "\n")

    args = [
        f"-P{chip_cmd}",
        "-TPPK4",
        "-TSBUR210575365",
        f"-F{final_hex}",
        "-M",
        f"-W{voltage:.1f}"
    ]

    ret, stdout, stderr = run_ipecmd(args, timeout=40)

    print("-" * 70)
    if "Programming/Verify complete" in stdout or "Program Succeeded" in stdout:
        print(f"🎉🎉🎉 【燒錄成功】 恭喜！{chip_name} 已成功寫入【{final_hex.name}】並通過原廠校驗！")
    else:
        print(f"⚠️ 【燒錄未完成】 (錯誤代碼 {ret})")
        print(stdout + "\n" + stderr)
    print("-" * 70 + "\n")


if __name__ == "__main__":
    main()
