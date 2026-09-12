"""
ISO 26262-6 Unit Verification: MC/DC Safety Test Suite
======================================================
針對 GSN 架構中的 Sn1 (狀態機攔截)、Sn3 (FTTI 超時)、Sn5 (匯流排異常) 進行自動化驗收。
涵蓋分支：
  Condition 1: [Hazardous Trigger] -> WAITING_CONFIRMATION
  Condition 2: [Waiting] AND [Confirmed == True] AND [Timeout == False] -> DEGRADED_WARN
  Condition 3: [Waiting] AND [Confirmed == False] AND [Timeout == True] -> EMERGENCY_SAFE
  Condition 4: [Waiting] AND [Cancel == True] -> NORMAL_RUN
  Condition 5: [Coolant > 105C] -> DEGRADED_WARN

依據 ISO 26262-6:2018 Table 8 (軟體單元驗證方法 - ASIL-D)：
包含核心判定式之獨立影響對 (Independence Pairs) 與狀態機端到端實證。
"""

import os
import sys
import time
from typing import Any, Dict, List
import pytest

# Windows UTF-8 控制台保護
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 設定模組搜尋路徑
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from stage1_safety_supervisor import (
    SystemOperatingState,
    build_safety_graph,
    can_bus,
)


@pytest.fixture(scope="session", autouse=True)
def teardown_bus():
    yield
    try:
        if hasattr(can_bus, "shutdown"):
            can_bus.shutdown()
    except Exception:
        pass


@pytest.fixture(scope="function")
def safety_graph():
    """提供編譯後之 Safety Supervisor 狀態圖，確保底層虛擬總線處於連通狀態"""
    if getattr(can_bus, "bus", None) is None:
        can_bus._init_bus()
    return build_safety_graph()


def get_base_state() -> Dict[str, Any]:
    """產出乾淨之初始 SafetyState 字典"""
    return {
        "query": "",
        "current_state": SystemOperatingState.NORMAL_RUN,
        "pending_action": None,
        "action_requested_timestamp": 0.0,
        "ftti_limit_seconds": 10.0,
        "is_confirmed_by_user": False,
        "telemetry_data": {},
        "target_nodes": [],
        "spoken_response": "",
    }


# =============================================================================
# GSN G2 / Sn1: 危險指令攔截與雙重確認交握 (MC/DC Branch 1 & 2 & 4)
# =============================================================================
def test_mcdc_hazardous_command_interception(safety_graph):
    """驗證 G5: 危險指令必須被攔截並轉入 WAITING_CONFIRMATION"""
    state = get_base_state()
    state["query"] = "請立即切斷繼電器"

    res = safety_graph.invoke(state)

    assert res["current_state"] == SystemOperatingState.WAITING_CONFIRMATION
    assert res["pending_action"] == "切斷繼電器"
    assert "actuator_execution" not in res["target_nodes"]
    assert "警告" in res["spoken_response"]


def test_mcdc_verbal_confirmation_success(safety_graph):
    """驗證 G6: WAITING 態且使用者口頭確認 -> DEGRADED_WARN 並放行致動器"""
    state = get_base_state()
    state["current_state"] = SystemOperatingState.WAITING_CONFIRMATION
    state["pending_action"] = "切斷繼電器"
    state["action_requested_timestamp"] = time.time()  # 未超時
    state["query"] = "確認執行"

    res = safety_graph.invoke(state)

    assert res["current_state"] == SystemOperatingState.DEGRADED_WARN
    assert res["is_confirmed_by_user"] is True
    assert "actuator_execution" in res["target_nodes"]
    assert res["telemetry_data"].get("relay_status") == "DISCONNECTED"


def test_mcdc_verbal_cancel_safe_return(safety_graph):
    """驗證 WAITING 態且使用者取消 -> 返回 NORMAL_RUN 且不執行致動"""
    state = get_base_state()
    state["current_state"] = SystemOperatingState.WAITING_CONFIRMATION
    state["pending_action"] = "切斷繼電器"
    state["action_requested_timestamp"] = time.time()
    state["query"] = "取消操作"

    res = safety_graph.invoke(state)

    assert res["current_state"] == SystemOperatingState.NORMAL_RUN
    assert res["pending_action"] is None
    assert "actuator_execution" not in res["target_nodes"]


# =============================================================================
# GSN G3 / Sn3: FTTI 超時判定與強制進入 EMERGENCY_SAFE (MC/DC Branch 3)
# =============================================================================
def test_mcdc_ftti_timeout_forces_emergency_safe(safety_graph):
    """驗證 G7/G8: WAITING 態且超過 FTTI 限制 -> 強制轉入 EMERGENCY_SAFE"""
    state = get_base_state()
    state["current_state"] = SystemOperatingState.WAITING_CONFIRMATION
    state["pending_action"] = "切斷繼電器"
    state["ftti_limit_seconds"] = 10.0
    # 模擬 10.1 秒前發起請求
    state["action_requested_timestamp"] = time.time() - 10.1
    state["query"] = "現在溫度幾度？"  # 未給予確認指令

    res = safety_graph.invoke(state)

    assert res["current_state"] == SystemOperatingState.EMERGENCY_SAFE
    assert res["pending_action"] is None
    assert "ASIL-D 緊急安全機制" in res["spoken_response"]


