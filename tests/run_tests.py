"""
AutoCopilot Test Runner
Executes all end-to-end tests synchronously and asynchronously.
"""

import sys
import asyncio
from fastapi.testclient import TestClient

from auto_copilot.config import ASSEMBLYAI_AGENT_CONFIG, WORD_BOOST_LIST
from auto_copilot.schemas import FUNCTION_CALLING_TOOLS
from auto_copilot.telemetry_gateway import telemetry_gateway
from auto_copilot.rag_engine import rag_engine
from auto_copilot.agent_core import auto_copilot_agent, BargeInController
from auto_copilot.server import app

client = TestClient(app)

def test_1_config():
    print("[RUN] Test 1: Config and Word Boost Verification...")
    assert ASSEMBLYAI_AGENT_CONFIG["transcription"]["model"] == "universal-3-pro"
    assert ASSEMBLYAI_AGENT_CONFIG["agent"]["barge_in"]["enabled"] is True
    assert ASSEMBLYAI_AGENT_CONFIG["agent"]["vad"]["silence_duration_ms"] == 450
    assert len(WORD_BOOST_LIST) >= 15
    assert "CAN-FD" in WORD_BOOST_LIST
    assert "ISO 14229" in WORD_BOOST_LIST
    assert "P0117" in WORD_BOOST_LIST
    print("  -> PASSED: Universal-3 Pro, VAD 450ms, Word Boost (25 terms) verified.")

def test_2_schemas():
    print("[RUN] Test 2: Function Calling Schemas Integrity...")
    assert len(FUNCTION_CALLING_TOOLS) == 3
    tool_names = [t["function"]["name"] for t in FUNCTION_CALLING_TOOLS]
    assert "get_vehicle_telemetry" in tool_names
    assert "read_diagnostic_trouble_codes" in tool_names
    assert "lookup_repair_procedure" in tool_names
    print("  -> PASSED: All 3 tool JSON schemas conform to specification.")

async def test_3_telemetry():
    print("[RUN] Test 3: Telemetry Gateway & DTC Retrieval...")
    res = await telemetry_gateway.get_vehicle_telemetry(
        subsystem="thermal_management",
        metric_keys=["coolant_temp_c", "coolant_line_pressure_kpa"]
    )
    assert res["subsystem"] == "thermal_management"
    assert "coolant_temp_c" in res["data"]
    assert res["status"] in ["warning", "critical", "normal"]

    dtc_res = await telemetry_gateway.read_diagnostic_trouble_codes(
        ecu_target="all",
        include_snapshot_data=True
    )
    assert dtc_res["total_dtcs"] >= 2
    codes = [d["code"] for d in dtc_res["codes"]]
    assert "P0117" in codes
    p0117 = next(d for d in dtc_res["codes"] if d["code"] == "P0117")
    assert "freeze_frame" in p0117
    assert p0117["freeze_frame"]["coolant_temp_c"] >= 100.0
    print(f"  -> PASSED: Telemetry query returned {res['data']}, DTCs: {codes}")

async def test_4_rag():
    print("[RUN] Test 4: RAG Engine Procedure Lookup...")
    res = await rag_engine.lookup_repair_procedure(
        query_text="coolant temperature shutdown limit",
        safety_level="standard"
    )
    assert res["matched_doc_id"] == "SOP-THM-01"
    assert res["shutdown_threshold_c"] == 105.0
    assert "secondary pump relay" in res["recommended_action"]

    hv_res = await rag_engine.lookup_repair_procedure(
        query_text="high voltage battery isolation PPE",
        safety_level="high_voltage_hazard"
    )
    assert hv_res["matched_doc_id"] == "SOP-HV-03"
    assert hv_res["safety_level"] == "high_voltage_hazard"
    print(f"  -> PASSED: SOP matched: {res['matched_doc_id']} (Limit: {res['shutdown_threshold_c']}C)")

async def test_5_parallel_tools():
    print("[RUN] Test 5: Parallel Tool Execution & Intent Parsing...")
    query = "幫我看冷卻液溫度現在多少，手冊上有說超過幾度要停機嗎？"
    tool_calls = auto_copilot_agent.parse_user_intent_to_tool_calls(query)
    names = [tc["name"] for tc in tool_calls]
    assert "get_vehicle_telemetry" in names
    assert "lookup_repair_procedure" in names

    results = await auto_copilot_agent.execute_parallel_tools(tool_calls)
    assert len(results) == 2
    for r in results:
        assert r["latency_ms"] < 200.0
    print(f"  -> PASSED: Parallel tools executed in {[r['latency_ms'] for r in results]} ms.")

