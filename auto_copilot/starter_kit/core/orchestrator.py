"""
voice-agent-langgraph-starter: core/orchestrator.py
===================================================
Standard LangGraph StateGraph scaffold with conditional edges,
parallel multi-agent fan-out/fan-in, and operator.ior dictionary merging.
"""

import asyncio
import operator
import time
from typing import Annotated, Any, Dict, List, TypedDict
from langgraph.graph import END, START, StateGraph

class AgentState(TypedDict):
    """Universal state schema for voice-driven multi-agent orchestration."""
    query: str
    target_intents: List[str]
    # operator.ior merges child dictionaries in-place without race conditions
    telemetry_data: Annotated[Dict[str, Any], operator.ior]
    diagnostic_data: Annotated[Dict[str, Any], operator.ior]
    knowledge_data: Annotated[Dict[str, Any], operator.ior]
    spoken_response: str
    active_nodes: List[str]
    execution_duration_ms: float

def build_voice_agent_graph(custom_nodes: Dict[str, Any] = None) -> StateGraph:
    """Builds and compiles a generic LangGraph StateGraph for multi-agent workflows."""
    graph = StateGraph(AgentState)

    # 1. Supervisor / Dispatcher
    def supervisor(state: AgentState) -> Dict[str, Any]:
        q = state["query"].lower()
        intents = []
        if any(k in q for k in ["status", "telemetry", "temp", "speed", "metric"]):
            intents.append("telemetry")
        if any(k in q for k in ["fault", "error", "code", "dtc"]):
            intents.append("diagnostic")
        if any(k in q for k in ["manual", "limit", "guide", "sop"]):
            intents.append("knowledge")
        if not intents:
            intents = ["telemetry"]
        return {"target_intents": intents}

    # 2. Worker Nodes (Fallbacks or Injected)
    def default_telemetry(state: AgentState) -> Dict[str, Any]:
        return {"telemetry_data": {"metric": "nominal", "timestamp": time.time()}}

    def default_diagnostic(state: AgentState) -> Dict[str, Any]:
        return {"diagnostic_data": {"status": "clear", "active_codes": []}}

    def default_knowledge(state: AgentState) -> Dict[str, Any]:
        return {"knowledge_data": {"sop": "standard_operating_procedure_ok"}}

    def synthesizer(state: AgentState) -> Dict[str, Any]:
        intents = state.get("target_intents", [])
        return {"spoken_response": f"Acknowledged. Processed intents: {', '.join(intents)}."}

    graph.add_node("supervisor", supervisor)
    graph.add_node("telemetry_agent", default_telemetry)
    graph.add_node("diagnostic_agent", default_diagnostic)
    graph.add_node("knowledge_agent", default_knowledge)
    graph.add_node("synthesizer", synthesizer)

    graph.add_edge(START, "supervisor")

    def route_supervisor(state: AgentState):
        targets = []
        intents = state.get("target_intents", [])
        if "telemetry" in intents:
            targets.append("telemetry_agent")
        if "diagnostic" in intents:
            targets.append("diagnostic_agent")
        if "knowledge" in intents:
            targets.append("knowledge_agent")
        return targets if targets else ["telemetry_agent"]

    graph.add_conditional_edges("supervisor", route_supervisor, {
        "telemetry_agent": "telemetry_agent",
        "diagnostic_agent": "diagnostic_agent",
        "knowledge_agent": "knowledge_agent"
    })

    graph.add_edge("telemetry_agent", "synthesizer")
    graph.add_edge("diagnostic_agent", "synthesizer")
    graph.add_edge("knowledge_agent", "synthesizer")
    graph.add_edge("synthesizer", END)

    return graph.compile()
