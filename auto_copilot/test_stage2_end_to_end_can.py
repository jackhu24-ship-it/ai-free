"""
test_stage2_end_to_end_can.py - Stage 2 Automotive CAN / CAN-FD and UDS End-to-End Test Suite
=============================================================================================
Validates:
1. Day 4: DBC matrix parsing (mock_vehicle.dbc) and CanInterfaceAdapter signal encode/decode.
2. Day 4: Background periodic simulation broadcaster on Virtual CAN.
3. Day 5: ISO 14229 UDS Service 0x19 02 (P0117, P0A80) and 80ms timeout protection.
4. Day 6: Closed-loop multi-agent interaction between LangGraph State Machine, CAN Bus, and UDS.
"""

import sys
import os
import time

# Add auto_copilot directory to sys.path
sys.path.insert(0, os.path.dirname(__file__))

from can_adapter import (
    CanInterfaceAdapter,
    FRAME_ID_THERMAL_TELEMETRY,
    FRAME_ID_BMS_STATE,
    FRAME_ID_PDM_ACTUATOR
)
from uds_service_client import UdsServiceClient
from stage1_safety_supervisor import build_safety_graph, SystemOperatingState


def test_dbc_loading_and_encoding():
    """Verify mock_vehicle.dbc loading and bidirectional signal encoding/decoding."""
    adapter = CanInterfaceAdapter(interface="virtual")
    try:
        assert adapter.db is not None, "DBC failed to load!"

        # 1. Thermal telemetry frame (0x120)
        thermal_in = {
            "Coolant_Temp": 104.0,
            "Pump_PWM": 45.0,
            "Line_Pressure": 142.5,
            "Motor_RPM": 3500,
            "Thermal_CRC": 12345
        }
        msg_thm = adapter.encode_message("Thermal_Powertrain_Telemetry", thermal_in)
        assert msg_thm is not None
        assert msg_thm.arbitration_id == FRAME_ID_THERMAL_TELEMETRY

        decoded_thm = adapter.decode_message(FRAME_ID_THERMAL_TELEMETRY, msg_thm.data)
        assert abs(decoded_thm["Coolant_Temp"] - 104.0) < 0.5
        assert abs(decoded_thm["Line_Pressure"] - 142.5) < 0.2
        assert decoded_thm["Motor_RPM"] == 3500

        # 2. BMS telemetry frame (0x180)
        bms_in = {
            "Bus_Voltage": 384.8,
            "Pack_Current": -18.5,
            "Pack_SOC": 82.0,
            "HV_Interlock": 1,
            "BMS_Status": 0,
            "BMS_CRC": 54321
        }
        msg_bms = adapter.encode_message("BMS_Battery_State", bms_in)
        assert msg_bms is not None
        assert msg_bms.arbitration_id == FRAME_ID_BMS_STATE

        decoded_bms = adapter.decode_message(FRAME_ID_BMS_STATE, msg_bms.data)
        assert abs(decoded_bms["Bus_Voltage"] - 384.8) < 0.2
        assert abs(decoded_bms["Pack_Current"] - (-18.5)) < 0.2
        assert decoded_bms["HV_Interlock"] == 1

        print("[PASS] test_dbc_loading_and_encoding passed 100%")
    finally:
        adapter.shutdown()


def test_virtual_can_broadcast_thread():
    """Verify background periodic simulation broadcaster streams live CAN frames."""
    adapter = CanInterfaceAdapter(interface="virtual")
    try:
        adapter.start_simulation_broadcast(interval=0.03)
        time.sleep(0.15)  # Let broadcast loop run for several frames

        telem = adapter.get_latest_telemetry()
        assert telem["coolant_temp_c"] > 100.0
        assert telem["bus_voltage_v"] == 384.8
        assert telem["line_pressure_kpa"] > 140.0
        assert telem["hv_interlock"] is True

        print(f"[PASS] test_virtual_can_broadcast_thread passed (Live Coolant: {telem['coolant_temp_c']} C, Voltage: {telem['bus_voltage_v']} V)")
    finally:
        adapter.shutdown()


