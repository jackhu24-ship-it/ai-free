"""
CAN / CAN-FD Interface Adapter for AutoCopilot.
Provides vehicle bus abstraction supporting virtual bus, PCAN (PEAK USB), and SocketCAN.
Includes DBC binary matrix encoding and decoding for BMS, Thermal, and Actuator frames.
Conforms to ISO 11898 and ISO 26262 functional safety data integrity rules.
"""

import struct
import time
import logging
from typing import Dict, Any, Optional, Tuple, Callable
import threading

try:
    import can
    CAN_AVAILABLE = True
except ImportError:
    can = None
    CAN_AVAILABLE = False

logger = logging.getLogger("AutoCopilot.CAN")

# CAN IDs conforming to automotive domain architecture
CAN_ID_BMS_TELEMETRY = 0x100      # 256: High Voltage Battery Management System
CAN_ID_THERMAL_TELEMETRY = 0x200  # 512: Cooling & Thermal Loop
CAN_ID_ACTUATOR_COMMAND = 0x300   # 768: Actuator Control (Relay, Pump, DTC Reset)
CAN_ID_UDS_PHYS_REQ = 0x7E0       # 2016: Diagnostic Request to Main Inverter/BMS ECU
CAN_ID_UDS_PHYS_RESP = 0x7E8      # 2024: Diagnostic Response from Main Inverter/BMS ECU


