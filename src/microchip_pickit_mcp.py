#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Microchip PICkit 4 晶片辨識與燒錄工具 (microchip_pickit_mcp.py)
"""

from __future__ import annotations

import sys
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

IPECMD_PATH = Path(r"C:\Program Files\Microchip\MPLABX\v6.15\mplab_platform\mplab_ipe\ipecmd.exe")

DEVICE_MAP = {
    "0x3066": "PIC16F18313",
    "0x6160": "PIC18F25K80",
    "0x6140": "PIC18F26K80",
    "0x6120": "PIC18F45K80",
    "0x6100": "PIC18F46K80",
    "0x2420": "PIC16F1936",
    "0x2440": "PIC16F1937",
    "0x1380": "PIC18F2580",
    "0x13a0": "PIC18F2680"
}

KNOWN_PROJECTS = {
    "745": {
        "name": "TGB-911745.X (量產版 CAN BUS)",
        "device": "18F25K80",
        "voltage": 5.0,
        "hex_path": Path(r"C:\MPLAB Program\TGB-911745.X_量產版 CAN BUS_2023-05-30_01\TGB-911745.X\dist\default\production\TGB-911745.X.production.hex")
    },
    "746": {
        "name": "TGB-912746.X",
        "device": "16F18313",
        "voltage": 5.0,
        "hex_path": Path(r"C:\MPLAB Program\TGB-912746.X_2026-06-22\TGB-912746.X\dist\default\production\TGB-912746.X.production.hex")
    }
}


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


def detect_chip_id() -> None:
    """自動偵測目標板上的晶片型號"""
    print("\n" + "="*70)
    print("🔍 正在透過 PICkit 4 掃描目標電路板上的晶片型號...")
    print("="*70)

    # 嘗試用 18F25K80 探測
    args = ["-P18F25K80", "-TPPK4", "-TSBUR210575365", "-W5.0", "-B"]
    ret, stdout, stderr = run_ipecmd(args, timeout=25)

    if "Target device" in stdout and "found" in stdout:
        m = re.search(r"Target device (.*?) found", stdout)
        dev_name = m.group(1) if m else "未知"
        m_id = re.search(r"Device Id\s*=\s*(0x[0-9a-fA-F]+)", stdout)
        dev_id = m_id.group(1) if m_id else ""
        print(f"🎉 偵測成功！電路板上的晶片型號為: 【{dev_name}】 (Device ID: {dev_id})")
        return

    # 若 18F 沒讀到，再用 16F18313 探測
    args2 = ["-P16F18313", "-TPPK4", "-TSBUR210575365", "-W5.0", "-B"]
    ret2, stdout2, stderr2 = run_ipecmd(args2, timeout=25)
    if "Target device" in stdout2 and "found" in stdout2:
        m2 = re.search(r"Target device (.*?) found", stdout2)
        dev_name2 = m2.group(1) if m2 else "未知"
        m_id2 = re.search(r"Device Id\s*=\s*(0x[0-9a-fA-F]+)", stdout2)
        dev_id2 = m_id2.group(1) if m_id2 else ""
        print(f"🎉 偵測成功！電路板上的晶片型號為: 【{dev_name2}】 (Device ID: {dev_id2})")
        return

    if "Target Device ID (0x0)" in stdout or "Target Device ID (0x0)" in stdout2:
        print("⚠️ 讀取到 Target Device ID (0x0)：晶片尚未接通！")
        print("👉 請確認 ICSP 5 針排線方向是否插對、針腳是否插緊。")
    else:
        print("輸出日誌：\n", stdout or stdout2)


def program_project(target: dict[str, Any]) -> dict[str, Any]:
    device = target["device"]
    voltage = target["voltage"]
    p_hex = target["hex_path"]
    serial_number = "BUR210575365"

    if not p_hex.exists():
        return {"success": False, "message": f"找不到燒錄檔: {p_hex}"}

    args = [
        f"-P{device}",
        "-TPPK4",
        f"-TS{serial_number}",
        f"-F{p_hex}",
        "-M"
    ]
    if voltage > 0:
        args.append(f"-W{voltage:.1f}")

    ret, stdout, stderr = run_ipecmd(args, timeout=40)

    if "Programming/Verify complete" in stdout or "Program Succeeded" in stdout:
        return {
            "success": True,
            "message": "🎉 燒錄與校驗 100% 成功！",
            "device": device,
            "raw_log": stdout
        }
    elif "Invalid Device ID" in stdout:
        return {
            "success": False,
            "error_type": "INVALID_DEVICE_ID",
            "message": f"⚠️ 偵測到 Target Device ID (0x0)，未接觸到 PIC{device} 晶片！\n👉 請檢查 ICSP 5 針排線是否對準插緊。",
            "raw_log": stdout
        }
    else:
        return {
            "success": False,
            "error_type": "PROGRAMMING_FAILED",
            "message": f"燒錄未完成 (代碼 {ret})",
            "raw_log": stdout + "\n" + stderr
        }


if __name__ == "__main__":
    if "--detect-chip" in sys.argv:
        detect_chip_id()
        sys.exit(0)

    target_key = None
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if "745" in arg:
            target_key = "745"
        elif "746" in arg:
            target_key = "746"

    if target_key and target_key in KNOWN_PROJECTS:
        selected = KNOWN_PROJECTS[target_key]
    else:
        print("\n" + "="*70)
        print("🚀 Microchip PICkit 4 專案選擇燒錄清單 (Five-Agent AI OS)")
        print("="*70)
        print("  【1】 燒錄 TGB-911745.X ➔ 目標晶片: PIC18F25K80 (5.0V)")
        print("  【2】 燒錄 TGB-912746.X ➔ 目標晶片: PIC16F18313 (5.0V)")
        print("="*70)
        choice = input("👉 請輸入要燒錄的專案編號 [1 或 2] (按 Enter 預設為 1): ").strip()
        if choice == "2" or "746" in choice:
            selected = KNOWN_PROJECTS["746"]
        else:
            selected = KNOWN_PROJECTS["745"]

    print("\n" + "="*70)
    print(f"🎯 正在準備燒錄: 【{selected['name']}】")
    print(f"📌 目標晶片: PIC{selected['device']} | 供電電壓: {selected['voltage']}V")
    print(f"📄 燒錄檔案: {selected['hex_path'].name}")
    print("="*70 + "\n")
    print(f"⏳ 正在連接 PICkit 4 寫入 PIC{selected['device']} 晶片中，請稍候...")

    res = program_project(selected)

    print("\n" + "-"*70)
    if res.get("success"):
        print(f"🎉 【燒錄成功】 PIC{selected['device']} 晶片已成功寫入【{selected['name']}】並通過校驗！")
    else:
        print("⚠️ 【燒錄提示】 " + res.get("message", "燒錄未完成"))
    print("-"*70 + "\n")
