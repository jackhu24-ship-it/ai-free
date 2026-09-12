"""
voice-agent-langgraph-starter: ui/dashboard.py
==============================================
Modular Streamlit Dashboard component with WebRTC audio capture,
live agent status cards, and stream_mode="updates" visualization.
"""

import streamlit as st

def render_agent_status_panel(active_nodes: list = None):
    """Renders real-time agent indicator cards in Streamlit."""
    active_nodes = active_nodes or []
    cols = st.columns(4)
    nodes = [
        ("Supervisor", "supervisor"),
        ("Telemetry Agent", "telemetry_agent"),
        ("Diagnostic Agent", "diagnostic_agent"),
        ("Knowledge Agent", "knowledge_agent")
    ]
    for idx, (label, node_id) in enumerate(nodes):
        with cols[idx]:
            is_active = node_id in active_nodes
            bg_color = "#052e16" if is_active else "#18181b"
            border_color = "#22c55e" if is_active else "#27272a"
            text_color = "#4ade80" if is_active else "#71717a"
            status_text = "ACTIVE" if is_active else "IDLE"
            
            st.markdown(
                f"""
                <div style="background:{bg_color}; border:1px solid {border_color}; border-radius:8px; padding:12px; text-align:center;">
                    <div style="font-weight:600; font-size:0.9rem; color:#f4f4f5;">{label}</div>
                    <div style="font-size:0.75rem; color:{text_color}; margin-top:4px; font-weight:700;">{status_text}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
