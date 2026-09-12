"""
Stage 1: ASIL Safety Supervisor State Machine with LangGraph
=============================================================
Features:
1. Vehicle Operating States: NORMAL_RUN, DEGRADED_WARN, EMERGENCY_SAFE, WAITING_CONFIRMATION
2. Two-Key Verbal Confirmation handshake for hazardous actuator commands.
3. Fault Tolerant Time Interval (FTTI) countdown & automatic safe state transition.
4. Reducer-safe state updates using operator.ior.
"""

import operator
import time
from enum import Enum
from typing import Annotated, Any, Dict, List, Optional, TypedDict
from langgraph.graph import END, START, StateGraph


# -----------------------------------------------------------------------------
# 1. 車載安全狀態與狀態定義 (ASIL Safe State Machine)
# -----------------------------------------------------------------------------
class SystemOperatingState(str, Enum):
    NORMAL_RUN = "NORMAL_RUN"
    DEGRADED_WARN = "DEGRADED_WARN"
    EMERGENCY_SAFE = "EMERGENCY_SAFE"
    WAITING_CONFIRMATION = "WAITING_CONFIRMATION"


class SafetyState(TypedDict):
    query: str
    current_state: SystemOperatingState
    pending_action: Optional[str]            # 暫態等待操作 (e.g., "CUT_PUMP_RELAY")
    action_requested_timestamp: float        # 請求時間戳，用於計算 FTTI
    ftti_limit_seconds: float                # FTTI 故障容忍超時門檻 (秒)
    is_confirmed_by_user: bool               # 是否已獲使用者口頭確認
    telemetry_data: Annotated[Dict[str, Any], operator.ior]
    target_nodes: List[str]
    spoken_response: str


# -----------------------------------------------------------------------------
# 2. Safety Supervisor 節點：狀態遷移與口頭雙重確認邏輯
# -----------------------------------------------------------------------------
def safety_supervisor_node(state: SafetyState) -> Dict[str, Any]:
    query = state.get("query", "").strip().lower()
    curr_state = state.get("current_state", SystemOperatingState.NORMAL_RUN)
    pending_action = state.get("pending_action")
    req_time = state.get("action_requested_timestamp", 0.0)
    ftti_limit = state.get("ftti_limit_seconds", 15.0)

    now = time.time()
    updates: Dict[str, Any] = {"target_nodes": []}

    # 檢查 1: 若處於等待確認狀態，檢查是否超時 (FTTI 逾時自動降級)
    if curr_state == SystemOperatingState.WAITING_CONFIRMATION:
        if now - req_time > ftti_limit:
            updates["current_state"] = SystemOperatingState.EMERGENCY_SAFE
            updates["pending_action"] = None
            updates["spoken_response"] = (
                f"安全超時！逾 {ftti_limit} 秒未獲確認，系統觸發 ASIL-D 緊急安全機制，已強制切斷高壓輸出！"
            )
            updates["target_nodes"] = ["synthesizer"]
            return updates

        # 檢查口語確認 (二階段確認交握)
        if any(w in query for w in ["確認", "執行", "yes", "confirm", "proceed"]):
            updates["current_state"] = SystemOperatingState.DEGRADED_WARN
            updates["is_confirmed_by_user"] = True
            updates["spoken_response"] = f"已取得授權，正在執行危險指令：{pending_action}。"
            updates["target_nodes"] = ["actuator_execution", "synthesizer"]
            updates["pending_action"] = None
            return updates
        elif any(w in query for w in ["取消", "停止", "cancel", "abort", "no"]):
            updates["current_state"] = SystemOperatingState.NORMAL_RUN
            updates["pending_action"] = None
            updates["spoken_response"] = "指令已取消，維持正常運行狀態。"
            updates["target_nodes"] = ["synthesizer"]
            return updates

    # 檢查 2: 攔截危險致動指令 (例如：切斷繼電器、斷開繼電器、cut relay、斷開高壓、清除故障碼)
    hazardous_triggers = ["切斷繼電器", "斷開繼電器", "cut relay", "斷開高壓", "清除故障碼"]
    matched_hazard = next((h for h in hazardous_triggers if h in query), None)

    if matched_hazard:
        # 不可直接執行，轉入 WAITING_CONFIRMATION
        updates["current_state"] = SystemOperatingState.WAITING_CONFIRMATION
        updates["pending_action"] = matched_hazard
        updates["action_requested_timestamp"] = now
        updates["spoken_response"] = (
            f"警告！偵測到高風險操作【{matched_hazard}】。這將影響動力與冷卻循環，請口頭回答「確認執行」或「取消」？"
        )
        updates["target_nodes"] = ["synthesizer"]
        return updates

    # 檢查 3: 一般遙測/診斷查詢 (轉派相應代理)
    target_nodes = []
    if any(w in query for w in ["溫度", "temperature", "coolant", "電壓", "數值"]):
        target_nodes.append("telemetry_agent")
    if not target_nodes:
        target_nodes.append("telemetry_agent")

    updates["target_nodes"] = target_nodes
    return updates


