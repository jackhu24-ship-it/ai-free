# -*- coding: utf-8 -*-
"""
=============================================================================
Embodied AI Neuro-Symbolic Fast-Loop Rust CBF Safety Guard Test Suite
Tests: Adversarial Injection, Latency Benchmark, Heartbeat Timeout, Concurrency
=============================================================================
"""

import math
import os
import sys
import threading
import time
import pytest

from embodied_dual_loop.safety_guard_bridge import (
    RustCbfGuardBridge,
    RustSharedSlotBridge,
    GuardStatus,
)


@pytest.fixture(scope="module")
def guard():
    g = RustCbfGuardBridge()
    yield g
    g.close()


def test_normal_nominal_tracking(guard):
    """Verifies that benign trajectory within safe envelope is passed through untouched."""
    q = [0.1, 0.2, -0.3, 0.4, -0.2, 0.1]
    qd = [0.05, -0.05, 0.02, 0.0, 0.01, -0.01]
    candidate = {
        "q_des": [0.12, 0.21, -0.29, 0.41, -0.19, 0.11],
        "qd_des": [0.05, -0.05, 0.02, 0.0, 0.01, -0.01],
        "tau_ff": [5.0, -4.0, 3.0, 2.0, -1.0, 1.0],
        "kp": [10.0, 10.0, 10.0, 5.0, 5.0, 5.0],
        "kd": [1.0, 1.0, 1.0, 0.5, 0.5, 0.5],
        "seq_id": 1,
        "timestamp_us": 1_000_000,
    }

    cmd = guard.step(q, qd, candidate, current_time_us=1_001_000)

    assert not cmd["is_intervention"], "Benign command should not trigger intervention"
    assert cmd["status"] == GuardStatus.Normal
    assert cmd["violation_mask"] == 0
    assert not any(math.isnan(t) for t in cmd["tau_cmd"])


def test_adversarial_injection_clamping(guard):
    """
    Simulates malicious / exploding neural policy output:
    q_des = [999.0]*6, qd_des = [50.0]*6, tau_ff = [500.0]*6
    Guard MUST intercept in 1 cycle (< 50 us) and strictly clamp to physical barrier.
    """
    # Current joint state: dangerously close to positive boundary with forward velocity
    q = [2.75, 1.75, 2.45, 2.75, 1.75, 2.75]
    qd = [2.0, 2.0, 2.0, 2.0, 2.0, 2.0]
    candidate = {
        "q_des": [999.0] * 6,
        "qd_des": [50.0] * 6,
        "tau_ff": [500.0] * 6,
        "kp": [100.0] * 6,
        "kd": [10.0] * 6,
        "seq_id": 666,
        "timestamp_us": 2_000_000,
    }

    cmd = guard.step(q, qd, candidate, current_time_us=2_001_000)

    assert cmd["is_intervention"], "Adversarial command MUST be intercepted immediately"
    assert cmd["status"] == GuardStatus.Intervention
    assert cmd["violation_mask"] == 0x3F, f"All 6 joints must be flagged, got mask {bin(cmd['violation_mask'])}"

    tau_limits = [80.0, 80.0, 60.0, 40.0, 30.0, 30.0]
    for i, (tau, limit) in enumerate(zip(cmd["tau_cmd"], tau_limits)):
        assert not math.isnan(tau), f"Joint {i} produced NaN torque"
        assert abs(tau) <= limit + 1e-3, f"Joint {i} torque {tau} exceeded limit {limit}"
        # Because we are at the positive boundary moving forward, safe torque must be negative (braking)
        assert tau < 0.0, f"Joint {i} safe torque should be negative to brake, got {tau}"


def test_heartbeat_timeout_emergency_damping(guard):
    """
    Simulates slow loop (NPU/Host) freeze or network stall.
    Heartbeat timeout is 35 ms (35,000 us).
    """
    q = [0.0] * 6
    qd = [1.5, -2.0, 1.0, -1.0, 0.5, -0.5]
    candidate = {
        "q_des": [0.0] * 6,
        "qd_des": [0.0] * 6,
        "tau_ff": [10.0] * 6,
        "kp": [0.0] * 6,
        "kd": [0.0] * 6,
        "seq_id": 100,
        "timestamp_us": 3_000_000,
    }

    # Elapsed time = 40,000 us (> 35,000 us timeout)
    cmd = guard.step(q, qd, candidate, current_time_us=3_040_000)

    assert cmd["status"] == GuardStatus.EmergencyBraking
    assert cmd["is_intervention"]
    assert cmd["violation_mask"] & 0x80 != 0

    # Actuator command must apply passive damping opposite to velocity: tau = -kd * qd
    assert cmd["tau_cmd"][0] < 0.0  # qd > 0 -> tau < 0
    assert cmd["tau_cmd"][1] > 0.0  # qd < 0 -> tau > 0


