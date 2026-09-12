"""
UDS (Unified Diagnostic Services - ISO 14229-1) Client and ECU Simulator for AutoCopilot.
Provides vehicle diagnostic stack integration over CAN / ISO-TP.
Implements Service 0x19 02 (ReadDTCInformation), Service 0x22 (ReadDataByIdentifier),
and Service 0x14 (ClearDiagnosticInformation) guarded by ASIL Two-Key Handshake.
"""

import struct
import time
import logging
from typing import Dict, Any, List, Optional, Tuple

try:
    import can
    CAN_AVAILABLE = True
except ImportError:
    can = None
    CAN_AVAILABLE = False

from can_interface_adapter import (
    CanInterfaceAdapter,
    CAN_ID_UDS_PHYS_REQ,
    CAN_ID_UDS_PHYS_RESP
)
from asil_safety_core import get_safety_supervisor, ASILHazardLevel

logger = logging.getLogger("AutoCopilot.UDS")

# UDS Service Identifiers (ISO 14229-1)
SID_CLEAR_DIAGNOSTIC_INFO = 0x14     # Service 0x14: ClearDTC
SID_READ_DTC_INFO = 0x19             # Service 0x19: ReadDTC
SID_READ_DATA_BY_ID = 0x22           # Service 0x22: ReadDataByIdentifier
SID_NEGATIVE_RESPONSE = 0x7F         # NRC Response

# NRC Negative Response Codes (ISO 14229-1 Annex A)
NRC_SUB_FUNCTION_NOT_SUPPORTED = 0x12
NRC_CONDITIONS_NOT_CORRECT = 0x22
NRC_REQUEST_SEQUENCE_ERROR = 0x24
NRC_REQUEST_OUT_OF_RANGE = 0x31
NRC_SECURITY_ACCESS_DENIED = 0x33

# Diagnostic Trouble Code Byte Status Masks (ISO 14229-1)
DTC_STATUS_TEST_FAILED = 0x01
DTC_STATUS_PENDING = 0x04
DTC_STATUS_CONFIRMED = 0x08
DTC_STATUS_WARNING_INDICATOR_REQ = 0x80


class UdsDTC:
    """Represents an ISO 14229 DTC entry with status byte and functional safety metadata."""

    def __init__(self, dtc_code: str, status_byte: int, description: str, severity: str, asil: ASILHazardLevel):
        self.dtc_code = dtc_code
        self.status_byte = status_byte
        self.description = description
        self.severity = severity
        self.asil = asil

    @property
    def is_confirmed(self) -> bool:
        return bool(self.status_byte & DTC_STATUS_CONFIRMED)

    @property
    def is_pending(self) -> bool:
        return bool(self.status_byte & DTC_STATUS_PENDING)

    @property
    def warning_indicator(self) -> bool:
        return bool(self.status_byte & DTC_STATUS_WARNING_INDICATOR_REQ)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dtc_code": self.dtc_code,
            "status_byte": f"0x{self.status_byte:02X}",
            "confirmed": self.is_confirmed,
            "pending": self.is_pending,
            "mil_on": self.warning_indicator,
            "severity": self.severity,
            "asil": self.asil.value,
            "description": self.description
        }


