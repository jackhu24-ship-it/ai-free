"""
AutoCopilot CAN & DBC Matrix Decoder Interface
Supports python-can virtual/hardware buses and standard automotive DBC decoding.
"""

import struct
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("AutoCopilot.CAN")

# CAN ID 映射表
CAN_ID_COOLANT_METRICS = 0x120
CAN_ID_INVERTER_METRICS = 0x130
CAN_ID_MOTOR_METRICS = 0x140
CAN_ID_UDS_DIAGNOSTIC = 0x7E8

class CANSignalDefinition:
    """Represents a standard DBC signal definition (StartBit, Length, Factor, Offset)."""
    def __init__(self, name: str, start_byte: int, length_bytes: int, factor: float, offset: float, unit: str):
        self.name = name
        self.start_byte = start_byte
        self.length_bytes = length_bytes
        self.factor = factor
        self.offset = offset
        self.unit = unit

class CANMessageDecoder:
    """
    Decodes standard raw CAN frames (ID + 8-byte payload) into physical engineering values.
    """
    def __init__(self):
        # 訊號規格字典
        self.signals = {
            # 0x120: Coolant Temp (uint16, factor 0.1, offset -40.0), Pressure (uint16, factor 1.0, offset 0.0)
            CAN_ID_COOLANT_METRICS: [
                CANSignalDefinition("coolant_temp_c", 0, 2, 0.1, -40.0, "°C"),
                CANSignalDefinition("coolant_line_pressure_kpa", 2, 2, 1.0, 0.0, "kPa"),
            ],
            # 0x130: Inverter Temp (uint16, factor 0.1, offset -40.0), Bus Voltage (uint16, factor 0.1, offset 0.0)
            CAN_ID_INVERTER_METRICS: [
                CANSignalDefinition("inverter_temp_c", 0, 2, 0.1, -40.0, "°C"),
                CANSignalDefinition("bus_voltage_v", 2, 2, 0.1, 0.0, "V"),
            ],
            # 0x140: Motor RPM (uint16, factor 1.0, offset 0.0)
            CAN_ID_MOTOR_METRICS: [
                CANSignalDefinition("motor_rpm", 0, 2, 1.0, 0.0, "RPM"),
            ]
        }

    def encode_frame(self, arbitration_id: int, physical_values: Dict[str, float]) -> bytes:
        """根據物理數值打包成 8-byte CAN Payload"""
        payload = bytearray(8)
        defs = self.signals.get(arbitration_id, [])
        for sig in defs:
            if sig.name in physical_values:
                val = physical_values[sig.name]
                raw_int = int((val - sig.offset) / sig.factor)
                if sig.length_bytes == 2:
                    struct.pack_into(">H", payload, sig.start_byte, max(0, min(65535, raw_int)))
                elif sig.length_bytes == 1:
                    struct.pack_into(">B", payload, sig.start_byte, max(0, min(255, raw_int)))
        return bytes(payload)

    def decode_frame(self, arbitration_id: int, payload: bytes) -> Dict[str, Any]:
        """將 8-byte CAN Payload 解碼為物理量工程數值"""
        results: Dict[str, Any] = {}
        defs = self.signals.get(arbitration_id, [])
        for sig in defs:
            if len(payload) >= sig.start_byte + sig.length_bytes:
                if sig.length_bytes == 2:
                    (raw_int,) = struct.unpack_from(">H", payload, sig.start_byte)
                elif sig.length_bytes == 1:
                    (raw_int,) = struct.unpack_from(">B", payload, sig.start_byte)
                else:
                    raw_int = 0
                phys_val = round(raw_int * sig.factor + sig.offset, 2)
                results[sig.name] = phys_val
        return results


class CANBusInterface:
    """
    High-level CAN Interface coordinating raw frame processing.
    """
    def __init__(self):
        self.decoder = CANMessageDecoder()
        self.latest_telemetry: Dict[str, float] = {
            "coolant_temp_c": 103.8,
            "coolant_line_pressure_kpa": 142.5,
            "inverter_temp_c": 64.2,
            "bus_voltage_v": 384.2,
            "motor_rpm": 2450.0
        }

    def process_incoming_frame(self, arbitration_id: int, payload: bytes) -> Dict[str, Any]:
        """接收並處理 CAN 訊框"""
        decoded = self.decoder.decode_frame(arbitration_id, payload)
        self.latest_telemetry.update(decoded)
        return decoded

    def generate_mock_can_stream(self) -> Dict[int, bytes]:
        """生成模擬 CAN 訊框映射 (用於離線與無實體 CAN 卡環境)"""
        return {
            CAN_ID_COOLANT_METRICS: self.decoder.encode_frame(CAN_ID_COOLANT_METRICS, self.latest_telemetry),
            CAN_ID_INVERTER_METRICS: self.decoder.encode_frame(CAN_ID_INVERTER_METRICS, self.latest_telemetry),
            CAN_ID_MOTOR_METRICS: self.decoder.encode_frame(CAN_ID_MOTOR_METRICS, self.latest_telemetry)
        }


# 全域單例
can_bus_interface = CANBusInterface()
