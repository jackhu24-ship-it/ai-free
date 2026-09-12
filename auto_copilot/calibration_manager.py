"""
AutoCopilot Calibration Matrix & ASAM A2L/CDF Parameter Manager
==============================================================
依據 霸丸總指揮官 標定資料庫 (A2L / CDF) 基線凍結令：
針對不同量產車型（客車、商用車、全地形車）建立受版本控管的標定參數矩陣，
並實施 ASIL-D 剛性安全邊界檢查（防止現場標定調校破壞 FTTI <= 40ms 極限）。
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict

# Windows UTF-8 控制台保護
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CALIB_DIR = os.path.join(CURRENT_DIR, "calibrations")
os.makedirs(CALIB_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("AutoCopilot.CalibrationManager")

# 剛性安全約束極限 (Safety Boundary Invariants - 不可逾越)
SAFETY_INVARIANTS = {
    "MAX_ALLOWED_FTTI_MS": 40.0,
    "MAX_CRC_FAULT_THRESHOLD": 3,
    "MAX_FILTER_TAU_MS": 50.0,
    "MAX_COOLANT_TEMP_LIMIT_C": 110.0,
}

# 預設三大多元車型標定矩陣
DEFAULT_VEHICLE_CALIBRATIONS = {
    "PASSENGER_SEDAN": {
        "profile_name": "Premium Electric Sedan (乘用純電轎車)",
        "ftti_target_ms": 40.0,
        "crc_fault_threshold": 3,
        "filter_tau_ms": 15.0,
        "max_safe_torque_nm": 250.0,
        "coolant_trip_temp_c": 105.0,
        "actuator_release_ms": 10.0,
        "target_ecu": "Bosch / Inovance Inverter MCU"
    },
    "COMMERCIAL_TRUCK": {
        "profile_name": "Heavy-Duty Commercial Truck (重型商用卡車)",
        "ftti_target_ms": 30.0,  # 重卡慣性大，安全關斷更嚴苛
        "crc_fault_threshold": 2,
        "filter_tau_ms": 25.0,
        "max_safe_torque_nm": 650.0,
        "coolant_trip_temp_c": 102.0,
        "actuator_release_ms": 8.0,
        "target_ecu": "Knorr-Bremse / Cummins PDM"
    },
    "OFF_ROAD_UTV": {
        "profile_name": "All-Terrain Off-Road UTV (極限全地形全地形車)",
        "ftti_target_ms": 35.0,
        "crc_fault_threshold": 3,
        "filter_tau_ms": 10.0,  # 顛簸路況低延遲響應
        "max_safe_torque_nm": 320.0,
        "coolant_trip_temp_c": 108.0,
        "actuator_release_ms": 12.0,
        "target_ecu": "BRP / Polaris Powertrain Controller"
    }
}


def validate_calibration(profile_id: str, params: Dict[str, Any]) -> bool:
    """驗證標定參數是否嚴格遵守 ASIL-D 剛性安全約束"""
    ftti = params.get("ftti_target_ms", 999.0)
    crc_th = params.get("crc_fault_threshold", 99)
    tau = params.get("filter_tau_ms", 999.0)
    temp = params.get("coolant_trip_temp_c", 999.0)
    
    if ftti > SAFETY_INVARIANTS["MAX_ALLOWED_FTTI_MS"]:
        logger.error(f"[{profile_id}] 標定違規：FTTI {ftti}ms > 上限 {SAFETY_INVARIANTS['MAX_ALLOWED_FTTI_MS']}ms！")
        return False
    if crc_th > SAFETY_INVARIANTS["MAX_CRC_FAULT_THRESHOLD"]:
        logger.error(f"[{profile_id}] 標定違規：CRC 容錯次數 {crc_th} > 上限 {SAFETY_INVARIANTS['MAX_CRC_FAULT_THRESHOLD']}！")
        return False
    if tau > SAFETY_INVARIANTS["MAX_FILTER_TAU_MS"]:
        logger.error(f"[{profile_id}] 標定違規：濾波時常數 {tau}ms > 上限 {SAFETY_INVARIANTS['MAX_FILTER_TAU_MS']}ms！")
        return False
    if temp > SAFETY_INVARIANTS["MAX_COOLANT_TEMP_LIMIT_C"]:
        logger.error(f"[{profile_id}] 標定違規：跳脫水溫 {temp}°C > 上限 {SAFETY_INVARIANTS['MAX_COOLANT_TEMP_LIMIT_C']}°C！")
        return False
        
    logger.info(f"[{profile_id}] 標定參數校驗通過，符合 ASIL-D 安全邊界。")
    return True


def generate_a2l_file(output_path: str) -> None:
    """生成 ASAM MCD-2 MC 標準 A2L 描述檔案"""
    a2l_content = f"""ASAP2_VERSION 1 71
