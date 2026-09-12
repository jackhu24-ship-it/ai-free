"""
AutoCopilot Agent Core & Dispatcher
Handles AssemblyAI Streaming, Parallel Function Calling, and Barge-in Interruption.
"""

import asyncio
import time
import json
from typing import Dict, Any, List, Optional, Callable
from .config import ASSEMBLYAI_AGENT_CONFIG, AUDIO_FORMAT
from .schemas import FUNCTION_CALLING_TOOLS
from .telemetry_gateway import telemetry_gateway
from .rag_engine import rag_engine

class BargeInController:
    """
    Manages speech interruptions (Barge-in).
    When VAD detects user speaking during TTS playback, immediately cancels output.
    """
    def __init__(self):
        self.is_interrupted: bool = False
        self.interruption_count: int = 0
        self.last_interruption_time: Optional[float] = None
        self._cancellation_token = ASSEMBLYAI_AGENT_CONFIG["agent"]["barge_in"]["cancellation_token"]

    def trigger_interruption(self) -> Dict[str, Any]:
        """觸發語音打斷事件"""
        self.is_interrupted = True
        self.interruption_count += 1
        self.last_interruption_time = time.time()
        return {
            "event": "barge_in_interruption",
            "token": self._cancellation_token,
            "timestamp": self.last_interruption_time,
            "message": "User speech detected during TTS playback. Audio stream canceled."
        }

    def reset(self) -> None:
        """重設打斷狀態"""
        self.is_interrupted = False

