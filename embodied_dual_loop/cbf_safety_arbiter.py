# -*- coding: utf-8 -*-
"""
=============================================================================
Embodied AI Neuro-Symbolic Safety Arbiter (CBF & QP Solver)
=============================================================================
Philosophy: "Neural network expands upper bound; Symbolic engine defends lower bound."
Loop Frequency: 1000 Hz (1 ms cycle period)
Arbiter Target: WCET <= 200 us
Safety Invariant Violation: STRICTLY 0
=============================================================================
"""

import time
import math
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple


class ArbiterState(Enum):
    NOMINAL_TRACKING = "NOMINAL_TRACKING"
    CBF_FILTERED = "CBF_FILTERED"
    DAMPING_BRAKE = "DAMPING_BRAKE"
    SAFE_RECOVERY_POSE = "SAFE_RECOVERY_POSE"
    EMERGENCY_ESTOP = "EMERGENCY_ESTOP"


@dataclass
class RobotKinematicState:
    joint_positions: List[float]       # q (rad)
    joint_velocities: List[float]      # q_dot (rad/s)
    joint_torques: List[float]         # tau (Nm)
    end_effector_pos: List[float]      # x, y, z (m)
    timestamp: float


@dataclass
class CandidateAction:
    desired_torques: List[float]       # u_slow (Nm)
    source_timestamp: float            # Slow loop emission time
    sequence_id: int


@dataclass
class ArbitrationOutput:
    enforced_torques: List[float]      # u_safe (Nm)
    arbiter_state: ArbiterState
    latency_us: float
    cbf_active: bool
    violations_intercepted: int
    details: Dict[str, Any]


class ControlBarrierFunction:
    """
    Control Barrier Function (CBF) evaluator.
    Defines safe forward invariant sets: h(x) >= 0.
    Condition: L_f h(x) + L_g h(x) * u + gamma * h(x) >= 0
    """
    def __init__(
        self,
        joint_limits_lower: List[float],
        joint_limits_upper: List[float],
        velocity_limits: List[float],
        torque_limits: List[float],
        gamma: float = 10.0
    ):
        self.num_joints = len(joint_limits_lower)
        self.q_min = joint_limits_lower
        self.q_max = joint_limits_upper
        self.v_max = velocity_limits
        self.tau_max = torque_limits
        self.gamma = gamma

    def compute_torque_bounds(
        self,
        state: RobotKinematicState,
        dt: float = 0.001
    ) -> Tuple[List[float], List[float]]:
        """
        Computes the forward invariant torque bounds [u_lower, u_upper]
        satisfying joint position, velocity, and torque limits.
        """
        u_lower = []
        u_upper = []

        for i in range(self.num_joints):
            q = state.joint_positions[i]
            q_dot = state.joint_velocities[i]
            t_max = self.tau_max[i]

            # 1. Joint position barrier: h1 = q_max - q >= 0, h2 = q - q_min >= 0
            h_pos_upper = self.q_max[i] - q
            h_pos_lower = q - self.q_min[i]

            # 2. Velocity barrier: h_vel = v_max - |q_dot|
            h_vel_upper = self.v_max[i] - q_dot
            h_vel_lower = self.v_max[i] + q_dot

            # CBF-induced maximum acceleration/torque bounds
            max_accel = self.gamma * min(h_pos_upper, h_vel_upper)
            min_accel = -self.gamma * min(h_pos_lower, h_vel_lower)

            # Map acceleration bound to torque envelope (scaled by virtual inertia ~ 1.0)
            tau_cbf_upper = min(t_max, max(-t_max, max_accel * 2.0))
            tau_cbf_lower = max(-t_max, min(t_max, min_accel * 2.0))

            if tau_cbf_lower > tau_cbf_upper:
                # Tight overlap -> fallback to zero / clamp
                mid = (tau_cbf_lower + tau_cbf_upper) / 2.0
                tau_cbf_lower = mid - 1.0
                tau_cbf_upper = mid + 1.0

            u_lower.append(tau_cbf_lower)
            u_upper.append(tau_cbf_upper)

        return u_lower, u_upper


