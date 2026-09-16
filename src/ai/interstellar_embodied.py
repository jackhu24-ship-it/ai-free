import time
import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum

class ClusterThermalState(Enum):
    COLD_IDLE = "COLD_IDLE"
    WARM_ECO = "WARM_ECO"
    HOT_BURST = "HOT_BURST"

@dataclass
class ComputeNodeTelemetry:
    node_id: str
    active_gpus: int
    load_ratio: float  # 0.0 to 1.0
    power_draw_kw: float
    green_energy_ratio: float  # 0.0 to 1.0 (Solar / Fusion / Stellar Wind)
    thermal_state: ClusterThermalState = ClusterThermalState.WARM_ECO

@dataclass
class SchedulingDecision:
    target_cluster: str
    allocated_gpus: int
    predicted_energy_kwh_per_knode: float
    scaled_nodes: int
    decision_latency_ms: float
    action_type: str  # SCALE_UP, SCALE_DOWN, OPTIMIZE_ROUTE

class NeuralEnergyArbiter:
    def __init__(self, energy_threshold_kwh: float = 0.55, max_scale_latency_s: float = 3.5):
        self.energy_threshold_kwh = energy_threshold_kwh
        self.max_scale_latency_s = max_scale_latency_s
        self.clusters: Dict[str, List[ComputeNodeTelemetry]] = {}

    def register_cluster(self, cluster_id: str, nodes: List[ComputeNodeTelemetry]) -> None:
        self.clusters[cluster_id] = nodes

    def _neural_energy_heuristic(self, node: ComputeNodeTelemetry) -> float:
        green_discount = 1.0 - (0.6 * node.green_energy_ratio)
        load_penalty = 0.3 + 0.7 * math.pow(node.load_ratio, 1.8)
        kwh_per_knode = (node.power_draw_kw * green_discount * load_penalty) / max(node.active_gpus * 2.5, 1.0)
        return round(kwh_per_knode, 4)

    def evaluate_and_schedule(self, cluster_id: str, incoming_tx_burst: int) -> SchedulingDecision:
        start_time = time.perf_counter()

        if cluster_id not in self.clusters or not self.clusters[cluster_id]:
            raise ValueError(f"Cluster '{cluster_id}' not found or empty.")

        nodes = self.clusters[cluster_id]
        total_gpus = sum(n.active_gpus for n in nodes)
        avg_load = sum(n.load_ratio for n in nodes) / len(nodes)
        
        cluster_energy_ratings = [self._neural_energy_heuristic(n) for n in nodes]
        avg_energy = sum(cluster_energy_ratings) / len(cluster_energy_ratings)

        action = "OPTIMIZE_ROUTE"
        scaled_nodes = 0
        allocated_gpus = total_gpus

        if incoming_tx_burst > 5000 and avg_load > 0.75:
            action = "SCALE_UP"
            scaled_nodes = max(1, int(len(nodes) * 0.5))
            allocated_gpus = total_gpus + (scaled_nodes * 8)
            avg_energy = min(avg_energy * 0.88, self.energy_threshold_kwh)
        elif incoming_tx_burst < 500 and avg_load < 0.25:
            action = "SCALE_DOWN"
            scaled_nodes = -max(1, int(len(nodes) * 0.3))
            allocated_gpus = max(8, total_gpus + (scaled_nodes * 8))

        decision_latency_ms = (time.perf_counter() - start_time) * 1000.0

        return SchedulingDecision(
            target_cluster=cluster_id,
            allocated_gpus=allocated_gpus,
            predicted_energy_kwh_per_knode=avg_energy,
            scaled_nodes=scaled_nodes,
            decision_latency_ms=decision_latency_ms,
            action_type=action
        )
