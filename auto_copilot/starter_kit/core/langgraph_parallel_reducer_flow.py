"""
=============================================================================
模組 B：LangGraph 並行狀態機 (langgraph_parallel_reducer_flow.py)
=============================================================================
Universal Multi-Agent Orchestration Pattern:
- LangGraph StateGraph with dynamic conditional edge fan-out/fan-in
- operator.ior dictionary merging (Zero race condition, zero lock contention)
- stream_mode="updates" progressive state streaming for sub-5ms latency observability
=============================================================================
"""

import asyncio
import operator
import time
from typing import Annotated, Any, AsyncGenerator, Dict, List, TypedDict
from langgraph.graph import END, START, StateGraph

class ParallelAgentState(TypedDict):
    """Universal state schema with lock-free dictionary reducers."""
    query: str
    target_intents: List[str]
    # operator.ior ensures child dictionaries merge in-place safely during concurrency
    telemetry_state: Annotated[Dict[str, Any], operator.ior]
    diagnostic_state: Annotated[Dict[str, Any], operator.ior]
    knowledge_state: Annotated[Dict[str, Any], operator.ior]
    spoken_response: str
    execution_duration_ms: float

def build_parallel_reducer_graph() -> StateGraph:
    """Builds and compiles the parallel fan-out/fan-in StateGraph."""
    graph = StateGraph(ParallelAgentState)

    # 1. Supervisor / Dispatcher
    def supervisor_node(state: ParallelAgentState) -> Dict[str, Any]:
        q = state["query"].lower()
        intents = []
        if any(k in q for k in ["temp", "telemetry", "speed", "voltage", "水溫", "遙測"]):
            intents.append("telemetry")
        if any(k in q for k in ["fault", "dtc", "code", "error", "故障"]):
            intents.append("diagnostic")
        if any(k in q for k in ["manual", "limit", "iso", "sop", "手冊", "規範"]):
            intents.append("knowledge")
        return {"target_intents": intents if intents else ["telemetry"]}

    # 2. Specialized Parallel Worker Nodes
    def telemetry_node(state: ParallelAgentState) -> Dict[str, Any]:
        return {"telemetry_state": {"coolant_temp_c": 104.2, "status": "NOMINAL", "latency_ms": 1.2}}

    def diagnostic_node(state: ParallelAgentState) -> Dict[str, Any]:
        return {"diagnostic_state": {"dtc_codes": ["P0117"], "severity": "HIGH", "latency_ms": 1.5}}

    def knowledge_node(state: ParallelAgentState) -> Dict[str, Any]:
        return {"knowledge_state": {"iso_limit_c": 105.0, "compliance": "ASIL-B", "latency_ms": 1.8}}

    # 3. Fan-in Synthesizer Node
    def synthesizer_node(state: ParallelAgentState) -> Dict[str, Any]:
        intents = state.get("target_intents", [])
        return {"spoken_response": f"Diagnostic complete across {len(intents)} subsystems."}

    # Register Nodes
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("telemetry_agent", telemetry_node)
    graph.add_node("diagnostic_agent", diagnostic_node)
    graph.add_node("knowledge_agent", knowledge_node)
    graph.add_node("synthesizer", synthesizer_node)

    # Edges & Conditional Fan-out
    graph.add_edge(START, "supervisor")

    def route_intents(state: ParallelAgentState) -> List[str]:
        routes = []
        intents = state.get("target_intents", [])
        if "telemetry" in intents:
            routes.append("telemetry_agent")
        if "diagnostic" in intents:
            routes.append("diagnostic_agent")
        if "knowledge" in intents:
            routes.append("knowledge_agent")
        return routes if routes else ["telemetry_agent"]

    graph.add_conditional_edges("supervisor", route_intents, {
        "telemetry_agent": "telemetry_agent",
        "diagnostic_agent": "diagnostic_agent",
        "knowledge_agent": "knowledge_agent"
    })

    # Fan-in convergence
    graph.add_edge("telemetry_agent", "synthesizer")
    graph.add_edge("diagnostic_agent", "synthesizer")
    graph.add_edge("knowledge_agent", "synthesizer")
    graph.add_edge("synthesizer", END)

    return graph.compile()

async def stream_agent_updates(query: str) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Executes the compiled graph in stream_mode="updates" to yield step-by-step activations.
    """
    compiled_graph = build_parallel_reducer_graph()
    initial_state = {
        "query": query,
        "target_intents": [],
        "telemetry_state": {},
        "diagnostic_state": {},
        "knowledge_state": {},
        "spoken_response": "",
        "execution_duration_ms": 0.0
    }
    t0 = time.perf_counter()
    # stream_mode="updates" yields only the updated node and its delta dictionary
    for update in compiled_graph.stream(initial_state, stream_mode="updates"):
        node_name = list(update.keys())[0]
        node_delta = update[node_name]
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        yield {
            "node": node_name,
            "delta": node_delta,
            "elapsed_ms": elapsed_ms
        }
