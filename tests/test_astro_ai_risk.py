import json
import os
import runpy
from unittest.mock import mock_open, patch
import pytest
from astro_ai_risk import AstroAiRiskEngine


def test_evaluate_portfolio_hedging_default():
    engine = AstroAiRiskEngine()
    report = engine.evaluate_portfolio_hedging()
    assert report["status"] == "ASTRO_AI_HEDGING_PASSED"
    assert report["total_aum_usd"] == 50_000_000.0
    assert report["portfolio_volatility_pct"] <= 1.20
    assert report["max_drawdown_pct"] <= 4.00
    assert "sharpe_ratio" in report
    assert "latency_ms" in report


def test_evaluate_portfolio_hedging_custom_aum():
    engine = AstroAiRiskEngine()
    custom_aum = 88_888_888.0
    report = engine.evaluate_portfolio_hedging(total_aum_usd=custom_aum)
    assert report["total_aum_usd"] == custom_aum
    assert report["status"] == "ASTRO_AI_HEDGING_PASSED"


def test_main_execution_block():
    runpy.run_module("astro_ai_risk", run_name="__main__")
