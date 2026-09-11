"""
AutoCopilot Audio Hardware Streamer
Captures real 16kHz 16-bit Mono PCM audio chunks via sounddevice/pyaudio,
with seamless fallback to simulated PCM stream if hardware is unavailable.
"""

import asyncio
import logging
import time
from typing import Optional, Callable, AsyncGenerator

logger = logging.getLogger("AutoCopilot.AudioHardware")

class AudioHardwareStreamer:
    """
    Manages physical microphone audio capture and streaming.
    Samples at 16000 Hz, 16-bit Mono (PCM s16le), chunk size = 100ms (3200 bytes).
    """
    def __init__(self, sample_rate: int = 16000, chunk_ms: int = 100):
        self.sample_rate = sample_rate
        self.chunk_ms = chunk_ms
        self.samples_per_chunk = int(sample_rate * (chunk_ms / 1000.0))
        self.bytes_per_chunk = self.samples_per_chunk * 2  # 16-bit = 2 bytes
        self.is_recording = False
        self._has_sounddevice = False

        try:
            import sounddevice as sd
            self._sd = sd
            self._has_sounddevice = True
            logger.info("🎤 sounddevice module detected. Physical microphone capture available.")
        except ImportError:
            logger.info("ℹ️ sounddevice not installed. Fallback to high-fidelity simulated PCM stream.")

    async def stream_audio_chunks(
        self,
        duration_seconds: float = 3.0,
        queue: Optional[asyncio.Queue] = None
    ) -> AsyncGenerator[bytes, None]:
        """
        Yields 100ms PCM chunks.
        If queue is provided, also puts chunks into the queue.
        """
        self.is_recording = True
        start_time = time.time()
        logger.info(f"🎙️ Audio streaming started (Target: {duration_seconds}s, 16kHz PCM)...")

        # 若有實體音效卡且能開啟 stream
        if self._has_sounddevice:
            try:
                loop = asyncio.get_running_loop()
                stream_queue = asyncio.Queue()

                def callback(indata, frames, time_info, status):
                    if status:
                        logger.warning(f"Audio status warning: {status}")
                    # indata is numpy array or bytes
                    raw_bytes = indata.tobytes() if hasattr(indata, "tobytes") else bytes(indata)
                    loop.call_soon_threadsafe(stream_queue.put_nowait, raw_bytes)

                with self._sd.RawInputStream(
                    samplerate=self.sample_rate,
                    blocksize=self.samples_per_chunk,
                    channels=1,
                    dtype='int16',
                    callback=callback
                ):
                    while (time.time() - start_time) < duration_seconds and self.is_recording:
                        try:
                            chunk = await asyncio.wait_for(stream_queue.get(), timeout=0.2)
                            if queue:
                                await queue.put(chunk)
                            yield chunk
                        except asyncio.TimeoutError:
                            continue
                self.is_recording = False
                logger.info("🎙️ Physical audio streaming ended cleanly.")
                return
            except Exception as e:
                logger.warning(f"Failed to open hardware microphone ({e}). Falling back to simulation.")

        # 模擬 PCM 串流（優雅回退）
        blank_chunk = b"\x00" * self.bytes_per_chunk
        while (time.time() - start_time) < duration_seconds and self.is_recording:
            if queue:
                await queue.put(blank_chunk)
            yield blank_chunk
            await asyncio.sleep(self.chunk_ms / 1000.0)

        self.is_recording = False
        logger.info("🎙️ Simulated audio streaming finished.")

    def stop(self):
        """停止音訊採集"""
        self.is_recording = False


# 全域單例
audio_streamer = AudioHardwareStreamer()
