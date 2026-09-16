import time
from typing import Dict

class NEAEngine:
    def __init__(self, max_capacity: int = 100000):
        self.max_capacity = max_capacity
        self.current_active_nodes = max_capacity
        self.energy_state = "HIGH_PERFORMANCE" # States: ECO_MODE, NORMAL, HIGH_PERFORMANCE
        self.power_consumption_kw = 5000.0 # Base consumption in KW

    def analyze_and_adjust(self, current_traffic_tps: int) -> Dict[str, any]:
        """
        Dynamically adjust active nodes and energy state based on traffic.
        Must execute under 0.05ms to avoid blocking network layer.
        """
        start_time = time.perf_counter()
        
        # Traffic analysis logic
        if current_traffic_tps < 5000:
            # Low traffic -> Eco mode (Deep Sleep)
            target_nodes = int(self.max_capacity * 0.10) # Keep 10% alive
            self.energy_state = "ECO_MODE"
            self.power_consumption_kw = 500.0
            
        elif current_traffic_tps < 50000:
            # Medium traffic -> Normal mode
            target_nodes = int(self.max_capacity * 0.50) # Keep 50% alive
            self.energy_state = "NORMAL"
            self.power_consumption_kw = 2500.0
            
        else:
            # High traffic -> High performance (Instant wake)
            target_nodes = self.max_capacity
            self.energy_state = "HIGH_PERFORMANCE"
            self.power_consumption_kw = 5000.0
            
        # Simulate instant wake-up or graceful shutdown overhead
        self.current_active_nodes = target_nodes
        
        adjustment_time_ms = (time.perf_counter() - start_time) * 1000
        
        return {
            "state": self.energy_state,
            "active_nodes": self.current_active_nodes,
            "power_kw": self.power_consumption_kw,
            "adjustment_time_ms": adjustment_time_ms
        }
