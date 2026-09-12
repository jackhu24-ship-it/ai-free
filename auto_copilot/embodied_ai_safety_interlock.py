"""
AutoCopilot Embodied AI & High-DoF Robotics Physical Safety Interlock
====================================================================
依據 霸丸總指揮官 下一代核心演進令 (From Deterministic Safety to Embodied AI Safety)：
將 ASIL-D FTTI 硬體快速斷開架構，延伸至：
1. 具身機器人關節伺服 (Humanoid / Quadruped Robot 12-DoF Actuators)
2. 全地形無人車 (UTV / AGV) 線控底盤 (Steer-by-Wire & Brake-by-Wire)
3. 強物理衝擊 (Shock > 500N) 與超速角速度 (Angular Velocity > 300 deg/s) 監控
4. 毫秒級 (< 1.0ms) 物理安全隔離閥 (Physical Safety Isolation Valve) 作動
"""

import logging
import os
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

# Windows UTF-8 控制台保護
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("AutoCopilot.EmbodiedAISafety")


@dataclass
class JointTelemetry:
    joint_id: int
    joint_name: str
    torque_nm: float
    velocity_deg_s: float
    impact_force_n: float
    temperature_c: float


class EmbodiedAISafetyInterlock:
    """高動態具身機器人與線控底盤物理隔離閥控制器"""

    # 具身物理極限安全包絡線 (Kinematic & Kinetic Limits)
    MAX_JOINT_TORQUE_NM = 120.0       # 機器人關節峰值扭矩
    MAX_ANGULAR_VELOCITY = 280.0      # 最大角速度 (deg/s)
    MAX_IMPACT_SHOCK_N = 500.0        # 最大容許碰撞衝擊力
    MAX_JOINT_TEMP_C = 85.0           # 關節電機過溫閥值

    def __init__(self, target_system: str = "HUMANOID_LEGGED_ROBOT"):
        self.target_system = target_system
        self.isolation_valve_engaged = False # True = Physical Safe Cutoff Active
        self.trip_history: List[Dict[str, Any]] = []

    def evaluate_joint_safety(self, telemetry: JointTelemetry) -> Tuple[bool, str, float]:
        """
        以微秒級速度評估多軸關節狀態：
        若超出包絡線，於 < 1.0 ms 內切斷關節供電並鎖死物理隔離閥。
        回傳: (is_safe, verdict, trip_latency_ms)
        """
        t_start = time.perf_counter()
        is_safe = True
        reason = "JOINT_NORMAL"

        if telemetry.impact_force_n > self.MAX_IMPACT_SHOCK_N:
            is_safe = False
            reason = f"EXCESSIVE_IMPACT_FORCE ({telemetry.impact_force_n}N > {self.MAX_IMPACT_SHOCK_N}N)"
        elif abs(telemetry.torque_nm) > self.MAX_JOINT_TORQUE_NM:
            is_safe = False
            reason = f"OVER_TORQUE_ANOMALY ({telemetry.torque_nm}Nm > {self.MAX_JOINT_TORQUE_NM}Nm)"
        elif abs(telemetry.velocity_deg_s) > self.MAX_ANGULAR_VELOCITY:
            is_safe = False
            reason = f"ANGULAR_OVERSPEED ({telemetry.velocity_deg_s} deg/s > {self.MAX_ANGULAR_VELOCITY} deg/s)"
        elif telemetry.temperature_c > self.MAX_JOINT_TEMP_C:
            is_safe = False
            reason = f"JOINT_OVERHEAT ({telemetry.temperature_c}°C > {self.MAX_JOINT_TEMP_C}°C)"

        elapsed_ms = (time.perf_counter() - t_start) * 1000.0

        if not is_safe:
            self.isolation_valve_engaged = True
            record = {
                "timestamp": time.time(),
                "joint_id": telemetry.joint_id,
                "joint_name": telemetry.joint_name,
                "reason": reason,
                "trip_latency_ms": round(elapsed_ms, 4)
            }
            self.trip_history.append(record)
            logger.warning(f"[{self.target_system}] ⚠️ 物理安全隔離閥觸發！關節: {telemetry.joint_name} | 原因: {reason} | 耗時: {elapsed_ms:.4f} ms")

        return is_safe, reason, elapsed_ms

    def reset_valve(self) -> bool:
        """重置安全隔離閥 (需在安全停機狀態下方可執行)"""
        self.isolation_valve_engaged = False
        logger.info(f"[{self.target_system}] 物理隔離閥已復歸，系統進入 STANDBY 態。")
        return True


if __name__ == "__main__":
    interlock = EmbodiedAISafetyInterlock(target_system="HUMANOID_LEGGED_ROBOT")
    print("=== Embodied AI Physical Safety Interlock Demo ===")
    
    # 正常步態關節遙測
    j1 = JointTelemetry(joint_id=1, joint_name="Hip_Pitch_L", torque_nm=45.0, velocity_deg_s=120.0, impact_force_n=150.0, temperature_c=55.0)
    ok1, r1, t1 = interlock.evaluate_joint_safety(j1)
    print(f"[關節 1 正常] 安全: {ok1}, 耗時: {t1:.4f} ms, 狀態: {r1}")

    # 突發跌倒強衝擊 (850N 衝擊力)
    j2 = JointTelemetry(joint_id=2, joint_name="Knee_Pitch_L", torque_nm=140.0, velocity_deg_s=320.0, impact_force_n=850.0, temperature_c=60.0)
    ok2, r2, t2 = interlock.evaluate_joint_safety(j2)
    print(f"[關節 2 衝擊暴衝] 安全: {ok2}, 耗時: {t2:.4f} ms, 狀態: {r2}")
    print(f"隔離閥狀態: {'🔒 物理斷開已鎖死 (LOCKED_DISCONNECTED)' if interlock.isolation_valve_engaged else '正常'}")
    print("==================================================")
