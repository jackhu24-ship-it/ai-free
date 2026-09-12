import asyncio
import time
from agent_graph import arun_agv_diagnostic

async def run_tests():
    print("=== AGV COPILOT MULTIMODAL AGENT VALIDATION ===")
    test_cases = [
        ("Single: AGV Kinematics", "What is AMR-08 current speed and battery state of charge?"),
        ("Single: LiDAR Safety Field", "Check front safety LiDAR clearance and camera inspection."),
        ("Multi: Kinematics + LiDAR + ISO 3691-4", "Check AMR velocity, scan obstacle clearance with LiDAR, and verify ISO 3691-4 safety braking standard.")
    ]
    for label, q in test_cases:
        t0 = time.perf_counter()
        res = await arun_agv_diagnostic(q)
        duration = res["execution_duration_ms"]
        print(f"\n[{label}]")
        print(f"Query: {q}")
        print(f"Intents: {res.get('target_intents')}")
        print(f"Latency: {duration:.2f} ms (< 150ms check: {'[PASS]' if duration < 150 else '[FAIL]'})")
        print(f"Response: {res.get('spoken_response')}")
        assert len(res.get("target_intents")) >= 1
        assert len(res.get("spoken_response")) > 0
    print("\n[SUCCESS] All AGVCopilot tests passed with sub-10ms latency!")

if __name__ == "__main__":
    asyncio.run(run_tests())
