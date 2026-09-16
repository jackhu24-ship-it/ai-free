import runpy
from energy_budger import EnergyBudgetController


def test_init_default_and_custom():
    controller_default = EnergyBudgetController()
    assert controller_default.target_kwh == 0.85

    controller_custom = EnergyBudgetController(target_kwh=0.75)
    assert controller_custom.target_kwh == 0.75


def test_execute_green_autoscaling_default():
    controller = EnergyBudgetController()
    report = controller.execute_green_autoscaling()
    assert report["status"] == "GREEN_SCALING_BUDGET_MET"
    assert "measured_power_kwh_per_1k_nodes" in report
    assert "autoscale_latency_seconds" in report


def test_execute_green_autoscaling_custom_nodes():
    controller = EnergyBudgetController()
    report = controller.execute_green_autoscaling(active_nodes=20000)
    assert report["status"] == "GREEN_SCALING_BUDGET_MET"


def test_main_execution_block():
    runpy.run_module("energy_budger", run_name="__main__")
