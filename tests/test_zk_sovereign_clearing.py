import runpy
import time
from zk_sovereign_clearing import ZKSovereignClearing, ClearingTransaction


def test_clearing_transaction_creation():
    tx = ClearingTransaction(
        tx_id="TX-777",
        sender_galaxy="MilkyWay-Sol",
        receiver_galaxy="Andromeda-Core",
        amount=100000.0,
        asset_type="ENERGY_CREDIT",
        timestamp_ms=time.time() * 1000.0,
    )
    assert tx.tx_id == "TX-777"
    assert tx.sender_galaxy == "MilkyWay-Sol"
    assert tx.receiver_galaxy == "Andromeda-Core"
    assert tx.amount == 100000.0
    assert tx.asset_type == "ENERGY_CREDIT"
    assert tx.timestamp_ms > 0


def test_zk_sovereign_clearing_init():
    engine = ZKSovereignClearing()
    assert "GDPR_ARTICLE_17" in engine.compliance_protocols
    assert "EU_MICA" in engine.compliance_protocols
    assert engine.cleared_ledger == {}


def test_process_and_clear():
    engine = ZKSovereignClearing()
    tx = ClearingTransaction(
        tx_id="TX-888",
        sender_galaxy="Sirius-Prime",
        receiver_galaxy="Centauri-Alpha",
        amount=50000.0,
        asset_type="SOLAR_HASH",
        timestamp_ms=time.time() * 1000.0,
    )
    
    proof = engine._generate_zk_snark_proof(tx)
    assert isinstance(proof, str)
    assert len(proof) > 0

    result = engine.process_and_clear(tx)
    assert "settlement_id" in result
    assert "zk_proof" in result
    assert result["audit_passed"] is True
    assert result["clearing_time_ms"] >= 0
    assert result["settlement_id"] in engine.cleared_ledger
    assert engine.cleared_ledger[result["settlement_id"]]["tx_id"] == "TX-888"


def test_main_execution_block():
    runpy.run_module("zk_sovereign_clearing", run_name="__main__")
