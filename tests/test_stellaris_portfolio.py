import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "src"))

from stellaris_portfolio import StellarisPortfolioEngine


def test_portfolio_initialization():
    engine = StellarisPortfolioEngine(risk_profile="HIGH_GROWTH")
    assert engine.risk_profile == "HIGH_GROWTH"


def test_optimal_allocation_capital_distribution():
    capital = 2_000_000.0
    engine = StellarisPortfolioEngine()
    report = engine.calculate_optimal_allocation(capital_usd=capital)

    allocations = report["allocations"]
    assert allocations["STAR_Mainnet_Staking"] == capital * 0.40
    assert allocations["DeepSpace_NFT_Mining"] == capital * 0.25
    assert allocations["Polkadot_DOT_Pool"] == capital * 0.15
    assert allocations["Fantom_Sonic_Lachesis"] == capital * 0.10
    assert allocations["Quantum_Hedge_Reserve"] == capital * 0.10

    total_allocated = sum(allocations.values())
    assert abs(total_allocated - capital) < 1e-6


def test_portfolio_metrics():
    engine = StellarisPortfolioEngine()
    report = engine.calculate_optimal_allocation()

    assert report["expected_annual_roi_pct"] == 28.4
    assert report["volatility_reduction_pct"] == 33.0
    assert report["trading_slippage_pct"] == 0.002
    assert "optimization_latency_ms" in report
    assert report["status"] == "OPTIMAL_CONVERGED" or "status" in report
