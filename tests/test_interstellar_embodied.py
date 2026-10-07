import pytest

from src.ai.interstellar_embodied import (
    ClusterThermalState,
    ComputeNodeTelemetry,
    NeuralEnergyArbiter,
    SchedulingDecision,
)


def test_thermal_state_enum():
    assert ClusterThermalState.COLD_IDLE.value == "COLD_IDLE"
    assert ClusterThermalState.WARM_ECO.value == "WARM_ECO"
    assert ClusterThermalState.HOT_BURST.value == "HOT_BURST"


def test_telemetry_and_decision_dataclasses():
    node = ComputeNodeTelemetry(
        node_id="node_01",
        active_gpus=8,
        load_ratio=0.5,
        power_draw_kw=12.0,
        green_energy_ratio=0.8,
        thermal_state=ClusterThermalState.HOT_BURST,
    )
    assert node.node_id == "node_01"
    assert node.thermal_state == ClusterThermalState.HOT_BURST

    decision = SchedulingDecision(
        target_cluster="c1",
        allocated_gpus=16,
        predicted_energy_kwh_per_knode=0.35,
        scaled_nodes=2,
        decision_latency_ms=0.015,
        action_type="SCALE_UP",
    )
    assert decision.action_type == "SCALE_UP"


def test_arbiter_initialization():
    arbiter = NeuralEnergyArbiter(energy_threshold_kwh=0.50, max_scale_latency_s=4.0)
    assert arbiter.energy_threshold_kwh == 0.50
    assert arbiter.max_scale_latency_s == 4.0
    assert arbiter.clusters == {}


def test_heuristic_zero_gpus():
    arbiter = NeuralEnergyArbiter()
    # active_gpus = 0 to trigger max(0, 1.0) denominator branch
    node = ComputeNodeTelemetry(
        node_id="idle_node",
        active_gpus=0,
        load_ratio=0.0,
        power_draw_kw=1.0,
        green_energy_ratio=0.0,
    )
    val = arbiter._neural_energy_heuristic(node)
    assert isinstance(val, float)
    assert val > 0


def test_evaluate_and_schedule_missing_or_empty_cluster():
    arbiter = NeuralEnergyArbiter()
    with pytest.raises(ValueError, match="not found or empty"):
        arbiter.evaluate_and_schedule("non_existent", 1000)

    arbiter.register_cluster("empty_c", [])
    with pytest.raises(ValueError, match="not found or empty"):
        arbiter.evaluate_and_schedule("empty_c", 1000)


def test_evaluate_and_schedule_scale_up():
    arbiter = NeuralEnergyArbiter(energy_threshold_kwh=0.55)
    nodes = [
        ComputeNodeTelemetry(
            "n1", active_gpus=8, load_ratio=0.85, power_draw_kw=15.0, green_energy_ratio=0.9
        ),
        ComputeNodeTelemetry(
            "n2", active_gpus=8, load_ratio=0.80, power_draw_kw=15.0, green_energy_ratio=0.9
        ),
    ]
    arbiter.register_cluster("cluster_alpha", nodes)

    decision = arbiter.evaluate_and_schedule("cluster_alpha", incoming_tx_burst=6000)
    assert decision.action_type == "SCALE_UP"
    assert decision.scaled_nodes > 0
    assert decision.allocated_gpus > 16
    assert decision.predicted_energy_kwh_per_knode <= arbiter.energy_threshold_kwh


def test_evaluate_and_schedule_scale_down():
    arbiter = NeuralEnergyArbiter(energy_threshold_kwh=0.55)
    nodes = [
        ComputeNodeTelemetry(
            "n1", active_gpus=8, load_ratio=0.10, power_draw_kw=2.0, green_energy_ratio=1.0
        ),
        ComputeNodeTelemetry(
            "n2", active_gpus=8, load_ratio=0.15, power_draw_kw=2.0, green_energy_ratio=1.0
        ),
        ComputeNodeTelemetry(
            "n3", active_gpus=8, load_ratio=0.10, power_draw_kw=2.0, green_energy_ratio=1.0
        ),
        ComputeNodeTelemetry(
            "n4", active_gpus=8, load_ratio=0.10, power_draw_kw=2.0, green_energy_ratio=1.0
        ),
    ]
    arbiter.register_cluster("cluster_beta", nodes)

    decision = arbiter.evaluate_and_schedule("cluster_beta", incoming_tx_burst=200)
    assert decision.action_type == "SCALE_DOWN"
    assert decision.scaled_nodes < 0
    assert decision.allocated_gpus >= 8


def test_evaluate_and_schedule_optimize_route():
    arbiter = NeuralEnergyArbiter()
    nodes = [
        ComputeNodeTelemetry(
            "n1", active_gpus=8, load_ratio=0.50, power_draw_kw=8.0, green_energy_ratio=0.5
        ),
    ]
    arbiter.register_cluster("cluster_gamma", nodes)

    decision = arbiter.evaluate_and_schedule("cluster_gamma", incoming_tx_burst=2000)
    assert decision.action_type == "OPTIMIZE_ROUTE"
    assert decision.scaled_nodes == 0
    assert decision.allocated_gpus == 8
    assert decision.decision_latency_ms >= 0
