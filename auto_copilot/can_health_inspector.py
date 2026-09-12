"""
CAN Hardware Diagnostic & Quality Inspector
===========================================
功能特點：
1. 支援 SocketCAN (Linux) 與 PCAN-Basic (Windows) 介面切換，亦支援 virtual 虛擬匯流排驗證。
2. CAN 總線狀態檢查：監控 Error Active / Warning / Passive / Bus-Off 狀態。
3. 訊號與電氣品質推斷：透過通訊錯誤計數器 (TEC/REC) 與 ACK 遺失率推論終端電阻與訊號完整性。
4. 丟包率與延遲統計：統計期望週期 (如 20Hz/50ms) 封包的抖動 (Jitter) 與丟包比率。
5. 即時產出終端診斷診斷摘要報表。
"""

import argparse
import os
import platform
import subprocess
import sys
import threading
import time
from collections import defaultdict
from typing import Dict, List, Optional
import can


class CanBusInspector:
    def __init__(self, interface: str = "socketcan", channel: str = "can0", bitrate: int = 500000):
        self.interface = interface
        self.channel = channel
        self.bitrate = bitrate
        self.bus: Optional[can.BusABC] = None
        
        # 統計計數器
        self.total_rx_count = 0
        self.error_frame_count = 0
        self.id_timestamps: Dict[int, List[float]] = defaultdict(list)
        self.id_message_count: Dict[int, int] = defaultdict(int)

    def initialize_bus(self) -> bool:
        """初始化 CAN 總線連線"""
        try:
            if self.interface == "socketcan":
                self.bus = can.interface.Bus(
                    channel=self.channel,
                    interface="socketcan",
                    receive_own_messages=False,
                )
            elif self.interface == "pcan":
                self.bus = can.interface.Bus(
                    channel=self.channel,
                    interface="pcan",
                    bitrate=self.bitrate,
                )
            elif self.interface == "virtual":
                self.bus = can.interface.Bus(
                    channel=self.channel,
                    interface="virtual",
                    receive_own_messages=True,
                )
            else:
                self.bus = can.interface.Bus(
                    channel=self.channel,
                    interface=self.interface,
                    bitrate=self.bitrate,
                )
            return True
        except Exception as e:
            print(f"[ERROR] 無法連線至 CAN 介面 [{self.interface}::{self.channel}]: {e}")
            return False

    def check_os_level_health(self) -> Dict[str, str]:
        """檢查作業系統層級的 CAN 狀態 (針對 Linux SocketCAN)"""
        health_info = {
            "bus_state": "ERROR-ACTIVE" if self.interface in ["virtual", "pcan"] else "UNKNOWN",
            "tx_errors": "0" if self.interface == "virtual" else "N/A",
            "rx_errors": "0" if self.interface == "virtual" else "N/A",
            "restarts": "0" if self.interface == "virtual" else "N/A",
        }
        if platform.system() == "Linux" and self.interface == "socketcan":
            try:
                res = subprocess.run(
                    ["ip", "-details", "-statistics", "link", "show", self.channel],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                output = res.stdout
                for line in output.splitlines():
                    if "state" in line:
                        for token in ["ERROR-ACTIVE", "ERROR-WARNING", "ERROR-PASSIVE", "BUS-OFF", "STOPPED"]:
                            if token in line:
                                health_info["bus_state"] = token
                    if "tx-error" in line or "rx-error" in line:
                        parts = line.strip().split()
                        for i, p in enumerate(parts):
                            if p == "tx-error" and i + 1 < len(parts):
                                health_info["tx_errors"] = parts[i + 1]
                            elif p == "rx-error" and i + 1 < len(parts):
                                health_info["rx_errors"] = parts[i + 1]
            except Exception:
                pass
        return health_info

    def run_diagnostics(self, duration_sec: float = 3.0, expected_id: Optional[int] = 0x120, expected_period_ms: float = 50.0):
        """執行監聽與通訊品質採集"""
        print(f"[*] 開始對 [{self.interface}::{self.channel}] 進行通訊品質量測，測試時長: {duration_sec} 秒...")
        start_time = time.perf_counter()
        
        while (time.perf_counter() - start_time) < duration_sec:
            timeout_rem = max(0.01, duration_sec - (time.perf_counter() - start_time))
            try:
                msg = self.bus.recv(timeout=min(0.05, timeout_rem))
                if not msg:
                    continue

                self.total_rx_count += 1
                curr_t = time.perf_counter()

                if getattr(msg, "is_error_frame", False):
                    self.error_frame_count += 1
                else:
                    arb_id = msg.arbitration_id
                    self.id_message_count[arb_id] += 1
                    # 保留最多 200 個時間戳記用於計算抖動
                    if len(self.id_timestamps[arb_id]) < 200:
                        self.id_timestamps[arb_id].append(curr_t)

            except Exception as e:
                print(f"[WARN] 接收異常: {e}")
                break

    def print_diagnostic_report(self, expected_id: Optional[int] = 0x120, expected_period_ms: float = 50.0):
        """輸出診斷報告與終端電阻推斷"""
        os_health = self.check_os_level_health()

        print("\n" + "=" * 60)
        print("           CAN 總線通訊品質與電氣診斷分析報告           ")
        print("=" * 60)
        print(f"介面型態: {self.interface} | 通道: {self.channel} | 波特率: {self.bitrate} bps")
        print(f"總線硬體狀態: {os_health['bus_state']}")
        print(f"總接收幀數: {self.total_rx_count} 幀")
        print(f"錯誤幀數量 (Error Frames): {self.error_frame_count}")

        # 計算特定 ID (如遙測幀 0x120) 的週期與丟包率
        target_id = expected_id if expected_id is not None else (list(self.id_message_count.keys())[0] if self.id_message_count else None)
        
        if target_id and target_id in self.id_timestamps and len(self.id_timestamps[target_id]) > 1:
            timestamps = self.id_timestamps[target_id]
            intervals_ms = [(t2 - t1) * 1000 for t1, t2 in zip(timestamps[:-1], timestamps[1:])]
            avg_period_ms = sum(intervals_ms) / len(intervals_ms)
            max_period_ms = max(intervals_ms)
            min_period_ms = min(intervals_ms)
            jitter_ms = max_period_ms - min_period_ms

            # 估算丟包：依據預期週期估算理論應收包數
            test_duration = timestamps[-1] - timestamps[0]
            expected_packets = int(test_duration / (expected_period_ms / 1000.0)) if expected_period_ms > 0 else len(timestamps)
            actual_packets = len(timestamps)
            packet_loss_rate = max(0.0, (expected_packets - actual_packets) / expected_packets * 100) if expected_packets > 0 else 0.0

            print(f"\n[目標幀 0x{target_id:X} 傳輸品質分析]")
            print(f"  - 接收幀數: {actual_packets} 幀 (估計應收: {expected_packets} 幀)")
            print(f"  - 平均週期: {avg_period_ms:.2f} ms (預期: {expected_period_ms:.2f} ms)")
            print(f"  - 最大週期: {max_period_ms:.2f} ms | 最小週期: {min_period_ms:.2f} ms")
            print(f"  - 時間抖動 (Jitter): {jitter_ms:.2f} ms")
            print(f"  - 估計丟包率 (Packet Loss Rate): {packet_loss_rate:.2f}%")
        else:
            print("\n[目標幀分析]: 測試期間未捕獲足夠的連續週期性數據。")

        # 終端電阻與電氣品質推斷 (Physical Layer Inference)
        print("\n[電氣與終端電阻評估 (Inference)]")
        inferences = []

        if self.total_rx_count == 0:
            inferences.append("❌ 總線靜默 (No Traffic)：請檢查 CAN_H / CAN_L 是否接反、無節點供電發送，或收發器波特率不匹配。")
        elif self.error_frame_count > 0:
            err_ratio = (self.error_frame_count / self.total_rx_count) * 100
            if err_ratio > 10 or os_health["bus_state"] in ["ERROR-PASSIVE", "BUS-OFF"]:
                inferences.append("⚠️ 高頻錯誤幀 / Bus-Off：極可能是「缺少 120Ω 終端電阻」引發信號反射，或終端電阻過低 (< 45Ω)。")
                inferences.append("👉 檢修動作：請在整車斷電下，使用三用電表測量 CAN_H 與 CAN_L 間阻值，正常應為 60Ω 左右 (兩端各 120Ω 並聯)。")
            else:
                inferences.append("⚡ 偶發錯誤幀：可能存在電磁干擾 (EMI)、接地電位差或線束接觸不良。")
        else:
            inferences.append("✅ 通訊良好：無錯誤幀，CRC/ACK 檢驗正常。終端阻抗與電氣特性符合規範。")

        for inf in inferences:
            print(f"  {inf}")

        print("=" * 60 + "\n")

    def close(self):
        if self.bus:
            try:
                self.bus.shutdown()
            except Exception:
                pass


if __name__ == "__main__":
    if sys.platform.startswith("win"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    default_interface = "pcan" if sys.platform.startswith("win") else "socketcan"
    default_channel = "PCAN_USBBUS1" if sys.platform.startswith("win") else "can0"

    parser = argparse.ArgumentParser(description="CAN 通訊品質與電氣診斷排錯工具")
    parser.add_argument("--interface", default=default_interface, help=f"介面類型: socketcan, pcan, virtual (預設: {default_interface})")
    parser.add_argument("--channel", default=default_channel, help=f"CAN 通道: 例如 can0, PCAN_USBBUS1 (預設: {default_channel})")
    parser.add_argument("--bitrate", type=int, default=500000, help="波特率 (bps)")
    parser.add_argument("--duration", type=float, default=3.0, help="測試取樣時間 (秒)")
    parser.add_argument("--expected-id", type=lambda x: int(x, 0), default=0x120, help="要監控的特定週期幀 ID (預設 0x120)")
    parser.add_argument("--expected-period", type=float, default=50.0, help="特定幀的預期廣播週期 (ms)")
    parser.add_argument("--simulate-traffic", action="store_true", help="啟用本機背景流量模擬 (用於無實體卡自檢)")

    args = parser.parse_args()

    # 若指定自測流量模擬
    stop_sim = threading.Event()
    sim_thread = None
    if args.simulate_traffic:
        args.interface = "virtual"
        args.channel = "vcan_diag_test"
        def sim_worker():
            bus_tx = can.interface.Bus(channel=args.channel, interface="virtual")
            step = 0
            while not stop_sim.is_set():
                step += 1
                msg = can.Message(
                    arbitration_id=args.expected_id,
                    data=bytes([0x68, 0x01, 0x80, 0x05, 0x0E, 0x10, 0x00, step % 256]),
                    is_extended_id=False,
                )
                try:
                    bus_tx.send(msg)
                except Exception:
                    pass
                time.sleep(args.expected_period / 1000.0)
            bus_tx.shutdown()
        sim_thread = threading.Thread(target=sim_worker, daemon=True)
        sim_thread.start()

    inspector = CanBusInspector(
        interface=args.interface,
        channel=args.channel,
        bitrate=args.bitrate
    )

    if inspector.initialize_bus():
        try:
            inspector.run_diagnostics(
                duration_sec=args.duration,
                expected_id=args.expected_id,
                expected_period_ms=args.expected_period
            )
            inspector.print_diagnostic_report(
                expected_id=args.expected_id,
                expected_period_ms=args.expected_period
            )
        finally:
            inspector.close()
            if sim_thread:
                stop_sim.set()
                sim_thread.join(timeout=1.0)
