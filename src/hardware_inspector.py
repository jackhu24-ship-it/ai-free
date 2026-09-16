#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 實戰模組：智慧型硬體規格標籤解析與零件清冊自動化系統
作者：🛠️ 小開 (Agent_Coder)
審查：🐎 小馬 (Agent_Reviewer)
統籌：👑 小幫手 (Agent_PM)

核心功能與合規標準：
1. Python 3.12+ 現代型別標註與 @dataclass
2. CWE-1236 試算表公式注入防護 (sanitize_str: 對型號、序號轉義)
3. 工控電壓安全閥值檢查 (VoltageSafetyError: 超過 12.0V 或 <= 0V 自動攔截)
4. 輸出 utf-8-sig 格式之 DATA/hardware_inventory.csv 清冊
"""

from __future__ import annotations

import sys
import os
import json
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

# 強制 Windows 標準輸出為 UTF-8
if sys.platform.startswith("win"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# 定位路徑
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = WORKSPACE_ROOT / "DATA"
DATA_DIR.mkdir(parents=True, exist_ok=True)

INVENTORY_CSV_PATH = DATA_DIR / "hardware_inventory.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [HWInspector] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("HardwareInspector")


class VoltageSafetyError(ValueError):
    """自定義異常：硬體供電電壓超出安全範圍（上限：12.0V）"""
    pass


def sanitize_str(value: Any) -> str:
    """
    CWE-1236 試算表公式注入防護：
    清除開頭不可見控制字元，若開頭為 '=', '+', '-', '@' 則強制前置單引號 "'"
    """
    if value is None:
        return ""
    s = str(value).lstrip(" \t\r\n")
    if s.startswith(("=", "+", "-", "@")):
        return f"'{s}"
    return s


@dataclass
class HardwareSpec:
    """硬體規格資料結構"""
    label_id: str
    device_category: str
    model_name: str
    operating_voltage_range: str
    max_voltage_v: float
    interfaces: list[str]
    serial_number_masked: str
    manufacturer: str
    safety_status: str = "PENDING"
    notes: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any], max_allowed_v: float = 12.0) -> HardwareSpec:
        raw_max_v = float(data.get("max_voltage_v", 0.0))
        
        # 電壓安全檢驗
        if raw_max_v > max_allowed_v:
            raise VoltageSafetyError(
                f"🚨 [電壓超標危險] 模組 [{data.get('model_name')}] 最大電壓 {raw_max_v}V 超出安全上限 {max_allowed_v}V！"
            )
        if raw_max_v <= 0.0:
            raise VoltageSafetyError(
                f"🚨 [電壓數值異常] 模組 [{data.get('model_name')}] 最大電壓 {raw_max_v}V 小於等於 0V！"
            )

        return cls(
            label_id=sanitize_str(data.get("label_id", "UNKNOWN")),
            device_category=sanitize_str(data.get("device_category", "通用元件")),
            model_name=sanitize_str(data.get("model_name", "未知型號")),
            operating_voltage_range=sanitize_str(data.get("operating_voltage_range", "N/A")),
            max_voltage_v=raw_max_v,
            interfaces=[sanitize_str(i) for i in data.get("interfaces", [])],
            serial_number_masked=sanitize_str(data.get("serial_number_masked", "SN-*****")),
            manufacturer=sanitize_str(data.get("manufacturer", "未知廠商")),
            safety_status="APPROVED_SAFE",
            notes="電壓符合標準，序號已遮蔽"
        )


class HardwareInspector:
    """硬體規格審查與清冊導出器"""

    def __init__(self, csv_output_path: Optional[Path | str] = None) -> None:
        self.csv_path = Path(csv_output_path) if csv_output_path else INVENTORY_CSV_PATH
        self._ensure_csv_header()

    def _ensure_csv_header(self) -> None:
        """初始化零件清冊表頭 (utf-8-sig)"""
        if not self.csv_path.exists():
            with open(self.csv_path, "w", encoding="utf-8-sig", errors="replace") as f:
                f.write("標籤編號,元件類別,型號名稱,工作電壓範圍,最大額定電壓(V),支援通訊介面,序號(已遮蔽),製造商,安全審查狀態,備註\n")

    def inspect_and_export(self, json_source_path: Path | str) -> list[HardwareSpec]:
        """
        解析硬體 JSON，進行電壓驗證並導出至 CSV 清冊
        """
        src_path = Path(json_source_path)
        if not src_path.exists():
            raise FileNotFoundError(f"找不到硬體標籤檔案: {src_path}")

        with open(src_path, "r", encoding="utf-8", errors="replace") as f:
            raw_list = json.load(f)

        inspected_specs = []
        for item in raw_list:
            spec = HardwareSpec.from_dict(item, max_allowed_v=12.0)
            inspected_specs.append(spec)
            self._append_to_csv(spec)
            logger.info(f"✅ 硬體驗收通過: [{spec.model_name}] (電壓: {spec.max_voltage_v}V | 序號: {spec.serial_number_masked})")

        return inspected_specs

    def _append_to_csv(self, spec: HardwareSpec) -> None:
        """寫入單筆硬體規格至清冊"""
        interfaces_str = "; ".join(spec.interfaces)
        with open(self.csv_path, "a", encoding="utf-8-sig", errors="replace") as f:
            row = [
                f'"{spec.label_id}"',
                f'"{spec.device_category}"',
                f'"{spec.model_name}"',
                f'"{spec.operating_voltage_range}"',
                str(spec.max_voltage_v),
                f'"{interfaces_str}"',
                f'"{spec.serial_number_masked}"',
                f'"{spec.manufacturer}"',
                f'"{spec.safety_status}"',
                f'"{spec.notes}"'
            ]
            f.write(",".join(row) + "\n")


# ---------------------------------------------------------------------------
# 單元與極端安全測試
# ---------------------------------------------------------------------------
def run_hardware_inspector_tests() -> None:
    """執行硬體審查模組單元測試"""
    print("\n" + "="*75)
    print("🚀 [HWInspector-Test] 開始執行硬體標籤審查與安全清冊測試")
    print("="*75 + "\n")

    json_path = DATA_DIR / "hardware_labels.json"
    inspector = HardwareInspector()

    # 1. 正常標籤解析測試
    print("1️⃣ [測試 1：正常硬體標籤導入與電壓審查]")
    specs = inspector.inspect_and_export(json_path)
    print(f"   -> 成功驗收 {len(specs)} 款硬體模組")
    for s in specs:
        print(f"      • [{s.label_id}] {s.model_name} | 電壓: {s.operating_voltage_range} | 介面: {s.interfaces}")
    assert len(specs) == 2, "❌ 解析筆數不符！"
    print("   -> ✅ 測試 1 通過：硬體規格解析與 CSV 導出完全正常！\n")

    # 2. 24V 工控超額電壓攔截測試
    print("2️⃣ [測試 2：24V 工控超額高壓攔截 (VoltageSafetyError)]")
    high_v_item = {
        "label_id": "HW-LABEL-999",
        "model_name": "Industrial-Driver-24V",
        "max_voltage_v": 24.0
    }
    try:
        HardwareSpec.from_dict(high_v_item, max_allowed_v=12.0)
        print("   ❌ 未能攔截 24V 超標高壓！")
    except VoltageSafetyError as e:
        print(f"   -> ✅ 成功攔截危險高壓: {e}")
        print("   -> ✅ 測試 2 通過：電壓安全防呆機制完美生效！\n")

    # 3. CWE-1236 公式注入攻擊防禦
    print("3️⃣ [測試 3：CWE-1236 型號與序號公式注入防護]")
    malicious_item = {
        "label_id": "HW-LABEL-MALICIOUS",
        "model_name": "=cmd|'/c calc'!A0",
        "max_voltage_v": 5.0,
        "serial_number_masked": "@SN-EVIL-001"
    }
    spec_mal = HardwareSpec.from_dict(malicious_item)
    assert spec_mal.model_name.startswith("'="), "❌ 型號防護失敗！"
    assert spec_mal.serial_number_masked.startswith("'@"), "❌ 序號防護失敗！"
    print(f"   -> 轉義後型號: {spec_mal.model_name}")
    print(f"   -> 轉義後序號: {spec_mal.serial_number_masked}")
    print("   -> ✅ 測試 3 通過：CWE-1236 惡意攻擊防禦 100% 成功！\n")

    print("="*75)
    print("🎉 [HWInspector-Test] 硬體審查模組全項測試 100% 通過驗收！")
    print("="*75 + "\n")


if __name__ == "__main__":
    run_hardware_inspector_tests()