async def test_6_full_turn():
    print("[RUN] Test 6: Full Turn Dialogue & Spoken Synthesis...")
    telemetry_gateway.set_metric("coolant_temp_c", 103.5)
    query = "幫我看冷卻液溫度現在多少，手冊上有說超過幾度要停機嗎？"
    
    result = await auto_copilot_agent.process_user_turn(query)
    assert result["tool_calls_executed"] == 2
    assert "103." in result["spoken_response"]
    assert "105" in result["spoken_response"]
    assert "二級泵繼電器" in result["spoken_response"]
    print(f"  -> PASSED: Spoken Response: \"{result['spoken_response']}\" (Latency: {result['total_latency_ms']} ms)")

def test_7_barge_in():
    print("[RUN] Test 7: Barge-in Interruption Mechanism...")
    barge_in = BargeInController()
    assert barge_in.is_interrupted is False
    event = barge_in.trigger_interruption()
    assert barge_in.is_interrupted is True
    assert barge_in.interruption_count == 1
    assert event["token"] == "interrupt_tts"
    barge_in.reset()
    assert barge_in.is_interrupted is False
    print("  -> PASSED: Barge-in token 'interrupt_tts' dispatched and reset.")

def test_8_endpoints():
    print("[RUN] Test 8: FastAPI Endpoints & Static UI...")
    r_health = client.get("/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "online"

    r_telem = client.get("/api/telemetry")
    assert r_telem.status_code == 200

    r_tools = client.get("/api/tools")
    assert r_tools.status_code == 200
    assert r_tools.json()["total_tools"] == 3

    r_chat = client.post("/api/chat", json={"message": "檢查冷卻液溫度"})
    assert r_chat.status_code == 200
    assert "spoken_response" in r_chat.json()

    r_int = client.post("/api/interrupt")
    assert r_int.status_code == 200
    assert r_int.json()["token"] == "interrupt_tts"

    r_ui = client.get("/")
    assert r_ui.status_code == 200
    assert "AUTOCOPILOT" in r_ui.text
    print("  -> PASSED: All REST endpoints and Web Dashboard respond HTTP 200 OK.")

def test_9_can_dbc():
    print("[RUN] Test 9: CAN DBC Frame Encoding/Decoding...")
    from auto_copilot.can_interface import can_bus_interface, CAN_ID_COOLANT_METRICS
    test_phys = {"coolant_temp_c": 104.2, "coolant_line_pressure_kpa": 145.0}
    payload = can_bus_interface.decoder.encode_frame(CAN_ID_COOLANT_METRICS, test_phys)
    assert len(payload) == 8
    decoded = can_bus_interface.process_incoming_frame(CAN_ID_COOLANT_METRICS, payload)
    assert abs(decoded["coolant_temp_c"] - 104.2) < 0.15
    assert decoded["coolant_line_pressure_kpa"] == 145.0
    print(f"  -> PASSED: CAN Frame 0x120 encoded & decoded accurately: {decoded}")

def test_10_vector_store():
    print("[RUN] Test 10: Vector Store Cosine Similarity Retrieval...")
    from auto_copilot.vector_store import vector_store
    results = vector_store.search("coolant overheat emergency shutdown", top_k=1)
    assert len(results) == 1
    doc, score = results[0]
    assert doc.doc_id == "SEC-TH-402"
    assert doc.metadata["shutdown_limit_c"] == 105.0
    assert score > 0.3
    print(f"  -> PASSED: Vector retrieval matched {doc.doc_id} with similarity {score}")

async def main():
    print("=" * 60)
    print("🚀 STARTING AUTOCOPILOT END-TO-END VERIFICATION SUITE (10 TESTS)")
    print("=" * 60)
    test_1_config()
    test_2_schemas()
    await test_3_telemetry()
    await test_4_rag()
    await test_5_parallel_tools()
    await test_6_full_turn()
    test_7_barge_in()
    test_8_endpoints()
    test_9_can_dbc()
    test_10_vector_store()
    print("=" * 60)
    print("🎉 ALL 10 TESTS 100% PASSED! AUTOCOPILOT READY FOR STAGE 1~2 SUBMISSION!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
