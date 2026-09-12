"""
Fleet Telemetry & Blackbox FIFO Protocol (車隊遙測與黑盒子環形緩衝中樞)
======================================================================
依據 ISO 26262-4 (Operation & Maintenance) 與 霸丸總指揮官 階段三長效運維規範：
1. 200ms ~ 500ms 原始報文環形緩衝區 (Circular Buffer / FIFO)
2. 降級事件 (DEGRADED_WARN / EMERGENCY_SAFE) 觸發瞬態凍結 (Pre-Trigger Freeze)
3. 提取觸發前 200ms 全匯流排原始 CAN/CAN-FD 幀並結構化導出快照
4. 提供車載邊緣日誌上報與狀態機模型回溯校準依據
"""

import collections
import json
import logging
import os
import sys
import time
from dataclasses import asdict, dataclass
from typing import Any, Deque, Dict, List, Optional
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("AutoCopilot.FleetBlackbox")


@dataclass
class BufferedCANFrame:
    timestamp: float
    arbitration_id: int
    data_hex: str
    dlc: int
    is_fd: bool
    is_rx: bool


@dataclass
class BlackboxSnapshot:
    snapshot_id: str
    trigger_timestamp: float
    trigger_state: str
    trigger_reason: str
    pre_trigger_duration_ms: float
    captured_frames_count: int
    frames: List[Dict[str, Any]]


class FleetTelemetryBlackbox:
    """場端遙測閉環：觸發前 200ms 原始報文黑盒子緩衝器"""

    def __init__(
        self,
        buffer_window_ms: float = 300.0,
        output_dir: Optional[str] = None
    ):
        self.buffer_window_ms = buffer_window_ms
        self.output_dir = output_dir or os.path.join(CURRENT_DIR, "blackbox_snapshots")
        os.makedirs(self.output_dir, exist_ok=True)

        # 雙端隊列維護滑動時間視窗
        self._buffer: Deque[BufferedCANFrame] = collections.deque(maxlen=1000)
        self.snapshot_history: List[BlackboxSnapshot] = []

    def record_frame(self, msg: can.Message, is_rx: bool = True):
        """將傳入或發出之 CAN 幀實時寫入環形緩衝區，並剔除過期幀"""
        now = time.time()
        ts = msg.timestamp if (hasattr(msg, "timestamp") and msg.timestamp and msg.timestamp > 1000000.0) else now
        
        buffered = BufferedCANFrame(
            timestamp=ts,
            arbitration_id=msg.arbitration_id,
            data_hex=msg.data.hex().upper() if msg.data else "",
            dlc=len(msg.data) if msg.data else 0,
            is_fd=getattr(msg, "is_fd", False),
            is_rx=is_rx
        )
        self._buffer.append(buffered)

        # 剔除超過 buffer_window_ms 的過期報文
        cutoff = now - (self.buffer_window_ms / 1000.0)
        while self._buffer and self._buffer[0].timestamp < cutoff:
            self._buffer.popleft()

    def capture_pre_trigger_snapshot(
        self,
        trigger_state: str,
        trigger_reason: str,
        lookback_ms: float = 200.0
    ) -> BlackboxSnapshot:
        """
        當觸發降級或安全關斷時，凍結並提取觸發前 200ms 的所有原始報文
        """
        now = time.time()
        cutoff = now - (lookback_ms / 1000.0)

        # 篩選落在觸發前 200ms 內的訊框
        captured = [asdict(f) for f in self._buffer if f.timestamp >= cutoff]

        snapshot_id = f"BB-{int(now * 1000)}-{trigger_state}"
        snapshot = BlackboxSnapshot(
            snapshot_id=snapshot_id,
            trigger_timestamp=now,
            trigger_state=trigger_state,
            trigger_reason=trigger_reason,
            pre_trigger_duration_ms=lookback_ms,
            captured_frames_count=len(captured),
            frames=captured
        )

        self.snapshot_history.append(snapshot)
        self._save_snapshot(snapshot)
        logger.info(f"[Blackbox] Captured {len(captured)} frames in pre-trigger {lookback_ms}ms window (ID: {snapshot_id})")
        return snapshot

    def _save_snapshot(self, snapshot: BlackboxSnapshot):
        """將黑盒子快照寫入持久化 JSON"""
        filepath = os.path.join(self.output_dir, f"{snapshot.snapshot_id}.json")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(asdict(snapshot), f, indent=2, ensure_ascii=False)
            logger.info(f"[Blackbox] Snapshot exported to {filepath}")
        except Exception as e:
            logger.warning(f"[Blackbox] Failed to save snapshot ({e})")


if __name__ == "__main__":
    print("=== Fleet Telemetry Blackbox Self-Test ===")
    blackbox = FleetTelemetryBlackbox(buffer_window_ms=300.0)

    # 模擬 50 幀高頻總線傳輸 (間隔 5ms，約 250ms 歷史)
    t_start = time.time()
    for i in range(50):
        msg = can.Message(
            arbitration_id=0x120 if i % 2 == 0 else 0x180,
            data=bytearray([i & 0xFF, 0x10, 0x20, 0x30]),
            is_extended_id=False
        )
        blackbox.record_frame(msg, is_rx=True)
        time.sleep(0.005)

    # 觸發緊急降級事件 (DEGRADED_WARN: 水溫過高)
    snap = blackbox.capture_pre_trigger_snapshot(
        trigger_state="DEGRADED_WARN",
        trigger_reason="Coolant temperature exceeded 105.0°C (DBC Frame 0x120)",
        lookback_ms=200.0
    )

    print(f"快照編號: {snap.snapshot_id}")
    print(f"回溯窗口: {snap.pre_trigger_duration_ms} ms")
    print(f"捕獲原始幀數: {snap.captured_frames_count} 幀")
    print("=== Fleet Telemetry Blackbox Self-Test Complete ===")
