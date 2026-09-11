"""
AutoCopilot - Real-Time Voice Agent Core
========================================
Demonstration script showing:
1. AssemblyAI Real-Time WebSocket integration pattern (Universal-3 Pro STT).
2. Asynchronous mock audio pipeline (PCM 16-bit 16kHz stream simulation).
3. Tool Execution Registry (Telemetry query, DTC lookup, Manual RAG).
4. Bi-directional message loop with barge-in / interruption handling.
"""

import asyncio
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("AutoCopilot")

# -------------------------------------------------------------------------
# Tool Registry & Mock Implementations
# -------------------------------------------------------------------------

class VehicleDiagnosticTools:
    """Mock implementations for Vehicle / Industrial hardware and manual tools."""

    @staticmethod
    async def get_vehicle_telemetry(subsystem: str, metric_keys: List[str]) -> Dict[str, Any]:
        """Simulates CAN / OBD-II / UDS bus telemetry reads."""
        await asyncio.sleep(0.06)  # simulate bus round-trip (~60ms)
        mock_db = {
            "thermal_management": {
                "coolant_temp_c": 103.8,
                "inverter_temp_c": 64.2,
                "coolant_line_pressure_kpa": 142.5,
            },
            "powertrain": {
                "motor_rpm": 2450,
                "bus_voltage_v": 384.2,
            },
            "battery_pack": {
                "pack_soc_percent": 68.5,
                "bus_voltage_v": 386.1,
            },
        }
        
        readings = {}
        sub_data = mock_db.get(subsystem, {})
        for key in metric_keys:
            readings[key] = sub_data.get(key, "N/A")
            
        status = "normal"
        if readings.get("coolant_temp_c", 0) > 100:
            status = "warning_high_temperature"
            
        return {
            "subsystem": subsystem,
            "timestamp": time.time(),
            "status": status,
            "readings": readings,
        }

    @staticmethod
    async def read_diagnostic_trouble_codes(ecu_target: str, include_snapshot_data: bool = False) -> Dict[str, Any]:
        """Simulates UDS Service 0x19 (ReadDTCInformation)."""
        await asyncio.sleep(0.08)  # simulate diagnostic session delay
        active_dtcs = [
            {
                "dtc": "P0117",
                "ecu": "engine_control",
                "description": "Engine Coolant Temperature Sensor 1 Circuit Low",
                "status": "active_confirmed",
                "snapshot": {"coolant_temp_c": 103.8, "voltage_v": 0.42} if include_snapshot_data else None,
            }
        ]
        
        if ecu_target != "all":
            active_dtcs = [d for d in active_dtcs if d["ecu"] == ecu_target]
            
        return {
            "ecu_target": ecu_target,
            "dtc_count": len(active_dtcs),
            "dtcs": active_dtcs,
        }

    @staticmethod
    async def lookup_repair_procedure(query_text: str, safety_level: str = "standard") -> Dict[str, Any]:
        """Simulates Vector Search over ISO / OEM Service Manuals."""
        await asyncio.sleep(0.12)  # simulate vector retrieval & reranking
        return {
            "query": query_text,
            "matched_section": "SEC-TH-402: Emergency Thermal Shutdown Procedure",
            "safety_clearance": safety_level,
            "shutdown_limit_c": 105.0,
            "recommended_sop": (
                "Step 1: Shift to neutral / idle. "
                "Step 2: Verify auxiliary cooling pump relay engagement. "
                "Step 3: If temperature exceeds 105C for >30s, trigger ASIL-B emergency safe state."
            ),
        }


# -------------------------------------------------------------------------
# Tool Calling Dispatcher
# -------------------------------------------------------------------------

TOOL_MAP = {
    "get_vehicle_telemetry": VehicleDiagnosticTools.get_vehicle_telemetry,
    "read_diagnostic_trouble_codes": VehicleDiagnosticTools.read_diagnostic_trouble_codes,
    "lookup_repair_procedure": VehicleDiagnosticTools.lookup_repair_procedure,
}

