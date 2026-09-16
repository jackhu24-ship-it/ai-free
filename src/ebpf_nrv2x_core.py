import time, struct, hashlib
from typing import Dict, List, Any

class EbpfKernelProbeType:
    KPROBE_CAN_TRANSMIT = 'kprobe_can_transmit'
    KPROBE_SOMEIP_DISPATCH = 'kprobe_someip_dispatch'
    TRACEPOINT_SCHED_SWITCH = 'tracepoint_sched_switch'
    XDP_PACKET_FILTER = 'xdp_packet_filter'

class AutomotiveEbpfObservabilityEngine:
    def __init__(self):
        self.attached_probes = {}
        self.jitter_records_us = []
        self.blocked_malicious_frames = 0

    def attach_probe(self, probe_type: str, hook_symbol: str) -> bool:
        self.attached_probes[probe_type] = {'hook': hook_symbol, 'attached_at': time.time(), 'event_count': 0}
        return True

    def trace_kernel_execution(self, probe_type: str, latency_us: float, payload_len: int) -> dict:
        if probe_type not in self.attached_probes: raise ValueError('Probe not attached')
        self.attached_probes[probe_type]['event_count'] += 1
        self.jitter_records_us.append(latency_us)
        return {'probe': probe_type, 'latency_us': latency_us, 'len': payload_len}

    def enforce_xdp_packet_filter(self, can_id: int, payload: bytes) -> bool:
        if can_id == 0x666 or len(payload) > 64:
            self.blocked_malicious_frames += 1
            return False
        return True

    def get_max_jitter_us(self) -> float:
        return max(self.jitter_records_us) if self.jitter_records_us else 0.0

class NrV2xCooperativePerceptionHub:
    def __init__(self, vehicle_id: str):
        self.vehicle_id = vehicle_id
        self.shared_objects = {}
        self.cpm_counter = 0

    def broadcast_cpm(self, objects: List[dict]) -> bytes:
        self.cpm_counter += 1
        header = struct.pack('>III', 0x56325801, self.cpm_counter, len(objects))
        buf = bytearray(header)
        for obj in objects:
            buf.extend(struct.pack('>ffff', float(obj['x']), float(obj['y']), float(obj['speed']), float(obj['conf'])))
        return bytes(buf)

    def receive_and_fuse_cpm(self, remote_id: str, packet: bytes) -> int:
        if len(packet) < 12: return 0
        magic, seq, count = struct.unpack('>III', packet[:12])
        if magic != 0x56325801: return 0
        offset = 12
        fused = 0
        for i in range(count):
            if offset + 16 > len(packet): break
            x, y, spd, conf = struct.unpack('>ffff', packet[offset:offset+16])
            self.shared_objects[str(remote_id) + '_' + str(i)] = {'x': x, 'y': y, 'speed': spd, 'conf': conf, 'time': time.time()}
            offset += 16
            fused += 1
        return fused

    def get_fused_target_count(self) -> int:
        return len(self.shared_objects)
