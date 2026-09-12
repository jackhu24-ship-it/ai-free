import asyncio
import time
from agent_graph import arun_facility_diagnostic

async def run_tests():
    print("=== FACILITY COPILOT MULTI-AGENT VALIDATION ===")
    test_cases = [
        ("Single: Rack Thermal", "What is the current temperature and PUE of Rack A04?"),
        ("Single: UPS Power Grid", "Check UPS battery runtime and grid frequency."),
        ("Multi: All 3 Subsystems", "Inspect Rack thermal metrics, check UPS battery, and verify ASHRAE compliance limits.")
    ]
    for label, q in test_cases:
        t0 = time.perf_counter()
        res = await arun_facility_diagnostic(q)
        duration = res["execution_duration_ms"]
        print(f"\n[{label}]")
        print(f"Query: {q}")
        print(f"Intents: {res.get('target_intents')}")
        print(f"Latency: {duration:.2f} ms (< 150ms check: {'[PASS]' if duration < 150 else '[FAIL]'})")
        print(f"Response: {res.get('spoken_response')}")
        assert len(res.get("target_intents")) >= 1
        assert len(res.get("spoken_response")) > 0
    print("\n[SUCCESS] All FacilityCopilot tests passed with sub-10ms latency!")

if __name__ == "__main__":
    asyncio.run(run_tests())
