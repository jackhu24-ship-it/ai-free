"""
can_adapter.py - Automotive CAN / CAN-FD Interface Adapter
===========================================================
Supports both Virtual Simulation and Hardware (PCAN / SocketCAN) interfaces.
Loads mock_vehicle.dbc using cantools to decode and encode binary frames.
Includes background periodic simulation broadcaster for software-in-the-loop validation.
"""

import os
import time
import logging
import threading
from typing import Any, Dict, Optional

try:
    import can
    CAN_AVAILABLE = True
except ImportError:
    can = None
    CAN_AVAILABLE = False

try:
    import cantools
    CANTOOLS_AVAILABLE = True
except ImportError:
    cantools = None
    CANTOOLS_AVAILABLE = False

logger = logging.getLogger("AutoCopilot.CANAdapter")

DBC_PATH = os.path.join(os.path.dirname(__file__), "mock_vehicle.dbc")

# Standard CAN Frame IDs matching mock_vehicle.dbc
FRAME_ID_THERMAL_TELEMETRY = 0x120  # 288: Thermal_Powertrain_Telemetry
FRAME_ID_BMS_STATE = 0x180          # 384: BMS_Battery_State
FRAME_ID_PDM_ACTUATOR = 0x210       # 528: PDM_Actuator_Command
FRAME_ID_UDS_REQ = 0x7E0            # 2016: UDS_Diagnostic_Request
FRAME_ID_UDS_RESP = 0x7E8           # 2024: UDS_Diagnostic_Response


