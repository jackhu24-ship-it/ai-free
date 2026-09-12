# -*- coding: utf-8 -*-
"""
=============================================================================
Dual-Loop Lock-Free Shared Memory RingBuffer (POSIX shm / Zenoh Emulation)
=============================================================================
Slow Loop (Cognitive VLA): 10 - 50 Hz writes
Fast Loop (Deterministic RTOS): 500 - 1000 Hz non-blocking reads
Max Jitter SLA: <= 50 microseconds
=============================================================================
"""

import time
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from embodied_dual_loop.cbf_safety_arbiter import CandidateAction


@dataclass
class RingBufferSlot:
    action: CandidateAction
    written_timestamp: float
    sequence_id: int
    is_valid: bool = False


class DualLoopIPCRingBuffer:
    """
    Simulated lock-free circular buffer representing shared memory IPC
    between Host Linux (PREEMPT_RT) and real-time core (RTOS / Cortex-R).
    """
    def __init__(self, capacity: int = 16):
        self.capacity = capacity
        self.buffer: List[Optional[RingBufferSlot]] = [None] * capacity
        self.write_idx = 0
        self.latest_seq = 0
        self.overruns = 0
        self.total_writes = 0
        self.total_reads = 0

    def write_candidate(self, torques: List[float], source_time: Optional[float] = None) -> int:
        """Called by Slow Loop (Cognitive VLA @ 30Hz)."""
        now = time.time() if source_time is None else source_time
        self.latest_seq += 1
        
        action = CandidateAction(
            desired_torques=torques,
            source_timestamp=now,
            sequence_id=self.latest_seq
        )
        
        slot = RingBufferSlot(
            action=action,
            written_timestamp=now,
            sequence_id=self.latest_seq,
            is_valid=True
        )

        idx = self.write_idx % self.capacity
        self.buffer[idx] = slot
        self.write_idx += 1
        self.total_writes += 1
        return self.latest_seq

    def read_latest(self) -> Optional[CandidateAction]:
        """Called by Fast Loop (Deterministic RTOS @ 1000Hz). Non-blocking O(1)."""
        self.total_reads += 1
        if self.write_idx == 0:
            return None

        latest_slot_idx = (self.write_idx - 1) % self.capacity
        slot = self.buffer[latest_slot_idx]
        if slot and slot.is_valid:
            return slot.action
        return None

    def get_ipc_telemetry(self) -> Dict[str, Any]:
        return {
            "capacity": self.capacity,
            "total_writes": self.total_writes,
            "total_reads": self.total_reads,
            "latest_sequence": self.latest_seq,
            "overruns": self.overruns
        }