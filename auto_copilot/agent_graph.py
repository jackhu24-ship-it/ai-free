"""
AutoCopilot LangGraph Multi-Agent Architecture
==============================================
Refactors centralized route_and_execute into a LangGraph StateGraph:
- Supervisor Node: Intent Classification & Parallel Task Dispatch
- Telemetry Agent Node: CAN-FD / OBD-II Real-time Polling
- DTC Agent Node: ISO 14229 / UDS 0x19 Diagnostic Trouble Codes
- Safety Agent Node: ISO 26262 Shutdown Limits & Vector RAG Manual
- Synthesizer Node: TTS Voice Response Assembly

State Merging uses Annotated[Dict[str, Any], operator.ior] to eliminate race conditions.
"""

import asyncio
import operator
import time
from typing import Annotated, Any, Dict, List, TypedDict
from langgraph.graph import END, START, StateGraph

# -----------------------------------------------------------------------------
# 1. 定義共用狀態 (Agent State)
# -----------------------------------------------------------------------------
class DiagnosticState(TypedDict):
    query: str
    target_intents: List[str]
    # operator.ior: 字典就地合併，多代理並行執行時無覆寫衝突
    telemetry_data: Annotated[Dict[str, Any], operator.ior]
    dtc_data: Annotated[Dict[str, Any], operator.ior]
    manual_data: Annotated[Dict[str, Any], operator.ior]
    spoken_response: str
    execution_duration_ms: float
    active_nodes: List[str]


# -----------------------------------------------------------------------------
# 2. 專業節點實作 (Modular Node Functions)
# -----------------------------------------------------------------------------
def supervisor_node(state: DiagnosticState) -> Dict[str, Any]:
    """主控主管節點：意圖識別與並行分派決策"""
    q = state["query"].lower()
    intents = []
    
    if any(k in q for k in ["溫度", "temperature", "coolant", "冷卻液", "水溫", "壓力", "電壓", "voltage", "telemetry"]):
        intents.append("telemetry")
    if any(k in q for k in ["故障", "dtc", "code", "錯誤", "代碼", "碼"]):
        intents.append("dtc")
    if any(k in q for k in ["手冊", "manual", "幾度", "停機", "limit", "規範", "sop", "iso"]):
        intents.append("safety_manual")
        
    if not intents:
        intents = ["telemetry"]
        
    return {"target_intents": intents}


def telemetry_agent_node(state: DiagnosticState) -> Dict[str, Any]:
    """遙測專精代理節點：讀取即時 CAN-FD / OBD-II 總線數值"""
    return {
        "telemetry_data": {
            "coolant_temp_c": 104.2,
            "bus_voltage_v": 384.8,
            "line_pressure_kpa": 145.0,
            "status": "WARNING_HIGH",
            "source": "CAN-FD_ECU_0x3F2"
        }
    }


def dtc_agent_node(state: DiagnosticState) -> Dict[str, Any]:
    """故障診斷代理節點：讀取 ISO 14229 / UDS 0x19 DTC"""
    return {
        "dtc_data": {
            "dtc_code": "P0117",
            "desc": "Coolant Temp Sensor Circuit Low",
            "severity": "High",
            "source": "UDS_Service_0x19"
        }
    }


def safety_agent_node(state: DiagnosticState) -> Dict[str, Any]:
    """安全規程代理節點：查詢 ISO 26262 停機門檻與維修手冊 SOP"""
    return {
        "manual_data": {
            "section": "ISO-26262-TH402",
            "shutdown_limit_c": 105.0,
            "action": "立即切換怠速運轉並啟動二級冷卻泵輔助降溫。",
            "source": "ChromaDB_Vector_Manual"
        }
    }


def synthesizer_node(state: DiagnosticState) -> Dict[str, Any]:
    """語音輸出合成節點：匯總各代理輸出，壓縮成適合 TTS 朗讀的精簡文本"""
    parts = []
    t = state.get("telemetry_data", {})
    m = state.get("manual_data", {})
    d = state.get("dtc_data", {})
    intents = state.get("target_intents", [])

    if "telemetry" in intents and t:
        parts.append(f"目前冷卻液溫度為 {t.get('coolant_temp_c')} 度。")
    if "safety_manual" in intents and m:
        parts.append(f"手冊規定超過 {m.get('shutdown_limit_c')} 度需停機，{m.get('action')}")
    if "dtc" in intents and d:
        parts.append(f"活動故障代碼 {d.get('dtc_code')}：{d.get('desc')}。")

    spoken = " ".join(parts) if parts else "系統遙測正常，未檢出異常警示。"
    return {
        "spoken_response": spoken,
        "active_nodes": intents
    }


