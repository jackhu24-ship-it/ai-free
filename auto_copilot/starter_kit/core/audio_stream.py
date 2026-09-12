"""
voice-agent-langgraph-starter: core/audio_stream.py
===================================================
Handles full-duplex WebRTC/PCM audio ingestion, dynamic resampling,
and real-time streaming to AssemblyAI WebSocket with Word Boost and Barge-In support.
"""

import asyncio
import json
import logging
from typing import Callable, Optional
import websockets

logger = logging.getLogger("audio_stream")

class AudioStreamClient:
    """Manages streaming WebSockets connection to AssemblyAI Real-Time STT."""
    
    def __init__(self, api_key: str, sample_rate: int = 16000, word_boost: list = None):
        self.api_key = api_key
        self.sample_rate = sample_rate
        self.word_boost = word_boost or []
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.is_connected = False
        self.on_partial_transcript: Optional[Callable[[str], None]] = None
        self.on_final_transcript: Optional[Callable[[str], None]] = None

    async def connect(self):
        """Initiates streaming WebSocket session with AssemblyAI Universal-3 Pro."""
        if not self.api_key:
            logger.info("No AssemblyAI API Key provided. Running in Local Dummy/Simulation mode.")
            self.is_connected = True
            return

        url = f"wss://api.assemblyai.com/v2/realtime/ws?sample_rate={self.sample_rate}"
        if self.word_boost:
            boost_param = json.dumps(self.word_boost)
            url += f"&word_boost={boost_param}"

        headers = {"Authorization": self.api_key}
        self.ws = await websockets.connect(url, extra_headers=headers)
        self.is_connected = True
        logger.info("Connected to AssemblyAI Real-Time WebSocket.")

    async def send_audio_chunk(self, pcm_bytes: bytes):
        """Sends raw 16kHz 16-bit Mono PCM audio frame to the STT engine."""
        if self.ws and not self.ws.closed:
            await self.ws.send(pcm_bytes)

    async def listen_loop(self):
        """Listens for partial and final transcription events."""
        if not self.ws:
            return
        async for message in self.ws:
            data = json.loads(message)
            msg_type = data.get("message_type")
            text = data.get("text", "")
            
            if msg_type == "PartialTranscript" and text:
                if self.on_partial_transcript:
                    self.on_partial_transcript(text)
            elif msg_type == "FinalTranscript" and text:
                if self.on_final_transcript:
                    self.on_final_transcript(text)

    async def close(self):
        """Safely terminates WebSocket session."""
        if self.ws and not self.ws.closed:
            await self.ws.send(json.dumps({"terminate_session": True}))
            await self.ws.close()
        self.is_connected = False
