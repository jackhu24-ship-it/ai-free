import time
import random
from typing import List, Set
import math

class Node:
    def __init__(self, node_id: str, is_malicious: bool = False):
        self.node_id = node_id
        self.is_malicious = is_malicious

class AIBFTEngine:
    def __init__(self, total_nodes: int):
        self.nodes: List[Node] = []
        self.total_nodes = total_nodes
        self.malicious_threshold = int(total_nodes * 0.33)
        
    def initialize_network(self, malicious_count: int):
        if malicious_count > self.malicious_threshold:
            raise ValueError(f"Too many malicious nodes! Max allowed is {self.malicious_threshold}")
            
        for i in range(malicious_count):
            self.nodes.append(Node(f"Node_{i}", is_malicious=True))
        for i in range(malicious_count, self.total_nodes):
            self.nodes.append(Node(f"Node_{i}", is_malicious=False))
            
    def propose_and_reach_consensus(self, block_data: str) -> dict:
        start_time = time.perf_counter()
        
        # 1. Proposal Phase
        time.sleep(0.15) 
        
        # 2. Pre-Vote Phase
        valid_votes = sum(1 for node in self.nodes if not node.is_malicious)
                
        time.sleep(0.08) 
        
        # 3. Commit Phase
        # Required is strictly > 2/3 of total nodes
        required_votes = math.floor(self.total_nodes * 2 / 3) + 1
        consensus_reached = valid_votes >= required_votes
        
        time.sleep(0.05)
        
        finality_time_ms = (time.perf_counter() - start_time) * 1000
        
        return {
            "consensus_reached": consensus_reached,
            "valid_votes": valid_votes,
            "required_votes": required_votes,
            "finality_time_ms": finality_time_ms
        }
