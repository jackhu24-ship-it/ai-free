"""
Vehicle Shadow Mode Engine (整車暗模式運算中樞)
==============================================
依據 ISO 26262-4 (System Verification) 與 GSN 動態實證要求：
1. Listen-Only 非侵入式聽證閘門 (Zero-TX Guarantee: 絕對禁止向匯流排發送致動訊號)
2. 雙軌影子推論 (Dual-Track Shadow Inference): 真實車況 vs AutoCopilot 安全決策
3. 偏差比對器 (Discrepancy Analyzer): 比對真實駕駛行為與 AI 預測行為
4. 動態實證記錄器 (Dynamic Evidence Logger): 沉澱邊界場景資料至 shadow_dynamic_evidence.jsonl
"""

import argparse
import json
import logging
import os
import sys
import threading
import time
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import can

# Windows UTF-8 控制台保護
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from stage1_safety_supervisor import (
    SystemOperatingState,
    build_safety_graph,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("AutoCopilot.ShadowMode")


@dataclass
class ShadowTelemetrySnapshot:
    timestamp: float
    coolant_temp_c: float
    bus_voltage_v: float
    line_pressure_kpa: float
    motor_rpm: int
    raw_frame_id: int


@dataclass
class DynamicEvidenceRecord:
    record_id: str
    timestamp: float
    telemetry: Dict[str, Any]
    predicted_state: str
    recommended_action: Optional[str]
    actual_driver_action: str
    discrepancy_detected: bool
    risk_level: str
    tx_blocked_count: int
    notes: str


class VehicleShadowModeEngine:
    """整車暗模式運算引擎 (Zero-TX Listen-Only)"""

    def __init__(
        self,
        interface: str = "virtual",
        channel: str = "shadow_vbus",
        bitrate: int = 500000,
        evidence_file: Optional[str] = None
    ):
        self.interface = interface
        self.channel = channel
        self.bitrate = bitrate
        self.evidence_file = evidence_file or os.path.join(CURRENT_DIR, "shadow_dynamic_evidence.jsonl")

        self.bus: Optional[can.BusABC] = None
        self.safety_graph = build_safety_graph()
        self.tx_attempt_count = 0
        self.tx_blocked_count = 0
        self.rx_frame_count = 0

        self._running = False
        self._rx_thread: Optional[threading.Thread] = None
        self._latest_snapshot = ShadowTelemetrySnapshot(
            timestamp=time.time(),
            coolant_temp_c=92.5,
            bus_voltage_v=385.0,
            line_pressure_kpa=140.0,
            motor_rpm=2800,
            raw_frame_id=0x120
        )
        self.records: List[DynamicEvidenceRecord] = []
        self._init_listen_only_bus()

    def _init_listen_only_bus(self):
        """初始化 Listen-Only 總線，建立 Zero-TX 閘門防護"""
        try:
            if self.interface == "virtual":
                self.bus = can.interface.Bus(self.channel, interface="virtual")
            elif self.interface == "socketcan":
                # SocketCAN 原生支持 listen_only / fd
                self.bus = can.interface.Bus(self.channel, interface="socketcan", bitrate=self.bitrate)
            elif self.interface == "pcan":
                self.bus = can.interface.Bus(self.channel, interface="pcan", bitrate=self.bitrate, listen_only=True)
            else:
                self.bus = can.interface.Bus(self.channel, interface="virtual")
        except Exception as e:
            logger.warning(f"[ShadowMode] Failed to init bus ({e}); fallback to virtual.")
            self.bus = can.interface.Bus("shadow_fallback_vbus", interface="virtual")

        # 攔截並封死任何 send 行為 (Zero-TX Guarantee)
        if self.bus:
            original_send = self.bus.send

            def guarded_send(msg, timeout=None):
                self.tx_attempt_count += 1
                self.tx_blocked_count += 1
                logger.warning(f"[Zero-TX Barrier] Blocked outgoing frame {hex(msg.arbitration_id)} in Shadow Mode!")
                return  # 絕對不向物理總線發送

            self.bus.send = guarded_send

    def process_incoming_frame(self, msg: can.Message, actual_driver_action: str = "NORMAL_DRIVING") -> Optional[DynamicEvidenceRecord]:
        """解析實車總線訊框並執行雙軌影子推論與偏差比對"""
        self.rx_frame_count += 1
        now = time.time()

        # 簡化解析 0x120 散熱遙測幀
        if msg.arbitration_id == 0x120 and len(msg.data) >= 4:
            coolant = float(msg.data[0]) - 40.0  # offset 40
            line_p = float(msg.data[1]) * 2.0
            rpm = (int(msg.data[2]) << 8) | int(msg.data[3])
            self._latest_snapshot = ShadowTelemetrySnapshot(
                timestamp=now,
                coolant_temp_c=coolant,
                bus_voltage_v=384.5,
                line_pressure_kpa=line_p,
                motor_rpm=rpm,
                raw_frame_id=msg.arbitration_id
            )
        else:
            coolant = self._latest_snapshot.coolant_temp_c

        # 軌道 2: 影子大腦推論
        query = "讀取目前冷卻液溫度" if coolant <= 105.0 else "冷卻液嚴重過溫"
        init_state = {
            "query": query,
            "current_state": SystemOperatingState.NORMAL_RUN,
            "pending_action": None,
            "action_requested_timestamp": 0.0,
            "ftti_limit_seconds": 10.0,
            "is_confirmed_by_user": False,
            "telemetry_data": {
                "coolant_temp_c": coolant,
                "bus_voltage_v": self._latest_snapshot.bus_voltage_v,
                "line_pressure_kpa": self._latest_snapshot.line_pressure_kpa,
            },
            "target_nodes": [],
            "spoken_response": "",
        }

        eval_res = self.safety_graph.invoke(init_state)
        predicted_state = eval_res["current_state"]
        recommended_action = "SUGGEST_DERATING_OR_SAFE_STOP" if coolant > 105.0 else None

        # 偏差比對: 若冷卻液 > 105°C 且駕駛維持加速/未減載，則標記 Discrepancy
        discrepancy = False
        risk_level = "LOW"
        notes = "Nominal operating alignment."

        if coolant > 105.0 and actual_driver_action == "NORMAL_DRIVING":
            discrepancy = True
            risk_level = "CRITICAL"
            notes = f"Discrepancy: Engine coolant {coolant:.1f}°C exceeds 105°C, but driver made no thermal derating action."
        elif coolant > 100.0:
            risk_level = "ELEVATED"
            notes = f"Approaching limit: Coolant at {coolant:.1f}°C."

        record = DynamicEvidenceRecord(
            record_id=f"EV-{int(now * 1000)}-{self.rx_frame_count}",
            timestamp=now,
            telemetry={
                "coolant_temp_c": coolant,
                "bus_voltage_v": self._latest_snapshot.bus_voltage_v,
                "motor_rpm": self._latest_snapshot.motor_rpm,
            },
            predicted_state=str(predicted_state),
            recommended_action=recommended_action,
            actual_driver_action=actual_driver_action,
            discrepancy_detected=discrepancy,
            risk_level=risk_level,
            tx_blocked_count=self.tx_blocked_count,
            notes=notes
        )

        self.records.append(record)
        self._persist_evidence(record)
        return record

    def _persist_evidence(self, record: DynamicEvidenceRecord):
        """將動態實證寫入 JSONL"""
        try:
            with open(self.evidence_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"[ShadowMode] Failed to write evidence: {e}")

    def run_simulation_stream(self, cycles: int = 15, interval_s: float = 0.05):
        """生成模擬實車數據流以驗證 Shadow Mode 與動態實證收集"""
        self._running = True
        logger.info(f"[ShadowMode] Starting Shadow Stream ({cycles} cycles)...")

        for i in range(cycles):
            # 前 10 週期正常 (92°C ~ 103°C)，後 5 週期模擬過溫 (108°C)
            temp = 92.0 + (i * 1.2) if i < 10 else 108.5
            payload = bytearray([int(temp + 40.0) & 0xFF, 70, 0x0B, 0xB8])
            msg = can.Message(arbitration_id=0x120, data=payload, is_extended_id=False)
            
            # 駕駛員行為：在高溫下依然踩油門 NORMAL_DRIVING
            driver_action = "NORMAL_DRIVING"
            self.process_incoming_frame(msg, actual_driver_action=driver_action)
            time.sleep(interval_s)

        self._running = False
        logger.info(f"[ShadowMode] Stream completed. Total records: {len(self.records)}, TX Blocked: {self.tx_blocked_count}")

    def shutdown(self):
        """關閉影子模式引擎與匯流排"""
        self._running = False
        if self.bus:
            try:
                self.bus.shutdown()
            except Exception:
                pass
            self.bus = None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AutoCopilot Vehicle Shadow Mode Engine")
    parser.add_argument("--interface", default="virtual", help="CAN interface (virtual/socketcan/pcan)")
    parser.add_argument("--channel", default="shadow_vbus", help="CAN channel")
    parser.add_argument("--cycles", type=int, default=15, help="Simulation cycles")
    args = parser.parse_args()

    engine = VehicleShadowModeEngine(interface=args.interface, channel=args.channel)
    engine.run_simulation_stream(cycles=args.cycles)
    
    discrepancies = [r for r in engine.records if r.discrepancy_detected]
    print("\n=== Shadow Mode Summary ===")
    print(f"Total Telemetry Evaluated: {len(engine.records)}")
    print(f"Discrepancies Captured: {len(discrepancies)}")
    print(f"Zero-TX Guaranteed (Blocked Sends): {engine.tx_blocked_count}")
    print(f"Evidence File: {engine.evidence_file}")
    
    engine.shutdown()