# -----------------------------------------------------------------------------
# 3. 執行節點與語音合成節點 (Workers & Synthesizer)
# -----------------------------------------------------------------------------
def telemetry_agent_node(state: SafetyState) -> Dict[str, Any]:
    """讀取車載感測器並依門檻更新警報狀態"""
    coolant = 106.2  # 模擬過溫
    status = "CRITICAL_HIGH" if coolant > 105.0 else "NORMAL"
    return {
        "telemetry_data": {"coolant_temp_c": coolant, "status": status},
        "current_state": (
            SystemOperatingState.DEGRADED_WARN if coolant > 105.0 else state.get("current_state")
        ),
    }


def actuator_execution_node(state: SafetyState) -> Dict[str, Any]:
    """實際向車載硬體下發致動指令 (只有通過確認才會到達此節點)"""
    return {"telemetry_data": {"relay_status": "DISCONNECTED", "safe_state_engaged": True}}


def synthesizer_node(state: SafetyState) -> Dict[str, Any]:
    """組裝最終 TTS 回覆語音"""
    # 若 Supervisor 已經有具體防護語音 (如確認提示、超時報警)，直接採用
    if state.get("spoken_response"):
        return {"spoken_response": state["spoken_response"]}

    # 否則組裝常規診斷結果
    t = state.get("telemetry_data", {})
    coolant = t.get("coolant_temp_c", 0)
    sys_state = state.get("current_state", SystemOperatingState.NORMAL_RUN)

    resp = f"目前冷卻液溫度為 {coolant} 度。"
    if sys_state == SystemOperatingState.DEGRADED_WARN:
        resp += " 系統已進入性能降級警示狀態，請留意硬體散熱。"

    return {"spoken_response": resp}


# -----------------------------------------------------------------------------
# 4. 條件路由與圖編譯 (Graph Assembly)
# -----------------------------------------------------------------------------
def route_from_supervisor(state: SafetyState) -> List[str]:
    return state.get("target_nodes", ["synthesizer"])


def build_safety_graph():
    builder = StateGraph(SafetyState)

    builder.add_node("safety_supervisor", safety_supervisor_node)
    builder.add_node("telemetry_agent", telemetry_agent_node)
    builder.add_node("actuator_execution", actuator_execution_node)
    builder.add_node("synthesizer", synthesizer_node)

    builder.add_edge(START, "safety_supervisor")

    builder.add_conditional_edges(
        "safety_supervisor",
        route_from_supervisor,
        {
            "telemetry_agent": "telemetry_agent",
            "actuator_execution": "actuator_execution",
            "synthesizer": "synthesizer",
        },
    )

    builder.add_edge("telemetry_agent", "synthesizer")
    builder.add_edge("actuator_execution", "synthesizer")
    builder.add_edge("synthesizer", END)

    return builder.compile()


# -----------------------------------------------------------------------------
# 5. 驗證情境演練
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    graph = build_safety_graph()

    print("--- [情境 1: 危險指令攔截 (觸發口語雙重確認)] ---")
    s1 = graph.invoke({
        "query": "幫我切斷繼電器！",
        "current_state": SystemOperatingState.NORMAL_RUN,
        "pending_action": None,
        "action_requested_timestamp": 0.0,
        "ftti_limit_seconds": 5.0,
        "is_confirmed_by_user": False,
        "telemetry_data": {},
        "target_nodes": [],
        "spoken_response": "",
    })
    print(f"當前狀態: {s1['current_state']}")
    print(f"語音輸出: {s1['spoken_response']}\n")

    print("--- [情境 2: 操作者回覆「確認執行」] ---")
    s2 = graph.invoke({
        **s1,
        "query": "確認執行",
        "spoken_response": "",
    })
    print(f"當前狀態: {s2['current_state']}")
    print(f"遙測反饋: {s2['telemetry_data']}")
    print(f"語音輸出: {s2['spoken_response']}\n")

    print("--- [情境 3: FTTI 故障容忍超時未確認 (自動觸發 EMERGENCY_SAFE)] ---")
    # 模擬 6 秒前發起的請求 (超時門檻 5 秒)
    s3 = graph.invoke({
        "query": "還有其他狀態嗎？",
        "current_state": SystemOperatingState.WAITING_CONFIRMATION,
        "pending_action": "切斷繼電器",
        "action_requested_timestamp": time.time() - 6.0,
        "ftti_limit_seconds": 5.0,
        "is_confirmed_by_user": False,
        "telemetry_data": {},
        "target_nodes": [],
        "spoken_response": "",
    })
    print(f"當前狀態: {s3['current_state']}")
    print(f"語音輸出: {s3['spoken_response']}")
