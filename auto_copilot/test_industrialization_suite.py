"""
Industrialization & SOP Automated Test Suite
============================================
驗證量產下線 (EOL)、多車型標定 (A2L)、車隊 700ms 黑盒子與 Safe AI Cage 護欄功能。
"""

import os
import pytest
import can
import time

from auto_copilot.eol_production_tester import EOLProductionTester
from auto_copilot.calibration_manager import freeze_calibration_baseline, validate_calibration, SAFETY_INVARIANTS
from auto_copilot.fleet_telemetry_blackbox import FleetTelemetryBlackbox
from auto_copilot.safe_ai_cage import SafeAICageSupervisor, SomeIpPacket


def test_eol_production_tester():
    """驗收 EOL 產線檢驗程序及耗時 (< 50ms)"""
    tester = EOLProductionTester(ecu_serial="ECU-TEST-2028", vin="VIN-TEST-9999")
    cert = tester.run_full_eol_inspection()
    
    assert cert["overall_verdict"] == "PASS"
    assert cert["total_inspection_time_ms"] < 50.0
    assert cert["tests"]["flash_rom_checksum"]["status"] == "PASS"
    assert cert["tests"]["secure_boot_hsm"]["status"] == "PASS"
    assert cert["tests"]["rapid_e2e_trip"]["response_time_ms"] <= 10.0
    assert cert["tests"]["rapid_sto_cutoff"]["response_time_ms"] <= 10.0


def test_calibration_baseline_and_invariants():
    """驗收多車型標定基線凍結與剛性安全邊界"""
    baseline = freeze_calibration_baseline()
    assert "PASSENGER_SEDAN" in baseline["profiles"]
    assert "COMMERCIAL_TRUCK" in baseline["profiles"]
    assert "OFF_ROAD_UTV" in baseline["profiles"]

    # 驗證客車 FTTI <= 40ms
    assert baseline["profiles"]["PASSENGER_SEDAN"]["ftti_target_ms"] <= 40.0

    # 驗證違規參數必須被攔截
    bad_profile = {
        "ftti_target_ms": 55.0, # 違規超過 40ms
        "crc_fault_threshold": 3,
        "filter_tau_ms": 15.0,
        "coolant_trip_temp_c": 105.0
    }
    assert validate_calibration("BAD_PROFILE", bad_profile) is False


def test_fleet_blackbox_700ms_window_and_fit():
    """驗收 500ms Pre ~ 200ms Post 黑盒子時序與 10 FIT 失效率"""
    bb = FleetTelemetryBlackbox(buffer_window_ms=1000.0)
    now = time.time()
    
    # 寫入 20 幀跨度報文
    for i in range(20):
        t = now - (20 - i) * 0.020
        msg = can.Message(arbitration_id=0x120, data=b"\x01\x02\x03\x04", timestamp=t)
        bb.record_frame(msg)
        
    snap = bb.capture_full_incident_snapshot(
        trigger_state="EMERGENCY_SAFE",
        trigger_reason="Test EOL incident trigger",
        pre_trigger_ms=500.0,
        post_trigger_ms=200.0,
        internal_signals={"torque_nm": 320.0, "temp_c": 106.0}
    )
    
    assert snap.trigger_state == "EMERGENCY_SAFE"
    assert snap.captured_frames_count > 0

    fit_res = bb.calculate_field_failure_rate(fleet_size=100000, average_hours_per_vehicle=2000.0, critical_failure_events=1)
    assert fit_res["measured_fit"] <= 10.0
    assert fit_res["compliance_verdict"] == "ASIL-D_COMPLIANT (<10 FIT)"


def test_safe_ai_cage_arbitration_and_someip():
    """驗收 Safe AI Cage 護欄暴衝攔截與 SOME/IP 封裝"""
    cage = SafeAICageSupervisor()
    
    # 正常決策 -> 放行
    a_ok, s_ok, stat_ok, t_ok = cage.arbitrate_ai_command(target_accel=1.5, target_steer_rate=20.0, ttc_estimate=3.0)
    assert a_ok == 1.5
    assert s_ok == 20.0
    assert "PASSTHROUGH" in stat_ok
    assert t_ok < 5.0 # 5ms 內完成

    # 暴衝決策 (+6.0 m/s^2, TTC 0.8s) -> 強制限幅與煞車
    a_bad, s_bad, stat_bad, t_bad = cage.arbitrate_ai_command(target_accel=6.0, target_steer_rate=90.0, ttc_estimate=0.8)
    assert a_bad == -4.5 # TTC 違規強制煞車
    assert s_bad == 40.0 # 轉向限幅於 40 deg/s
    assert "INTERVENED" in stat_bad
    assert t_bad < 5.0

    # 驗證 SOME/IP 編解碼
    raw_packet = cage.pack_to_someip_ethernet(a_bad, s_bad, status_code=0x01)
    assert len(raw_packet) >= 16
    decoded = SomeIpPacket.decode(raw_packet)
    assert decoded.service_id == 0x1020
    assert decoded.method_id == 0x8001
