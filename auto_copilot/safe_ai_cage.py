"""
AutoCopilot Safe AI Supervisor (Safety Cage) & Safety over Ethernet (SOME/IP)
=============================================================================
依據 霸丸總指揮官 衍生架構拓展令 (Roadmap Expansion)：
1. AI 決策外層安全護欄 (Safety Cage)：
   監控與仲裁未具 ASIL-D 認證之端到端 (E2E) 自動駕駛 / 語音大模型輸出，
   在毫秒級 (< 5ms) 實施動態包絡線裁決，防止 AI 幻覺輸出引發實車失控。
2. 跨域安全協同 (Safety over Ethernet):
   升級適配 SOME/IP (AUTOSAR FOA) 與車載乙太網 (IEEE 802.3cg/ch)，
   原生適配中央計算 (CVC) + 區域控制器 (Zonal Controller) 架構。
"""

import logging
import os
import struct
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

# Windows UTF-8 控制台保護
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("AutoCopilot.SafeAICage")


@dataclass
class SomeIpPacket:
    """SOME/IP (Scalable service-Oriented MiddlewarE over IP) 16-Byte Header"""
    service_id: int          # 16-bit
    method_id: int           # 16-bit (Method or Event)
    length: int              # 32-bit (Payload length + 8 bytes)
    client_id: int           # 16-bit
    session_id: int          # 16-bit
    protocol_version: int = 1 # 8-bit
    interface_version: int = 1# 8-bit
    message_type: int = 0x02 # 8-bit (0x00=Request, 0x02=Notification)
    return_code: int = 0x00  # 8-bit (0x00=E_OK)
    payload: bytes = b""

    def encode(self) -> bytes:
        """編碼為標準 16-Byte Header + Payload"""
        msg_id = (self.service_id << 16) | self.method_id
        req_id = (self.client_id << 16) | self.session_id
        length = len(self.payload) + 8
        header = struct.pack(
            "!IIIBBBB",
            msg_id,
            length,
            req_id,
            self.protocol_version,
            self.interface_version,
            self.message_type,
            self.return_code
        )
        return header + self.payload

    @classmethod
    def decode(cls, data: bytes) -> "SomeIpPacket":
        """自乙太網位元流解碼 SOME/IP 報文"""
        if len(data) < 16:
            raise ValueError(f"SOME/IP 報文長度不足 16 Bytes (實際: {len(data)})")
        msg_id, length, req_id, proto, iface, m_type, ret = struct.unpack("!IIIBBBB", data[:16])
        payload = data[16:16 + length - 8]
        return cls(
            service_id=(msg_id >> 16) & 0xFFFF,
            method_id=msg_id & 0xFFFF,
            length=length,
            client_id=(req_id >> 16) & 0xFFFF,
            session_id=req_id & 0xFFFF,
            protocol_version=proto,
            interface_version=iface,
            message_type=m_type,
            return_code=ret,
            payload=payload
        )


