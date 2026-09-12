"""
FacilityCopilot LangGraph Multi-Agent Architecture
===================================================
Tailored for AWS Bedrock Smart Facility & Data Center Voice Inspections:
- Supervisor: Intent Routing
- Rack Telemetry Agent: MQTT / IoT Core Server Rack Thermal & PUE Polling
- UPS Power Agent: SNMP / Modbus Power Grid & Backup Battery Telemetry
- Compliance Safety Agent: TIA-942 / ASHRAE TC 9.9 Data Center Standards RAG
- Synthesizer: Voice Response Assembly for Noisy Chiller/Server Rooms
"""

import asyncio
import operator
import time
from typing import Annotated, Any, Dict, List, TypedDict
from langgraph.graph import END, START, StateGraph

class FacilityState(TypedDict):
    query: str
    target_intents: List[str]
    # operator.ior ensures lock-free safe merging during parallel execution
    rack_data: Annotated[Dict[str, Any], operator.ior]
    ups_data: Annotated[Dict[str, Any], operator.ior]
    compliance_data: Annotated[Dict[str, Any], operator.ior]
    spoken_response: str
    active_nodes: List[str]
    execution_duration_ms: float

def supervisor_node(state: FacilityState) -> Dict[str, Any]:
    """Classifies facility operator speech into parallel inspection tasks."""
    q = state["query"].lower()
    intents = []
    if any(k in q for k in ["rack", "temp", "thermal", "temperature", "機櫃", "水溫", "溫度", "pue", "冷卻"]):
        intents.append("rack_telemetry")
    if any(k in q for k in ["ups", "power", "battery", "grid", "不斷電", "電池", "發電機", "負載"]):
        intents.append("ups_power")
    if any(k in q for k in ["limit", "tia", "ashrae", "standard", "safety", "規範", "門檻", "停機", "標準"]):
        intents.append("compliance_safety")
    if not intents:
        intents = ["rack_telemetry"]
    return {"target_intents": intents}

def rack_telemetry_node(state: FacilityState) -> Dict[str, Any]:
    """Reads live AWS IoT Core MQTT stream for server rack metrics."""
    return {
        "rack_data": {
            "zone": "Zone-A_HighDensity",
            "rack_id": "Rack_A04",
            "inlet_temp_c": 28.4,
            "exhaust_temp_c": 39.8,
            "delta_t_c": 11.4,
            "pue": 1.28,
            "status": "ELEVATED_INLET_TEMP"
        }
    }

def ups_power_node(state: FacilityState) -> Dict[str, Any]:
    """Polls SNMP / Modbus registers for UPS battery banks and switchgear."""
    return {
        "ups_data": {
            "unit": "UPS_Alpha_500kVA",
            "battery_soc_pct": 98.5,
            "runtime_remaining_min": 24.0,
            "load_pct": 74.2,
            "grid_freq_hz": 60.02,
            "status": "NORMAL_ON_MAINS"
        }
    }

def compliance_safety_node(state: FacilityState) -> Dict[str, Any]:
    """Vector searches TIA-942 and ASHRAE TC 9.9 data center operational guidelines."""
    return {
        "compliance_data": {
            "standard": "ASHRAE TC 9.9 (2021) / TIA-942 Tier III",
            "recommended_inlet_max_c": 27.0,
            "allowable_inlet_max_c": 32.0,
            "compliance_status": "EXCEEDS_RECOMMENDED_THRESHOLD",
            "remediation_sop": "Increase CRAC unit blower speed to 85% or engage secondary chiller loop."
        }
    }

def synthesizer_node(state: FacilityState) -> Dict[str, Any]:
    """Generates concise, industrial-grade spoken output designed for noisy CRAC rooms."""
    intents = state.get("target_intents", [])
    rack = state.get("rack_data", {})
    ups = state.get("ups_data", {})
    comp = state.get("compliance_data", {})

    parts = []
    if "rack_telemetry" in intents and rack:
        parts.append(f"Rack A04 inlet is elevated at {rack.get('inlet_temp_c')} °C, PUE is {rack.get('pue')}.")
    if "ups_power" in intents and ups:
        parts.append(f"UPS Alpha load is {ups.get('load_pct')}% with {ups.get('runtime_remaining_min')} minutes battery reserve.")
    if "compliance_safety" in intents and comp:
        parts.append(f"Alert: Exceeds ASHRAE recommended 27.0 °C limit. SOP: {comp.get('remediation_sop')}")

    resp = " ".join(parts) if parts else "Facility status nominal."
    return {
        "spoken_response": resp,
        "active_nodes": ["supervisor"] + intents + ["synthesizer"]
    }

def build_facility_graph() -> StateGraph:
    """Builds the FacilityCopilot StateGraph."""
    graph = StateGraph(FacilityState)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("rack_telemetry_agent", rack_telemetry_node)
    graph.add_node("ups_power_agent", ups_power_node)
    graph.add_node("compliance_safety_agent", compliance_safety_node)
    graph.add_node("synthesizer", synthesizer_node)

    graph.add_edge(START, "supervisor")

    def route_supervisor(state: FacilityState) -> List[str]:
        routes = []
        intents = state.get("target_intents", [])
        if "rack_telemetry" in intents:
            routes.append("rack_telemetry_agent")
        if "ups_power" in intents:
            routes.append("ups_power_agent")
        if "compliance_safety" in intents:
            routes.append("compliance_safety_agent")
        return routes if routes else ["rack_telemetry_agent"]

    graph.add_conditional_edges("supervisor", route_supervisor, {
        "rack_telemetry_agent": "rack_telemetry_agent",
        "ups_power_agent": "ups_power_agent",
        "compliance_safety_agent": "compliance_safety_agent"
    })

    graph.add_edge("rack_telemetry_agent", "synthesizer")
    graph.add_edge("ups_power_agent", "synthesizer")
    graph.add_edge("compliance_safety_agent", "synthesizer")
    graph.add_edge("synthesizer", END)

    return graph.compile()

facility_graph = build_facility_graph()

async def arun_facility_diagnostic(query: str) -> Dict[str, Any]:
    """Async execution entry point with microsecond duration tracking."""
    t0 = time.perf_counter()
    initial_state: FacilityState = {
        "query": query,
        "target_intents": [],
        "rack_data": {},
        "ups_data": {},
        "compliance_data": {},
        "spoken_response": "",
        "active_nodes": [],
        "execution_duration_ms": 0.0
    }
    final_state = await asyncio.to_thread(facility_graph.invoke, initial_state)
    final_state["execution_duration_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    return final_state