async def execute_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Dynamically dispatches and executes requested tool calls asynchronously."""
    handler = TOOL_MAP.get(tool_name)
    if not handler:
        logger.error(f"Unknown tool requested: {tool_name}")
        return {"error": f"Tool '{tool_name}' not found."}
    
    logger.info(f"⚙️ [Tool Call] Executing '{tool_name}' with args: {arguments}")
    start_t = time.perf_counter()
    try:
        result = await handler(**arguments)
        duration_ms = (time.perf_counter() - start_t) * 1000
        logger.info(f"✅ [Tool Result] Finished in {duration_ms:.1f}ms: {json.dumps(result, ensure_ascii=False)}")
        return result
    except Exception as exc:
        logger.exception(f"❌ [Tool Error] Execution failed for {tool_name}: {exc}")
        return {"error": str(exc)}


# -------------------------------------------------------------------------
# AssemblyAI Stream & Voice Agent Client
# -------------------------------------------------------------------------

class AutoCopilotClient:
    """Manages full-duplex communication with AssemblyAI real-time stream."""

    def __init__(self, api_key: str, sample_rate: int = 16000):
        self.api_key = api_key
        self.sample_rate = sample_rate
        self.base_ws_url = f"wss://api.assemblyai.com/v2/realtime/ws?sample_rate={sample_rate}"
        self.is_running = False
        self.barge_in_active = False

    async def simulate_mic_audio_stream(self, queue: asyncio.Queue, duration_seconds: float = 3.0):
        """Simulates 100ms PCM 16kHz audio chunks generated by a microphone."""
        chunk_size = int(self.sample_rate * 0.1 * 2)  # 100ms * 16kHz * 2 bytes (16-bit)
        blank_pcm_chunk = b"\x00" * chunk_size
        
        logger.info("🎙️ Microphone stream started (Simulated 16kHz PCM)...")
        start = time.time()
        while time.time() - start < duration_seconds and self.is_running:
            await queue.put(blank_pcm_chunk)
            await asyncio.sleep(0.1)
        logger.info("🎙️ Microphone stream finished.")

    async def run_mock_agent_session(self):
        """Runs an end-to-end simulated turn with AssemblyAI events and Tool Calling."""
        logger.info("🚀 Starting AutoCopilot Voice Agent Session...")
        self.is_running = True
        audio_queue = asyncio.Queue()

        # Producer task (Microphone)
        mic_task = asyncio.create_task(self.simulate_mic_audio_stream(audio_queue, duration_seconds=2.0))

        # Consumer & Agent orchestrator
        agent_task = asyncio.create_task(self._mock_event_lifecycle(audio_queue))

        await asyncio.gather(mic_task, agent_task)
        logger.info("🏁 AutoCopilot session ended cleanly.")

    async def _mock_event_lifecycle(self, audio_queue: asyncio.Queue):
        """Simulates AssemblyAI WebSocket lifecycle: Handshake -> Transcribe -> Turn -> Tool -> TTS."""
        await asyncio.sleep(0.3)
        logger.info("🔗 [WebSocket] Connected to AssemblyAI Real-Time Service.")
        logger.info("⚙️ [SessionConfig] Word Boost applied: ['CAN-FD', 'DTC', 'ASIL', 'ISO 14229', 'coolant']")

        # Consume a few audio frames to represent active speech
        while not audio_queue.empty():
            _ = await audio_queue.get()
            await asyncio.sleep(0.05)

        # 1. Speech Recognition Event (Partial & Final)
        logger.info("🗣️ [User Utterance Detected]: '幫我看冷卻液溫度現在多少，手冊上有說超過幾度要停機嗎？'")
        logger.info("⚡ [AssemblyAI STT Finalized] Confidence: 0.985 | Latency: 210ms")

        # 2. LLM Reasoning triggers parallel tool execution
        logger.info("🤖 [Agent Core] Intent resolved. Emitting 2 parallel tool invocations...")
        
        tool_tasks = [
            execute_tool_call(
                "get_vehicle_telemetry",
                {"subsystem": "thermal_management", "metric_keys": ["coolant_temp_c", "coolant_line_pressure_kpa"]},
            ),
            execute_tool_call(
                "lookup_repair_procedure",
                {"query_text": "coolant temperature shutdown limit", "safety_level": "standard"},
            ),
        ]

        # Parallel dispatch
        telemetry_res, sop_res = await asyncio.gather(*tool_tasks)

        # 3. Formulate Spoken Output
        coolant_val = telemetry_res["readings"]["coolant_temp_c"]
        limit_val = sop_res["shutdown_limit_c"]
        
        spoken_response = (
            f"目前冷卻液溫度為 {coolant_val} 度，接近手冊規範的 {limit_val} 度停機上限。"
            "手冊建議維持怠速運轉並檢查二級冷卻泵繼電器。"
        )

        logger.info(f"🔊 [Agent TTS Output Stream]: \"{spoken_response}\"")

        # 4. Demonstrate Barge-in handling
        await asyncio.sleep(0.4)
        logger.info("⚡ [VAD Event] User speech detected during TTS playback! (Barge-in / Interruption)")
        logger.info("🛑 [Cancellation] Immediately halted TTS audio buffer playback and reset turn-taking state.")

        self.is_running = False


# -------------------------------------------------------------------------
# Standalone Runner
# -------------------------------------------------------------------------

if __name__ == "__main__":
    api_key = os.environ.get("ASSEMBLYAI_API_KEY", "mock_assemblyai_key_hackathon")
    copilot = AutoCopilotClient(api_key=api_key)
    asyncio.run(copilot.run_mock_agent_session())