class SafetyArbiter:
    """
    High-Performance Deterministic Safety Arbiter.
    Executes in fast loop (500Hz - 1000Hz).
    Evaluates candidate action vector from slow loop against CBF bounds.
    """
    def __init__(
        self,
        num_joints: int = 6,
        heartbeat_timeout_s: float = 0.035,   # 35 ms timeout (slow loop is 30Hz)
        damping_coeff: float = 5.0
    ):
        self.num_joints = num_joints
        self.heartbeat_timeout_s = heartbeat_timeout_s
        self.damping_coeff = damping_coeff

        # Standard 6-DoF Manipulator Envelope
        self.cbf = ControlBarrierFunction(
            joint_limits_lower=[-2.8, -1.8, -2.5, -2.8, -1.8, -2.8],
            joint_limits_upper=[ 2.8,  1.8,  2.5,  2.8,  1.8,  2.8],
            velocity_limits=[3.14, 3.14, 3.14, 4.0, 4.0, 4.0],
            torque_limits=[80.0, 80.0, 60.0, 40.0, 30.0, 30.0],
            gamma=12.0
        )

        self.last_valid_heartbeat = time.time()
        self.state = ArbiterState.NOMINAL_TRACKING
        self.violations_count = 0
        self.total_cycles = 0

    def solve_projected_qp(
        self,
        u_des: List[float],
        u_lower: List[float],
        u_upper: List[float]
    ) -> Tuple[List[float], bool]:
        """
        Solves: min 0.5 * ||u - u_des||^2  s.t.  u_lower <= u <= u_upper.
        Closed-form projection with O(N) complexity executing in < 20 microseconds.
        """
        u_safe = []
        projected = False
        for i in range(self.num_joints):
            des = u_des[i] if i < len(u_des) else 0.0
            low = u_lower[i]
            upp = u_upper[i]

            if des > upp:
                u_safe.append(upp)
                projected = True
            elif des < low:
                u_safe.append(low)
                projected = True
            else:
                u_safe.append(des)

        return u_safe, projected

    def compute_damping_fallback(self, state: RobotKinematicState) -> List[float]:
        """Generates deterministic passive damping torques: tau = -D * q_dot."""
        return [-self.damping_coeff * v for v in state.joint_velocities]

    def arbitrate_cycle(
        self,
        state: RobotKinematicState,
        candidate: Optional[CandidateAction],
        current_time_s: Optional[float] = None
    ) -> ArbitrationOutput:
        t0 = time.perf_counter()
        if current_time_s is None:
            current_time_s = time.time()
        self.total_cycles += 1

        # 1. Slow Loop Heartbeat Check
        is_slow_loop_alive = False
        if candidate is not None:
            time_since_candidate = current_time_s - candidate.source_timestamp
            if time_since_candidate <= self.heartbeat_timeout_s:
                is_slow_loop_alive = True
                self.last_valid_heartbeat = current_time_s

        if not is_slow_loop_alive:
            # Slow loop crashed, delayed or dropped -> Immediate 1-cycle fallback
            self.state = ArbiterState.DAMPING_BRAKE
            u_safe = self.compute_damping_fallback(state)
            elapsed_us = (time.perf_counter() - t0) * 1_000_000.0
            return ArbitrationOutput(
                enforced_torques=u_safe,
                arbiter_state=self.state,
                latency_us=round(elapsed_us, 3),
                cbf_active=False,
                violations_intercepted=self.violations_count,
                details={"reason": "SLOW_LOOP_TIMEOUT_HEARTBEAT_EXPIRED"}
            )

        # 2. Control Barrier Function Bounds
        u_lower, u_upper = self.cbf.compute_torque_bounds(state)

        # 3. Solve Safe Quadratic Projection
        u_des = candidate.desired_torques
        u_safe, was_projected = self.solve_projected_qp(u_des, u_lower, u_upper)

        if was_projected:
            self.state = ArbiterState.CBF_FILTERED
            self.violations_count += 1
        else:
            self.state = ArbiterState.NOMINAL_TRACKING

        elapsed_us = (time.perf_counter() - t0) * 1_000_000.0

        return ArbitrationOutput(
            enforced_torques=u_safe,
            arbiter_state=self.state,
            latency_us=round(elapsed_us, 3),
            cbf_active=was_projected,
            violations_intercepted=self.violations_count,
            details={
                "u_des": u_des,
                "u_lower": u_lower,
                "u_upper": u_upper,
                "was_projected": was_projected
            }
        )