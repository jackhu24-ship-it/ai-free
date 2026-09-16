"""
fault_injector.py - ASIL-B 硬體與總線故障注入引擎 (Fault Injection Framework)
支援：Pin-Level 開路/短路、CAN/LIN 泛洪與 CRC 錯亂、跨通道偏差注入
"""
from __future__ import annotations
import time
from typing import Callable, Dict, Any

class HardwareFaultInjector:
    def __init__(self):
        self.active_faults: Dict[str, Any] = {}
        self.injection_history = []

    def inject_pin_fault(self, channel: int, fault_type: str, duration_ms: int = 100):
        """模擬引腳對地短路 (GND)、對電源短路 (BAT+) 或開路 (OPEN)"""
        key = f"PIN_CH_{channel}"
        self.active_faults[key] = {
            "type": fault_type,
            "start": time.time(),
            "duration": duration_ms
        }
        self.injection_history.append((key, fault_type))

    def inject_bus_corruption(self, bus_id: str, mode: str = "CRC_ERROR"):
        """模擬 CAN FD / LIN 總線 CRC 錯誤或節點沉默"""
        self.active_faults[f"BUS_{bus_id}"] = mode
        self.injection_history.append((bus_id, mode))

    def clear_all(self):
        self.active_faults.clear()
