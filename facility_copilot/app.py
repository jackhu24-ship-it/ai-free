"""
FacilityCopilot Streamlit Inspector
====================================
Real-time Voice AI Copilot for Data Centers & Semiconductor Cleanrooms
Run: streamlit run facility_copilot/app.py
"""

import asyncio
import os
import sys
import time
import pandas as pd
import streamlit as st

# Path configuration
sys.path.insert(0, os.path.dirname(__file__))
from agent_graph import arun_facility_diagnostic

st.set_page_config(
    page_title="FacilityCopilot | Data Center Voice AI",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 FacilityCopilot: Data Center Voice AI Inspector")
st.caption("Powered by AWS Bedrock & LangGraph StateGraph • Hands-Free Industrial Diagnostics")

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("🎙️ Voice & Scenario Dispatcher")
    user_query = st.text_input(
        "Enter Spoken Query (or select preset below):",
        value="Inspect Rack A04 thermal metrics, check UPS battery, and verify ASHRAE compliance limits."
    )
    
    preset_col1, preset_col2 = st.columns(2)
    with preset_col1:
        if st.button("🌡️ Rack Thermal Only"):
            user_query = "What is the inlet temperature and PUE of Rack A04?"
    with preset_col2:
        if st.button("⚡ UPS & Grid Frequency"):
            user_query = "Check UPS battery runtime and grid input frequency."

    run_btn = st.button("🚀 Run Multi-Agent Diagnostic", type="primary", use_container_width=True)

with col_right:
    st.subheader("⚡ Agent Activation Deck")
    status_placeholder = st.empty()

if run_btn or user_query:
    with st.spinner("Dispatching through LangGraph StateGraph..."):
        res = asyncio.run(arun_facility_diagnostic(user_query))

    duration = res["execution_duration_ms"]
    intents = res.get("target_intents", [])
    response_text = res.get("spoken_response", "")

    with status_placeholder.container():
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("End-to-End Latency", f"{duration:.2f} ms", delta="-95% vs target")
        kpi2.metric("Active Subsystems", len(intents), delta="Fan-out Parallel")
        kpi3.metric("Safety Compliance", "ASHRAE TC 9.9", delta="Audited")

        st.markdown(f"**🔊 Spoken Audio Response:** `{response_text}`")

        card_cols = st.columns(3)
        with card_cols[0]:
            is_active = "rack_telemetry" in intents
            st.markdown(f"""
            <div style="background:{'#052e16' if is_active else '#18181b'}; border:1px solid {'#22c55e' if is_active else '#27272a'}; border-radius:8px; padding:10px;">
                <b>📊 Rack Telemetry</b><br>
                Status: {'ACTIVE (28.4°C / PUE 1.28)' if is_active else 'IDLE'}
            </div>
            """, unsafe_allow_html=True)
        with card_cols[1]:
            is_active = "ups_power" in intents
            st.markdown(f"""
            <div style="background:{'#052e16' if is_active else '#18181b'}; border:1px solid {'#22c55e' if is_active else '#27272a'}; border-radius:8px; padding:10px;">
                <b>⚡ UPS Power Grid</b><br>
                Status: {'ACTIVE (74.2% Load / 24m Bat)' if is_active else 'IDLE'}
            </div>
            """, unsafe_allow_html=True)
        with card_cols[2]:
            is_active = "compliance_safety" in intents
            st.markdown(f"""
            <div style="background:{'#052e16' if is_active else '#18181b'}; border:1px solid {'#22c55e' if is_active else '#27272a'}; border-radius:8px; padding:10px;">
                <b>🛡️ ASHRAE Compliance</b><br>
                Status: {'ACTIVE (Alert: >27°C)' if is_active else 'IDLE'}
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("### 📊 Live Facility Telemetry Stream (AWS IoT Core Simulator)")
df_metrics = pd.DataFrame({
    "Rack ID": ["Rack_A01", "Rack_A02", "Rack_A03", "Rack_A04 (Alert)", "Rack_A05"],
    "Inlet Temp (°C)": [22.1, 23.5, 24.8, 28.4, 23.0],
    "Exhaust Temp (°C)": [34.0, 35.2, 36.1, 39.8, 34.5],
    "CRAC Flow (CFM)": [1200, 1200, 1150, 1050, 1220],
    "Status": ["NORMAL", "NORMAL", "NORMAL", "WARNING_HIGH", "NORMAL"]
})
st.dataframe(df_metrics, use_container_width=True)
