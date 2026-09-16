from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import heapq

@dataclass
class RoutePath:
    path: List[str]
    estimated_latency_ms: float

class HDRPEngine:
    def __init__(self, latency_target_ms: float = 0.035):
        self.latency_target_ms = latency_target_ms
        self.nodes: Dict[str, Tuple[float, ...]] = {}
        # adjacency list: node -> dict of neighbor -> (latency_ms, loss_rate, qber, is_active)
        self.graph: Dict[str, Dict[str, dict]] = {}

    def register_node(self, node_id: str, coords: Tuple[float, ...]):
        self.nodes[node_id] = coords
        if node_id not in self.graph:
            self.graph[node_id] = {}

    def set_link(self, node_a: str, node_b: str, latency_ms: float, loss_rate: float, qber: float):
        if node_a not in self.graph:
            self.graph[node_a] = {}
        if node_b not in self.graph:
            self.graph[node_b] = {}
        
        link_data = {
            "latency_ms": latency_ms,
            "loss_rate": loss_rate,
            "qber": qber,
            "is_active": True
        }
        self.graph[node_a][node_b] = link_data.copy()
        self.graph[node_b][node_a] = link_data.copy()

    def set_link_status(self, node_a: str, node_b: str, is_active: bool):
        if node_a in self.graph and node_b in self.graph[node_a]:
            self.graph[node_a][node_b]["is_active"] = is_active
        if node_b in self.graph and node_a in self.graph[node_b]:
            self.graph[node_b][node_a]["is_active"] = is_active

    def _calculate_cost(self, link_data: dict) -> float:
        """Calculate effective cost taking QBER and loss rate into account"""
        base_latency = link_data["latency_ms"]
        # Penalize heavily if QBER is very high (e.g., > 0.5)
        qber_penalty = 1.0 + (link_data["qber"] * 10.0) 
        if link_data["qber"] > 0.1:
            qber_penalty += link_data["qber"] * 100.0 # Exponential surge penalty
        return base_latency * qber_penalty

    def find_optimal_route(self, source: str, target: str) -> Optional[RoutePath]:
        if source not in self.graph or target not in self.graph:
            return None

        # Dijkstra's algorithm for lowest effective cost
        queue = [(0.0, source, [source], 0.0)] # (cost, current_node, path, actual_latency)
        visited = set()

        while queue:
            current_cost, current_node, path, actual_latency = heapq.heappop(queue)

            if current_node == target:
                return RoutePath(path=path, estimated_latency_ms=actual_latency)

            if current_node in visited:
                continue
            visited.add(current_node)

            for neighbor, link_data in self.graph[current_node].items():
                if not link_data["is_active"]:
                    continue
                
                step_cost = self._calculate_cost(link_data)
                heapq.heappush(queue, (
                    current_cost + step_cost,
                    neighbor,
                    path + [neighbor],
                    actual_latency + link_data["latency_ms"]
                ))

        return None
