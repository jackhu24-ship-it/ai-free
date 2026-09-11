"""
AutoCopilot - Standalone Voice Agent Core Entrypoint
===================================================
Direct root entrypoint for running the AutoCopilot Real-Time Voice Agent.
Supports environment variable ASSEMBLYAI_API_KEY.
"""

import os
import sys
import asyncio

# Ensure local auto_copilot module is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auto_copilot.demo_realtime_core import AutoCopilotClient

if __name__ == "__main__":
    api_key = os.environ.get("ASSEMBLYAI_API_KEY", "mock_assemblyai_key_hackathon")
    copilot = AutoCopilotClient(api_key=api_key)
    asyncio.run(copilot.run_mock_agent_session())