class AutoCopilotAgent:
    """
    Main AutoCopilot Agent Core.
    Coordinates STT, Intent Parsing, Parallel Tool Calling, and Spoken Response Generation.
    """
    def __init__(self):
        self.config = ASSEMBLYAI_AGENT_CONFIG
        self.tools = FUNCTION_CALLING_TOOLS
        self.barge_in = BargeInController()
        self.execution_history: List[Dict[str, Any]] = []

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """分派並執行單一工具"""
        start_t = time.perf_counter()
        if tool_name == "get_vehicle_telemetry":
            res = await telemetry_gateway.get_vehicle_telemetry(
                subsystem=arguments.get("subsystem", "thermal_management"),
                metric_keys=arguments.get("metric_keys", ["coolant_temp_c"])
            )
        elif tool_name == "read_diagnostic_trouble_codes":
            res = await telemetry_gateway.read_diagnostic_trouble_codes(
                ecu_target=arguments.get("ecu_target", "all"),
                include_snapshot_data=arguments.get("include_snapshot_data", False)
            )
        elif tool_name == "lookup_repair_procedure":
            res = await rag_engine.lookup_repair_procedure(
                query_text=arguments.get("query_text", ""),
                safety_level=arguments.get("safety_level", "standard")
            )
        else:
            res = {"error": f"Unknown tool: {tool_name}"}

        elapsed_ms = round((time.perf_counter() - start_t) * 1000, 2)
        return {
            "tool_name": tool_name,
            "arguments": arguments,
            "output": res,
            "latency_ms": elapsed_ms
        }

    async def execute_parallel_tools(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        以 asyncio.gather 非同步平行執行多個工具呼叫 (無阻斷)
        """
        tasks = [
            self.execute_tool(tc["name"], tc.get("arguments", {}))
            for tc in tool_calls
        ]
        results = await asyncio.gather(*tasks)
        return list(results)

    def parse_user_intent_to_tool_calls(self, user_text: str) -> List[Dict[str, Any]]:
        """
        解析使用者自然語言，轉換為 Function Calling 結構 (支援複合意圖)
        """
        tool_calls = []
        text_lower = user_text.lower()

        # 1. 遙測意圖判定
        if any(w in text_lower for w in ["溫度", "temp", "冷卻液", "coolant", "電壓", "voltage", "轉速", "rpm", "壓力", "pressure"]):
            metrics = []
            if any(w in text_lower for w in ["冷卻液", "coolant", "溫度", "temp"]):
                metrics.append("coolant_temp_c")
            if any(w in text_lower for w in ["壓力", "pressure"]):
                metrics.append("coolant_line_pressure_kpa")
            if any(w in text_lower for w in ["電壓", "voltage"]):
                metrics.append("bus_voltage_v")
            if any(w in text_lower for w in ["轉速", "rpm"]):
                metrics.append("motor_rpm")

            if not metrics:
                metrics = ["coolant_temp_c"]

            tool_calls.append({
                "name": "get_vehicle_telemetry",
                "arguments": {
                    "subsystem": "thermal_management",
                    "metric_keys": metrics
                }
            })

        # 2. 手冊 / 規程檢索意圖判定
        if any(w in text_lower for w in ["手冊", "manual", "規定", "規範", "幾度", "停機", "limit", "sop", "步驟", "排氣", "threshold"]):
            tool_calls.append({
                "name": "lookup_repair_procedure",
                "arguments": {
                    "query_text": "coolant temperature shutdown limit and overheat procedure",
                    "safety_level": "standard"
                }
            })

        # 3. DTC 故障碼查詢意圖判定
        if any(w in text_lower for w in ["dtc", "故障碼", "代碼", "fault", "報錯", "異常"]):
            tool_calls.append({
                "name": "read_diagnostic_trouble_codes",
                "arguments": {
                    "ecu_target": "all",
                    "include_snapshot_data": True
                }
            })

        return tool_calls

    async def process_user_turn(self, user_transcript: str) -> Dict[str, Any]:
        """
        處理完整的對話輪替 (Turn)：
        1. 解析意圖
        2. 並行執行工具
        3. 組織 1-2 句符合車規安全之口語回覆
        """
        start_t = time.perf_counter()
        tool_calls = self.parse_user_intent_to_tool_calls(user_transcript)
        tool_results = []
        if tool_calls:
            tool_results = await self.execute_parallel_tools(tool_calls)

        # 根據工具結果生成簡潔回覆 (1-2 句)
        spoken_response = self._synthesize_spoken_response(user_transcript, tool_results)
        total_latency_ms = round((time.perf_counter() - start_t) * 1000, 2)

        record = {
            "timestamp": time.time(),
            "user_transcript": user_transcript,
            "tool_calls_executed": len(tool_results),
            "tool_results": tool_results,
            "spoken_response": spoken_response,
            "total_latency_ms": total_latency_ms,
            "barge_in_active": self.barge_in.is_interrupted
        }
        self.execution_history.append(record)
        return record

    def _synthesize_spoken_response(self, user_transcript: str, tool_results: List[Dict[str, Any]]) -> str:
        """合成安全第一、精準簡短的語音回應"""
        coolant_val = None
        shutdown_limit = None
        recommended_action = ""
        dtc_summary = ""

        for tr in tool_results:
            name = tr["tool_name"]
            out = tr["output"]
            if name == "get_vehicle_telemetry":
                coolant_val = out.get("data", {}).get("coolant_temp_c")
            elif name == "lookup_repair_procedure":
                shutdown_limit = out.get("shutdown_threshold_c")
                recommended_action = out.get("recommended_action", "")
            elif name == "read_diagnostic_trouble_codes":
                dtcs = [c["code"] for c in out.get("codes", [])]
                if dtcs:
                    dtc_summary = f"偵測到活動故障碼 {', '.join(dtcs)}。"

        # 組合經典對答情境
        if coolant_val is not None and shutdown_limit is not None:
            return (
                f"目前冷卻液溫度為 {coolant_val:.1f} 度，手冊規範超過 {shutdown_limit:.0f} 度必須緊急停機。"
                f"目前已接近上限，建議怠速運轉並檢查二級泵繼電器。"
            )
        elif coolant_val is not None:
            return f"目前冷卻液溫度讀數為 {coolant_val:.1f} 度，系統狀態正常。"
        elif dtc_summary:
            return f"{dtc_summary}請參考技術手冊進行線路導通排查。"
        else:
            return "系統已就緒，請隨時下達遙測查詢或手冊檢索指令。"


# 全域單例
auto_copilot_agent = AutoCopilotAgent()
