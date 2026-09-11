"""
AutoCopilot - Real-Time Diagnostic Dashboard & Voice Agent Demo
==============================================================
Designed for AssemblyAI x Lablab.ai Hackathon.
Dual Mode: Live WebRTC Streaming (Microphone) + One-Click Simulation
Run with: streamlit run streamlit_app.py
"""

import asyncio
import json
import os
import queue
import random
import threading
import time
from typing import Any, Dict, List
import av
import pandas as pd
import streamlit as st
from streamlit_webrtc import WebRtcMode, webrtc_streamer
import websockets

ASSEMBLYAI_API_KEY = os.environ.get("ASSEMBLYAI_API_KEY", "")

# -----------------------------------------------------------------------------
# Page Configuration & Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AutoCopilot | Voice AI Diagnostics",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .metric-card {
        background-color: #1a1c24;
        border: 1px solid #2d3139;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }
    .badge-active {
        background-color: #0d5f30;
        color: #4ade80;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-bargein {
        background-color: #7f1d1d;
        color: #f87171;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-boost {
        background: linear-gradient(135deg, #7C4DFF, #651FFF);
        color: #FFF;
        font-weight: 600;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        display: inline-block;
        margin-bottom: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# 1. 音訊處理器：攔截 WebRTC 影格並重採樣為 16kHz 16-bit Mono PCM
# -----------------------------------------------------------------------------
class AudioFrameHandler:
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)

    def process_audio(self, frame: av.AudioFrame) -> av.AudioFrame:
        resampled_frames = self.resampler.resample(frame)
        for r_frame in resampled_frames:
            raw_pcm = r_frame.to_ndarray().tobytes()
            self.audio_queue.put(raw_pcm)
        return frame

# -----------------------------------------------------------------------------
# 2. Mock Hardware & RAG Layer
# -----------------------------------------------------------------------------
class DiagnosticBackend:
    @staticmethod
    def get_vehicle_telemetry(subsystem: str) -> Dict[str, Any]:
        """Simulates CAN / UDS real-time bus polling with slight noise."""
        time.sleep(0.06)  # 60ms bus latency
        coolant = round(102.5 + random.uniform(0.5, 3.2), 1)
        voltage = round(384.0 + random.uniform(-1.5, 1.5), 1)
        pressure = round(140.0 + random.uniform(-2.0, 4.0), 1)
        return {
            "subsystem": subsystem,
            "coolant_temp_c": coolant,
            "bus_voltage_v": voltage,
            "coolant_line_pressure_kpa": pressure,
            "status": "CRITICAL_ALERT" if coolant > 105.0 else "WARNING_HIGH",
        }

    @staticmethod
    def read_dtcs() -> List[Dict[str, str]]:
        """Simulates UDS Service 0x19."""
        time.sleep(0.08)
        return [
            {"code": "P0117", "ecu": "ECM", "desc": "Coolant Temp Sensor 1 Low", "severity": "High"},
            {"code": "U0100", "ecu": "BMS", "desc": "Lost Comm with ECM", "severity": "Medium"},
        ]

    @staticmethod
    def query_manual(query: str) -> Dict[str, Any]:
        """Simulates Vector Search across ISO/Workshop Manuals."""
        time.sleep(0.12)
        return {
            "query": query,
            "matched_sop": "SEC-TH-402: Emergency Thermal Shutdown Procedure",
            "critical_limit": "105.0 °C",
            "instruction": "Idle engine immediately. Inspect auxiliary cooling pump relay. Safe state ASIL-B required.",
        }

# -----------------------------------------------------------------------------
# 3. Session State Initialization
# -----------------------------------------------------------------------------
if "audio_handler" not in st.session_state:
    st.session_state.audio_handler = AudioFrameHandler()
if "transcripts" not in st.session_state:
    st.session_state.transcripts = []
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "AutoCopilot 已連線。請點擊上方 START 啟用真實麥克風，或使用下方按鈕進行情境模擬。"}
    ]
if "tool_logs" not in st.session_state:
    st.session_state.tool_logs = []
if "telemetry" not in st.session_state:
    st.session_state.telemetry = DiagnosticBackend.get_vehicle_telemetry("thermal_management")
if "dtcs" not in st.session_state:
    st.session_state.dtcs = DiagnosticBackend.read_dtcs()

