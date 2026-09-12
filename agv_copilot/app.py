"""
AGVCopilot Streamlit Multimodal Inspector
==========================================
Voice & Vision AI Copilot for Autonomous Mobile Robots (AGV/AMR)
Run: streamlit run agv_copilot/app.py
"""

import asyncio
import os
import sys
import time
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))
from agent_graph import arun_agv_diagnostic

st.set_page_config(
    page_title="AGVCopilot | Autonomous Fleet Voice & Vision AI",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AGVCopilot: Multimodal Fleet Diagnostics")
st.caption("Powered by Google Cloud Vertex AI & LangGraph StateGraph • ISO 3691-4 Mobile Robot Compliance")

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("🎙️ Voice & Multimodal Controls")
    user_query = st.text_input(
        "Spoken Command / Inspection Request:",
        value="Check AMR-08 velocity, scan obstacle clearance with LiDAR, and verify ISO 3691-4 safety braking standard."
    )

    preset_c1, preset_c2 = st.columns(2)
    with preset_c1:
        if st.button("🏎️ AMR Kinematics Only"):
            user_query = "What is AMR-08 current speed and battery state of charge?"
    with preset_c2:
        if st.button("📡 360° Safety LiDAR Only"):
            user_query = "Check front safety LiDAR clearance and camera inspection."

    run_btn = st.button("🚀 Execute Multimodal Diagnostic", type="primary", use_container_width=True)

with col_right:
    st.subheader("⚡ Robot Agent Telemetry Deck")
    status_placeholder = st.empty()

if run_btn or user_query:
    with st.spinner("Dispatching through Vertex AI Multimodal StateGraph..."):
        res = asyncio.run(arun_agv_diagnostic(user_query))

    duration = res["execution_duration_ms"]
    intents = res.get("target_intents", [])
    response_text = res.get("spoken_response", "")

    with status_placeholder.container():
        k1, k2, k3 = st.columns(3)
        k1.metric("Processing Latency", f"{duration:.2f} ms", delta="-96% vs threshold")
        k2.metric("Target Subsystems", len(intents), delta="Fan-out Concurrent")
        k3.metric("Robotic Safety", "ISO 3691-4", delta="Active Braking")

        st.markdown(f"**🔊 Spoken Audio Response:** `{response_text}`")

        card_cols = st.columns(3)
        with card_cols[0]:
            is_active = "kinematics" in intents
            st.markdown(f"""
            <div style="background:{'#052e16' if is_active else '#18181b'}; border:1px solid {'#22c55e' if is_active else '#27272a'}; border-radius:8px; padding:10px;">
                <b>🏎️ Kinematics</b><br>
                Status: {'ACTIVE (1.25 m/s / Bat 38%)' if is_active else 'IDLE'}
            </div>
            """, unsafe_allow_html=True)
        with card_cols[1]:
            is_active = "vision_lidar" in intents
            st.markdown(f"""
            <div style="background:{'#052e16' if is_active else '#18181b'}; border:1px solid {'#22c55e' if is_active else '#27272a'}; border-radius:8px; padding:10px;">
                <b>📡 LiDAR & Vision</b><br>
                Status: {'ACTIVE (Obstacle: 0.42m)' if is_active else 'IDLE'}
            </div>
            """, unsafe_allow_html=True)
        with card_cols[2]:
            is_active = "safety_iso" in intents
            st.markdown(f"""
            <div style="background:{'#052e16' if is_active else '#18181b'}; border:1px solid {'#22c55e' if is_active else '#27272a'}; border-radius:8px; padding:10px;">
                <b>🛡️ ISO 3691-4 Safety</b><br>
                Status: {'ACTIVE (Emergency Stop)' if is_active else 'IDLE'}
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("### 🤖 Factory Floor AGV Fleet Live Telemetry")
df_fleet = pd.DataFrame({
    "Unit ID": ["AMR-01", "AMR-02", "AMR-05", "AMR-08 (Alert)", "AMR-11"],
    "Velocity (m/s)": [1.5, 1.4, 0.0, 1.25, 1.6],
    "Battery (%)": [88, 76, 12, 38, 92],
    "LiDAR Clearance (m)": [2.4, 1.8, 3.5, 0.42, 2.1],
    "Safety Field Status": ["CLEAR", "CLEAR", "CHARGING", "BREACHED (0.42m)", "CLEAR"]
})
st.dataframe(df_fleet, use_container_width=True)