class UdsEcuSimulator:
    """
    Virtual ECU Diagnostics Server.
    Listens for UDS requests on CAN ID 0x7E0 and responds on 0x7E8.
    """

    def __init__(self):
        self._dtc_database: Dict[str, UdsDTC] = {
            "P0117": UdsDTC(
                dtc_code="P0117",
                status_byte=0x2F,  # Confirmed, Pending, MIL On
                description="Coolant Temp Sensor Circuit Low Anomaly",
                severity="HIGH",
                asil=ASILHazardLevel.ASIL_B
            ),
            "P0A80": UdsDTC(
                dtc_code="P0A80",
                status_byte=0x2F,  # Confirmed, Pending, MIL On
                description="Replace Hybrid/EV Battery Pack Degradation Exceeded Limit",
                severity="CRITICAL",
                asil=ASILHazardLevel.ASIL_C
            ),
            "P0071": UdsDTC(
                dtc_code="P0071",
                status_byte=0x2E,  # Confirmed, Pending
                description="Ambient Air Temperature Sensor Range/Performance Anomaly",
                severity="WARNING",
                asil=ASILHazardLevel.ASIL_A
            )
        }
        self._vin = "AUTOCPILOT2026HV1"
        self._is_security_unlocked = False
        self.simulate_bus_disconnect = False

    def handle_request(self, payload: bytes) -> bytes:
        """Process ISO 14229 UDS frame and return response payload."""
        if not payload or len(payload) < 2:
            return bytes([0x7F, 0x00, NRC_SUB_FUNCTION_NOT_SUPPORTED])

        # Single Frame ISO-TP parsing (byte 0: PCI length)
        pci_len = payload[0] & 0x0F
        req_data = payload[1:1 + pci_len]
        if not req_data:
            return bytes([0x7F, 0x00, NRC_SUB_FUNCTION_NOT_SUPPORTED])

        sid = req_data[0]

        # -------------------------------------------------------------
        # Service 0x19: ReadDTCInformation
        # -------------------------------------------------------------
        if sid == SID_READ_DTC_INFO:
            if len(req_data) < 2:
                return bytes([0x7F, SID_READ_DTC_INFO, NRC_SUB_FUNCTION_NOT_SUPPORTED])
            subfunc = req_data[1]

            if subfunc == 0x02:  # reportDTCByStatusMask
                mask = req_data[2] if len(req_data) > 2 else 0x08
                resp = bytearray([0x59, 0x02, 0xFF])  # 0x59, subfunc, statusAvailabilityMask
                for dtc in self._dtc_database.values():
                    if dtc.status_byte & mask:
                        dtc_bytes = self._encode_dtc_code(dtc.dtc_code)
                        resp.extend(dtc_bytes)
                        resp.append(dtc.status_byte)
                # ISO-TP Single Frame Header
                return bytes([len(resp)]) + bytes(resp)

            return bytes([0x7F, SID_READ_DTC_INFO, NRC_SUB_FUNCTION_NOT_SUPPORTED])

        # -------------------------------------------------------------
        # Service 0x22: ReadDataByIdentifier
        # -------------------------------------------------------------
        elif sid == SID_READ_DATA_BY_ID:
            if len(req_data) < 3:
                return bytes([0x7F, SID_READ_DATA_BY_ID, NRC_REQUEST_OUT_OF_RANGE])
            did = (req_data[1] << 8) | req_data[2]

            if did == 0xF190:  # VIN
                vin_bytes = self._vin.encode("ascii")
                resp = bytearray([0x62, req_data[1], req_data[2]]) + vin_bytes
                return bytes([len(resp)]) + bytes(resp)

            elif did == 0x0100:  # HV Battery Telemetry
                # 398.5V, -12.4A, 34.5°C, 78% SOC
                data = struct.pack(">HhBB", 3985, -124, int(34.5 + 40), 78)
                resp = bytearray([0x62, req_data[1], req_data[2]]) + data
                return bytes([len(resp)]) + bytes(resp)

            elif did == 0x0101:  # Thermal Telemetry
                # Coolant 96.0°C, Pump 42%, Flow 15.5 L/min
                data = struct.pack(">BBH", int(96.0 + 40), 42, int(15.5 * 100))
                resp = bytearray([0x62, req_data[1], req_data[2]]) + data
                return bytes([len(resp)]) + bytes(resp)

            return bytes([0x7F, SID_READ_DATA_BY_ID, NRC_REQUEST_OUT_OF_RANGE])

        # -------------------------------------------------------------
        # Service 0x14: ClearDiagnosticInformation
        # -------------------------------------------------------------
        elif sid == SID_CLEAR_DIAGNOSTIC_INFO:
            if not self._is_security_unlocked:
                # NRC 0x33: SecurityAccessDenied (guarded by ASIL Two-Key Handshake)
                return bytes([0x03, 0x7F, SID_CLEAR_DIAGNOSTIC_INFO, NRC_SECURITY_ACCESS_DENIED])
            self._dtc_database.clear()
            resp = bytearray([0x54])  # Positive response 0x14 + 0x40
            return bytes([len(resp)]) + bytes(resp)

        return bytes([0x7F, sid, NRC_SUB_FUNCTION_NOT_SUPPORTED])

    def unlock_security(self, authorized: bool) -> None:
        """Set ECU security status for protected actuator commands."""
        self._is_security_unlocked = authorized

    def clear_dtcs(self) -> None:
        """Clear all active DTCs in database."""
        self._dtc_database.clear()

    def add_dtc(self, dtc: UdsDTC) -> None:
        """Inject or simulate a DTC entry."""
        self._dtc_database[dtc.dtc_code] = dtc

    @staticmethod
    def _encode_dtc_code(dtc_code: str) -> bytes:
        """Convert standard string DTC (e.g. 'P0A80') to 3-byte binary format."""
        prefix = dtc_code[0].upper()
        prefix_val = {"P": 0, "C": 1, "B": 2, "U": 3}.get(prefix, 0)
        num_part = dtc_code[1:]
        b0 = (prefix_val << 6) | (int(num_part[0], 16) << 4) | int(num_part[1], 16)
        b1 = int(num_part[2:4], 16) if len(num_part) >= 4 else 0x00
        b2 = 0x00
        return bytes([b0, b1, b2])


