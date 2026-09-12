"""
Test Suite: HIL Vehicle Matrix & Shadow Mode Verification (TC-HIL-01 ~ TC-HIL-05)
==================================================================================
驗證 ISO 26262-4 / ISO 26262-6 車載硬體在環故障注入與整車暗模式運算能力：
  TC-HIL-01: 報文階梯式延遲與抖動注入 (SLA <= 350ms)
  TC-HIL-02: CRC 位元翻轉毀損與重傳容錯 (Bit-Flip Detection)
  TC-HIL-03: 看門狗心跳遺失與剛性超時安全關斷 (FTTI 200ms)
  TC-HIL-04: Shadow Mode 零侵入廣播防禦 (Zero-TX Barrier)
  TC-HIL-05: 實車雙軌影子推論、偏差比對與動態實證沉澱 (Dynamic Evidence)
"""

import json
import os
import sys
import tempfile
import time
import pytest
import can

# Windows UTF-8 控制台保護
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from hil_vehicle_matrix import (
    DegradationStrategy,
    HILVehicleFaultInjector,
)
from vehicle_shadow_mode import (
    VehicleShadowModeEngine,
)


# =============================================================================
# Fixtures
# =============================================================================
@pytest.fixture
def fault_injector():
    injector = HILVehicleFaultInjector(interface="virtual", channel="pytest_hil_vbus")
    yield injector
    injector.shutdown()


@pytest.fixture
def shadow_engine(tmp_path):
    evidence_path = os.path.join(tmp_path, "test_shadow_evidence.jsonl")
    engine = VehicleShadowModeEngine(
        interface="virtual",
        channel="pytest_shadow_vbus",
        evidence_file=evidence_path
    )
    yield engine
    engine.shutdown()


# =============================================================================
# TC-HIL-01: 報文延遲與抖動注入
# =============================================================================
def test_hil_tc01_message_latency_and_jitter(fault_injector):
    """驗證 TC-HIL-01: 報文延遲注入在 SLA 門檻內的正常運行與超時時的降級判定"""
    # 正常延遲 (50ms < 350ms SLA)
    res_normal = fault_injector.inject_latency(
        frame_id=0x120,
        base_delay_ms=25.0,
        jitter_pct=0.1,
        sla_threshold_ms=350.0
    )
    assert res_normal.passed is True
    assert res_normal.strategy == DegradationStrategy.NORMAL
    assert res_normal.details["sla_violated"] is False

    # 超時延遲注入 (400ms > 350ms SLA)
    res_violated = fault_injector.inject_latency(
        frame_id=0x120,
        base_delay_ms=400.0,
        jitter_pct=0.05,
        sla_threshold_ms=350.0
    )
    assert res_violated.passed is True
    assert res_violated.strategy == DegradationStrategy.FAIL_OPERATIONAL
    assert res_violated.details["sla_violated"] is True


# =============================================================================
# TC-HIL-02: CRC 位元翻轉與訊框毀損
# =============================================================================
def test_hil_tc02_crc_bit_flipping_corruption(fault_injector):
    """驗證 TC-HIL-02: 模擬 CRC 位元翻轉引發之報文毀損與檢出"""
    res = fault_injector.inject_crc_corruption(frame_id=0x180, corrupt_bits=2)
    
    assert res.passed is True
    assert res.details["detected"] is True
    assert res.strategy == DegradationStrategy.FAIL_OPERATIONAL
    assert res.details["original_hex"] != res.details["corrupted_hex"]


# =============================================================================
# TC-HIL-03: 看門狗心跳中斷與 FTTI 剛性降級
# =============================================================================
def test_hil_tc03_watchdog_timeout_failsafe(fault_injector):
    """驗證 TC-HIL-03: 心跳中斷逾 200ms FTTI 門檻時，強制觸發 FAIL_SAFE 降級"""
    res = fault_injector.inject_watchdog_timeout(
        heartbeat_id=0x080,
        interruption_duration_s=0.22,
        ftti_limit_s=0.20
    )
    
    assert res.passed is True
    assert res.strategy == DegradationStrategy.FAIL_SAFE
    assert res.details["timeout_triggered"] is True
    assert res.ftti_elapsed_s >= 0.20


# =============================================================================
# TC-HIL-04: Shadow Mode 零侵入廣播防禦 (Zero-TX Barrier)
# =============================================================================
def test_shadow_mode_zero_tx_barrier(shadow_engine):
    """驗證 TC-HIL-04: 暗模式運算期間，任何對 CAN 總線之發送均被 100% 攔截 (Zero-TX)"""
    assert shadow_engine.tx_blocked_count == 0

    # 嘗試非法發送 0x210 致動指令
    illegal_msg = can.Message(arbitration_id=0x210, data=bytearray([1, 0, 0, 0]), is_extended_id=False)
    shadow_engine.bus.send(illegal_msg)
    shadow_engine.bus.send(illegal_msg)

    # 驗證阻擋計數器遞增，且實體發送量為 0
    assert shadow_engine.tx_blocked_count == 2
    assert shadow_engine.tx_attempt_count == 2


# =============================================================================
# TC-HIL-05: 實車雙軌影子推論、偏差比對與動態實證沉澱
# =============================================================================
def test_shadow_mode_discrepancy_and_dynamic_evidence(shadow_engine):
    """驗證 TC-HIL-05: 雙軌影子推論、駕駛行為偏差檢出與動態實證檔案沉澱"""
    # 注入正常水溫報文 (94°C)
    msg_normal = can.Message(
        arbitration_id=0x120,
        data=bytearray([int(94.0 + 40.0), 70, 0x0B, 0xB8]),
        is_extended_id=False
    )
    r1 = shadow_engine.process_incoming_frame(msg_normal, actual_driver_action="NORMAL_DRIVING")
    assert r1.discrepancy_detected is False
    assert r1.risk_level == "LOW"

    # 注入極端過溫報文 (109°C)，駕駛卻依然全載狂飆
    msg_overheat = can.Message(
        arbitration_id=0x120,
        data=bytearray([int(109.0 + 40.0), 70, 0x0B, 0xB8]),
        is_extended_id=False
    )
    r2 = shadow_engine.process_incoming_frame(msg_overheat, actual_driver_action="NORMAL_DRIVING")
    assert r2.discrepancy_detected is True
    assert r2.risk_level == "CRITICAL"
    assert "DEGRADED_WARN" in r2.predicted_state
    assert r2.recommended_action == "SUGGEST_DERATING_OR_SAFE_STOP"

    # 驗證動態實證持久化 JSONL 檔案
    assert os.path.exists(shadow_engine.evidence_file)
    with open(shadow_engine.evidence_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    assert len(lines) >= 2
    rec_json = json.loads(lines[-1])
    assert rec_json["discrepancy_detected"] is True
    assert rec_json["risk_level"] == "CRITICAL"
