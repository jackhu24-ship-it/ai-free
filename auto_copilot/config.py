"""
AutoCopilot Configuration
AssemblyAI Voice Agent & Streaming Settings
"""

import json
from typing import Dict, Any, List

# 音訊規格
AUDIO_FORMAT: Dict[str, Any] = {
    "encoding": "pcm_s16le",
    "sample_rate": 16000,
    "channels": 1,
    "chunk_duration_ms": 100,
    "bytes_per_sample": 2,
    "chunk_size_bytes": 3200  # 16000 * 2 * (100 / 1000)
}

# 工業與車載專用術語增強清單 (Word Boost)
WORD_BOOST_LIST: List[str] = [
    "CAN-FD", "CAN bus", "UDS", "DTC", "ASIL", "ASIL-B", "ASIL-D",
    "ISO 14229", "ISO 26262", "FTTI", "coolant", "ECU", "MCU",
    "P0117", "P0300", "U0100", "BMS", "telemetry", "MOSFET", "relay",
    "inverter", "soc", "kpa", "rpm", "diagnostic", "freeze-frame"
]

# AssemblyAI Agent 完整連線配置
ASSEMBLYAI_AGENT_CONFIG: Dict[str, Any] = {
    "audio_format": {
        "encoding": "pcm_s16le",
        "sample_rate": 16000,
        "channels": 1
    },
    "transcription": {
        "model": "universal-3-pro",
        "language_code": "en",  # 支援多語
        "word_boost": WORD_BOOST_LIST,
        "boost_param": "high"  # 確保生僻工程縮寫不被同音通用詞置換
    },
    "agent": {
        "vad": {
            "speech_threshold": 0.5,
            "silence_duration_ms": 450  # 450ms 靜音判定句尾
        },
        "barge_in": {
            "enabled": True,  # 允許工程師隨時用語音打斷 Agent 發言
            "cancellation_token": "interrupt_tts"
        },
        "system_prompt": (
            "You are AutoCopilot, an expert real-time automotive and industrial diagnostic copilot. "
            "Your user is working hands-on on physical hardware. "
            "Keep all spoken answers concise, safety-first, and limited to 1-2 clear sentences. "
            "When specific parameters (temperature, DTC, pressure) or procedures are requested, "
            "call the appropriate function immediately before answering."
        )
    }
}