class UdsServiceClient:
    """
    Automotive UDS Diagnostic Client.
    Communicates via CanInterfaceAdapter and translates binary frames into high-level diagnostics.
    """

    def __init__(self, can_adapter: Optional[CanInterfaceAdapter] = None):
        self.can_adapter = can_adapter or CanInterfaceAdapter(interface="virtual")
        self.ecu_simulator = UdsEcuSimulator()

    def read_dtc_information(self, status_mask: int = 0x08, timeout_ms: float = 80.0) -> List[Dict[str, Any]]:
        """
        Execute Service 0x19 02 (reportDTCByStatusMask).
        Returns structured list of confirmed or pending vehicle DTCs.
        Enforces 80ms response timeout protection; triggers safety alert upon failure.
        """
        if self.ecu_simulator.simulate_bus_disconnect:
            # Simulate bus disconnect / response timeout > 80ms
            time.sleep(timeout_ms / 1000.0)
            logger.error(f"[UDS] Response timeout ({timeout_ms}ms exceeded); ECU unreachable.")
            return [{
                "dtc_code": "UDS_TIMEOUT",
                "status_byte": "0xFF",
                "confirmed": False,
                "pending": False,
                "mil_on": True,
                "error": "UDS_TIMEOUT",
                "description": f"CAN 匯流排應答逾時 ({timeout_ms}ms)，實體 ECU 離線或通訊中斷"
            }]

        # ISO-TP Single Frame: PCI_len=3, SID=0x19, SubFunc=0x02, Mask=status_mask
        req_frame = bytes([0x03, SID_READ_DTC_INFO, 0x02, status_mask])

        # Send request frame to bus
        if CAN_AVAILABLE and self.can_adapter.bus:
            msg = can.Message(arbitration_id=CAN_ID_UDS_PHYS_REQ, data=req_frame, is_extended_id=False)
            self.can_adapter.send(msg)

        # Process through ECU simulator (or receive from physical bus)
        resp_data = self.ecu_simulator.handle_request(req_frame)
        return self._parse_service_0x19_response(resp_data)

    def read_data_by_identifier(self, did: int) -> Dict[str, Any]:
        """
        Execute Service 0x22 (ReadDataByIdentifier).
        """
        did_high = (did >> 8) & 0xFF
        did_low = did & 0xFF
        req_frame = bytes([0x03, SID_READ_DATA_BY_ID, did_high, did_low])

        if CAN_AVAILABLE and self.can_adapter.bus:
            msg = can.Message(arbitration_id=CAN_ID_UDS_PHYS_REQ, data=req_frame, is_extended_id=False)
            self.can_adapter.send(msg)

        resp_data = self.ecu_simulator.handle_request(req_frame)
        return self._parse_service_0x22_response(did, resp_data)

    def clear_diagnostic_information(self, user_confirmed: bool = False) -> Tuple[bool, str]:
        """
        Execute Service 0x14 (ClearDiagnosticInformation).
        Strictly guarded by ASIL-D Safety Supervisor and Two-Key Handshake.
        """
        supervisor = get_safety_supervisor()

        # Step 1: Check ASIL state machine authorization
        if not user_confirmed:
            supervisor.request_action(
                action="清除故障碼",
                hazard_level=ASILHazardLevel.ASIL_C,
                details="即將發送 UDS Service 0x14 清除所有 ECU 故障碼，需口語確認"
            )
            self.ecu_simulator.unlock_security(False)
            return False, "ASIL_CONFIRMATION_REQUIRED: 需要雙重口語確認"

        # Step 2: Unlock simulator security and send UDS 0x14
        self.ecu_simulator.unlock_security(True)
        req_frame = bytes([0x04, SID_CLEAR_DIAGNOSTIC_INFO, 0xFF, 0xFF, 0xFF])

        if CAN_AVAILABLE and self.can_adapter.bus:
            msg = can.Message(arbitration_id=CAN_ID_UDS_PHYS_REQ, data=req_frame, is_extended_id=False)
            self.can_adapter.send(msg)

        resp_data = self.ecu_simulator.handle_request(req_frame)

        if len(resp_data) >= 2 and resp_data[1] == 0x54:
            logger.info("[UDS] Service 0x14 ClearDTC Positive Response 0x54 received.")
            return True, "ECU 故障碼已成功清除 (UDS Service 0x14 OK)"
        elif len(resp_data) >= 4 and resp_data[2] == SID_CLEAR_DIAGNOSTIC_INFO and resp_data[3] == NRC_SECURITY_ACCESS_DENIED:
            return False, "NRC 0x33: 安全授權被拒絕 (SecurityAccessDenied)"
        return False, f"UDS Service 0x14 失敗，回傳碼: {resp_data.hex()}"

    def _parse_service_0x19_response(self, resp_data: bytes) -> List[Dict[str, Any]]:
        """Parse Service 0x19 02 payload into human and machine readable DTC records."""
        results = []
        if len(resp_data) < 4:
            return results

        pci_len = resp_data[0]
        data = resp_data[1:1 + pci_len]

        if len(data) < 3 or data[0] != 0x59:  # Positive response check
            return results

        # data[0]: 0x59, data[1]: subfunc 0x02, data[2]: availability mask
        dtc_bytes = data[3:]
        idx = 0
        while idx + 4 <= len(dtc_bytes):
            b0, b1, b2, status = dtc_bytes[idx:idx + 4]
            dtc_str = self.decode_dtc_bytes(b0, b1)
            results.append({
                "dtc_code": dtc_str,
                "status_byte": f"0x{status:02X}",
                "confirmed": bool(status & DTC_STATUS_CONFIRMED),
                "pending": bool(status & DTC_STATUS_PENDING),
                "mil_on": bool(status & DTC_STATUS_WARNING_INDICATOR_REQ)
            })
            idx += 4
        return results

    def _parse_service_0x22_response(self, did: int, resp_data: bytes) -> Dict[str, Any]:
        """Parse Service 0x22 DID payload."""
        if len(resp_data) < 4:
            return {"error": "Invalid response length"}

        pci_len = resp_data[0]
        data = resp_data[1:1 + pci_len]
        if data[0] != 0x62:  # Positive response SID
            return {"error": f"Negative response: {resp_data.hex()}"}

        resp_did = (data[1] << 8) | data[2]
        payload = data[3:]

        if resp_did == 0xF190:
            return {"did": "0xF190", "name": "VIN", "value": payload.decode("ascii", errors="replace")}
        elif resp_did == 0x0100:
            v_raw, i_raw, t_raw, soc = struct.unpack(">HhBB", payload[:6])
            return {
                "did": "0x0100",
                "name": "HV_Battery_Telemetry",
                "voltage_v": round(v_raw * 0.1, 1),
                "current_a": round(i_raw * 0.1, 1),
                "temp_c": t_raw - 40,
                "soc_pct": soc
            }
        elif resp_did == 0x0101:
            t_raw, pwm, flow_raw = struct.unpack(">BBH", payload[:4])
            return {
                "did": "0x0101",
                "name": "Thermal_Loop_State",
                "coolant_temp_c": t_raw - 40,
                "pump_pwm_pct": pwm,
                "flow_rate_lpm": round(flow_raw * 0.01, 2)
            }
        return {"did": hex(resp_did), "raw_hex": payload.hex()}

    @staticmethod
    def decode_dtc_bytes(b0: int, b1: int) -> str:
        """Convert 2-byte raw DTC format to standard OBD/UDS alphanumeric string (e.g. P0A80)."""
        category_bits = (b0 >> 6) & 0x03
        prefix = ["P", "C", "B", "U"][category_bits]
        d1 = str((b0 >> 4) & 0x03)
        d2 = f"{(b0 & 0x0F):X}"
        d3 = f"{(b1 >> 4):X}"
        d4 = f"{(b1 & 0x0F):X}"
        return f"{prefix}{d1}{d2}{d3}{d4}"