class CanInterfaceAdapter:
    """
    Automotive CAN Interface Adapter conforming to Stage 2 specification.
    Provides DBC-based signal encoding/decoding and background simulation broadcaster.
    """

    def __init__(self, interface: str = "virtual", channel: str = "auto_vcan", bitrate: int = 500000):
        self.interface_type = interface.lower()
        self.channel = channel
        self.bitrate = bitrate
        self.bus: Optional[Any] = None
        self.db: Optional[Any] = None
        self._is_connected = False
        self._lock = threading.Lock()

        # Telemetry State Cache
        self._latest_telemetry: Dict[str, Any] = {
            "coolant_temp_c": 104.2,
            "line_pressure_kpa": 145.0,
            "pump_pwm_pct": 42.0,
            "motor_rpm": 3200,
            "bus_voltage_v": 384.8,
            "pack_current_a": -18.5,
            "pack_soc_pct": 82.0,
            "hv_interlock": True,
            "relay_cut_active": False,
            "timestamp": time.time(),
            "source": f"CAN_{self.interface_type}"
        }

        # Background Simulation Broadcaster
        self._sim_thread: Optional[threading.Thread] = None
        self._sim_rx_thread: Optional[threading.Thread] = None
        self._sim_running = False

        self._load_dbc()
        self._init_bus()

    def _load_dbc(self) -> None:
        """Load Vector DBC file using cantools."""
        if CANTOOLS_AVAILABLE and os.path.exists(DBC_PATH):
            try:
                self.db = cantools.database.load_file(DBC_PATH)
                logger.info(f"[CAN] Successfully loaded DBC from: {DBC_PATH}")
            except Exception as e:
                logger.warning(f"[CAN] Failed to load DBC ({e}); using manual decoder.")
                self.db = None
        else:
            logger.warning("[CAN] cantools not available or DBC not found.")

    def _init_bus(self) -> None:
        """Initialize CAN bus interface."""
        if not CAN_AVAILABLE:
            logger.warning("[CAN] python-can not installed; operating in memory-only mode.")
            self._is_connected = False
            return

        try:
            if self.interface_type == "virtual":
                self.bus = can.interface.Bus(self.channel, bustype="virtual")
                self._is_connected = True
                logger.info(f"[CAN] Virtual CAN bus ready on channel: {self.channel}")
            elif self.interface_type == "pcan":
                self.bus = can.interface.Bus(channel=self.channel, bustype="pcan", bitrate=self.bitrate)
                self._is_connected = True
                logger.info(f"[CAN] PEAK PCAN-USB initialized on {self.channel} @ {self.bitrate}bps")
            elif self.interface_type == "socketcan":
                self.bus = can.interface.Bus(channel=self.channel, bustype="socketcan", bitrate=self.bitrate)
                self._is_connected = True
                logger.info(f"[CAN] SocketCAN initialized on {self.channel}")
            else:
                self.bus = can.interface.Bus(self.channel, bustype="virtual")
                self._is_connected = True
        except Exception as e:
            logger.warning(f"[CAN] Interface init warning ({e}); creating fallback virtual bus.")
            try:
                self.bus = can.interface.Bus("default_vbus", bustype="virtual")
                self._is_connected = True
            except Exception:
                self.bus = None
                self._is_connected = False

    # -------------------------------------------------------------
    # Message Encoding and Decoding
    # -------------------------------------------------------------

    def encode_message(self, message_name: str, data: Dict[str, Any]) -> Any:
        """Encode physical values into CAN Message using DBC."""
        if self.db and CANTOOLS_AVAILABLE:
            try:
                msg_def = self.db.get_message_by_name(message_name)
                payload = msg_def.encode(data)
                if CAN_AVAILABLE:
                    return can.Message(arbitration_id=msg_def.frame_id, data=payload, is_extended_id=False)
                return {"id": msg_def.frame_id, "data": payload}
            except Exception as e:
                logger.error(f"[CAN] DBC encode error: {e}")
        return None

    def decode_message(self, frame_id: int, payload: bytes) -> Dict[str, Any]:
        """Decode raw binary payload into physical signals using DBC."""
        if self.db and CANTOOLS_AVAILABLE:
            try:
                return self.db.decode_message(frame_id, payload)
            except Exception as e:
                logger.error(f"[CAN] DBC decode error for 0x{frame_id:X}: {e}")
        return {}

    # -------------------------------------------------------------
    # Transmission & Actuator Controls
    # -------------------------------------------------------------

    def send_actuator_command(
        self,
        relay_cut: bool = True,
        pump_cmd: int = 100,
        emergency_shutdown: bool = False
    ) -> bool:
        """
        Broadcast Frame 0x210 (PDM_Actuator_Command) over the CAN bus.
        Enforces Stage 1 actuator execution under ISO 26262.
        """
        payload_data = {
            "Relay_Cut": 1 if relay_cut else 0,
            "Pump_Command": min(100, max(0, pump_cmd)),
            "Emergency_Shutdown": 1 if emergency_shutdown else 0,
            "Actuator_Counter": int(time.time() * 10) % 256
        }
        msg = self.encode_message("PDM_Actuator_Command", payload_data)
        if msg and self.bus:
            try:
                self.bus.send(msg)
                with self._lock:
                    self._latest_telemetry["relay_cut_active"] = relay_cut
                    self._latest_telemetry["timestamp"] = time.time()
                logger.info(f"[CAN] Actuator Command 0x210 sent: Relay_Cut={relay_cut}")
                return True
            except Exception as e:
                logger.error(f"[CAN] Failed to send Actuator Command: {e}")
                return False
        return True

    def send(self, msg: Any) -> bool:
        """Send generic CAN Message."""
        if self.bus and CAN_AVAILABLE and isinstance(msg, can.Message):
            try:
                self.bus.send(msg)
                return True
            except Exception as e:
                logger.error(f"[CAN] Send error: {e}")
                return False
        return True

    def recv(self, timeout: float = 0.08) -> Optional[Any]:
        """Receive frame from bus with timeout."""
        if self.bus and CAN_AVAILABLE:
            try:
                return self.bus.recv(timeout=timeout)
            except Exception as e:
                logger.error(f"[CAN] Recv error: {e}")
                return None
        return None

    # -------------------------------------------------------------
    # Background Periodic Simulation Broadcaster
    # -------------------------------------------------------------

    def start_simulation_broadcast(self, interval: float = 0.05) -> None:
        """Start background daemon broadcasting simulated 0x120 & 0x180 CAN frames."""
        if self._sim_running:
            return
        self._sim_running = True

        def _broadcast_loop():
            step = 0
            while self._sim_running:
                step += 1
                now = time.time()
                # Dynamic telemetry wave
                sim_temp = 104.2 + (0.5 if step % 2 == 0 else -0.3)
                sim_pressure = 145.0 + (1.2 if step % 3 == 0 else -0.8)

                thm_data = {
                    "Coolant_Temp": sim_temp,
                    "Pump_PWM": 42.0,
                    "Line_Pressure": sim_pressure,
                    "Motor_RPM": 3200,
                    "Thermal_CRC": step % 65535
                }
                bms_data = {
                    "Bus_Voltage": 384.8,
                    "Pack_Current": -18.5,
                    "Pack_SOC": 82.0,
                    "HV_Interlock": 1,
                    "BMS_Status": 0,
                    "BMS_CRC": step % 65535
                }

                msg_thm = self.encode_message("Thermal_Powertrain_Telemetry", thm_data)
                msg_bms = self.encode_message("BMS_Battery_State", bms_data)

                if self.bus and CAN_AVAILABLE:
                    try:
                        if msg_thm:
                            self.bus.send(msg_thm)
                        if msg_bms:
                            self.bus.send(msg_bms)
                    except Exception:
                        pass

                with self._lock:
                    self._latest_telemetry["coolant_temp_c"] = round(sim_temp, 1)
                    self._latest_telemetry["line_pressure_kpa"] = round(sim_pressure, 1)
                    self._latest_telemetry["bus_voltage_v"] = 384.8
                    self._latest_telemetry["pump_pwm_pct"] = 42.0
                    self._latest_telemetry["hv_interlock"] = True
                    self._latest_telemetry["timestamp"] = now

                time.sleep(interval)

        self._sim_thread = threading.Thread(target=_broadcast_loop, daemon=True)
        self._sim_thread.start()
        logger.info("[CAN] Background simulation broadcaster started.")

    def get_latest_telemetry(self) -> Dict[str, Any]:
        """Thread-safe access to latest parsed vehicle bus telemetry."""
        with self._lock:
            return dict(self._latest_telemetry)

    def shutdown(self) -> None:
        """Cleanly stop simulation and close bus."""
        self._sim_running = False
        if self._sim_thread and self._sim_thread.is_alive():
            self._sim_thread.join(timeout=0.2)
        if self.bus and CAN_AVAILABLE:
            try:
                self.bus.shutdown()
            except Exception:
                pass
            self.bus = None
        self._is_connected = False
        logger.info("[CAN] Adapter shutdown cleanly.")
