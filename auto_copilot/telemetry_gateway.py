"""
AutoCopilot CAN / OBD-II Telemetry Gateway
Provides simulated and live physical metrics & DTC fault codes.
"""

import time
import random
from typing import Dict, Any, List, Optional
from .schemas import SubsystemType, MetricKeyType, EcuTargetType

class TelemetryGateway:
    """
    CAN/OBD-II Telemetry & Diagnostic Gateway.
    Simulates real-time ECU bus data with safety thresholds.
    """
    def __init__(self):
        # 基準遙測狀態
        self._metrics: Dict[str, float] = {
            "coolant_temp_c": 103.5,            # 冷卻液溫度 (接近 105 警告線)
            "inverter_temp_c": 68.2,             # 逆變器溫度
            "bus_voltage_v": 398.4,              # 高壓母線電壓
            "motor_rpm": 3250.0,                 # 馬達轉速
            "coolant_line_pressure_kpa": 142.0,  # 冷卻管路壓力
            "pack_soc_percent": 76.5             # 電池電量 SoC
        }
        
        # 子系統與指標對應
        self._subsystem_map: Dict[SubsystemType, List[MetricKeyType]] = {
            "thermal_management": ["coolant_temp_c", "inverter_temp_c", "coolant_line_pressure_kpa"],
            "powertrain": ["motor_rpm", "inverter_temp_c"],
            "battery_pack": ["bus_voltage_v", "pack_soc_percent"],
            "chassis_brakes": ["bus_voltage_v"]
        }

        # 診斷故障碼 (DTC) 資料庫 (符合 ISO 14229 / SAE J2012)
        self._dtc_database: List[Dict[str, Any]] = [
            {
                "code": "P0117",
                "ecu": "engine_control",
                "status": "active",
                "description": "Engine Coolant Temperature Sensor 1 Circuit Low",
                "severity": "high",
                "freeze_frame": {
                    "coolant_temp_c": 103.5,
                    "engine_load_pct": 78.4,
                    "rpm": 3250.0,
                    "vehicle_speed_kmh": 65.0,
                    "timestamp": time.time() - 120
                }
            },
            {
                "code": "U0100",
                "ecu": "battery_management",
                "status": "pending",
                "description": "Lost Communication With ECM/PCM 'A'",
                "severity": "medium",
                "freeze_frame": {
                    "bus_voltage_v": 398.4,
                    "timestamp": time.time() - 300
                }
            }
        ]

    def set_metric(self, key: str, value: float) -> None:
        """動態更新指定指標值 (可用於測試與示波器模擬)"""
        if key in self._metrics:
            self._metrics[key] = value

    def get_all_metrics(self) -> Dict[str, Any]:
        """讀取全量遙測狀態 (含時間戳與狀態判定)"""
        # 加上微小即時波動
        jitter = (random.random() - 0.5) * 0.2
        metrics = {k: round(v + jitter, 2) for k, v in self._metrics.items()}
        
        # 評估健康狀態
        status = "normal"
        if metrics["coolant_temp_c"] >= 105.0:
            status = "CRITICAL_SHUTDOWN_REQUIRED"
        elif metrics["coolant_temp_c"] >= 100.0:
            status = "warning_high_temperature"

        return {
            "timestamp": time.time(),
            "overall_status": status,
            "metrics": metrics
        }

    async def get_vehicle_telemetry(
        self,
        subsystem: SubsystemType,
        metric_keys: List[MetricKeyType]
    ) -> Dict[str, Any]:
        """
        Tool 1 實作：讀取特定子系統與感測器指標
        """
        results: Dict[str, Any] = {}
        for key in metric_keys:
            if key in self._metrics:
                # 加上微小波動保持即時感
                val = round(self._metrics[key] + (random.random() - 0.5) * 0.1, 2)
                results[key] = val
        
        # 針對冷卻液溫度的特定警示標註
        status = "normal"
        coolant_temp = results.get("coolant_temp_c", self._metrics["coolant_temp_c"])
        if coolant_temp >= 105.0:
            status = "critical"
        elif coolant_temp >= 100.0:
            status = "warning"

        return {
            "subsystem": subsystem,
            "status": status,
            "data": results,
            "source": "CAN_BUS_GATEWAY_NODE_0x1A"
        }

    async def read_diagnostic_trouble_codes(
        self,
        ecu_target: EcuTargetType = "all",
        include_snapshot_data: bool = False
    ) -> Dict[str, Any]:
        """
        Tool 2 實作：查詢 DTC 故障代碼
        """
        matched_dtcs: List[Dict[str, Any]] = []
        for dtc in self._dtc_database:
            if ecu_target == "all" or dtc["ecu"] == ecu_target:
                item = {
                    "code": dtc["code"],
                    "ecu": dtc["ecu"],
                    "status": dtc["status"],
                    "description": dtc["description"],
                    "severity": dtc["severity"]
                }
                if include_snapshot_data:
                    item["freeze_frame"] = dtc.get("freeze_frame", {})
                matched_dtcs.append(item)

        return {
            "ecu_target": ecu_target,
            "total_dtcs": len(matched_dtcs),
            "codes": matched_dtcs,
            "protocol": "ISO 14229 (UDS on CAN-FD)"
        }


# 全域單例
telemetry_gateway = TelemetryGateway()
