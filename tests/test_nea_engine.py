from src.energy.nea_engine import NEAEngine


def test_nea_engine_initialization():
    engine = NEAEngine(max_capacity=100000)
    assert engine.max_capacity == 100000
    assert engine.current_active_nodes == 100000
    assert engine.energy_state == "HIGH_PERFORMANCE"
    assert engine.power_consumption_kw == 5000.0


def test_nea_engine_eco_mode():
    engine = NEAEngine(max_capacity=100000)
    res = engine.analyze_and_adjust(current_traffic_tps=3000)
    assert res["state"] == "ECO_MODE"
    assert res["active_nodes"] == 10000
    assert res["power_kw"] == 500.0
    assert res["adjustment_time_ms"] >= 0


def test_nea_engine_normal_mode():
    engine = NEAEngine(max_capacity=100000)
    res = engine.analyze_and_adjust(current_traffic_tps=25000)
    assert res["state"] == "NORMAL"
    assert res["active_nodes"] == 50000
    assert res["power_kw"] == 2500.0
    assert res["adjustment_time_ms"] >= 0


def test_nea_engine_high_performance_mode():
    engine = NEAEngine(max_capacity=100000)
    # Put it in ECO first
    engine.analyze_and_adjust(current_traffic_tps=1000)
    # Then burst
    res = engine.analyze_and_adjust(current_traffic_tps=80000)
    assert res["state"] == "HIGH_PERFORMANCE"
    assert res["active_nodes"] == 100000
    assert res["power_kw"] == 5000.0
    assert res["adjustment_time_ms"] >= 0