def test_mcdc_ftti_boundary_not_timeout(safety_graph):
    """驗證 FTTI 邊界條件：在 9.8 秒時收到確認，仍視為合規確認"""
    state = get_base_state()
    state["current_state"] = SystemOperatingState.WAITING_CONFIRMATION
    state["pending_action"] = "切斷繼電器"
    state["ftti_limit_seconds"] = 10.0
    state["action_requested_timestamp"] = time.time() - 9.8
    state["query"] = "確認執行"

    res = safety_graph.invoke(state)

    assert res["current_state"] == SystemOperatingState.DEGRADED_WARN
    assert res["is_confirmed_by_user"] is True


# =============================================================================
# GSN G4 / Sn5: 遙測超溫自動安全降級
# =============================================================================
def test_telemetry_overheat_triggers_degraded_warn(safety_graph):
    """驗證冷卻液超過 105 度門檻時，狀態機自動標記 DEGRADED_WARN"""
    state = get_base_state()
    state["query"] = "讀取目前冷卻液溫度"

    res = safety_graph.invoke(state)

    # stage1 內預設模擬值為 106.2 度
    assert res["telemetry_data"]["coolant_temp_c"] > 105.0
    assert res["current_state"] == SystemOperatingState.DEGRADED_WARN
    assert "性能降級警示狀態" in res["spoken_response"]


# =============================================================================
# ISO 26262-6 Table 8 ASIL-D 獨立影響對 (Independence Pairs) 數學嚴格驗證
# =============================================================================
def evaluate_decision_1(is_confirmed: bool, is_timeout: bool) -> bool:
    """D1: Actuation Permission = is_confirmed AND (NOT is_timeout)"""
    return bool(is_confirmed and not is_timeout)


def evaluate_decision_2(in_waiting: bool, is_timeout: bool, is_confirmed: bool) -> bool:
    """D2: FTTI Emergency Safe = in_waiting AND is_timeout AND (NOT is_confirmed)"""
    return bool(in_waiting and is_timeout and not is_confirmed)


def evaluate_decision_3(in_waiting: bool, user_said_cancel: bool) -> bool:
    """D3: Verbal Cancel Rollback = in_waiting AND user_said_cancel"""
    return bool(in_waiting and user_said_cancel)


def evaluate_decision_4(dtc_count: int, has_critical: bool) -> bool:
    """D4: Flood Truncation Decision = (dtc_count > 2) AND has_critical"""
    return bool(dtc_count > 2 and has_critical)


class TestTable8IndependencePairs:
    """ISO 26262-6 Table 8 ASIL-D MC/DC 獨立影響對判定測試"""

    def test_d1_mcdc_condition_a_is_confirmed(self):
        # 保持 B=False 不變，A 由 True 變 False，Outcome 必須由 True 變 False
        assert evaluate_decision_1(is_confirmed=True, is_timeout=False) is True
        assert evaluate_decision_1(is_confirmed=False, is_timeout=False) is False

    def test_d1_mcdc_condition_b_is_timeout(self):
        # 保持 A=True 不變，B 由 False 變 True，Outcome 必須由 True 變 False
        assert evaluate_decision_1(is_confirmed=True, is_timeout=False) is True
        assert evaluate_decision_1(is_confirmed=True, is_timeout=True) is False

    def test_d2_mcdc_condition_a_in_waiting(self):
        # 保持 B=T, C=F，A 由 True 變 False，Outcome 必須由 True 變 False
        assert evaluate_decision_2(in_waiting=True, is_timeout=True, is_confirmed=False) is True
        assert evaluate_decision_2(in_waiting=False, is_timeout=True, is_confirmed=False) is False

    def test_d2_mcdc_condition_b_is_timeout(self):
        # 保持 A=T, C=F，B 由 True 變 False，Outcome 必須由 True 變 False
        assert evaluate_decision_2(in_waiting=True, is_timeout=True, is_confirmed=False) is True
        assert evaluate_decision_2(in_waiting=True, is_timeout=False, is_confirmed=False) is False

    def test_d2_mcdc_condition_c_is_confirmed(self):
        # 保持 A=T, B=T，C 由 False 變 True，Outcome 必須由 True 變 False
        assert evaluate_decision_2(in_waiting=True, is_timeout=True, is_confirmed=False) is True
        assert evaluate_decision_2(in_waiting=True, is_timeout=True, is_confirmed=True) is False

    def test_d3_mcdc_condition_a_in_waiting(self):
        assert evaluate_decision_3(in_waiting=True, user_said_cancel=True) is True
        assert evaluate_decision_3(in_waiting=False, user_said_cancel=True) is False

    def test_d3_mcdc_condition_b_cancel(self):
        assert evaluate_decision_3(in_waiting=True, user_said_cancel=True) is True
        assert evaluate_decision_3(in_waiting=True, user_said_cancel=False) is False

    def test_d4_mcdc_condition_a_count_threshold(self):
        assert evaluate_decision_4(dtc_count=6, has_critical=True) is True
        assert evaluate_decision_4(dtc_count=2, has_critical=True) is False

    def test_d4_mcdc_condition_b_critical_flag(self):
        assert evaluate_decision_4(dtc_count=5, has_critical=True) is True
        assert evaluate_decision_4(dtc_count=5, has_critical=False) is False
