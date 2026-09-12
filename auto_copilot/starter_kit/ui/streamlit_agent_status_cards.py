"""
=============================================================================
模組 C：Streamlit 多代理視覺化模板 (streamlit_agent_status_cards.py)
=============================================================================
Universal Frontend Pattern for Multi-Agent Observability:
- Dynamic st.empty() containers for zero-page-reload updates
- Color-coded micro-states: IDLE (#71717a), ACTIVE (#22c55e), DONE (#3b82f6)
- Millisecond latency badges and live execution tracing
=============================================================================
"""

import time
from typing import Dict, List, Optional
import streamlit as st

class AgentCardManager:
    """
    Manages dynamic Streamlit status cards for concurrent multi-agent nodes.
    """
    def __init__(self, node_definitions: List[Dict[str, str]] = None):
        # Default node configuration
        self.nodes = node_definitions or [
            {"id": "supervisor", "name": "👑 Supervisor", "role": "Intent Routing"},
            {"id": "telemetry_agent", "name": "📊 Telemetry Agent", "role": "CAN-FD Polling"},
            {"id": "diagnostic_agent", "name": "⚠️ DTC Agent", "role": "UDS 0x19 Diagnosis"},
            {"id": "knowledge_agent", "name": "🛡️ Safety Agent", "role": "ISO Manual RAG"},
            {"id": "synthesizer", "name": "🔊 Synthesizer", "role": "Voice Assembly"}
        ]
        self.placeholders: Dict[str, Any] = {}
        self.states: Dict[str, Dict[str, Any]] = {
            n["id"]: {"status": "IDLE", "latency_ms": 0.0, "details": ""}
            for n in self.nodes
        }

    def render_initial_layout(self):
        """Builds the Streamlit column layout with empty placeholders."""
        cols = st.columns(len(self.nodes))
        for idx, node in enumerate(self.nodes):
            with cols[idx]:
                self.placeholders[node["id"]] = st.empty()
                self._draw_single_card(node["id"])

    def update_node_state(self, node_id: str, status: str, latency_ms: float = 0.0, details: str = ""):
        """Dynamically redraws a single card within its placeholder."""
        if node_id in self.states:
            self.states[node_id]["status"] = status
            if latency_ms > 0:
                self.states[node_id]["latency_ms"] = latency_ms
            if details:
                self.states[node_id]["details"] = details
            self._draw_single_card(node_id)

    def _draw_single_card(self, node_id: str):
        node_meta = next(n for n in self.nodes if n["id"] == node_id)
        state = self.states[node_id]
        status = state["status"]
        latency = state["latency_ms"]

        # Color mapping
        if status == "ACTIVE":
            bg = "#052e16"
            border = "#22c55e"
            badge_bg = "#16a34a"
            badge_txt = "#ffffff"
        elif status == "DONE":
            bg = "#172554"
            border = "#3b82f6"
            badge_bg = "#2563eb"
            badge_txt = "#ffffff"
        else: # IDLE
            bg = "#18181b"
            border = "#27272a"
            badge_bg = "#3f3f46"
            badge_txt = "#a1a1aa"

        card_html = f"""
        <div style="background:{bg}; border:1px solid {border}; border-radius:8px; padding:12px; margin-bottom:8px; transition: all 0.2s;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:700; font-size:0.85rem; color:#f4f4f5;">{node_meta['name']}</span>
                <span style="background:{badge_bg}; color:{badge_txt}; font-size:0.7rem; padding:2px 6px; border-radius:4px; font-weight:800;">{status}</span>
            </div>
            <div style="font-size:0.75rem; color:#a1a1aa; margin-top:4px;">{node_meta['role']}</div>
            <div style="font-family:monospace; font-size:0.75rem; color:#38bdf8; margin-top:8px;">
                {f"{latency:.1f} ms" if latency > 0 else "-- ms"}
            </div>
        </div>
        """
        if node_id in self.placeholders:
            self.placeholders[node_id].markdown(card_html, unsafe_allow_html=True)
