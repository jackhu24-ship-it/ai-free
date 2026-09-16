#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 輕量級 Python MCP Server 工具 (lightweight_mcp_server.py) - 終極旗艦版 (方案 A + B + C)
=============================================================================
作者：🛠️ 小開 (Agent_Coder)
統籌：👑 小幫手 (Agent_PM)
調研：👁️ 小Ｏ (Agent_Research)
審查：🐎 小馬 (Agent_Reviewer)

終極全功能矩陣：
1. 【方案 A: 客戶端指紋感知與追蹤】：自動記錄 Antigravity / OpenCode / Hermes 客戶端來源與請求度量。
2. 【方案 A: 主動式異常報警 (Watchdog Alert)】：嚴重異常透過 Windows 原生彈窗與提示音即時推播。
3. 【方案 B: 本地 Ollama 影子管家 GC 蒸餾】：雙閾值觸發 qwen2.5:3b 進行 L1 滾動修剪與 L2 知識提煉。
4. 【方案 C: MCU 硬體數位孿生模擬器】：燒錄前精準模擬 PIC16F18313 / 18F25K80 時序波形與安全校驗。
5. 【方案 C: 4-Core 跨 Agent 即時事件總線】：Zero-Touch Pub/Sub 事件廣播，實現跨 Agent 自動流轉。
"""

from __future__ import annotations

import sys
import os
import time
import json
import asyncio
import logging
import platform
import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# 引入核心子模組
SRC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC_DIR))
from autonomous_memory_mcp import autonomous_engine
from mcu_digital_twin import mcu_twin, MCUDigitalTwin
from event_bus import event_bus, AdvancedEventBus

# 基礎路徑配置
SERVER_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = SERVER_ROOT / "DATA" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
SERVER_LOG_FILE = LOG_DIR / "mcp_server.log"

SERVER_NAME = "five-agent-autonomous-mcp"
SERVER_VERSION = "3.0.0"


class AsyncLogManager:
    """高效能非同步日誌隊列管理器（具備併發安全鎖與自癒重試）"""

    def __init__(self, log_file: Path, max_queue_size: int = 1000, flush_interval: float = 1.0):
        self.log_file = log_file
        self.queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=max_queue_size)
        self.flush_interval = flush_interval
        self.is_running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self.total_logged_count = 0
        self.collision_retries_count = 0

    async def start(self):
        if not self.is_running:
            self.is_running = True
            self._worker_task = asyncio.create_task(self._log_worker(), name="AsyncLogWorker")

    async def stop(self):
        self.is_running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        await self._flush_remaining()

    async def log(self, level: str, message: str, agent_tag: str = "System", metadata: Optional[dict[str, Any]] = None) -> bool:
        entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "level": level.upper(),
            "agent": agent_tag,
            "message": message,
            "metadata": metadata or {}
        }
        try:
            self.queue.put_nowait(entry)
            return True
        except asyncio.QueueFull:
            await self._write_entry_direct(entry)
            return True

    async def _log_worker(self):
        buffer: list[dict[str, Any]] = []
        last_flush = time.monotonic()

        while self.is_running:
            try:
                timeout = max(0.1, self.flush_interval - (time.monotonic() - last_flush))
                try:
                    entry = await asyncio.wait_for(self.queue.get(), timeout=timeout)
                    buffer.append(entry)
                    self.queue.task_done()
                except asyncio.TimeoutError:
                    pass

                if buffer and (len(buffer) >= 20 or (time.monotonic() - last_flush) >= self.flush_interval):
                    await self._batch_write(buffer)
                    self.total_logged_count += len(buffer)
                    buffer.clear()
                    last_flush = time.monotonic()

            except asyncio.CancelledError:
                break
            except Exception:
                self.collision_retries_count += 1
                await asyncio.sleep(0.2)

    async def _batch_write(self, entries: list[dict[str, Any]], max_retries: int = 3):
        lines = [json.dumps(e, ensure_ascii=False) + "\n" for e in entries]
        for attempt in range(max_retries):
            try:
                async with self._lock:
                    with open(self.log_file, "a", encoding="utf-8", errors="replace") as f:
                        f.writelines(lines)
                return
            except (IOError, PermissionError):
                self.collision_retries_count += 1
                if attempt == max_retries - 1:
                    fallback_file = self.log_file.with_suffix(".fallback.log")
                    with open(fallback_file, "a", encoding="utf-8", errors="replace") as f:
                        f.writelines(lines)
                else:
                    await asyncio.sleep(0.05 * (2 ** attempt))

    async def _write_entry_direct(self, entry: dict[str, Any]):
        async with self._lock:
            with open(self.log_file, "a", encoding="utf-8", errors="replace") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self.total_logged_count += 1

    async def _flush_remaining(self):
        entries = []
        while not self.queue.empty():
            try:
                entries.append(self.queue.get_nowait())
                self.queue.task_done()
            except asyncio.QueueEmpty:
                break
        if entries:
            await self._batch_write(entries)
            self.total_logged_count += len(entries)


class LightweightMCPServer:
    """輕量級 Python MCP Server 核心實現 (方案 A + B + C 終極整合)"""

    def __init__(self):
        self.start_time = time.time()
        self.log_manager = AsyncLogManager(SERVER_LOG_FILE)
        self.autonomous_engine = autonomous_engine
        self.mcu_twin = mcu_twin
        self.event_bus = event_bus
        self.request_count = 0
        self.error_count = 0
        self.tools_registry: dict[str, Any] = {}
        self._daemon_task: Optional[asyncio.Task] = None
        self._register_all_tools()
        self._setup_event_bus_wiring()

    def _setup_event_bus_wiring(self):
        """配置 4 Core Agents 預設事件流轉管線"""
        async def on_code_generated(evt):
            await self.log_manager.log("INFO", f"[EventBus] Coder 產出代碼: {evt['payload'].get('file')}", agent_tag="Reviewer")

        async def on_simulation_passed(evt):
            await self.log_manager.log("INFO", f"[EventBus] 數位孿生驗證通過: {evt['payload'].get('chip_model')}", agent_tag="PM")

        self.event_bus.subscribe("EVENT_CODE_GENERATED", on_code_generated)
        self.event_bus.subscribe("EVENT_SIMULATION_PASSED", on_simulation_passed)

    def _register_all_tools(self):
        self.tools_registry = {
            # ===== 基礎維運工具 =====
            "health_check": {
                "description": "執行 Server 全面健康檢查與狀態度量 (Health Check Endpoint)",
                "input_schema": {
                    "type": "object",
                    "properties": {"detailed": {"type": "boolean", "description": "是否回傳詳細系統指標"}}
                },
                "handler": self._tool_health_check
            },
            "get_system_metrics": {
                "description": "獲取 CPU、記憶體、Python 執行期與系統負載指標 (System Metrics)",
                "input_schema": {"type": "object", "properties": {}},
                "handler": self._tool_get_system_metrics
            },
            "echo_ping": {
                "description": "回傳 Echo 測試信號與往返延遲 (Latency Probe)",
                "input_schema": {
                    "type": "object",
                    "properties": {"message": {"type": "string", "description": "回傳訊息"}}
                },
                "handler": self._tool_echo_ping
            },
            "read_recent_logs": {
                "description": "讀取最近 N 條非同步寫入的伺服器日誌 (Log Retrieval)",
                "input_schema": {
                    "type": "object",
                    "properties": {"limit": {"type": "integer", "description": "讀取筆數 (預設 10, 最大 100)"}}
                },
                "handler": self._tool_read_recent_logs
            },
            # ===== 方案 A + B 增強工具 =====
            "log_event": {
                "description": "[方案 A] 非同步記錄事件日誌至 L1 並追蹤客戶端指紋與異常報警 (Client Fingerprint Logging)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "client_id": {"type": "string", "description": "發起客戶端名稱 (如 Antigravity / OpenCode / Hermes)"},
                        "level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], "description": "日誌等級"},
                        "message": {"type": "string", "description": "事件訊息內文"},
                        "role": {"type": "string", "description": "Agent 角色代碼 (PM / Coder / Reviewer / Vision)"}
                    },
                    "required": ["client_id", "level", "message"]
                },
                "handler": self._tool_log_event
            },
            "run_memory_gc": {
                "description": "[方案 B] 執行 Ollama 本地影子管家蒸餾與 L1 記憶修剪 (Run Memory GC)",
                "input_schema": {
                    "type": "object",
                    "properties": {"force": {"type": "boolean", "description": "是否強制觸發蒸餾 (忽略行數門檻)"}}
                },
                "handler": self._tool_run_memory_gc
            },
            "get_client_stats": {
                "description": "[方案 A] 查詢所有已連線客戶端來源統計 (Client Fingerprint Statistics)",
                "input_schema": {"type": "object", "properties": {}},
                "handler": self._tool_get_client_stats
            },
            "trigger_alert": {
                "description": "[方案 A] 發送主動式系統警告彈窗通知 (Trigger Toast Alert)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "警告標題"},
                        "message": {"type": "string", "description": "警告內文"}
                    },
                    "required": ["title", "message"]
                },
                "handler": self._tool_trigger_alert
            },
            "get_memory_status": {
                "description": "[方案 A+B] 查詢當前三層記憶健康度與 GC 統計資訊",
                "input_schema": {"type": "object", "properties": {}},
                "handler": self._tool_get_memory_status
            },
            # ===== 方案 C 數位孿生與事件總線工具 =====
            "simulate_mcu_firmware": {
                "description": "[方案 C] 執行 MCU 數位孿生時序模擬 (MCU Hardware Digital Twin Simulation)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "chip_model": {"type": "string", "description": "晶片型號 (如 PIC16F18313 / PIC18F25K80)"},
                        "start_delay": {"type": "number", "description": "開機保護延遲 (秒, 預設 1.0)"},
                        "alarm_freq": {"type": "number", "description": "警報反轉頻率 (Hz, 預設 2.0)"},
                        "mute_delay": {"type": "number", "description": "前置靜音延遲 (秒, 預設 3.0)"},
                        "duration_ms": {"type": "number", "description": "模擬總時間 (毫秒, 預設 8000.0)"}
                    }
                },
                "handler": self._tool_simulate_mcu_firmware
            },
            "publish_agent_event": {
                "description": "[方案 C] 發布跨 Agent 即時事件至事件總線 (Publish Inter-Agent Event)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "event_type": {"type": "string", "description": "事件主題 (如 EVENT_CODE_GENERATED / EVENT_REVIEW_PASSED)"},
                        "payload": {"type": "object", "description": "事件承載資料"},
                        "publisher": {"type": "string", "description": "發布者 Agent 代碼 (PM / Coder / Reviewer / Vision)"}
                    },
                    "required": ["event_type", "payload"]
                },
                "handler": self._tool_publish_agent_event
            },
            "get_event_bus_history": {
                "description": "[方案 C] 查詢跨 Agent 事件總線歷史紀錄與統計",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "讀取筆數 (預設 20)"},
                        "event_type": {"type": "string", "description": "過濾特定事件主題"}
                    }
                },
                "handler": self._tool_get_event_bus_history
            },
            "run_digital_twin_preburn_check": {
                "description": "[方案 C] 執行實體燒錄前數位孿生安全合規預檢 (Pre-burn Simulation Check)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "chip_model": {"type": "string", "description": "晶片型號 (預設 PIC16F18313)"},
                        "start_delay": {"type": "number", "description": "開機保護延遲 (秒)"},
                        "alarm_freq": {"type": "number", "description": "警報頻率 (Hz)"},
                        "mute_delay": {"type": "number", "description": "前置靜音延遲 (秒)"}
                    }
                },
                "handler": self._tool_run_digital_twin_preburn_check
            }
        }

    async def start(self):
        """啟動全套服務引擎"""
        await self.log_manager.start()
        self._daemon_task = asyncio.create_task(
            self.autonomous_engine.start_background_daemon(interval_seconds=3600),
            name="ShadowGCDaemon"
        )
        await self.log_manager.log("INFO", f"MCP Server '{SERVER_NAME}' v{SERVER_VERSION} (方案A+B+C終極旗艦版) 啟動完成", agent_tag="PM")

    async def stop(self):
        if self._daemon_task:
            self._daemon_task.cancel()
        await self.log_manager.log("INFO", f"MCP Server '{SERVER_NAME}' 正在正常關閉", agent_tag="PM")
        await self.log_manager.stop()

    # ================= 工具實作 =================
    async def _tool_health_check(self, detailed: bool = False) -> dict[str, Any]:
        uptime_sec = round(time.time() - self.start_time, 2)
        mem_status = self.autonomous_engine.get_status()
        bus_stats = self.event_bus.get_stats()
        status = {
            "status": "HEALTHY",
            "server_name": SERVER_NAME,
            "version": SERVER_VERSION,
            "uptime_seconds": uptime_sec,
            "uptime_formatted": str(datetime.timedelta(seconds=int(uptime_sec))),
            "requests_served": self.request_count,
            "errors_recorded": self.error_count,
            "async_queue_depth": self.log_manager.queue.qsize(),
            "l1_memory_lines": mem_status["l1_lines"],
            "active_clients": mem_status["active_clients_count"],
            "event_bus_stats": bus_stats,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        if detailed:
            status["system_info"] = {
                "os": platform.platform(),
                "python_version": sys.version.split()[0],
                "active_threads": os.cpu_count() or 1,
                "process_id": os.getpid()
            }
            status["client_stats"] = mem_status["clients"]
        return status

    async def _tool_log_event(self, client_id: str, level: str, message: str, role: str = "System") -> dict[str, Any]:
        res = await self.autonomous_engine.log_event(client_id, level, message, role)
        await self.log_manager.log(level, f"[{client_id}] {message}", agent_tag=role)
        return res

    async def _tool_run_memory_gc(self, force: bool = False) -> dict[str, Any]:
        return await self.autonomous_engine.run_shadow_gc(force=force)

    async def _tool_get_client_stats(self) -> dict[str, Any]:
        return {
            "total_clients": len(self.autonomous_engine.client_stats),
            "clients": self.autonomous_engine.client_stats
        }

    async def _tool_trigger_alert(self, title: str, message: str) -> dict[str, Any]:
        self.autonomous_engine.trigger_alert(title, message)
        return {"status": "alert_triggered", "title": title, "message": message}

    async def _tool_get_memory_status(self) -> dict[str, Any]:
        return self.autonomous_engine.get_status()

    async def _tool_simulate_mcu_firmware(
        self, 
        chip_model: str = "PIC16F18313", 
        start_delay: float = 1.0, 
        alarm_freq: float = 2.0, 
        mute_delay: float = 3.0, 
        duration_ms: float = 8000.0
    ) -> dict[str, Any]:
        twin = MCUDigitalTwin(chip_model=chip_model)
        twin.configure_parameters(start_delay=start_delay, alarm_freq=alarm_freq, mute_delay=mute_delay)
        return twin.run_simulation(total_time_ms=duration_ms)

    async def _tool_publish_agent_event(self, event_type: str, payload: dict[str, Any], publisher: str = "System") -> dict[str, Any]:
        return await self.event_bus.publish(event_type, payload, publisher=publisher)

    async def _tool_get_event_bus_history(self, limit: int = 20, event_type: Optional[str] = None) -> dict[str, Any]:
        return {
            "stats": self.event_bus.get_stats(),
            "history": self.event_bus.get_history(limit=limit, event_type=event_type)
        }

    async def _tool_run_digital_twin_preburn_check(
        self, 
        chip_model: str = "PIC16F18313", 
        start_delay: float = 1.0, 
        alarm_freq: float = 2.0, 
        mute_delay: float = 3.0
    ) -> dict[str, Any]:
        twin = MCUDigitalTwin(chip_model=chip_model)
        twin.configure_parameters(start_delay=start_delay, alarm_freq=alarm_freq, mute_delay=mute_delay)
        sim_res = twin.run_simulation(total_time_ms=8000.0)

        passed = sim_res["verification_passed"]
        report = {
            "preburn_status": "APPROVED" if passed else "REJECTED",
            "chip_model": chip_model,
            "verification_details": sim_res["verification_report"],
            "measured_freq_hz": sim_res["summary_metrics"]["measured_freq_hz"],
            "target_freq_hz": alarm_freq,
            "safety_verdict": "時序與狀態機驗證通過，允許一鍵 PICkit 4 實體燒錄！" if passed else "時序偏差過大，請調整參數後重新模擬。"
        }
        
        # 發布事件至總線
        await self.event_bus.publish(
            "EVENT_PREBURN_CHECK_COMPLETED", 
            report, 
            publisher="DigitalTwin"
        )
        return report

    async def _tool_get_system_metrics(self) -> dict[str, Any]:
        import gc
        return {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "cpu_cores": os.cpu_count(),
            "pid": os.getpid(),
            "gc_counts": gc.get_count(),
            "queue_status": {"depth": self.log_manager.queue.qsize(), "is_running": self.log_manager.is_running},
            "timestamp": time.time()
        }

    async def _tool_echo_ping(self, message: str = "pong") -> dict[str, Any]:
        return {"echo": message, "received_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "server_time": time.time()}

    async def _tool_read_recent_logs(self, limit: int = 10) -> dict[str, Any]:
        limit = min(max(1, limit), 100)
        logs = []
        if SERVER_LOG_FILE.exists():
            try:
                with open(SERVER_LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
                    all_lines = f.readlines()
                    for line in all_lines[-limit:]:
                        line = line.strip()
                        if line:
                            try:
                                logs.append(json.loads(line))
                            except json.JSONDecodeError:
                                logs.append({"raw": line})
            except Exception as e:
                return {"error": f"讀取日誌異常: {e}", "logs": []}
        return {"count": len(logs), "requested_limit": limit, "logs": logs}

    # ================= JSON-RPC 2.0 處理器 =================
    async def handle_jsonrpc_request(self, request: dict[str, Any], client_hint: str = "GenericClient") -> dict[str, Any]:
        self.request_count += 1
        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        self.autonomous_engine.record_client(client_hint)

        if method == "tools/list":
            tools_list = []
            for name, meta in self.tools_registry.items():
                tools_list.append({
                    "name": name,
                    "description": meta["description"],
                    "inputSchema": meta["input_schema"]
                })
            return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools_list}}

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name not in self.tools_registry:
                self.error_count += 1
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"未知的工具方法: '{tool_name}'",
                        "available_tools": list(self.tools_registry.keys())
                    }
                }

            handler = self.tools_registry[tool_name]["handler"]
            try:
                result = await handler(**arguments)
                return {"jsonrpc": "2.0", "id": req_id, "result": result}
            except TypeError as e:
                self.error_count += 1
                return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": f"參數不匹配: {e}"}}
            except Exception as e:
                self.error_count += 1
                await self.log_manager.log("ERROR", f"工具 [{tool_name}] 執行異常: {e}", agent_tag="Reviewer")
                return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": f"內部執行錯誤: {e}"}}

        elif method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {"status": "pong", "time": time.time()}}

        else:
            self.error_count += 1
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"不支援的 JSON-RPC 方法: '{method}'"}}

    async def run_stdio_server(self):
        await self.start()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_running_loop().connect_read_pipe(lambda: protocol, sys.stdin)

        while True:
            try:
                line = await reader.readline()
                if not line:
                    break
                line_str = line.decode("utf-8", errors="replace").strip()
                if not line_str:
                    continue

                try:
                    req_obj = json.loads(line_str)
                    resp = await self.handle_jsonrpc_request(req_obj, client_hint="StdioClient")
                except json.JSONDecodeError as e:
                    resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": f"JSON 解析錯誤: {e}"}}

                sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
                sys.stdout.flush()

            except asyncio.CancelledError:
                break
            except Exception as e:
                await self.log_manager.log("CRITICAL", f"Stdio 傳輸崩潰異常: {e}", agent_tag="Reviewer")

        await self.stop()


mcp_server = LightweightMCPServer()


if __name__ == "__main__":
    asyncio.run(mcp_server.run_stdio_server())