def test_uds_service_0x19_and_timeout():
    """Verify ISO 14229 Service 0x19 02 (P0117, P0A80) and 80ms timeout protection."""
    adapter = CanInterfaceAdapter(interface="virtual")
    uds_client = UdsServiceClient(adapter)
    try:
        # Normal query: Expect P0117 and P0A80
        dtcs = uds_client.read_dtc_information(status_mask=0x08)
        assert len(dtcs) >= 2
        dtc_codes = [d["dtc_code"] for d in dtcs]
        assert "P0117" in dtc_codes, "P0117 must be present!"
        assert "P0A80" in dtc_codes, "P0A80 must be present!"

        # Test 80ms timeout protection on bus disconnect
        uds_client.ecu_simulator.simulate_bus_disconnect = True
        timeout_start = time.perf_counter()
        timeout_res = uds_client.read_dtc_information(status_mask=0x08, timeout_ms=80.0)
        elapsed_ms = (time.perf_counter() - timeout_start) * 1000

        assert timeout_res[0]["dtc_code"] == "UDS_TIMEOUT"
        assert "CAN 匯流排應答逾時" in timeout_res[0]["description"]
        assert elapsed_ms >= 75.0  # Verified 80ms timeout interval

        print(f"[PASS] test_uds_service_0x19_and_timeout passed (Timeout verified at {elapsed_ms:.1f}ms)")
    finally:
        adapter.shutdown()


def test_closed_loop_langgraph_with_can_bus():
    """Verify end-to-end interaction: Voice Query -> Safety Supervisor -> CAN DBC -> Frame 0x210 TX."""
    graph = build_safety_graph()

    # Step 1: Query normal telemetry via CAN bus
    s1 = graph.invoke({
        "query": "請查詢冷卻水溫與母線電壓數值",
        "current_state": SystemOperatingState.NORMAL_RUN,
        "pending_action": None,
        "action_requested_timestamp": 0.0,
        "ftti_limit_seconds": 5.0,
        "is_confirmed_by_user": False,
        "telemetry_data": {},
        "target_nodes": [],
        "spoken_response": "",
    })
    assert s1["current_state"] == SystemOperatingState.DEGRADED_WARN or s1["current_state"] == SystemOperatingState.NORMAL_RUN
    assert "目前冷卻液溫度" in s1["spoken_response"]
    print("[Step 1: Live CAN Telemetry Query Succeeded]")

    # Step 2: Hazardous actuator command -> Supervisor intercepts in WAITING_CONFIRMATION
    s2 = graph.invoke({
        "query": "立即幫我切斷繼電器！",
        "current_state": SystemOperatingState.NORMAL_RUN,
        "pending_action": None,
        "action_requested_timestamp": 0.0,
        "ftti_limit_seconds": 5.0,
        "is_confirmed_by_user": False,
        "telemetry_data": {},
        "target_nodes": [],
        "spoken_response": "",
    })
    assert s2["current_state"] == SystemOperatingState.WAITING_CONFIRMATION
    assert "警告" in s2["spoken_response"]
    assert "確認執行" in s2["spoken_response"]
    print("[Step 2: Dangerous Actuator Command Intercepted]")

    # Step 3: Two-Key confirmation -> Execute and broadcast Frame 0x210 over CAN bus
    s3 = graph.invoke({
        **s2,
        "query": "確認執行",
        "spoken_response": "",
    })
    assert s3["current_state"] == SystemOperatingState.DEGRADED_WARN
    assert s3["telemetry_data"]["relay_status"] == "DISCONNECTED"
    assert "0x210 PDM_Actuator_Command" in s3["telemetry_data"]["can_tx_frame"]
    print("[Step 3: Two-Key Handshake Passed and 0x210 CAN Frame Broadcasted]")

    # Clean shutdown
    from stage1_safety_supervisor import can_bus
    can_bus.shutdown()


if __name__ == "__main__":
    print("==================================================================")
    print("STAGE 2: CAN/CAN-FD PROTOCOL STACK & UDS END-TO-END VERIFICATION")
    print("==================================================================")
    test_dbc_loading_and_encoding()
    test_virtual_can_broadcast_thread()
    test_uds_service_0x19_and_timeout()
    test_closed_loop_langgraph_with_can_bus()
    print("==================================================================")
    print("[PASS] ALL STAGE 2 END-TO-END TESTS PASSED 100%!")
    print("==================================================================")
