# -*- coding: utf-8 -*-
"""
=============================================================================
Embodied AI Neuro-Symbolic Dual-Loop KPI Verification Test Suite
=============================================================================
Validates all 5 Core KPIs & Safety Gates:
  1. Fast Loop Jitter <= 50 microseconds
  2. Safety Invariant Violation STRICTLY ZERO (Zero-Violation)
  3. CBF/QP Arbitration Latency <= 200 microseconds (WCET)
  4. Boundary Takeover & Safe Fallback <= 1 ms (Single-cycle reaction)
  5. Domain Randomization (+/- 30% load perturbation) Stability
=============================================================================
"""

import time
import pytest
from embodied_dual_loop.cbf_safety_arbiter import (
    SafetyArbiter,
    ArbiterState,
    RobotKinematicState,
    CandidateAction
)
from embodied_dual_loop.dual_loop_ipc_ringbuffer import DualLoopIPCRingBuffer
from embodied_dual_loop.mujoco_dynamic_barrier_model import MultiDoFRobotDynamicsModel


def test_kpi1_fast_loop_jitter():
    """KPI 1: 驗證快環時鐘與非阻塞讀取抖動 (Jitter <= 50us)"""
    ipc = DualLoopIPCRingBuffer(capacity=16)
    ipc.write_candidate([10.0, -10.0, 5.0, 0.0, 0.0, 0.0])

    delays = []
    for _ in range(200):
        t0 = time.perf_counter()
        _ = ipc.read_latest()
        elapsed_us = (time.perf_counter() - t0) * 1_000_000.0
        delays.append(elapsed_us)

    max_jitter_us = max(delays)
    # IPC 非阻塞記憶體讀取耗時極短，遠低於 50us SLA
    assert max_jitter_us <= 50.0, f"Max jitter {max_jitter_us}us exceeded 50us threshold"


def test_kpi2_safety_invariant_violations_strictly_zero():
    """KPI 2: 驗證物理約束違背率嚴格為 0 (注入劇毒動作指令，100% 攔截)"""
    arbiter = SafetyArbiter(num_joints=6)
    
    # 建立基準機器人狀態
    state = RobotKinematicState(
        joint_positions=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        joint_velocities=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        joint_torques=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        end_effector_pos=[0.55, 0.0, 0.35],
        timestamp=time.time()
    )

    # 注入超出物理極限之劇毒力矩 (力矩 250 Nm，極限為 80 Nm)
    toxic_candidate = CandidateAction(
        desired_torques=[250.0, -250.0, 180.0, -120.0, 90.0, -90.0],
        source_timestamp=time.time(),
        sequence_id=1
    )

    violations_detected = 0
    for _ in range(50):
        out = arbiter.arbitrate_cycle(state, toxic_candidate)
        # 檢驗輸出絕對不可超過 tau_max (80, 80, 60, 40, 30, 30)
        limits = [80.0, 80.0, 60.0, 40.0, 30.0, 30.0]
        for i in range(6):
            assert abs(out.enforced_torques[i]) <= limits[i] + 1e-4, f"Torque limit violated on joint {i}"
        
        assert out.cbf_active is True
        assert out.arbiter_state == ArbiterState.CBF_FILTERED
        violations_detected += 1

    assert violations_detected == 50
    assert arbiter.violations_count == 50


def test_kpi3_cbf_qp_arbitration_latency():
    """KPI 3: 驗證 CBF 屏障過濾與 QP 求解耗時 (WCET <= 200us)"""
    arbiter = SafetyArbiter(num_joints=6)
    state = RobotKinematicState(
        joint_positions=[0.5, -0.3, 0.2, 0.1, -0.1, 0.0],
        joint_velocities=[0.2, -0.1, 0.05, 0.0, 0.0, 0.0],
        joint_torques=[10.0, 5.0, 2.0, 0.0, 0.0, 0.0],
        end_effector_pos=[0.5, 0.1, 0.35],
        timestamp=time.time()
    )
    candidate = CandidateAction(
        desired_torques=[45.0, -35.0, 20.0, 10.0, -5.0, 2.0],
        source_timestamp=time.time(),
        sequence_id=10
    )

    latencies_us = []
    for _ in range(500):
        out = arbiter.arbitrate_cycle(state, candidate)
        latencies_us.append(out.latency_us)

    worst_case_us = max(latencies_us)
    # 閉式解二次規劃投影極為敏捷，實測遠低於 200us
    assert worst_case_us <= 200.0, f"WCET {worst_case_us}us exceeded 200us limit"


def test_kpi4_slow_loop_crash_single_cycle_fallback():
    """KPI 4: 驗證異常工況 (慢環超時崩潰) 於單週期 (<= 1ms) 切換至 Safe Fallback"""
    arbiter = SafetyArbiter(num_joints=6, heartbeat_timeout_s=0.035)
    state = RobotKinematicState(
        joint_positions=[0.0] * 6,
        joint_velocities=[1.5, -1.0, 0.5, 0.0, 0.0, 0.0],
        joint_torques=[0.0] * 6,
        end_effector_pos=[0.55, 0.0, 0.35],
        timestamp=100.0
    )

    # 慢環在 50ms 前發送最後一次訊號 (逾期 50ms > 35ms 心跳門檻)
    stale_candidate = CandidateAction(
        desired_torques=[20.0] * 6,
        source_timestamp=100.0 - 0.050,
        sequence_id=99
    )

    t0 = time.perf_counter()
    out = arbiter.arbitrate_cycle(state, stale_candidate, current_time_s=100.0)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    # 驗證單週期內接管 (<= 1.0 ms)
    assert elapsed_ms <= 1.0
    assert out.arbiter_state == ArbiterState.DAMPING_BRAKE
    # 驗證阻尼制動產生反向力矩 (-D * q_dot)
    assert out.enforced_torques[0] < 0.0   # q_dot > 0 -> tau < 0
    assert out.enforced_torques[1] > 0.0   # q_dot < 0 -> tau > 0


def test_kpi5_domain_randomization_stability():
    """KPI 5: 驗證動力學域隨機化 (+/- 30% 負載突變) 下系統運行不失穩"""
    model = MultiDoFRobotDynamicsModel(num_joints=6)
    arbiter = SafetyArbiter(num_joints=6)

    # 施加極端 +30% 負載與 -25% 阻尼擾動
    model.apply_domain_randomization(mass_pct=0.30, damping_pct=-0.25)

    sim_state = model.step_simulation([0.0] * 6)
    
    for step in range(100):
        # 慢環給予規律運動指令
        target_torque = [20.0 * ((-1) ** (step // 20))] * 6
        candidate = CandidateAction(
            desired_torques=target_torque,
            source_timestamp=sim_state.timestamp,
            sequence_id=step
        )
        
        arb_out = arbiter.arbitrate_cycle(sim_state, candidate, current_time_s=sim_state.timestamp)
        sim_state = model.step_simulation(arb_out.enforced_torques)

        # 斷言速度未發散，系統保持在受控動態邊界內 (q_dot <= 4.0 rad/s)
        for v in sim_state.joint_velocities:
            assert abs(v) <= 4.0