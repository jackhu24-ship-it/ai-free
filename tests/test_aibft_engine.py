from unittest.mock import patch

import pytest

from src.consensus.aibft_engine import AIBFTEngine, Node
from src.consensus.aibft_engine_v2 import (
    AIBFTEngine as AIBFTEngineV2,
)
from src.consensus.aibft_engine_v2 import (
    Block,
    BlockStatus,
    Vote,
)


def test_node_init():
    n1 = Node("n1")
    assert n1.node_id == "n1"
    assert n1.is_malicious is False

    n2 = Node("n2", is_malicious=True)
    assert n2.is_malicious is True


def test_aibft_engine_v1_init_and_threshold():
    engine = AIBFTEngine(total_nodes=10)
    assert engine.total_nodes == 10
    assert engine.malicious_threshold == 3  # int(10 * 0.33)


def test_aibft_engine_v1_initialize_network():
    engine = AIBFTEngine(total_nodes=10)
    engine.initialize_network(malicious_count=2)
    assert len(engine.nodes) == 10
    malicious_nodes = [n for n in engine.nodes if n.is_malicious]
    assert len(malicious_nodes) == 2

    # Exceed threshold
    engine_bad = AIBFTEngine(total_nodes=10)
    with pytest.raises(ValueError, match="Too many malicious nodes"):
        engine_bad.initialize_network(malicious_count=4)


@patch("time.sleep", return_value=None)
def test_aibft_engine_v1_consensus(mock_sleep):
    engine = AIBFTEngine(total_nodes=10)
    engine.initialize_network(malicious_count=2)

    res = engine.propose_and_reach_consensus("block_data_001")
    assert res["consensus_reached"] is True
    assert res["valid_votes"] == 8
    assert res["required_votes"] == 7  # floor(10*2/3) + 1 = 6 + 1 = 7
    assert res["finality_time_ms"] >= 0

    # Simulate valid votes < required votes
    for node in engine.nodes:
        node.is_malicious = True
    res_fail = engine.propose_and_reach_consensus("block_data_fail")
    assert res_fail["consensus_reached"] is False
    assert res_fail["valid_votes"] == 0


def test_aibft_v2_enums_and_dataclasses():
    assert BlockStatus.PROPOSED.value == "PROPOSED"
    assert BlockStatus.FINALIZED.value == "FINALIZED"

    vote = Vote(
        voter_id="v1",
        block_hash="hash1",
        round_num=1,
        stage="PREPARE",
        signature="sig1",
    )
    assert vote.voter_id == "v1"

    block = Block(
        block_height=1,
        round_num=1,
        proposer_id="p1",
        transactions=["tx1", "tx2"],
        previous_hash="0x0",
    )
    h = block.calculate_hash()
    assert isinstance(h, str)
    assert len(h) == 64


def test_aibft_v2_mark_malicious():
    nodes = ["n1", "n2", "n3", "n4"]
    engine = AIBFTEngineV2(node_ids=nodes)
    engine.mark_node_malicious("n1")
    assert "n1" in engine.malicious_nodes
    # Unknown node
    engine.mark_node_malicious("n999")
    assert "n999" not in engine.malicious_nodes


def test_aibft_v2_submit_vote_branches():
    nodes = ["n1", "n2", "n3", "n4"]
    engine = AIBFTEngineV2(node_ids=nodes)
    block = engine.propose_block("n1", 1, 1, ["tx1"], "prev")

    # Invalid voter
    assert not engine.submit_vote("unknown", block.block_hash, 1, "PREPARE")
    # Invalid block hash
    assert not engine.submit_vote("n2", "unknown_hash", 1, "PREPARE")
    # Malicious vote flag
    assert not engine.submit_vote("n2", block.block_hash, 1, "PREPARE", is_malicious_vote=True)
    # Marked malicious node
    engine.mark_node_malicious("n4")
    assert not engine.submit_vote("n4", block.block_hash, 1, "PREPARE")

    # PREPARE stage votes until quorum
    # total=4, max_faulty = (4-1)//3 = 1, quorum = 2*1 + 1 = 3
    assert not engine.submit_vote("n1", block.block_hash, 1, "PREPARE")
    assert not engine.submit_vote("n2", block.block_hash, 1, "PREPARE")
    assert engine.submit_vote("n3", block.block_hash, 1, "PREPARE")
    assert block.status == BlockStatus.PREPARED

    # COMMIT stage votes until quorum
    assert not engine.submit_vote("n1", block.block_hash, 1, "COMMIT")
    assert not engine.submit_vote("n2", block.block_hash, 1, "COMMIT")
    assert engine.submit_vote("n3", block.block_hash, 1, "COMMIT")
    assert block.status == BlockStatus.FINALIZED
    assert block.finalized_at_ms is not None

    # Alternative COMMITTED stage name
    block2 = engine.propose_block("n1", 2, 1, ["tx2"], block.block_hash)
    engine.submit_vote("n1", block2.block_hash, 1, "COMMITTED")
    engine.submit_vote("n2", block2.block_hash, 1, "COMMITTED")
    assert engine.submit_vote("n3", block2.block_hash, 1, "COMMITTED")

    # Unrecognized stage
    assert not engine.submit_vote("n1", block2.block_hash, 1, "UNKNOWN_STAGE")


def test_aibft_v2_execute_pipelined_consensus():
    nodes = ["n1", "n2", "n3", "n4"]
    engine = AIBFTEngineV2(node_ids=nodes)
    block, duration = engine.execute_pipelined_consensus("n1", 1, 1, ["txA", "txB"], "0x00")
    assert block.status == BlockStatus.FINALIZED
    assert duration >= 0

    # Pipeline when quorum cannot be reached (status remains PROPOSED)
    engine_failing = AIBFTEngineV2(node_ids=nodes)
    for n in ["n2", "n3", "n4"]:
        engine_failing.mark_node_malicious(n)
    block_fail, _ = engine_failing.execute_pipelined_consensus("n1", 2, 1, ["txC"], "0x00")
    assert block_fail.status == BlockStatus.PROPOSED