class SafeAICageSupervisor:
    """ASIL-D 外層安全護欄 (Safety Cage)：實時仲裁端到端神經網路演算法輸出"""

    # 剛性物理動力學包絡線 (Physical Safety Envelope)
    MAX_ACCELERATION_MPS2 = 2.5       # 最大舒適/安全正向加速度
    MIN_DECELERATION_MPS2 = -4.5      # 最大一般煞車減速度
    MAX_STEER_RATE_DEG_S = 40.0       # 最大轉向角速度
    MIN_TTC_SECONDS = 1.5             # 碰撞時間裕度 (Time to Collision)

    def __init__(self, node_name: str = "SafetyCage_Zonal_GW"):
        self.node_name = node_name
        self.session_counter = 0
        self.total_arbitrations = 0
        self.override_interventions = 0

    def arbitrate_ai_command(
        self,
        target_accel: float,
        target_steer_rate: float,
        ttc_estimate: float,
        ai_model_confidence: float = 0.95
    ) -> Tuple[float, float, str, float]:
        """
        仲裁 AI 模型給出的控制量。
        回傳: (safe_accel, safe_steer_rate, cage_status, reaction_time_ms)
        """
        t_start = time.perf_counter()
        self.total_arbitrations += 1
        is_override = False
        reason = "NORMAL_PASS"

        # 1. 檢驗 TTC 碰撞裕度
        if ttc_estimate < self.MIN_TTC_SECONDS:
            is_override = True
            safe_accel = self.MIN_DECELERATION_MPS2
            reason = f"CAGE_OVERRIDE_TTC_VIOLATION ({ttc_estimate:.2f}s < {self.MIN_TTC_SECONDS}s)"
        else:
            # 2. 檢驗加速度包絡線
            if target_accel > self.MAX_ACCELERATION_MPS2:
                is_override = True
                safe_accel = self.MAX_ACCELERATION_MPS2
                reason = f"CAGE_OVERRIDE_MAX_ACCEL_CLAMPED ({target_accel} -> {self.MAX_ACCELERATION_MPS2})"
            elif target_accel < self.MIN_DECELERATION_MPS2:
                safe_accel = self.MIN_DECELERATION_MPS2
            else:
                safe_accel = target_accel

        # 3. 檢驗轉向角速度包絡線
        if abs(target_steer_rate) > self.MAX_STEER_RATE_DEG_S:
            is_override = True
            safe_steer_rate = self.MAX_STEER_RATE_DEG_S if target_steer_rate > 0 else -self.MAX_STEER_RATE_DEG_S
            reason += f" | CAGE_OVERRIDE_STEER_RATE_CLAMPED"
        else:
            safe_steer_rate = target_steer_rate

        if is_override:
            self.override_interventions += 1

        elapsed_ms = (time.perf_counter() - t_start) * 1000.0
        cage_status = "INTERVENED" if is_override else "PASSTHROUGH"
        return safe_accel, safe_steer_rate, f"{cage_status}: {reason}", elapsed_ms

    def pack_to_someip_ethernet(
        self,
        safe_accel: float,
        safe_steer_rate: float,
        status_code: int = 0x00
    ) -> bytes:
        """將經安全護欄裁決後之控制指令封裝為 100BASE-T1 / SOME/IP 乙太網訊框"""
        self.session_counter = (self.session_counter + 1) & 0xFFFF
        # Payload: Accel(float4), SteerRate(float4), Status(uint4) = 12 Bytes
        payload = struct.pack("!ffI", safe_accel, safe_steer_rate, status_code)
        
        packet = SomeIpPacket(
            service_id=0x1020,     # Zonal Safety Actuation Service
            method_id=0x8001,      # Actuator Safe Command Event
            length=len(payload) + 8,
            client_id=0x0001,      # AutoCopilot Supervisor Core
            session_id=self.session_counter,
            message_type=0x02,     # Notification
            payload=payload
        )
        return packet.encode()


if __name__ == "__main__":
    cage = SafeAICageSupervisor()

    print("=== AutoCopilot Safe AI Cage & SOME/IP Demo ===")
    
    # 案例 1: 正常 AI 決策
    a1, s1, r1, t1 = cage.arbitrate_ai_command(target_accel=1.2, target_steer_rate=15.0, ttc_estimate=4.5)
    print(f"[案例 1 - 正常輸入] 加速度: {a1} m/s^2, 轉向: {s1} deg/s, 狀態: {r1}, 耗時: {t1:.4f} ms")

    # 案例 2: AI 幻覺輸出危險暴衝 (+5.8 m/s^2 加速度)
    a2, s2, r2, t2 = cage.arbitrate_ai_command(target_accel=5.8, target_steer_rate=80.0, ttc_estimate=0.9)
    print(f"[案例 2 - 幻覺暴衝] 護欄限幅加速度: {a2} m/s^2, 轉向角速度: {s2} deg/s, 狀態: {r2}, 耗時: {t2:.4f} ms")

    # 封裝為 SOME/IP 乙太網報文
    someip_bytes = cage.pack_to_someip_ethernet(a2, s2, status_code=0x01)
    decoded = SomeIpPacket.decode(someip_bytes)
    print(f"\n[Safety over Ethernet] SOME/IP 封裝位元組: {len(someip_bytes)} Bytes")
    print(f"Service ID: {hex(decoded.service_id)} | Method ID: {hex(decoded.method_id)} | Session: {decoded.session_id}")
    print("================================================\n")
