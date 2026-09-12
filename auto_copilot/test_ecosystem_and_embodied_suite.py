"""
Ecosystem, Standardization & Embodied AI Automated Test Suite
============================================================
驗證晶片原廠 MCAL 擴展、具身智慧物理安全隔離閥、數位孿生測試雲與失效數據庫。
"""

import os
import pytest

from auto_copilot.mcal_safety_extension import MCALHardwareSafetyExtension
from auto_copilot.embodied_ai_safety_interlock import EmbodiedAISafetyInterlock, JointTelemetry
from auto_copilot.virtual_testbed_cloud import VirtualTestbedCloud
from auto_copilot.lessons_learned_db import build_knowledge_graph


def test_mcal_hardware_safety_extension():
    """驗證晶片原廠 (Infineon/NXP/ST) MCAL 硬體中斷與雙核鎖步故障下拉"""
    mcal = MCALHardwareSafetyExtension(target_silicon="INFINEON_AURIX_TC397")
    init_state = mcal.verify_register_state()
    assert init_state["lockstep_core_status"] == "LOCKED_SYNCHRONIZED"
    assert init_state["pwm_power_bridge_gate"] == "ENABLED"

    # 觸發 NMI 鎖步硬體中斷
    is_fast, latency_us = mcal.trigger_nmi_lockstep_fault_isr()
    assert is_fast is True
    assert latency_us <= 10.0 # 極速執行

    fault_state = mcal.verify_register_state()
    assert fault_state["lockstep_core_status"] == "FAULT_DIVERGENCE_DETECTED"
    assert fault_state["pwm_power_bridge_gate"] == "PHYSICALLY_PULLED_DOWN_STO"


def test_embodied_ai_safety_interlock():
    """驗證具身機器人關節與線控底盤物理安全隔離閥"""
    interlock = EmbodiedAISafetyInterlock(target_system="HUMANOID_LEGGED_ROBOT")
    
    # 正常關節負載
    j_normal = JointTelemetry(joint_id=1, joint_name="Hip_Roll", torque_nm=30.0, velocity_deg_s=100.0, impact_force_n=120.0, temperature_c=50.0)
    ok1, reason1, t1 = interlock.evaluate_joint_safety(j_normal)
    assert ok1 is True
    assert "NORMAL" in reason1
    assert t1 < 1.0

    # 強衝擊異常 (650N > 500N)
    j_shock = JointTelemetry(joint_id=2, joint_name="Ankle_Pitch", torque_nm=110.0, velocity_deg_s=250.0, impact_force_n=650.0, temperature_c=52.0)
    ok2, reason2, t2 = interlock.evaluate_joint_safety(j_shock)
    assert ok2 is False
    assert "EXCESSIVE_IMPACT_FORCE" in reason2
    assert t2 < 1.0
    assert interlock.isolation_valve_engaged is True

    # 復歸測試
    assert interlock.reset_valve() is True
    assert interlock.isolation_valve_engaged is False


def test_virtual_testbed_cloud_10k_scenarios():
    """驗證雲端數位孿生測試床 10,000 級場景高速回歸"""
    vtb = VirtualTestbedCloud(target_runs=10000)
    res = vtb.run_mass_regression_matrix()
    
    assert res["total_scenarios"] == 10000
    assert res["pass_rate_percent"] == 100.0
    assert res["total_elapsed_seconds"] < 1.0 # 1 秒內完成
    assert res["gsn_certification_verdict"] == "Sn_Cloud_10k_Regression_Certified"


def test_lessons_learned_knowledge_graph():
    """驗證車規失效數據庫與知識圖譜編譯"""
    kg = build_knowledge_graph()
    assert kg["total_failures_indexed"] >= 4
    assert "ROOT_ELECTRICAL_NOISE" in kg["categories_covered"]
    assert "ROOT_AI_HALLUCINATION" in kg["categories_covered"]