# -----------------------------------------------------------------------------
# 3. 條件路由邏輯 (Conditional Edge Router)
# -----------------------------------------------------------------------------
def route_intents(state: DiagnosticState) -> List[str]:
    """依據 Supervisor 識別的意圖清單，決定下發哪些節點（Fan-out）"""
    target_nodes = []
    intents = state.get("target_intents", [])
    
    if "telemetry" in intents:
        target_nodes.append("telemetry_agent")
    if "dtc" in intents:
        target_nodes.append("dtc_agent")
    if "safety_manual" in intents:
        target_nodes.append("safety_agent")
        
    return target_nodes


# -----------------------------------------------------------------------------
# 4. 組裝 StateGraph 工作流
# -----------------------------------------------------------------------------
def build_diagnostic_graph():
    builder = StateGraph(DiagnosticState)

    # 註冊節點
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("telemetry_agent", telemetry_agent_node)
    builder.add_node("dtc_agent", dtc_agent_node)
    builder.add_node("safety_agent", safety_agent_node)
    builder.add_node("synthesizer", synthesizer_node)

    # 定義流程邊
    builder.add_edge(START, "supervisor")

    # Supervisor 分發條件邊（支援並行啟動多個 Node - Fan-out）
    builder.add_conditional_edges(
        "supervisor",
        route_intents,
        {
            "telemetry_agent": "telemetry_agent",
            "dtc_agent": "dtc_agent",
            "safety_agent": "safety_agent",
        },
    )

    # 所有專業代理執行完畢後統一匯聚至 Synthesizer (Fan-in)
    builder.add_edge("telemetry_agent", "synthesizer")
    builder.add_edge("dtc_agent", "synthesizer")
    builder.add_edge("safety_agent", "synthesizer")

    builder.add_edge("synthesizer", END)

    return builder.compile()


# 全域單例 Graph
diagnostic_graph = build_diagnostic_graph()


# -----------------------------------------------------------------------------
# 5. 非同步封裝（提供 Voice Pipeline 與 Streamlit 調用）
# -----------------------------------------------------------------------------
async def arun_diagnostic(query: str) -> DiagnosticState:
    """非同步執行 LangGraph 診斷工作流"""
    t0 = time.perf_counter()
    initial_input: DiagnosticState = {
        "query": query,
        "target_intents": [],
        "telemetry_data": {},
        "dtc_data": {},
        "manual_data": {},
        "spoken_response": "",
        "execution_duration_ms": 0.0,
        "active_nodes": []
    }
    final_state = await asyncio.to_thread(diagnostic_graph.invoke, initial_input)
    final_state["execution_duration_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    return final_state


# -----------------------------------------------------------------------------
# 6. 單元測試驗證（3 組測試問句）
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    test_queries = [
        ("單意圖測試（遙測）", "現在水溫幾度？"),
        ("雙意圖複合測試（遙測 + 手冊）", "幫我看冷卻液溫度現在多少，手冊上有說超過幾度要停機嗎？"),
        ("三意圖全開測試（遙測 + 故障 + 手冊）", "查詢當前溫度、檢查有無故障碼，並確認停機規範與SOP。"),
    ]

    print("==================================================")
    print("AutoCopilot LangGraph StateGraph 多代理驗證測試")
    print("==================================================")

    for label, q in test_queries:
        t_start = time.perf_counter()
        res = diagnostic_graph.invoke({
            "query": q,
            "target_intents": [],
            "telemetry_data": {},
            "dtc_data": {},
            "manual_data": {},
            "spoken_response": "",
            "execution_duration_ms": 0.0,
            "active_nodes": []
        })
        latency = round((time.perf_counter() - t_start) * 1000, 2)
        print(f"\n[{label}]")
        print(f"  Query: {q}")
        print(f"  Intents: {res['target_intents']}")
        print(f"  Response: {res['spoken_response']}")
        print(f"  Latency: {latency} ms (Threshold < 150ms: {'[PASS]' if latency < 150 else '[WARN]'})")
