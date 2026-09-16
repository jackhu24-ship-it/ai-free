from typing import Tuple, List, Optional, Set, Dict
import time
import hashlib
from dataclasses import dataclass, field
from enum import Enum

class BlockStatus(Enum):
    PROPOSED = "PROPOSED"
    PREPARED = "PREPARED"
    COMMITTED = "COMMITTED"
    FINALIZED = "FINALIZED"
    REJECTED = "REJECTED"

@dataclass
class Vote:
    voter_id: str
    block_hash: str
    round_num: int
    stage: str
    signature: str
    timestamp_ms: float = field(default_factory=lambda: time.time() * 1000.0)

@dataclass
class Block:
    block_height: int
    round_num: int
    proposer_id: str
    transactions: List[str]
    previous_hash: str
    block_hash: str = ""
    status: BlockStatus = BlockStatus.PROPOSED
    created_at_ms: float = field(default_factory=lambda: time.time() * 1000.0)
    finalized_at_ms: Optional[float] = None

    def calculate_hash(self) -> str:
        payload = f"{self.block_height}:{self.round_num}:{self.proposer_id}:{self.previous_hash}:{','.join(self.transactions)}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

class AIBFTEngine:
    def __init__(self, node_ids: List[str], max_latency_ms: float = 250.0, max_finality_s: float = 1.5):
        self.node_ids: List[str] = node_ids
        self.total_nodes: int = len(node_ids)
        self.max_faulty_nodes: int = (self.total_nodes - 1) // 3
        self.quorum_size: int = 2 * self.max_faulty_nodes + 1
        
        self.max_latency_ms = max_latency_ms
        self.max_finality_s = max_finality_s

        self.blocks: Dict[str, Block] = {}
        self.prepare_votes: Dict[str, Dict[str, Vote]] = {}
        self.commit_votes: Dict[str, Dict[str, Vote]] = {}
        self.malicious_nodes: Set[str] = set()

    def mark_node_malicious(self, node_id: str) -> None:
        if node_id in self.node_ids:
            self.malicious_nodes.add(node_id)

    def propose_block(self, proposer_id: str, block_height: int, round_num: int, txs: List[str], prev_hash: str) -> Block:
        block = Block(
            block_height=block_height,
            round_num=round_num,
            proposer_id=proposer_id,
            transactions=txs,
            previous_hash=prev_hash
        )
        block.block_hash = block.calculate_hash()
        self.blocks[block.block_hash] = block
        self.prepare_votes[block.block_hash] = {}
        self.commit_votes[block.block_hash] = {}
        return block

    def submit_vote(self, voter_id: str, block_hash: str, round_num: int, stage: str, is_malicious_vote: bool = False) -> bool:
        if voter_id not in self.node_ids or block_hash not in self.blocks:
            return False
        if voter_id in self.malicious_nodes or is_malicious_vote:
            return False

        sig = hashlib.sha256(f"{voter_id}:{block_hash}:{stage}".encode("utf-8")).hexdigest()
        vote = Vote(voter_id=voter_id, block_hash=block_hash, round_num=round_num, stage=stage, signature=sig)

        if stage == "PREPARE":
            self.prepare_votes[block_hash][voter_id] = vote
            if len(self.prepare_votes[block_hash]) >= self.quorum_size:
                self.blocks[block_hash].status = BlockStatus.PREPARED
                return True
        elif stage == "COMMITTED" or stage == "COMMIT":
            self.commit_votes[block_hash][voter_id] = vote
            if len(self.commit_votes[block_hash]) >= self.quorum_size:
                block = self.blocks[block_hash]
                block.status = BlockStatus.FINALIZED
                block.finalized_at_ms = time.time() * 1000.0
                return True

        return False

    def execute_pipelined_consensus(self, proposer_id: str, block_height: int, round_num: int, txs: List[str], prev_hash: str) -> Tuple[Block, float]:
        start_time = time.perf_counter()
        block = self.propose_block(proposer_id, block_height, round_num, txs, prev_hash)

        for node in self.node_ids:
            if node != proposer_id:
                self.submit_vote(node, block.block_hash, round_num, "PREPARE")

        if block.status == BlockStatus.PREPARED:
            for node in self.node_ids:
                self.submit_vote(node, block.block_hash, round_num, "COMMIT")

        finality_duration_s = (time.perf_counter() - start_time)
        return block, finality_duration_s