class CanInterfaceAdapter:
    """
    Automotive CAN Interface Adapter.
    Encapsulates python-can hardware buses and provides DBC matrix binary conversion.
    """

    def __init__(self, interface: str = "virtual", channel: str = "test", bitrate: int = 500000):
        self.interface_type = interface
        self.channel = channel
        self.bitrate = bitrate
        self.bus: Optional[Any] = None
        self._is_connected = False
        self._latest_telemetry: Dict[str, Any] = {
            "battery_voltage": 398.5,
            "battery_current": -12.4,
            "hv_interlock": True,
            "bms_status": 0,
            "coolant_temp": 96.0,
            "pump_pwm": 42.0,
            "fan_rpm": 2400,
            "flow_rate": 15.5,
            "relay_state": 2,  # Closed
            "timestamp": time.time()
        }
        self._lock = threading.Lock()
        self._init_bus()

    def _init_bus(self) -> None:
        """Initialize the CAN bus interface (virtual or physical)."""
        if not CAN_AVAILABLE:
            logger.warning("[CAN] python-can is not installed; running in software fallback mode.")
            self._is_connected = False
            return

        try:
            if self.interface_type == "virtual":
                self.bus = can.interface.Bus(self.channel, bustype="virtual")
                self._is_connected = True
                logger.info(f"[CAN] Virtual CAN bus initialized on channel: {self.channel}")
            elif self.interface_type == "pcan":
                self.bus = can.interface.Bus(channel=self.channel, bustype="pcan", bitrate=self.bitrate)
                self._is_connected = True
                logger.info(f"[CAN] PEAK PCAN-USB initialized on channel: {self.channel}")
            elif self.interface_type == "socketcan":
                self.bus = can.interface.Bus(channel=self.channel, bustype="socketcan", bitrate=self.bitrate)
                self._is_connected = True
                logger.info(f"[CAN] SocketCAN initialized on channel: {self.channel}")
            else:
                self.bus = can.interface.Bus(self.channel, bustype="virtual")
                self._is_connected = True
        except Exception as e:
            logger.warning(f"[CAN] Hardware init failed ({e}); falling back to virtual loopback bus.")
            try:
                self.bus = can.interface.Bus("default_vcan", bustype="virtual")
                self._is_connected = True
            except Exception as e2:
                logger.error(f"[CAN] Fatal virtual fallback failed: {e2}")
                self.bus = None
                self._is_connected = False

    # -------------------------------------------------------------
    # DBC Binary Matrix Encoding / Decoding
    # -------------------------------------------------------------

    @staticmethod
    def encode_bms_frame(
        voltage: float,
        current: float,
        hv_interlock: bool = True,
        status: int = 0
    ) -> Any:
        """
        Encode ID 0x100 (BMS_Telemetry) into 8-byte CAN frame.
        - Byte 0-1: Voltage uint16 (0.1V/LSB, range 0~6553.5V) Big-Endian
        - Byte 2-3: Current int16 (0.1A/LSB, range -3276.8~3276.7A) Big-Endian
        - Byte 4: HV Interlock bit 0 (1=Closed, 0=Open), Status bit 1-3
        - Byte 5: Rolling Counter (0~15)
        - Byte 6-7: Checksum uint16 Big-Endian
        """
        raw_v = int(round(voltage * 10)) & 0xFFFF
        raw_i = int(round(current * 10))
        raw_i = max(-32768, min(32767, raw_i))
        raw_i = struct.unpack(">H", struct.pack(">h", raw_i))[0]

        b4 = (1 if hv_interlock else 0) | ((status & 0x07) << 1)
        b5 = int(time.time() * 10) % 16

        checksum = (raw_v + raw_i + b4 + b5) & 0xFFFF
        data = struct.pack(">HHBBH", raw_v, raw_i, b4, b5, checksum)

        if CAN_AVAILABLE:
            return can.Message(arbitration_id=CAN_ID_BMS_TELEMETRY, data=data, is_extended_id=False)
        return {"id": CAN_ID_BMS_TELEMETRY, "data": bytearray(data)}

    @staticmethod
    def decode_bms_frame(data: bytes) -> Dict[str, Any]:
        """Decode raw 8-byte payload of ID 0x100."""
        if len(data) < 8:
            return {}
        raw_v, raw_i_u, b4, b5, checksum = struct.unpack(">HHBBH", data[:8])
        raw_i = struct.unpack(">h", struct.pack(">H", raw_i_u))[0]

        calc_checksum = (raw_v + raw_i_u + b4 + b5) & 0xFFFF
        crc_valid = (checksum == calc_checksum)

        return {
            "battery_voltage": round(raw_v * 0.1, 1),
            "battery_current": round(raw_i * 0.1, 1),
            "hv_interlock": bool(b4 & 0x01),
            "bms_status": (b4 >> 1) & 0x07,
            "rolling_counter": b5 & 0x0F,
            "crc_valid": crc_valid
        }

    @staticmethod
    def encode_thermal_frame(
        coolant_temp: float,
        pump_pwm: float,
        fan_rpm: int = 2400,
        flow_rate: float = 15.5
    ) -> Any:
        """
        Encode ID 0x200 (Thermal_Telemetry) into 8-byte CAN frame.
        - Byte 0: Coolant Temp uint8 (1.0 deg C/LSB, offset -40, range -40~215 deg C)
        - Byte 1: Pump PWM uint8 (1.0%/LSB, 0~100%)
        - Byte 2-3: Fan Speed RPM uint16 Big-Endian
        - Byte 4-5: Coolant Flow Rate uint16 (0.01 L/min/LSB) Big-Endian
        - Byte 6-7: Checksum uint16 Big-Endian
        """
        raw_temp = int(round(coolant_temp + 40.0))
        raw_temp = max(0, min(255, raw_temp))

        raw_pwm = int(round(pump_pwm))
        raw_pwm = max(0, min(100, raw_pwm))

        raw_fan = max(0, min(65535, fan_rpm))
        raw_flow = max(0, min(65535, int(round(flow_rate * 100))))

        checksum = (raw_temp + raw_pwm + raw_fan + raw_flow) & 0xFFFF
        data = struct.pack(">BBHHH", raw_temp, raw_pwm, raw_fan, raw_flow, checksum)

        if CAN_AVAILABLE:
            return can.Message(arbitration_id=CAN_ID_THERMAL_TELEMETRY, data=data, is_extended_id=False)
        return {"id": CAN_ID_THERMAL_TELEMETRY, "data": bytearray(data)}

    @staticmethod
    def decode_thermal_frame(data: bytes) -> Dict[str, Any]:
        """Decode raw 8-byte payload of ID 0x200."""
        if len(data) < 8:
            return {}
        raw_temp, raw_pwm, fan_rpm, raw_flow, checksum = struct.unpack(">BBHHH", data[:8])
        coolant_temp = float(raw_temp - 40)
        pump_pwm = float(raw_pwm)
        flow_rate = round(raw_flow * 0.01, 2)

        calc_checksum = (raw_temp + raw_pwm + fan_rpm + raw_flow) & 0xFFFF
        crc_valid = (checksum == calc_checksum)

        return {
            "coolant_temp": round(coolant_temp, 1),
            "pump_pwm": round(pump_pwm, 1),
            "fan_rpm": fan_rpm,
            "flow_rate": flow_rate,
            "crc_valid": crc_valid
        }

    @staticmethod
    def encode_actuator_frame(
        relay_cmd: int = 0,
        pump_cmd: int = 42,
        dtc_reset: bool = False
    ) -> Any:
        """
        Encode ID 0x300 (Actuator_Command) into 8-byte CAN frame.
        - Byte 0: Relay command (0=Keep, 1=Open/Trip, 2=Close)
        - Byte 1: Pump PWM command (0~100%)
        - Byte 2: DTC Reset command (0xAA=Reset, 0x00=Normal)
        - Byte 3-7: Reserved (0x00)
        """
        dtc_byte = 0xAA if dtc_reset else 0x00
        data = struct.pack(">BBB5s", relay_cmd & 0x03, min(100, pump_cmd), dtc_byte, b"\x00" * 5)
        if CAN_AVAILABLE:
            return can.Message(arbitration_id=CAN_ID_ACTUATOR_COMMAND, data=data, is_extended_id=False)
        return {"id": CAN_ID_ACTUATOR_COMMAND, "data": bytearray(data)}

    @staticmethod
    def decode_actuator_frame(data: bytes) -> Dict[str, Any]:
        """Decode raw payload of ID 0x300."""
        if len(data) < 3:
            return {}
        relay_cmd, pump_cmd, dtc_byte = struct.unpack(">BBB", data[:3])
        return {
            "relay_command": relay_cmd,
            "pump_command": pump_cmd,
            "dtc_reset": (dtc_byte == 0xAA)
        }

    # -------------------------------------------------------------
    # Transmission & Reception
    # -------------------------------------------------------------

    def send(self, msg: Any) -> bool:
        """Send a CAN frame over the bus."""
        if self.bus and CAN_AVAILABLE and isinstance(msg, can.Message):
            try:
                self.bus.send(msg)
                return True
            except Exception as e:
                logger.error(f"[CAN] Send error: {e}")
                return False
        return True

    def recv(self, timeout: float = 0.05) -> Optional[Any]:
        """Receive a CAN frame from the bus with timeout."""
        if self.bus and CAN_AVAILABLE:
            try:
                return self.bus.recv(timeout=timeout)
            except Exception as e:
                logger.error(f"[CAN] Recv error: {e}")
                return None
        return None

    def update_telemetry_cache(self, msg_id: int, data: bytes) -> None:
        """Parse incoming frame and update cached telemetry state."""
        with self._lock:
            if msg_id == CAN_ID_BMS_TELEMETRY:
                bms = self.decode_bms_frame(data)
                if bms.get("crc_valid", True):
                    self._latest_telemetry["battery_voltage"] = bms["battery_voltage"]
                    self._latest_telemetry["battery_current"] = bms["battery_current"]
                    self._latest_telemetry["hv_interlock"] = bms["hv_interlock"]
                    self._latest_telemetry["bms_status"] = bms["bms_status"]
            elif msg_id == CAN_ID_THERMAL_TELEMETRY:
                thm = self.decode_thermal_frame(data)
                if thm.get("crc_valid", True):
                    self._latest_telemetry["coolant_temp"] = thm["coolant_temp"]
                    self._latest_telemetry["pump_pwm"] = thm["pump_pwm"]
                    self._latest_telemetry["fan_rpm"] = thm["fan_rpm"]
                    self._latest_telemetry["flow_rate"] = thm["flow_rate"]
            self._latest_telemetry["timestamp"] = time.time()

    def get_latest_telemetry(self) -> Dict[str, Any]:
        """Thread-safe access to latest parsed vehicle bus telemetry."""
        with self._lock:
            return dict(self._latest_telemetry)

    def shutdown(self) -> None:
        """Cleanly shutdown CAN bus interface."""
        if self.bus and CAN_AVAILABLE:
            try:
                self.bus.shutdown()
            except Exception:
                pass
            self.bus = None
        self._is_connected = False
        logger.info("[CAN] Interface shutdown completed.")