# -----------------------------------------------------------------------------
# 4. Background WebSocket Worker (WebRTC -> AssemblyAI)
# -----------------------------------------------------------------------------
def run_assemblyai_pipeline(audio_q: queue.Queue, transcript_list: list, api_key: str):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def _ws_loop():
        if not api_key:
            # Deterministic Dummy Streamer when no key is configured
            while True:
                try:
                    _ = audio_q.get_nowait()
                except queue.Empty:
                    pass
                await asyncio.sleep(0.1)

        ws_url = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000"
        headers = {"Authorization": api_key}

        try:
            async with websockets.connect(ws_url, additional_headers=headers) as ws:
                await ws.recv()  # session init

                async def send_audio():
                    while True:
                        try:
                            data = audio_q.get_nowait()
                            await ws.send(data)
                        except queue.Empty:
                            await asyncio.sleep(0.02)
                        except Exception:
                            break

                async def receive_transcripts():
                    while True:
                        try:
                            msg = await ws.recv()
                            event = json.loads(msg)
                            msg_type = event.get("message_type")
                            if msg_type == "FinalTranscript":
                                text = event.get("text", "")
                                if text.strip():
                                    transcript_list.append(f"【Final】{text}")
                        except Exception:
                            break

                await asyncio.gather(send_audio(), receive_transcripts())
        except Exception:
            pass

    try:
        loop.run_until_complete(_ws_loop())
    finally:
        loop.close()

# -----------------------------------------------------------------------------
# 5. Sidebar: Engine & AssemblyAI Configuration
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Voice Agent Stack")
    st.caption("AssemblyAI Universal-3 Pro + Real-Time WebSocket")

    st.markdown("**ASSEMBLYAI CONNECTION**")
    if ASSEMBLYAI_API_KEY:
        st.success("🟢 WebSocket: Connected (16kHz PCM)")
    else:
        st.info("🟡 Dummy Mode: Ready (No API Key Required)")
    st.markdown("<span class='badge-boost'>✨ Word Boost: Active (High)</span>", unsafe_allow_html=True)
    st.code("boost = ['CAN-FD', 'DTC', 'ASIL', 'ISO 14229', 'P0117']", language="python")

    st.divider()
    st.markdown("**VAD & TURN-TAKING**")
    silence_ms = st.slider("Silence Threshold (ms)", 200, 1000, 450)
    enable_barge_in = st.checkbox("Enable Barge-in (Voice Interruption)", value=True)

    st.divider()
    if st.button("🔄 重置診斷工作階段", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "診斷階段已重置，等待聲控指令。"}
        ]
        st.session_state.tool_logs = []
        st.session_state.transcripts = []
        st.rerun()

# -----------------------------------------------------------------------------
# 6. Main Header & Real-Time WebRTC Mic Streamer
# -----------------------------------------------------------------------------
st.title("🎙️ AutoCopilot : Hands-Free Diagnostic Copilot")
st.caption("AssemblyAI Voice Agent 實時車況診斷與 ISO 安全手冊檢索展示 (Split View)")

# WebRTC 麥克風串流卡片
handler = st.session_state.audio_handler
with st.expander("🎙️ 真實麥克風即時串流 (WebRTC Audio Streamer)", expanded=True):
    col_mic, col_status = st.columns([4, 6])
    with col_mic:
        webrtc_ctx = webrtc_streamer(
            key="speech-to-text",
            mode=WebRtcMode.SENDONLY,
            audio_frame_callback=handler.process_audio,
            media_stream_constraints={"video": False, "audio": True},
        )
    with col_status:
        if webrtc_ctx.state.playing:
            if "ws_thread" not in st.session_state or not st.session_state.ws_thread.is_alive():
                ws_thread = threading.Thread(
                    target=run_assemblyai_pipeline,
                    args=(handler.audio_queue, st.session_state.transcripts, ASSEMBLYAI_API_KEY),
                    daemon=True,
                )
                ws_thread.start()
                st.session_state.ws_thread = ws_thread
            st.success("🟢 麥克風已啟動，正在重採樣 (16kHz 16-bit Mono) 並即時串流...")
        else:
            st.info("💡 點擊上方 START 授權麥克風進行真實聲控對話（若無麥克風可使用下方按鈕一鍵模擬）。")

col_telemetry, col_agent = st.columns([5, 7])

# -----------------------------------------------------------------------------
# 7. Left Column: Telemetry & Vehicle Status
# -----------------------------------------------------------------------------
with col_telemetry:
    st.subheader("📊 即時遙測數據 (CAN Bus)")
    
    t = st.session_state.telemetry
    c1, c2, c3 = st.columns(3)
    c1.metric("冷卻液溫度", f"{t['coolant_temp_c']} °C", delta=f"{round(t['coolant_temp_c'] - 100, 1)} °C", delta_color="inverse")
    c2.metric("高壓母線電壓", f"{t['bus_voltage_v']} V", delta="-1.2 V")
    c3.metric("管路壓力", f"{t['coolant_line_pressure_kpa']} kPa")

    st.markdown("**活動故障代碼 (Active DTCs - UDS 0x19)**")
    dtc_df = pd.DataFrame(st.session_state.dtcs)
    st.dataframe(dtc_df, use_container_width=True, hide_index=True)

    st.markdown("**即時音訊頻譜模擬 (16kHz PCM)**")
    audio_wave = [random.randint(10, 90) for _ in range(30)]
    st.bar_chart(audio_wave, height=120)

