"""
AutoCopilot FastAPI Async Gateway & Server
Coordinates Web Audio streaming, Telemetry WebSocket, and Function Calling events.
"""

import asyncio
import json
import time
from typing import Dict, Any, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import ASSEMBLYAI_AGENT_CONFIG, AUDIO_FORMAT, WORD_BOOST_LIST
from .schemas import FUNCTION_CALLING_TOOLS
from .telemetry_gateway import telemetry_gateway
from .agent_core import auto_copilot_agent

app = FastAPI(
    title="AutoCopilot Gateway",
    description="Hands-free Automotive & Industrial Diagnostic Voice Agent Gateway",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

# -------------------------------------------------------------
# REST Endpoints
# -------------------------------------------------------------
@app.get("/health")
async def health_check():
    return {
        "status": "online",
        "service": "AutoCopilot Voice Gateway",
        "version": "1.0.0",
        "assemblyai_model": ASSEMBLYAI_AGENT_CONFIG["transcription"]["model"],
        "word_boost_terms_count": len(WORD_BOOST_LIST),
        "barge_in_enabled": ASSEMBLYAI_AGENT_CONFIG["agent"]["barge_in"]["enabled"]
    }

@app.get("/api/telemetry")
async def get_telemetry():
    return telemetry_gateway.get_all_metrics()

@app.get("/api/tools")
async def get_tools():
    return {
        "tools": FUNCTION_CALLING_TOOLS,
        "total_tools": len(FUNCTION_CALLING_TOOLS)
    }

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    result = await auto_copilot_agent.process_user_turn(req.message)
    return result

@app.post("/api/interrupt")
async def interrupt_endpoint():
    interruption_event = auto_copilot_agent.barge_in.trigger_interruption()
    return interruption_event

@app.get("/api/history")
async def get_history():
    return {
        "history": auto_copilot_agent.execution_history,
        "interruption_count": auto_copilot_agent.barge_in.interruption_count
    }

# -------------------------------------------------------------
# WebSockets: Real-time Telemetry Stream (10Hz)
# -------------------------------------------------------------
@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            metrics = telemetry_gateway.get_all_metrics()
            await websocket.send_json(metrics)
            await asyncio.sleep(0.1)  # 10Hz
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

# -------------------------------------------------------------
# WebSockets: Audio Stream & Turn-taking (PCM 16kHz)
# -------------------------------------------------------------
@app.websocket("/ws/audio")
async def websocket_audio(websocket: WebSocket):
    await websocket.accept()
    auto_copilot_agent.barge_in.reset()
    try:
        while True:
            # 接收客戶端 PCM Chunk (二進位或 JSON 封裝)
            message = await websocket.receive()
            if "bytes" in message:
                pcm_data = message["bytes"]
                # 模擬音訊活動與 Barge-in
                if auto_copilot_agent.barge_in.is_interrupted:
                    await websocket.send_json({
                        "event": "interruption",
                        "token": "interrupt_tts",
                        "message": "TTS stream stopped due to user barge-in."
                    })
            elif "text" in message:
                data = json.loads(message["text"])
                action = data.get("action")
                if action == "query_transcript":
                    transcript = data.get("text", "")
                    result = await auto_copilot_agent.process_user_turn(transcript)
                    await websocket.send_json({"event": "turn_completed", "data": result})
                elif action == "barge_in":
                    event = auto_copilot_agent.barge_in.trigger_interruption()
                    await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

# -------------------------------------------------------------
# HTML UI: Dark Industrial Diagnostics Dashboard
# -------------------------------------------------------------
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AutoCopilot | 即時聲控車載診斷副駕</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #090c10;
            --surface: #121820;
            --border: #232d3d;
            --accent: #00d2ff;
            --warning: #ffaa00;
            --critical: #ff3366;
            --success: #00ff88;
            --text-main: #f0f6fc;
            --text-muted: #8b949e;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: var(--bg);
            color: var(--text-main);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        header {
            background-color: var(--surface);
            border-bottom: 1px solid var(--border);
            padding: 12px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 800;
            font-size: 18px;
            color: var(--accent);
            letter-spacing: 1px;
        }
        .badge {
            background: rgba(0, 210, 255, 0.12);
            color: var(--accent);
            border: 1px solid rgba(0, 210, 255, 0.3);
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 4px;
        }
        .status-pill {
            display: flex;
            align-items: center;
            gap: 8px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            padding: 4px 12px;
            border-radius: 20px;
            background: #17202c;
            border: 1px solid var(--border);
        }
        .indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--success);
            box-shadow: 0 0 8px var(--success);
            animation: pulse 2s infinite;
        }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        
        .main-container {
            display: grid;
            grid-template-columns: 1fr 1.2fr 1fr;
            flex: 1;
            overflow: hidden;
        }
        .panel {
            padding: 16px;
            overflow-y: auto;
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        .panel:last-child { border-right: none; }
        
        .panel-title {
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border);
            padding-bottom: 8px;
        }

        /* Gauges & Telemetry Cards */
        .gauges-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }
        .gauge-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .gauge-card.critical {
            border-color: var(--critical);
            background: rgba(255, 51, 102, 0.08);
        }
        .gauge-card.warning {
            border-color: var(--warning);
            background: rgba(255, 170, 0, 0.08);
        }
        .gauge-label {
            font-size: 11px;
            color: var(--text-muted);
            text-transform: uppercase;
        }
        .gauge-val {
            font-family: 'JetBrains Mono', monospace;
            font-size: 20px;
            font-weight: 700;
            color: var(--accent);
        }
        .gauge-val.critical { color: var(--critical); }
        .gauge-val.warning { color: var(--warning); }
        .gauge-unit { font-size: 11px; color: var(--text-muted); font-weight: normal; margin-left: 4px; }

        /* DTC Section */
        .dtc-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .dtc-item {
            background: #161e29;
            border-left: 3px solid var(--warning);
            border-radius: 4px;
            padding: 8px 10px;
            font-size: 11px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .dtc-code {
            font-family: 'JetBrains Mono', monospace;
            font-weight: 700;
            color: var(--warning);
        }

        /* Voice State Badges */
        .voice-state-bar {
            display: flex;
            gap: 8px;
            align-items: center;
            justify-content: space-between;
            background: #090c10;
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 8px 12px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
        }
        .state-tag {
            padding: 2px 8px;
            border-radius: 4px;
            background: #1a2332;
            color: var(--text-muted);
        }
        .state-tag.active {
            background: rgba(0, 255, 136, 0.2);
            color: var(--success);
            border: 1px solid var(--success);
        }
        .state-tag.barge-in-flash {
            background: rgba(255, 51, 102, 0.3);
            color: var(--critical);
            border: 1px solid var(--critical);
            animation: flash 0.6s infinite alternate;
        }
        @keyframes flash { from { opacity: 0.5; } to { opacity: 1; } }

        /* Audio Visualizer */
        .audio-visualizer {
            height: 44px;
            background: #090c10;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 5px;
            padding: 0 10px;
            border: 1px solid var(--border);
        }
        .wave-bar {
            width: 4px;
            height: 8px;
            background: var(--accent);
            border-radius: 2px;
            transition: height 0.1s ease;
        }

        /* Chat Stream */
        .chat-stream {
            flex: 1;
            background: #0c1017;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 14px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 10px;
            font-size: 13px;
            min-height: 240px;
            max-height: 380px;
        }
        .chat-bubble {
            padding: 10px 14px;
            border-radius: 6px;
            max-width: 90%;
            line-height: 1.5;
        }
        .chat-bubble.user {
            background: #1f2937;
            align-self: flex-end;
            color: #e5e7eb;
        }
        .chat-bubble.agent {
            background: rgba(0, 210, 255, 0.1);
            border: 1px solid rgba(0, 210, 255, 0.25);
            align-self: flex-start;
            color: #d1f4ff;
        }
        .chat-bubble.barge-in {
            background: rgba(255, 51, 102, 0.15);
            border: 1px solid var(--critical);
            color: #ff99aa;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            align-self: center;
        }

        /* Transparency Panel (Right) */
        .transparency-box {
            background: #0c1017;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
        }
        .json-viewer {
            background: #06090e;
            padding: 10px;
            border-radius: 6px;
            border: 1px solid var(--border);
            color: #a5d6ff;
            max-height: 150px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-break: break-all;
        }
        .citation-card {
            background: #161e29;
            border-left: 3px solid var(--accent);
            padding: 10px;
            border-radius: 4px;
            font-size: 11px;
            line-height: 1.4;
        }
        .word-boost-cloud {
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
        }
        .boost-tag {
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 3px;
            background: #1b2533;
            color: #79c0ff;
            border: 1px solid #23344d;
        }

        .controls {
            display: flex;
            gap: 10px;
        }
        input[type="text"] {
            flex: 1;
            background: #0c1017;
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 10px 14px;
            color: white;
            font-size: 13px;
            outline: none;
        }
        input[type="text"]:focus { border-color: var(--accent); }
        button {
            background: var(--accent);
            color: #000;
            font-weight: 600;
            border: none;
            padding: 10px 16px;
            border-radius: 6px;
            cursor: pointer;
            transition: opacity 0.2s;
        }
        button:hover { opacity: 0.9; }
        button.btn-danger {
            background: var(--critical);
            color: white;
        }
    </style>
</head>
<body>
    <header>
        <div class="brand">
            <span>⚡ AUTOCOPILOT</span>
            <span class="badge">ASSEMBLYAI VOICE AGENT</span>
            <span class="badge">CAN-FD UDS GATEWAY</span>
        </div>
        <div class="status-pill">
            <div class="indicator"></div>
            <span>STREAMING STT (Universal-3 Pro) | 16kHz PCM (100ms)</span>
        </div>
    </header>

    <div class="main-container">
        <!-- 1. 左側：診斷數據 (Diagnostics) -->
        <div class="panel">
            <div class="panel-title">
                <span>車載即時遙測 (CAN Telemetry 10Hz)</span>
                <span id="system-status" style="color: var(--warning);">OVERHEAT WARNING</span>
            </div>

            <div class="gauges-grid">
                <div class="gauge-card warning" id="card-coolant">
                    <span class="gauge-label">冷卻液溫度 (Coolant)</span>
                    <span class="gauge-val warning" id="val-coolant">103.8<span class="gauge-unit">°C</span></span>
                </div>
                <div class="gauge-card" id="card-pressure">
                    <span class="gauge-label">管路壓力 (Pressure)</span>
                    <span class="gauge-val" id="val-pressure">142.5<span class="gauge-unit">kPa</span></span>
                </div>
                <div class="gauge-card" id="card-voltage">
                    <span class="gauge-label">母線高壓 (Voltage)</span>
                    <span class="gauge-val" id="val-voltage">384.2<span class="gauge-unit">V</span></span>
                </div>
                <div class="gauge-card" id="card-rpm">
                    <span class="gauge-label">馬達轉速 (Motor RPM)</span>
                    <span class="gauge-val" id="val-rpm">2,450<span class="gauge-unit">RPM</span></span>
                </div>
                <div class="gauge-card" id="card-inverter">
                    <span class="gauge-label">逆變器溫度 (Inverter)</span>
                    <span class="gauge-val" id="val-inverter">64.2<span class="gauge-unit">°C</span></span>
                </div>
                <div class="gauge-card" id="card-soc">
                    <span class="gauge-label">電池電量 (Pack SoC)</span>
                    <span class="gauge-val" id="val-soc">68.5<span class="gauge-unit">%</span></span>
                </div>
            </div>

            <div class="panel-title">
                <span>活動故障碼 (ISO 14229 DTCs)</span>
                <span class="badge" style="color: var(--warning);">1 ACTIVE / 1 PENDING</span>
            </div>
            <div class="dtc-list">
                <div class="dtc-item">
                    <div>
                        <span class="dtc-code">P0117</span>
                        <span style="margin-left: 6px; color: #eee;">Coolant Temp Sensor 1 Low</span>
                    </div>
                    <span class="badge">ECU: Engine</span>
                </div>
                <div class="dtc-item" style="border-left-color: var(--accent);">
                    <div>
                        <span class="dtc-code" style="color: var(--accent);">U0100</span>
                        <span style="margin-left: 6px; color: #eee;">Lost Comm With ECM 'A'</span>
                    </div>
                    <span class="badge">ECU: BMS</span>
                </div>
            </div>

            <div class="panel-title">
                <span>Word Boost 專用語增強</span>
            </div>
            <div class="word-boost-cloud">
                <span class="boost-tag">CAN-FD</span>
                <span class="boost-tag">UDS 0x19</span>
                <span class="boost-tag">ASIL-B</span>
                <span class="boost-tag">ASIL-D</span>
                <span class="boost-tag">ISO 14229</span>
                <span class="boost-tag">ISO 26262</span>
                <span class="boost-tag">P0117</span>
                <span class="boost-tag">coolant</span>
                <span class="boost-tag">relay</span>
                <span class="boost-tag">BMS</span>
            </div>
        </div>

        <!-- 2. 中間：語音狀態 (Voice Agent Hub) -->
        <div class="panel">
            <div class="panel-title">
                <span>語音狀態與對話 (Voice Agent Hub)</span>
                <span class="badge">VAD: 450ms</span>
            </div>

            <div class="voice-state-bar">
                <span class="state-tag active" id="state-listen">● LISTENING</span>
                <span class="state-tag" id="state-proc">⚙️ PROCESSING</span>
                <span class="state-tag" id="state-speak">🔊 SPEAKING</span>
                <span class="state-tag" id="state-barge">🛑 BARGE-IN</span>
            </div>

            <div class="audio-visualizer">
                <div class="wave-bar" style="height: 12px;"></div>
                <div class="wave-bar" style="height: 24px;"></div>
                <div class="wave-bar" style="height: 38px;"></div>
                <div class="wave-bar" style="height: 18px;"></div>
                <div class="wave-bar" style="height: 30px;"></div>
                <div class="wave-bar" style="height: 42px;"></div>
                <div class="wave-bar" style="height: 20px;"></div>
                <div class="wave-bar" style="height: 14px;"></div>
            </div>

            <div style="display: flex; justify-content: flex-end;">
                <button class="btn-danger" onclick="triggerBargeIn()" style="font-size: 11px; padding: 6px 12px;">
                    🚨 模擬語音打斷 (Barge-In)
                </button>
            </div>

            <div class="chat-stream" id="chat-stream-box">
                <div class="chat-bubble agent">
                    AutoCopilot 聲控診斷副駕已連線。您可以自然發問，例如：「幫我看冷卻液溫度現在多少，手冊上有說超過幾度要停機嗎？」
                </div>
            </div>

            <div class="controls">
                <input type="text" id="user-input" placeholder="輸入或以語音發問 (Enter 送出)..." value="幫我看冷卻液溫度現在多少，手冊上有說超過幾度要停機嗎？">
                <button onclick="sendQuery()">🎙️ 發問</button>
            </div>
        </div>

        <!-- 3. 右側：決策透明度 (Decision Transparency) -->
        <div class="panel">
            <div class="panel-title">
                <span>決策透明度與工具呼叫 (Tool Calling & RAG)</span>
                <span class="badge" style="color: var(--success);">ASYNC.GATHER</span>
            </div>

            <div class="transparency-box">
                <span style="color: var(--text-muted); font-size: 10px;">TRIGGERED TOOL CALLS (JSON PARAMETERS):</span>
                <div class="json-viewer" id="json-tool-calls">
[
  {
    "tool": "get_vehicle_telemetry",
    "subsystem": "thermal_management",
    "metrics": ["coolant_temp_c", "coolant_line_pressure_kpa"]
  },
  {
    "tool": "lookup_repair_procedure",
    "query": "coolant temperature shutdown limit",
    "safety": "standard"
  }
]</div>

                <div style="display: flex; justify-content: space-between; font-size: 11px; margin-top: 4px;">
                    <span>並行執行耗時 (Latency):</span>
                    <span id="latency-val" style="color: var(--accent); font-weight: bold;">0.26 ms</span>
                </div>
            </div>

            <div class="panel-title">
                <span>手冊檢索引文 (Service Manual Citation)</span>
            </div>
            <div class="citation-card" id="citation-box">
                <div style="font-weight: bold; color: var(--accent); margin-bottom: 4px;">SEC-TH-402: Emergency Thermal Shutdown Procedure</div>
                <div style="color: #ccc; font-size: 11px;">
                    Under ISO 26262 ASIL-B thermal supervisory rules: If coolant temperature reaches or exceeds 105.0°C, emergency shutdown protocol is MANDATORY. Shift to neutral/idle and inspect secondary pump relay.
                </div>
                <div style="margin-top: 6px; color: var(--warning); font-size: 10px;">Safety Clearance: standard | Shutdown Limit: 105.0°C</div>
            </div>

            <div class="panel-title">
                <span>即時系統日誌 (Audit Log)</span>
            </div>
            <div class="json-viewer" id="audit-log" style="max-height: 120px;">
[01:46:31] Session started with Universal-3 Pro.
[01:46:31] Word Boost 25 terms registered.
[01:46:32] Turn completed cleanly.</div>
        </div>
    </div>

    <script>
        // 定時抓取 Telemetry
        async function fetchTelemetry() {
            try {
                const res = await fetch('/api/telemetry');
                const data = await res.json();
                const m = data.metrics;
                document.getElementById('val-coolant').innerHTML = m.coolant_temp_c + '<span class="gauge-unit">°C</span>';
                document.getElementById('val-pressure').innerHTML = m.coolant_line_pressure_kpa + '<span class="gauge-unit">kPa</span>';
                document.getElementById('val-voltage').innerHTML = m.bus_voltage_v + '<span class="gauge-unit">V</span>';
                document.getElementById('val-rpm').innerHTML = m.motor_rpm.toLocaleString() + '<span class="gauge-unit">RPM</span>';
                document.getElementById('val-inverter').innerHTML = m.inverter_temp_c + '<span class="gauge-unit">°C</span>';
                document.getElementById('val-soc').innerHTML = m.pack_soc_percent + '<span class="gauge-unit">%</span>';
            } catch (e) {}
        }
        setInterval(fetchTelemetry, 1000);

        // 狀態切換
        function setState(state) {
            document.getElementById('state-listen').className = 'state-tag' + (state === 'listen' ? ' active' : '');
            document.getElementById('state-proc').className = 'state-tag' + (state === 'proc' ? ' active' : '');
            document.getElementById('state-speak').className = 'state-tag' + (state === 'speak' ? ' active' : '');
            document.getElementById('state-barge').className = 'state-tag' + (state === 'barge' ? ' barge-in-flash' : '');
        }

        // 模擬語音打斷
        async function triggerBargeIn() {
            setState('barge');
            try {
                const res = await fetch('/api/interrupt', { method: 'POST' });
                const data = await res.json();
                const chatBox = document.getElementById('chat-stream-box');
                chatBox.innerHTML += `<div class="chat-bubble barge-in">⚡ [BARGE-IN INTERRUPTED] 偵測到使用者語音插話！立即中斷 TTS 輸出並重置對話 Context。</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;
                
                const audit = document.getElementById('audit-log');
                audit.innerHTML += `\\n[BARGE-IN] Token 'interrupt_tts' dispatched. Audio canceled.`;
                audit.scrollTop = audit.scrollHeight;

                setTimeout(() => setState('listen'), 1500);
            } catch (e) {}
        }

        // 發送查詢
        async function sendQuery() {
            const input = document.getElementById('user-input');
            const query = input.value.trim();
            if (!query) return;

            setState('proc');
            const chatBox = document.getElementById('chat-stream-box');
            chatBox.innerHTML += `<div class="chat-bubble user">${query}</div>`;
            chatBox.scrollTop = chatBox.scrollHeight;

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ message: query })
                });
                const data = await res.json();

                // 更新右側透明度面板
                document.getElementById('latency-val').innerText = data.total_latency_ms + ' ms';
                if (data.tool_results && data.tool_results.length > 0) {
                    document.getElementById('json-tool-calls').innerText = JSON.stringify(data.tool_results.map(t => ({
                        tool: t.tool_name,
                        args: t.arguments,
                        latency_ms: t.latency_ms
                    })), null, 2);
                }

                // 渲染 Agent 回應
                setState('speak');
                chatBox.innerHTML += `<div class="chat-bubble agent">${data.spoken_response}</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;

                const audit = document.getElementById('audit-log');
                audit.innerHTML += `\\n[TURN] Completed in ${data.total_latency_ms}ms with ${data.tool_calls_executed} parallel tools.`;
                audit.scrollTop = audit.scrollHeight;

                setTimeout(() => setState('listen'), 2000);
            } catch (e) {
                chatBox.innerHTML += `<div class="chat-bubble agent" style="color: var(--critical);">連線錯誤，請檢查後端網關。</div>`;
                setState('listen');
            }
        }

        document.getElementById('user-input').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') sendQuery();
        });

        // 視覺化動態波形模擬
        setInterval(() => {
            const bars = document.querySelectorAll('.wave-bar');
            bars.forEach(b => {
                const h = Math.floor(Math.random() * 32) + 8;
                b.style.height = h + 'px';
            });
        }, 120);
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    return DASHBOARD_HTML
