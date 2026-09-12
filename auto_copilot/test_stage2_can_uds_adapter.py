"""
Unit and Integration Tests for Stage 2: Automotive CAN Bus and ISO 14229 UDS Protocol Stack.
Validates DBC matrix binary encoding/decoding, UDS Service 0x19 02, Service 0x22,
and ASIL-protected Service 0x14.
"""

import sys
import os
import time
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from can_interface_adapter import CanInterfaceAdapter, CAN_ID_BMS_TELEMETRY, CAN_ID_THERMAL_TELEMETRY, CAN_ID_ACTUATOR_COMMAND
from uds_service_client import UdsServiceClient, UdsEcuSimulator, UdsDTC
from asil_safety_core import get_safety_supervisor, VehicleSafeState, ASILHazardLevel


def test_can_dbc_bms_encoding_decoding():
    """Verify BMS Frame (0x100) binary DBC encoding and decoding accuracy."""
    adapter = CanInterfaceAdapter(interface="virtual")
    try:
        test_v = 398.5
        test_i = -12.4
        test_hv = True
        test_status = 1

        msg = adapter.encode_bms_frame(voltage=test_v, current=test_i, hv_interlock=test_hv, status=test_status)
        data = msg.data if hasattr(msg, "data") else msg["data"]

        decoded = adapter.decode_bms_frame(bytes(data))

        assert decoded["crc_valid"] is True
        assert abs(decoded["battery_voltage"] - test_v) < 0.15
        assert abs(decoded["battery_current"] - test_i) < 0.15
        assert decoded["hv_interlock"] is True
        assert decoded["bms_status"] == test_status
        print("[PASS] test_can_dbc_bms_encoding_decoding passed")
    finally:
        adapter.shutdown()


def test_can_dbc_thermal_encoding_decoding():
    """Verify Thermal Frame (0x200) binary DBC encoding and decoding."""
    adapter = CanInterfaceAdapter(interface="virtual")
    try:
        test_temp = 96.0
        test_pwm = 42.0
        test_fan = 2400
        test_flow = 15.5

        msg = adapter.encode_thermal_frame(coolant_temp=test_temp, pump_pwm=test_pwm, fan_rpm=test_fan, flow_rate=test_flow)
        data = msg.data if hasattr(msg, "data") else msg["data"]

        decoded = adapter.decode_thermal_frame(bytes(data))

        assert decoded["crc_valid"] is True
        assert abs(decoded["coolant_temp"] - test_temp) < 0.5
        assert abs(decoded["pump_pwm"] - test_pwm) < 0.5
        assert decoded["fan_rpm"] == test_fan
        assert abs(decoded["flow_rate"] - test_flow) < 0.1
        print("[PASS] test_can_dbc_thermal_encoding_decoding passed")
    finally:
        adapter.shutdown()


def test_can_dbc_actuator_encoding_decoding():
    """Verify Actuator Frame (0x300) binary encoding and decoding."""
    adapter = CanInterfaceAdapter(interface="virtual")
    try:
        msg = adapter.encode_actuator_frame(relay_cmd=1, pump_cmd=75, dtc_reset=True)
        data = msg.data if hasattr(msg, "data") else msg["data"]

        decoded = adapter.decode_actuator_frame(bytes(data))
        assert decoded["relay_command"] == 1
        assert decoded["pump_command"] == 75
        assert decoded["dtc_reset"] is True
        print("[PASS] test_can_dbc_actuator_encoding_decoding passed")
    finally:
        adapter.shutdown()


def test_uds_service_0x19_read_dtc():
    """Verify ISO 14229 Service 0x19 02 (ReadDTCInformationByStatusMask)."""
    adapter = CanInterfaceAdapter(interface="virtual")
    uds_client = UdsServiceClient(adapter)
    try:
        dtcs = uds_client.read_dtc_information(status_mask=0x08)

        assert len(dtcs) >= 2
        dtc_codes = [d["dtc_code"] for d in dtcs]
        assert "P0A80" in dtc_codes
        assert "P0071" in dtc_codes

        # Check status attributes
        p0a80 = next(d for d in dtcs if d["dtc_code"] == "P0A80")
        assert p0a80["confirmed"] is True
        assert p0a80["pending"] is True
        print(f"[PASS] test_uds_service_0x19_read_dtc passed: {dtc_codes}")
    finally:
        adapter.shutdown()


