"""
AutoCopilot End-to-End Unit & Integration Test Suite
Verifies AssemblyAI Voice Agent, Parallel Tool Calling, Barge-in, and RAG.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient

from auto_copilot.config import ASSEMBLYAI_AGENT_CONFIG, WORD_BOOST_LIST
from auto_copilot.schemas import FUNCTION_CALLING_TOOLS
from auto_copilot.telemetry_gateway import telemetry_gateway
from auto_copilot.rag_engine import rag_engine
from auto_copilot.agent_core import auto_copilot_agent, BargeInController
from auto_copilot.server import app

client = TestClient(app)

# -------------------------------------------------------------
# Test 1: Configuration & Word Boost Verification
# -------------------------------------------------------------
def test_config_and_word_boost():
    assert ASSEMBLYAI_AGENT_CONFIG["transcription"]["model"] == "universal-3-pro"
    assert ASSEMBLYAI_AGENT_CONFIG["agent"]["barge_in"]["enabled"] is True
    assert ASSEMBLYAI_AGENT_CONFIG["agent"]["vad"]["silence_duration_ms"] == 450
    assert len(WORD_BOOST_LIST) >= 15
    assert "CAN-FD" in WORD_BOOST_LIST
    assert "ISO 14229" in WORD_BOOST_LIST
    assert "P0117" in WORD_BOOST_LIST

# -------------------------------------------------------------
# Test 2: Function Calling Schemas Integrity
# -------------------------------------------------------------
def test_function_calling_schemas():
    assert len(FUNCTION_CALLING_TOOLS) == 3
    tool_names = [t["function"]["name"] for t in FUNCTION_CALLING_TOOLS]
    assert "get_vehicle_telemetry" in tool_names
    assert "read_diagnostic_trouble_codes" in tool_names
    assert "lookup_repair_procedure" in tool_names

# -------------------------------------------------------------
# Test 3: Telemetry Gateway & DTC Retrieval
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_telemetry_gateway():
    res = await telemetry_gateway.get_vehicle_telemetry(
        subsystem="thermal_management",
        metric_keys=["coolant_temp_c", "coolant_line_pressure_kpa"]
    )
    assert res["subsystem"] == "thermal_management"
    assert "coolant_temp_c" in res["data"]
    assert res["status"] in ["warning", "critical", "normal"]

    # 測試 DTC 讀取 (包含凍結幀)
    dtc_res = await telemetry_gateway.read_diagnostic_trouble_codes(
        ecu_target="all",
        include_snapshot_data=True
    )
    assert dtc_res["total_dtcs"] >= 2
    codes = [d["code"] for d in dtc_res["codes"]]
    assert "P0117" in codes
    p0117_entry = next(d for d in dtc_res["codes"] if d["code"] == "P0117")
    assert "freeze_frame" in p0117_entry
    assert p0117_entry["freeze_frame"]["coolant_temp_c"] >= 100.0

# -------------------------------------------------------------
# Test 4: RAG Engine Procedure Lookup
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_rag_engine_lookup():
    # 檢索冷卻液超溫停機規程
    res = await rag_engine.lookup_repair_procedure(
        query_text="coolant temperature shutdown limit",
        safety_level="standard"
    )
    assert res["matched_doc_id"] == "SOP-THM-01"
    assert res["shutdown_threshold_c"] == 105.0
    assert "secondary pump relay" in res["recommended_action"]

    # 檢索高壓安全防護規程
    hv_res = await rag_engine.lookup_repair_procedure(
        query_text="high voltage battery isolation PPE",
        safety_level="high_voltage_hazard"
    )
    assert hv_res["matched_doc_id"] == "SOP-HV-03"
    assert hv_res["safety_level"] == "high_voltage_hazard"

# -------------------------------------------------------------
# Test 5: Parallel Tool Calling & Intent Parsing
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_parallel_tool_execution():
    query = "幫我看冷卻液溫度現在多少，手冊上有說超過幾度要停機嗎？"
    tool_calls = auto_copilot_agent.parse_user_intent_to_tool_calls(query)
    
    # 必須同時識別並觸發 Telemetry 與 RAG 兩大工具
    names = [tc["name"] for tc in tool_calls]
    assert "get_vehicle_telemetry" in names
    assert "lookup_repair_procedure" in names

    # 平行非同步執行
    results = await auto_copilot_agent.execute_parallel_tools(tool_calls)
    assert len(results) == 2
    for r in results:
        assert r["latency_ms"] < 200.0  # 微秒級執行，遠低於 200ms

# -------------------------------------------------------------
# Test 6: Full Turn Dialogue & Spoken Synthesis
# -------------------------------------------------------------
@pytest.mark.asyncio
async def test_full_turn_process():
    telemetry_gateway.set_metric("coolant_temp_c", 103.5)
    query = "幫我看冷卻液溫度現在多少，手冊上有說超過幾度要停機嗎？"
    
    result = await auto_copilot_agent.process_user_turn(query)
    assert result["tool_calls_executed"] == 2
    assert "103.5" in result["spoken_response"]
    assert "105" in result["spoken_response"]
    assert "二級泵繼電器" in result["spoken_response"]
    assert result["total_latency_ms"] < 100.0

# -------------------------------------------------------------
# Test 7: Barge-in Interruption Mechanism
# -------------------------------------------------------------
def test_barge_in_interruption():
    barge_in = BargeInController()
    assert barge_in.is_interrupted is False
    
    event = barge_in.trigger_interruption()
    assert barge_in.is_interrupted is True
    assert barge_in.interruption_count == 1
    assert event["token"] == "interrupt_tts"
    
    barge_in.reset()
    assert barge_in.is_interrupted is False

# -------------------------------------------------------------
# Test 8: FastAPI REST Endpoints & Health Check
# -------------------------------------------------------------
def test_fastapi_endpoints():
    # Health
    r_health = client.get("/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "online"

    # Telemetry API
    r_telem = client.get("/api/telemetry")
    assert r_telem.status_code == 200
    assert "metrics" in r_telem.json()

    # Tools API
    r_tools = client.get("/api/tools")
    assert r_tools.status_code == 200
    assert r_tools.json()["total_tools"] == 3

    # Chat API
    r_chat = client.post("/api/chat", json={"message": "檢查冷卻液溫度"})
    assert r_chat.status_code == 200
    assert "spoken_response" in r_chat.json()

    # Interrupt API
    r_int = client.post("/api/interrupt")
    assert r_int.status_code == 200
    assert r_int.json()["token"] == "interrupt_tts"

    # Static Dashboard
    r_ui = client.get("/")
    assert r_ui.status_code == 200
    assert "AutoCopilot" in r_ui.text