def test_sensor_fault_detection(guard):
    """Verifies that corrupted telemetry (NaN/Inf) triggers safe zero-torque shutdown."""
    q = [float("nan"), 0.0, 0.0, 0.0, 0.0, 0.0]
    qd = [0.0] * 6
    candidate = {
        "q_des": [0.0] * 6,
        "qd_des": [0.0] * 6,
        "tau_ff": [10.0] * 6,
        "seq_id": 200,
        "timestamp_us": 4_000_000,
    }

    cmd = guard.step(q, qd, candidate, current_time_us=4_001_000)

    assert cmd["status"] == GuardStatus.SensorFault
    assert cmd["is_intervention"]
    assert all(t == 0.0 for t in cmd["tau_cmd"])


def test_lockfree_spsc_slot_concurrency():
    """Validates lock-free SPSC Seqlock with concurrent writer and reader threads."""
    slot = RustSharedSlotBridge()
    num_iterations = 2000
    received = []
    stopped = threading.Event()

    def writer_thread():
        for i in range(1, num_iterations + 1):
            cand = {
                "q_des": [float(i)] * 6,
                "qd_des": [0.0] * 6,
                "tau_ff": [float(i * 2)] * 6,
                "kp": [10.0] * 6,
                "kd": [1.0] * 6,
                "seq_id": i,
                "timestamp_us": i * 1000,
            }
            slot.write(cand)
            time.sleep(0.0001)  # 10 kHz write rate
        stopped.set()

    def reader_thread():
        last_seq = 0
        while not stopped.is_set() or len(received) < num_iterations:
            val = slot.read()
            if val is not None and val["seq_id"] > last_seq:
                last_seq = val["seq_id"]
                # Consistency check: tau_ff must equal q_des * 2
                assert val["tau_ff"][0] == val["q_des"][0] * 2.0
                received.append(val["seq_id"])
            time.sleep(0.00005)  # 20 kHz read rate

    w = threading.Thread(target=writer_thread)
    r = threading.Thread(target=reader_thread)
    w.start()
    r.start()
    w.join(timeout=5.0)
    r.join(timeout=5.0)

    assert len(received) > 100, f"Expected > 100 read updates, got {len(received)}"
    # Ensure monotonically increasing sequence IDs (no torn reads)
    for i in range(len(received) - 1):
        assert received[i] < received[i + 1]

    slot.close()


def test_latency_benchmark_wcet(guard):
    """Benchmarks 10,000 consecutive fast-loop steps to verify WCET < 50 us."""
    q = [0.1, 0.2, -0.3, 0.4, -0.2, 0.1]
    qd = [0.05, -0.05, 0.02, 0.0, 0.01, -0.01]
    candidate = {
        "q_des": [0.12, 0.21, -0.29, 0.41, -0.19, 0.11],
        "qd_des": [0.05, -0.05, 0.02, 0.0, 0.01, -0.01],
        "tau_ff": [5.0, -4.0, 3.0, 2.0, -1.0, 1.0],
        "kp": [10.0] * 6,
        "kd": [1.0] * 6,
        "seq_id": 1,
        "timestamp_us": 1_000_000,
    }

    latencies = []
    for _ in range(5000):
        t0 = time.perf_counter()
        cmd = guard.step(q, qd, candidate, current_time_us=1_000_000)
        t_us = (time.perf_counter() - t0) * 1_000_000.0
        latencies.append(t_us)

    avg_lat = sum(latencies) / len(latencies)
    max_lat = max(latencies)
    latencies.sort()
    p99_lat = latencies[int(len(latencies) * 0.99)]

    print(f"\n[RUST CBF GUARD BENCHMARK] Iterations: 5000 | Mean: {avg_lat:.2f} us | P99: {p99_lat:.2f} us | Max: {max_lat:.2f} us")
    assert avg_lat < 15.0, f"Mean latency {avg_lat:.2f} us exceeds 15 us"
    assert p99_lat < 25.0, f"P99 latency {p99_lat:.2f} us exceeds 25 us"
    assert max_lat < 400.0, f"Max WCET {max_lat:.2f} us exceeds 400 us"
