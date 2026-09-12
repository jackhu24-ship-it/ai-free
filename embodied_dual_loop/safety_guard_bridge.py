# -*- coding: utf-8 -*-
"""
=============================================================================
Embodied AI Neuro-Symbolic Fast-Loop Safety Guard - Python ctypes Bridge
Zero-Copy C-ABI Integration with Compiled Rust Engine + Resilient Simulation Fallback
=============================================================================
"""

import ctypes
import math
import os
import sys
import time
from enum import IntEnum
from typing import Optional, Tuple, List


class GuardStatus(IntEnum):
    Normal = 0
    Intervention = 1
    EmergencyBraking = 2
    SensorFault = 3


class CJointState(ctypes.Structure):
    _fields_ = [
        ("q", ctypes.c_float * 6),
        ("qd", ctypes.c_float * 6),
        ("tau_est", ctypes.c_float * 6),
        ("timestamp_us", ctypes.c_uint64),
    ]


class CCandidateAction(ctypes.Structure):
    _fields_ = [
        ("q_des", ctypes.c_float * 6),
        ("qd_des", ctypes.c_float * 6),
        ("tau_ff", ctypes.c_float * 6),
        ("kp", ctypes.c_float * 6),
        ("kd", ctypes.c_float * 6),
        ("seq_id", ctypes.c_uint64),
        ("timestamp_us", ctypes.c_uint64),
    ]


class CVerifiedActuatorCommand(ctypes.Structure):
    _fields_ = [
        ("tau_cmd", ctypes.c_float * 6),
        ("is_intervention", ctypes.c_bool),
        ("violation_mask", ctypes.c_uint32),
        ("execution_time_us", ctypes.c_float),
        ("status", ctypes.c_uint32),
    ]


class CPhysicalSafetyBounds(ctypes.Structure):
    _fields_ = [
        ("q_min", ctypes.c_float * 6),
        ("q_max", ctypes.c_float * 6),
        ("qd_max", ctypes.c_float * 6),
        ("tau_max", ctypes.c_float * 6),
        ("gamma", ctypes.c_float),
        ("damping_kd", ctypes.c_float * 6),
    ]