def test_uds_service_0x22_read_did():
    """Verify ISO 14229 Service 0x22 (ReadDataByIdentifier) for VIN and Telemetry."""
    adapter = CanInterfaceAdapter(interface="virtual")
    uds_client = UdsServiceClient(adapter)
    try:
        # DID 0xF190: VIN
        vin_resp = uds_client.read_data_by_identifier(0xF190)
        assert vin_resp.get("name") == "VIN"
        assert vin_resp.get("value") == "AUTOCPILOT2026HV1"

        # DID 0x0100: HV Battery Telemetry
        bms_resp = uds_client.read_data_by_identifier(0x0100)
        assert bms_resp.get("name") == "HV_Battery_Telemetry"
        assert bms_resp["voltage_v"] == 398.5
        assert bms_resp["current_a"] == -12.4
        assert bms_resp["soc_pct"] == 78

        # DID 0x0101: Thermal Loop State
        thermal_resp = uds_client.read_data_by_identifier(0x0101)
        assert thermal_resp.get("name") == "Thermal_Loop_State"
        assert thermal_resp["coolant_temp_c"] == 96.0
        assert thermal_resp["pump_pwm_pct"] == 42
        print("[PASS] test_uds_service_0x22_read_did passed")
    finally:
        adapter.shutdown()


def test_uds_service_0x14_cleardtc_asil_handshake():
    """Verify Service 0x14 is blocked without ASIL Two-Key Handshake, and passes with it."""
    supervisor = get_safety_supervisor()
    supervisor.reset()
    adapter = CanInterfaceAdapter(interface="virtual")
    uds_client = UdsServiceClient(adapter)
    try:
        # Step 1: Attempt to clear without confirmation -> Must be rejected
        success, reason = uds_client.clear_diagnostic_information(user_confirmed=False)
        assert success is False
        assert "ASIL_CONFIRMATION_REQUIRED" in reason
        assert supervisor.current_state == VehicleSafeState.WAITING_CONFIRMATION

        # Verify DTCs still present in ECU
        dtcs = uds_client.read_dtc_information()
        assert len(dtcs) > 0

        # Step 2: Confirm via Two-Key Handshake
        supervisor.validate_confirmation("確認執行")
        assert supervisor.current_state == VehicleSafeState.NORMAL_RUN

        # Step 3: Now execute with confirmation granted
        success, msg = uds_client.clear_diagnostic_information(user_confirmed=True)
        assert success is True
        assert "UDS Service 0x14 OK" in msg

        # Step 4: Verify DTCs are now cleared in ECU
        dtcs_after = uds_client.read_dtc_information()
        assert len(dtcs_after) == 0
        print("[PASS] test_uds_service_0x14_cleardtc_asil_handshake passed")
    finally:
        adapter.shutdown()


def test_bus_loopback_latency():
    """Benchmark CAN message encoding + roundtrip handling latency (< 5ms)."""
    adapter = CanInterfaceAdapter(interface="virtual")
    uds_client = UdsServiceClient(adapter)
    try:
        start = time.perf_counter()
        for _ in range(50):
            _ = uds_client.read_dtc_information(0x08)
        elapsed_ms = (time.perf_counter() - start) * 1000 / 50.0

        print(f"[BENCHMARK] Average CAN/UDS transaction latency: {elapsed_ms:.3f} ms")
        assert elapsed_ms < 5.0  # Must be well below 5ms
        print("[PASS] test_bus_loopback_latency passed")
    finally:
        adapter.shutdown()


if __name__ == "__main__":
    test_can_dbc_bms_encoding_decoding()
    test_can_dbc_thermal_encoding_decoding()
    test_can_dbc_actuator_encoding_decoding()
    test_uds_service_0x19_read_dtc()
    test_uds_service_0x22_read_did()
    test_uds_service_0x14_cleardtc_asil_handshake()
    test_bus_loopback_latency()
    print("ALL 7 STAGE 2 PROTOCOL TESTS PASSED 100%!")
