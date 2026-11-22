"""
PHANToM Grid :: PLE Harness Atomic Closure Test Suite
Asserts four sovereign gates and physical compliance.
"""
import unittest
import os
import sys
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))
from ple_agent_harness import PhysicalEngineeringHarness

class TestPLEHarnessClosure(unittest.TestCase):
    def setUp(self):
        self.harness = PhysicalEngineeringHarness()

    def test_mechanical_mep_clash_free(self):
        task = {
            "domain": "mechanical",
            "sub_tasks": ["mep_clash_detection_corridor", "pipe_routing"]
        }
        res = self.harness.evaluate_task(task)
        self.assertEqual(res["status"], "SUCCESS")
        for sub, details in res["sub_task_results"].items():
            self.assertEqual(details["clash_count"], 0)
            self.assertEqual(details["status"], "CLASH_FREE_PASS")

    def test_electrical_voltage_drop_compliance(self):
        task = {
            "domain": "electrical",
            "sub_tasks": ["feeder_sizing_main_panel"]
        }
        res = self.harness.evaluate_task(task)
        details = res["sub_task_results"]["feeder_sizing_main_panel"]
        self.assertTrue(details["voltage_drop_compliant"])
        self.assertLess(details["voltage_drop_percent"], 3.0)
        self.assertEqual(details["status"], "ELECTRICAL_CODE_PASS")

    def test_structural_deflection_compliance(self):
        task = {
            "domain": "structural",
            "sub_tasks": ["steel_beam_load_test"]
        }
        res = self.harness.evaluate_task(task)
        details = res["sub_task_results"]["steel_beam_load_test"]
        self.assertTrue(details["structural_compliant"])
        self.assertLessEqual(details["actual_deflection_mm"], details["allowable_deflection_mm"])

    def test_sovereign_gates_zdr_and_vram(self):
        task = {"domain": "all", "sub_tasks": ["code_compliance"]}
        res = self.harness.evaluate_task(task)
        self.assertLessEqual(res["vram_peak_gb"], 50.0)
        self.assertEqual(res["zdr_status"]["residual_mb"], 0.00)
        self.assertEqual(res["zdr_status"]["pass_1"], "0xAA")
        self.assertEqual(res["zdr_status"]["pass_2"], "0x00")

if __name__ == "__main__":
    unittest.main()
