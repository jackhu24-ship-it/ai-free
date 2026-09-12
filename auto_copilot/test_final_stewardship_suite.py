# -*- coding: utf-8 -*-
"""
=============================================================================
AutoCopilot Milestone 94 Test Suite: Final Exit & Stewardship Verification
=============================================================================
Covers:
1. Open SDV Core (Apache 2.0) & Commercial Hook Demarcation
2. Synthesizable Silicon RTL Verilog Model & 1-Cycle Cutoff (2.5ns)
3. Silicon IP Core Royalty Financial Engine
4. Autonomous Generational Stewardship Engine
5. ISO/TC 22 EDSC & ISO 21448 SOTIF Metrics Verification
=============================================================================
"""

import os
import pytest
from auto_copilot.open_sdv_core import OpenVehicleStateMachine, OpenVehicleState, OpenTelemetryFrame, LicenseTier
from auto_copilot.rtl_hardware_model import SafetyFastAbortArbiterModel, RTLTripReason, SiliconRoyaltyCalculator
from auto_copilot.autonomous_stewardship_engine import AutonomousStewardshipEngine


def test_open_sdv_dual_licensing_and_hooks():
    """驗證開源版 (Apache 2.0) 狀態機與商業閉源鉤子截斷"""
    sm = OpenVehicleStateMachine(LicenseTier.OPEN_APACHE2)
    assert sm.state == OpenVehicleState.INIT

    # 基礎開源遙測流轉
    frame = OpenTelemetryFrame(timestamp=1000.0, bus_id=0x100, data=b'\x01\x02', dlc=2)
    res = sm.process_telemetry(frame)
    assert res["processed"] is True
    assert sm.state == OpenVehicleState.STANDBY

    # 商業版掛載硬體防護鉤子
    def commercial_safety_interceptor(target_state: str, context: dict) -> bool:
        if "OVERTORQUE_HAZARD" in context.get("reason", ""):
            return False
        return True

    sm.register_commercial_hook(commercial_safety_interceptor)
    assert sm.get_audit_summary()["is_commercial_secured"] is True

    # 正常轉換允許
    assert sm.transition_to(OpenVehicleState.ACTIVE, "Normal Operator Enable") is True
    assert sm.state == OpenVehicleState.ACTIVE

    # 危險異常被商業鉤子強制切斷至 SAFE_STOP
    assert sm.transition_to(OpenVehicleState.ACTIVE, "OVERTORQUE_HAZARD_INJECTED") is False
    assert sm.state == OpenVehicleState.SAFE_STOP


def test_silicon_rtl_fast_abort_cycle_latency():
    """驗證晶片級硬體 IP Core 1 個時脈週期 (2.5ns @ 400MHz) 極限切斷"""
    model = SafetyFastAbortArbiterModel(clock_freq_mhz=400)
    assert model.clock_period_ns == 2.5

    # 上電復位預設安全鎖定
    model.reset()
    assert model.power_stage_en is False
    assert model.safe_state_tripped is True

    # 經由安全硬體安全模組 (HSM) 授權解鎖
    step = model.clock_step(
        hsm_unlock_key=SafetyFastAbortArbiterModel.HSM_UNLOCK_MAGIC,
        hsm_clear_trip=True
    )
    assert step.power_stage_en is True
    assert step.safe_state_tripped is False

    # 正常包絡線內運作 (扭矩 80 <= 包絡上限 100)
    step_norm = model.clock_step(torque_cmd=80, torque_valid=True, envelope_max=100)
    assert step_norm.power_stage_en is True
    assert step_norm.nmi_irq is False
    assert step_norm.trip_reason == RTLTripReason.REASON_NONE

    # 注入超出包絡線超扭矩 (扭矩 150 > 100) -> 必須在 1 個時脈週期內關斷功率級並觸發 NMI
    step_over = model.clock_step(torque_cmd=150, torque_valid=True, envelope_max=100)
    assert step_over.power_stage_en is False
    assert step_over.safe_state_tripped is True
    assert step_over.nmi_irq is True
    assert step_over.trip_reason == RTLTripReason.REASON_OVERTORQUE
    assert step_over.latency_cycles == 1

    # 驗證 CRC 翻轉故障注入
    model.clock_step(hsm_unlock_key=SafetyFastAbortArbiterModel.HSM_UNLOCK_MAGIC, hsm_clear_trip=True)
    step_crc = model.clock_step(e2e_crc_err=True)
    assert step_crc.power_stage_en is False
    assert step_crc.trip_reason == RTLTripReason.REASON_CRC_ERR
    assert step_crc.latency_cycles == 1

    # 驗證外部硬體保護下拉 (ext_fault_n = False)
    model.clock_step(hsm_unlock_key=SafetyFastAbortArbiterModel.HSM_UNLOCK_MAGIC, hsm_clear_trip=True)
    step_ext = model.clock_step(ext_fault_n=False)
    assert step_ext.power_stage_en is False
    assert step_ext.trip_reason == RTLTripReason.REASON_EXT_FAULT


def test_silicon_ip_royalty_financial_model():
    """驗證晶片級純利潤授權財務模型 (2000萬顆晶片出貨量)"""
    fin = SiliconRoyaltyCalculator.calculate_royalty(
        units_shipped=20_000_000,
        royalty_per_die_usd=0.25,
        nre_upfront_usd=2_500_000.0,
        maintenance_annual_usd=350_000.0
    )
    assert fin["variable_royalty_usd"] == 5_000_000.0
    assert fin["total_gross_usd"] == 7_850_000.0
    assert fin["net_margin_pct"] == 94.5
    assert fin["pure_profit_usd"] > 7_400_000.0


def test_autonomous_stewardship_engine_evaluation():
    """驗證無人化世代傳承與自演進治理引擎 (健康度滿分 100)"""
    workspace = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    engine = AutonomousStewardshipEngine(workspace)
    audit = engine.run_full_governance_audit()

    assert audit.overall_health_score == 100.0
    assert audit.dual_licensing_passed is True
    assert audit.rtl_integrity_passed is True
    assert audit.sotif_metrics_passed is True
    assert len(audit.violations) == 0


def test_sotif_standard_proposal_metrics():
    """驗證 ISO/TC 22 EDSC 與 SOTIF 標準草案文字完整性"""
    workspace = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    proposal_path = os.path.join(workspace, "auto_copilot", "docs", "ISO_TC22_SOTIF_SAFETY_CAGE_PROPOSAL.md")
    assert os.path.exists(proposal_path)

    with open(proposal_path, "r", encoding="utf-8") as f:
        text = f.read()

    assert "EDSC-REQ-001" in text
    assert "EDSC-REQ-002" in text
    assert "EDSC-REQ-003" in text
    assert "15,000,000" in text
    assert "5.0 FIT" in text

