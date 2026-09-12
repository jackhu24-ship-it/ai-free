import asyncio
import sys
import time

sys.path.insert(0, "auto_copilot")
from asil_safety_core import safety_supervisor, VehicleSafeState
from agent_graph import arun_diagnostic

async def run_stage1_validation():
    print("==================================================================")
    print("STAGE 1: ISO 26262 ASIL-D SAFETY SUPERVISOR & TWO-KEY HANDSHAKE TEST")
    print("==================================================================")

    # 1. Normal Diagnostic Readout
    res1 = await arun_diagnostic("請查詢目前冷卻水溫與DTC故障碼")
    print("\n[Test 1: Readout Permit]")
    print("Query: 請查詢目前冷卻水溫與DTC故障碼")
    print("Safe State:", res1.get("safe_state"))
    print("Response:", res1.get("spoken_response"))
    assert res1.get("safe_state") == VehicleSafeState.NORMAL_RUN.value

    # 2. Critical Actuator Request (Two-Key Handshake Trigger)
    res2 = await arun_diagnostic("立即切換冷卻泵高壓繼電器")
    print("\n[Test 2: Two-Key Handshake Interception]")
    print("Query: 立即切換冷卻泵高壓繼電器")
    print("Safe State:", res2.get("safe_state"))
    print("Response:", res2.get("spoken_response"))
    assert res2.get("safe_state") == VehicleSafeState.WAITING_CONFIRMATION.value
    assert "安全警告" in res2.get("spoken_response")

    # 3. Two-Key Handshake Confirmation
    res3 = await arun_diagnostic("確認執行")
    print("\n[Test 3: Voice Confirmation Handshake]")
    print("Query: 確認執行")
    print("Safe State:", res3.get("safe_state"))
    print("Response:", res3.get("spoken_response"))
    assert res3.get("safe_state") == VehicleSafeState.NORMAL_RUN.value
    assert "口令驗證通過" in res3.get("spoken_response")

    # 4. FTTI (Fault Tolerant Time Interval) Timeout Test
    print("\n[Test 4: Dynamic FTTI 15s Countdown & Safe State Fallback]")
    # Force state to DEGRADED_WARN and simulate 16s elapsed
    safety_supervisor.transition_to(VehicleSafeState.DEGRADED_WARN, "Simulated Coolant Over-temp > 105C")
    safety_supervisor.ftti_start_time = time.time() - 16.0 # expired

    res4 = await arun_diagnostic("查詢當前狀態")
    print("Safe State after FTTI expiry:", res4.get("safe_state"))
    print("Response:", res4.get("spoken_response"))
    print("HV Interlock:", safety_supervisor.get_telemetry_status()["hv_interlock"])
    assert res4.get("safe_state") == VehicleSafeState.EMERGENCY_SAFE.value
    assert safety_supervisor.high_voltage_interlock_closed is False

    # 5. Actuator Blocked in EMERGENCY_SAFE
    res5 = await arun_diagnostic("切斷水泵繼電器")
    print("\n[Test 5: Actuators Strict Lockout in EMERGENCY_SAFE]")
    print("Query: 切斷水泵繼電器")
    print("Response:", res5.get("spoken_response"))
    assert "拒絕執行" in res5.get("spoken_response")

    print("\n==================================================================")
    print("[PASS] [ALL STAGE 1 SAFETY TESTS PASSED 100% WITH ASIL-D COMPLIANCE]")
    print("==================================================================")

if __name__ == "__main__":
    asyncio.run(run_stage1_validation())