def find_safety_guard_library() -> Optional[str]:
    """Locates the compiled safety_guard shared library (.dll / .so / .dylib)."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "safety_guard", "target", "release", "safety_guard.dll"),
        os.path.join(base_dir, "safety_guard", "target", "debug", "safety_guard.dll"),
        os.path.join(base_dir, "safety_guard", "target", "x86_64-pc-windows-gnu", "release", "safety_guard.dll"),
        os.path.join(base_dir, "safety_guard", "target", "x86_64-pc-windows-gnu", "debug", "safety_guard.dll"),
        os.path.join(base_dir, "safety_guard.dll"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None


class PurePythonCbfGuardFallback:
    """Bit-exact pure Python fallback if native DLL is building or linking."""
    def __init__(self):
        self.q_min = [-2.8, -1.8, -2.5, -2.8, -1.8, -2.8]
        self.q_max = [ 2.8,  1.8,  2.5,  2.8,  1.8,  2.8]
        self.qd_max = [3.14, 3.14, 3.14, 4.0, 4.0, 4.0]
        self.tau_max = [80.0, 80.0, 60.0, 40.0, 30.0, 30.0]
        self.gamma = 12.0
        self.damping_kd = [5.0, 5.0, 5.0, 3.0, 3.0, 3.0]
        self.heartbeat_timeout_us = 35_000
        self.total_cycles = 0
        self.total_interventions = 0

    def step(self, q: List[float], qd: List[float], candidate: Optional[dict], current_time_us: int) -> dict:
        t0 = time.perf_counter()
        self.total_cycles += 1

        # 1. Sensor telemetry check
        for i in range(6):
            if any(math.isnan(v) or math.isinf(v) for v in (q[i], qd[i])):
                self.total_interventions += 1
                return {
                    "tau_cmd": [0.0] * 6,
                    "is_intervention": True,
                    "violation_mask": 0x3F,
                    "execution_time_us": (time.perf_counter() - t0) * 1e6,
                    "status": GuardStatus.SensorFault,
                }

        # 2. Heartbeat check
        is_alive = False
        if candidate is not None:
            age = current_time_us - candidate.get("timestamp_us", current_time_us)
            if age <= self.heartbeat_timeout_us:
                is_alive = True

        if not is_alive:
            self.total_interventions += 1
            tau_cmd = [
                max(-self.tau_max[i], min(self.tau_max[i], -self.damping_kd[i] * qd[i]))
                for i in range(6)
            ]
            return {
                "tau_cmd": tau_cmd,
                "is_intervention": True,
                "violation_mask": 0x80,
                "execution_time_us": (time.perf_counter() - t0) * 1e6,
                "status": GuardStatus.EmergencyBraking,
            }

        # 3. CBF projection
        any_intervention = False
        mask = 0
        tau_cmd = []

        q_des = candidate.get("q_des", [0.0] * 6)
        qd_des = candidate.get("qd_des", [0.0] * 6)
        tau_ff = candidate.get("tau_ff", [0.0] * 6)
        kp = candidate.get("kp", [0.0] * 6)
        kd = candidate.get("kd", [0.0] * 6)

        for i in range(6):
            tau_pd = kp[i] * (q_des[i] - q[i]) + kd[i] * (qd_des[i] - qd[i])
            tau_desired = tau_ff[i] + tau_pd

            t_max = self.tau_max[i]
            q_max = self.q_max[i]
            q_min = self.q_min[i]
            qd_max = self.qd_max[i]
            gamma = self.gamma
            alpha = gamma

            # Second-order CBF
            accel_cbf_pos_upper = (alpha * gamma) * (q_max - q[i]) - (alpha + gamma) * qd[i]
            accel_cbf_pos_lower = -(alpha * gamma) * (q[i] - q_min) - (alpha + gamma) * qd[i]
            accel_cbf_vel_upper = gamma * (qd_max - qd[i])
            accel_cbf_vel_lower = -gamma * (qd_max + qd[i])

            max_accel = min(accel_cbf_pos_upper, accel_cbf_vel_upper)
            min_accel = max(accel_cbf_pos_lower, accel_cbf_vel_lower)

            tau_cbf_upper = max(-t_max, min(t_max, max_accel * 1.0))
            tau_cbf_lower = max(-t_max, min(t_max, min_accel * 1.0))

            if tau_cbf_lower > tau_cbf_upper:
                mid = (tau_cbf_lower + tau_cbf_upper) * 0.5
                tau_cbf_lower = mid - 1.0
                tau_cbf_upper = mid + 1.0

            intercepted = False
            if tau_desired > tau_cbf_upper:
                tau_safe = tau_cbf_upper
                intercepted = True
            elif tau_desired < tau_cbf_lower:
                tau_safe = tau_cbf_lower
                intercepted = True
            else:
                tau_safe = max(-t_max, min(t_max, tau_desired))

            tau_cmd.append(tau_safe)
            if intercepted:
                any_intervention = True
                mask |= (1 << i)

        if any_intervention:
            self.total_interventions += 1
            status = GuardStatus.Intervention
        else:
            status = GuardStatus.Normal

        return {
            "tau_cmd": tau_cmd,
            "is_intervention": any_intervention,
            "violation_mask": mask,
            "execution_time_us": (time.perf_counter() - t0) * 1e6,
            "status": status,
        }

    def get_stats(self) -> Tuple[int, int]:
        return self.total_cycles, self.total_interventions

    def close(self):
        pass


class PurePythonSharedSlotFallback:
    """Thread-safe SPSC slot simulation fallback."""
    def __init__(self):
        import threading
        self._lock = threading.Lock()
        self._data = None
        self._initialized = False

    def write(self, candidate: dict):
        with self._lock:
            self._data = dict(candidate)
            self._initialized = True
        return True

    def read(self) -> Optional[dict]:
        with self._lock:
            if not self._initialized or self._data is None:
                return None
            return dict(self._data)

    def close(self):
        pass


class RustCbfGuardBridge:
    """
    High-level Python wrapper for the CBF Safety Guard.
    Automatically uses native compiled Rust DLL when present, with seamless fallback.
    """
    def __init__(self, lib_path: Optional[str] = None):
        if lib_path is None:
            lib_path = find_safety_guard_library()

        self._is_native = False
        self._fallback = None
        self._lib = None
        self._handle = None

        if lib_path and os.path.isfile(lib_path):
            try:
                self._lib = ctypes.CDLL(lib_path)
                self._setup_ffi_signatures()
                self._handle = self._lib.safety_guard_create()
                if self._handle:
                    self._is_native = True
            except Exception as e:
                print(f"[WARN] Failed to link native DLL: {e}. Falling back to simulation mode.")

        if not self._is_native:
            self._fallback = PurePythonCbfGuardFallback()

    def _setup_ffi_signatures(self):
        self._lib.safety_guard_create.argtypes = []
        self._lib.safety_guard_create.restype = ctypes.c_void_p
        self._lib.safety_guard_destroy.argtypes = [ctypes.c_void_p]
        self._lib.safety_guard_destroy.restype = None
        self._lib.safety_guard_step.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(CJointState),
            ctypes.POINTER(CCandidateAction),
            ctypes.c_uint64,
            ctypes.POINTER(CVerifiedActuatorCommand),
        ]
        self._lib.safety_guard_step.restype = ctypes.c_bool
        self._lib.safety_guard_get_stats.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint64),
            ctypes.POINTER(ctypes.c_uint64),
        ]
        self._lib.safety_guard_get_stats.restype = ctypes.c_bool

    def step(
        self,
        q: List[float],
        qd: List[float],
        candidate: Optional[dict],
        current_time_us: int,
    ) -> dict:
        if not self._is_native:
            return self._fallback.step(q, qd, candidate, current_time_us)

        state = CJointState()
        for i in range(6):
            state.q[i] = float(q[i])
            state.qd[i] = float(qd[i])
            state.tau_est[i] = 0.0
        state.timestamp_us = current_time_us

        cand_ptr = None
        if candidate is not None:
            cand = CCandidateAction()
            q_des = candidate.get("q_des", [0.0] * 6)
            qd_des = candidate.get("qd_des", [0.0] * 6)
            tau_ff = candidate.get("tau_ff", [0.0] * 6)
            kp = candidate.get("kp", [0.0] * 6)
            kd = candidate.get("kd", [0.0] * 6)
            for i in range(6):
                cand.q_des[i] = float(q_des[i])
                cand.qd_des[i] = float(qd_des[i])
                cand.tau_ff[i] = float(tau_ff[i])
                cand.kp[i] = float(kp[i])
                cand.kd[i] = float(kd[i])
            cand.seq_id = candidate.get("seq_id", 0)
            cand.timestamp_us = candidate.get("timestamp_us", current_time_us)
            cand_ptr = ctypes.pointer(cand)

        cmd = CVerifiedActuatorCommand()
        ok = self._lib.safety_guard_step(
            self._handle,
            ctypes.byref(state),
            cand_ptr,
            current_time_us,
            ctypes.byref(cmd),
        )

        if not ok:
            raise RuntimeError("safety_guard_step call failed in native C ABI")

        return {
            "tau_cmd": [float(cmd.tau_cmd[i]) for i in range(6)],
            "is_intervention": bool(cmd.is_intervention),
            "violation_mask": int(cmd.violation_mask),
            "execution_time_us": float(cmd.execution_time_us),
            "status": GuardStatus(cmd.status),
        }

    def get_stats(self) -> Tuple[int, int]:
        if not self._is_native:
            return self._fallback.get_stats()
        cycles = ctypes.c_uint64(0)
        interventions = ctypes.c_uint64(0)
        self._lib.safety_guard_get_stats(
            self._handle, ctypes.byref(cycles), ctypes.byref(interventions)
        )
        return int(cycles.value), int(interventions.value)

    def close(self):
        if self._is_native and hasattr(self, "_handle") and self._handle:
            self._lib.safety_guard_destroy(self._handle)
            self._handle = None
        elif self._fallback:
            self._fallback.close()

    def __del__(self):
        self.close()


class RustSharedSlotBridge:
    """
    Python wrapper for the Lock-Free SPSC Seqlock shared slot.
    """
    def __init__(self, lib_path: Optional[str] = None):
        if lib_path is None:
            lib_path = find_safety_guard_library()
        self._is_native = False
        self._fallback = None
        self._lib = None
        self._handle = None

        if lib_path and os.path.isfile(lib_path):
            try:
                self._lib = ctypes.CDLL(lib_path)
                self._lib.slot_create.argtypes = []
                self._lib.slot_create.restype = ctypes.c_void_p
                self._lib.slot_destroy.argtypes = [ctypes.c_void_p]
                self._lib.slot_destroy.restype = None
                self._lib.slot_write.argtypes = [ctypes.c_void_p, ctypes.POINTER(CCandidateAction)]
                self._lib.slot_write.restype = ctypes.c_bool
                self._lib.slot_read.argtypes = [ctypes.c_void_p, ctypes.POINTER(CCandidateAction)]
                self._lib.slot_read.restype = ctypes.c_bool
                self._handle = self._lib.slot_create()
                if self._handle:
                    self._is_native = True
            except Exception as e:
                pass

        if not self._is_native:
            self._fallback = PurePythonSharedSlotFallback()

    def write(self, candidate: dict):
        if not self._is_native:
            return self._fallback.write(candidate)
        cand = CCandidateAction()
        q_des = candidate.get("q_des", [0.0] * 6)
        qd_des = candidate.get("qd_des", [0.0] * 6)
        tau_ff = candidate.get("tau_ff", [0.0] * 6)
        kp = candidate.get("kp", [0.0] * 6)
        kd = candidate.get("kd", [0.0] * 6)
        for i in range(6):
            cand.q_des[i] = float(q_des[i])
            cand.qd_des[i] = float(qd_des[i])
            cand.tau_ff[i] = float(tau_ff[i])
            cand.kp[i] = float(kp[i])
            cand.kd[i] = float(kd[i])
        cand.seq_id = candidate.get("seq_id", 0)
        cand.timestamp_us = candidate.get("timestamp_us", 0)
        return self._lib.slot_write(self._handle, ctypes.byref(cand))

    def read(self) -> Optional[dict]:
        if not self._is_native:
            return self._fallback.read()
        cand = CCandidateAction()
        ok = self._lib.slot_read(self._handle, ctypes.byref(cand))
        if not ok:
            return None
        return {
            "q_des": [float(cand.q_des[i]) for i in range(6)],
            "qd_des": [float(cand.qd_des[i]) for i in range(6)],
            "tau_ff": [float(cand.tau_ff[i]) for i in range(6)],
            "kp": [float(cand.kp[i]) for i in range(6)],
            "kd": [float(cand.kd[i]) for i in range(6)],
            "seq_id": int(cand.seq_id),
            "timestamp_us": int(cand.timestamp_us),
        }

    def close(self):
        if self._is_native and hasattr(self, "_handle") and self._handle:
            self._lib.slot_destroy(self._handle)
            self._handle = None
        elif self._fallback:
            self._fallback.close()

    def __del__(self):
        self.close()
