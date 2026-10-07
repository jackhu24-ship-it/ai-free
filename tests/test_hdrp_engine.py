import pytest

from src.router.hdrp_engine import HDRPEngine, RoutePath


def test_hdrp_initialization():
    engine = HDRPEngine(latency_target_ms=0.035)
    assert engine.latency_target_ms == 0.035
    assert engine.nodes == {}
    assert engine.graph == {}


def test_register_node():
    engine = HDRPEngine()
    engine.register_node("node_A", (1.0, 2.0, 3.0))
    assert "node_A" in engine.nodes
    assert engine.nodes["node_A"] == (1.0, 2.0, 3.0)
    assert "node_A" in engine.graph

    # Register again
    engine.register_node("node_A", (1.0, 2.0, 3.0))
    assert engine.nodes["node_A"] == (1.0, 2.0, 3.0)


def test_set_link_and_status():
    engine = HDRPEngine()
    engine.set_link("node_A", "node_B", latency_ms=0.015, loss_rate=0.01, qber=0.02)
    assert "node_A" in engine.graph
    assert "node_B" in engine.graph
    assert engine.graph["node_A"]["node_B"]["is_active"] is True

    # Disable link
    engine.set_link_status("node_A", "node_B", is_active=False)
    assert engine.graph["node_A"]["node_B"]["is_active"] is False
    assert engine.graph["node_B"]["node_A"]["is_active"] is False

    # Link status for non-existent node/link (safe branch check)
    engine.set_link_status("node_X", "node_Y", is_active=False)
    engine.set_link_status("node_A", "node_Z", is_active=False)


def test_calculate_cost_branches():
    engine = HDRPEngine()
    # Low QBER <= 0.1
    cost_low = engine._calculate_cost({"latency_ms": 10.0, "qber": 0.05, "loss_rate": 0.0})
    assert cost_low == 10.0 * (1.0 + 0.05 * 10.0)

    # High QBER > 0.1
    cost_high = engine._calculate_cost({"latency_ms": 10.0, "qber": 0.2, "loss_rate": 0.0})
    expected_penalty = (1.0 + 0.2 * 10.0) + (0.2 * 100.0)
    assert cost_high == 10.0 * expected_penalty


def test_find_optimal_route_source_target_missing():
    engine = HDRPEngine()
    engine.register_node("node_A", (0.0,))
    assert engine.find_optimal_route("node_A", "node_B") is None
    assert engine.find_optimal_route("node_X", "node_A") is None


def test_find_optimal_route_success():
    engine = HDRPEngine()
    # A -> B -> C
    # A -> C (direct but high latency or high qber)
    engine.register_node("A", (0.0,))
    engine.register_node("B", (1.0,))
    engine.register_node("C", (2.0,))

    engine.set_link("A", "B", latency_ms=0.010, loss_rate=0.0, qber=0.01)
    engine.set_link("B", "C", latency_ms=0.010, loss_rate=0.0, qber=0.01)
    engine.set_link("A", "C", latency_ms=0.050, loss_rate=0.0, qber=0.50)

    route = engine.find_optimal_route("A", "C")
    assert isinstance(route, RoutePath)
    assert route.path == ["A", "B", "C"]
    assert pytest.approx(route.estimated_latency_ms, rel=1e-3) == 0.020


def test_find_optimal_route_no_path_and_inactive_links():
    engine = HDRPEngine()
    engine.register_node("A", (0.0,))
    engine.register_node("B", (1.0,))
    engine.register_node("C", (2.0,))

    engine.set_link("A", "B", latency_ms=0.01, loss_rate=0.0, qber=0.01)
    engine.set_link("B", "C", latency_ms=0.01, loss_rate=0.0, qber=0.01)

    # Inactivate B-C link
    engine.set_link_status("B", "C", is_active=False)

    route = engine.find_optimal_route("A", "C")
    assert route is None


def test_find_optimal_route_visited_branch():
    engine = HDRPEngine()
    # Diamond graph to exercise visited set:
    # A -> B -> D
    # A -> C -> D
    # B <-> C cross link
    for n in ["A", "B", "C", "D"]:
        engine.register_node(n, (0.0,))

    engine.set_link("A", "B", latency_ms=0.01, loss_rate=0.0, qber=0.01)
    engine.set_link("A", "C", latency_ms=0.01, loss_rate=0.0, qber=0.01)
    engine.set_link("B", "C", latency_ms=0.001, loss_rate=0.0, qber=0.01)
    engine.set_link("B", "D", latency_ms=0.02, loss_rate=0.0, qber=0.01)
    engine.set_link("C", "D", latency_ms=0.02, loss_rate=0.0, qber=0.01)

    route = engine.find_optimal_route("A", "D")
    assert route is not None
    assert route.path[0] == "A"
    assert route.path[-1] == "D"