/begin PROJECT AutoCopilot_Industrial_ECU "AutoCopilot ASIL-D Calibration Description"
  /begin HEADER "AutoCopilot SOP 2028 Calibration"
    VERSION "4.0.0"
  /end HEADER
  /begin MODULE AutoCopilot_Core ""
    /begin CHARACTERISTIC FTTI_Target_Limit "Maximum Fault Tolerant Time Interval"
      VALUE 0x001000 ULONG 0.0 40.0
      FORMAT "%4.1f"
      UNIT "ms"
    /end CHARACTERISTIC
    /begin CHARACTERISTIC CRC_Fault_Threshold "Continuous CRC-8 Error Threshold"
      VALUE 0x001004 UBYTE 1.0 3.0
      FORMAT "%1.0f"
      UNIT "frames"
    /end CHARACTERISTIC
    /begin CHARACTERISTIC Max_Safe_Torque "Upper Bound Safe Torque"
      VALUE 0x001008 FLOAT 0.0 700.0
      FORMAT "%5.1f"
      UNIT "Nm"
    /end CHARACTERISTIC
  /end MODULE
/end PROJECT
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(a2l_content)
    logger.info(f"ASAM MCD-2 MC A2L 檔案已生成: {output_path}")


def freeze_calibration_baseline() -> Dict[str, Any]:
    """凍結多車型標定基線，生成 JSON 與 A2L 檔案"""
    logger.info("啟動 AutoCopilot 標定資料庫 (CDF/A2L) 基線凍結...")
    
    baseline = {
        "baseline_title": "AutoCopilot ASIL-D Multi-Vehicle Calibration Baseline",
        "frozen_at": datetime.now().isoformat(),
        "asild_safety_invariants": SAFETY_INVARIANTS,
        "profiles": {}
    }
    
    for pid, params in DEFAULT_VEHICLE_CALIBRATIONS.items():
        is_valid = validate_calibration(pid, params)
        if not is_valid:
            raise ValueError(f"Profile {pid} violated safety boundary!")
        baseline["profiles"][pid] = {
            "validation_status": "COMPLIANT_ASIL_D",
            **params
        }
        
    json_path = os.path.join(CALIB_DIR, "AUTOCP_CALIBRATION_MATRIX.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2, ensure_ascii=False)
        
    a2l_path = os.path.join(CALIB_DIR, "AutoCopilot_Core.a2l")
    generate_a2l_file(a2l_path)
    
    logger.info(f"標定基線凍結成功！包含 {len(baseline['profiles'])} 大車型設定。")
    return baseline


if __name__ == "__main__":
    res = freeze_calibration_baseline()
    print("\n=== AutoCopilot 車型標定基線矩陣 (Calibration Baseline) ===")
    print(f"發行標題: {res['baseline_title']}")
    print(f"凍結時間: {res['frozen_at']}")
    print("----------------------------------------------------------")
    for pid, pdata in res["profiles"].items():
        print(f"[{pdata['validation_status']}] {pid} ({pdata['profile_name']})")
        print(f"    FTTI: {pdata['ftti_target_ms']} ms | CRC 閥值: {pdata['crc_fault_threshold']} 幀 | 扭矩上限: {pdata['max_safe_torque_nm']} Nm")
    print("==========================================================")