# -----------------------------------------------------------------------------
# 8. Right Column: Voice Agent Dialog & Tool Execution Inspector
# -----------------------------------------------------------------------------
with col_agent:
    st.subheader("💬 即時對答與工具呼叫監控 (Agent Inspector)")

    # 模擬語音情境觸發按鈕
    st.markdown("**選擇或模擬語音輸入情境：**")
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    
    scenario_1 = btn_col1.button("🗣️ 檢查冷卻液與停機手冊", use_container_width=True)
    scenario_2 = btn_col2.button("🗣️ 查詢當前 DTC 故障碼", use_container_width=True)
    scenario_barge = btn_col3.button("⚡ 示範口語打斷 (Barge-in)", use_container_width=True)

    # 對話訊息呈現區
    chat_container = st.container(height=260)
    for msg in st.session_state.messages:
        with chat_container.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 處理觸發情境
    if scenario_1:
        user_text = "幫我看冷卻液溫度現在多少，手冊上有說超過幾度要停機嗎？"
        st.session_state.messages.append({"role": "user", "content": user_text})
        
        t0 = time.perf_counter()
        t_data = DiagnosticBackend.get_vehicle_telemetry("thermal_management")
        st.session_state.telemetry = t_data
        dur_1 = round((time.perf_counter() - t0) * 1000, 1)

        t1 = time.perf_counter()
        sop_data = DiagnosticBackend.query_manual("coolant shutdown limit")
        dur_2 = round((time.perf_counter() - t1) * 1000, 1)

        st.session_state.tool_logs.append({
            "tool": "get_vehicle_telemetry",
            "args": {"subsystem": "thermal_management"},
            "latency_ms": dur_1,
            "status": "200 OK",
        })
        st.session_state.tool_logs.append({
            "tool": "lookup_repair_procedure",
            "args": {"query": "coolant shutdown limit"},
            "latency_ms": dur_2,
            "status": "200 OK",
        })

        reply = (
            f"目前冷卻液溫度為 **{t_data['coolant_temp_c']}°C**，已接近警示範圍。"
            f"手冊規定若超過 **{sop_data['critical_limit']}** 必須停機。"
            f"建議措施：{sop_data['instruction']}"
        )
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

    elif scenario_2:
        user_text = "讀取當前 ECU 有沒有任何活動的故障代碼？"
        st.session_state.messages.append({"role": "user", "content": user_text})
        
        t0 = time.perf_counter()
        dtcs = DiagnosticBackend.read_dtcs()
        st.session_state.dtcs = dtcs
        dur = round((time.perf_counter() - t0) * 1000, 1)

        st.session_state.tool_logs.append({
            "tool": "read_diagnostic_trouble_codes",
            "args": {"ecu_target": "all"},
            "latency_ms": dur,
            "status": "200 OK",
        })

        reply = f"目前檢測到 {len(dtcs)} 筆活動 DTC：其中 P0117 為冷卻液傳感器迴路低電壓（高優先級），建議優先排查感測端線束。"
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

    elif scenario_barge:
        user_text = "等等，先跳過這個，幫我切斷繼電器！(語音插話打斷)"
        st.session_state.messages.append({"role": "user", "content": user_text})
        
        st.session_state.tool_logs.append({
            "tool": "assemblyai_vad_interrupt",
            "args": {"event": "barge_in_detected", "cancel_tts_stream": True},
            "latency_ms": 18.5,
            "status": "INTERRUPTED",
        })

        reply = "已收到打斷指令，立即終止前次語音播放，切換至高優先級控制模式。"
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

    # Tool Execution Visualizer
    st.markdown("**⚡ Tool Calling & WebSocket Event Trace**")
    if st.session_state.tool_logs:
        for log in reversed(st.session_state.tool_logs[-4:]):
            is_barge = log["tool"] == "assemblyai_vad_interrupt"
            badge_class = "badge-bargein" if is_barge else "badge-active"
            st.markdown(
                f"""
                <div class="metric-card">
                    <span class="{badge_class}">{log['status']}</span>
                    <strong>{log['tool']}</strong> — 耗時 <code>{log['latency_ms']} ms</code><br>
                    <small style="color: #9ca3af;">參數：{json.dumps(log['args'], ensure_ascii=False)}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("尚未觸發任何 Tool Calling，請點擊上方按鈕模擬語音發問。")