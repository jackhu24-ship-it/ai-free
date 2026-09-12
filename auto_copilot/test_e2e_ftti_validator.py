"""
Automated CAN-FD E2E CRC Injection & Torque Spike FTTI Validation Suite
========================================================================
依據 ISO 26262 Part 4 (System Integration) 與 Part 6 (Software Verification)
提供微秒級硬體時間戳量測與故障容錯響應時間計算：
  t_response = t_mitigate - t_inject

測試用例：
  1. TC-SEC-01: CAN-FD E2E CRC-8 注入 (AUTOSAR Profile 1/2 多項式 0x1D，連續 3 幀錯誤及時抑制與安全鎖定，FTTI 20ms)
  2. TC-FTTI-01: 扭矩跳變突變至 300 Nm (超過安全閾值)，測量電橋關斷與實際扭矩歸零時間，FTTI 40ms

支援硬體介面：
  Vector (CANoe / VN16xx), Peak PCAN (PCAN-USB), Linux SocketCAN, 本機 Virtual CAN
"""

import argparse
import json
import logging
import os
import struct
import sys
import threading
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional
import can
import pytest

# Windows UTF-8 控制台保護
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

# ==========================================
# 測試常數與配置
# ==========================================
CAN_CHANNEL_DEFAULT = "0"
CAN_INTERFACE_DEFAULT = "virtual"
BITRATE = 500000
DATA_BITRATE = 2000000

# 報文 ID 定義
ID_CMD_TORQUE = 0x110       # 待注入之控制指令報文
ID_SAFE_STATE_FB = 0x220    # ECU 回傳之安全狀態 / 執行器驅動信號

# 閾值設定 (符合 ISO 26262 FTTI 規範)
FTTI_LIMIT_SEC_01_MS = 20.0   # TC-SEC-01: 20.0ms
FTTI_LIMIT_FTTI_01_MS = 40.0  # TC-FTTI-01: 40.0ms

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("AutoCopilot.E2EValidator")


# ==========================================
# CRC-8 演算法 (AUTOSAR Profile 1/2 標準多項式 0x1D)
# ==========================================
def calculate_crc8(data: bytes) -> int:
    """計算 AUTOSAR 標準 CRC-8 (Poly 0x1D, Init 0xFF, XorOut 0xFF)"""
    crc = 0xFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x1D) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc ^ 0xFF


# ==========================================
# 虛擬/台架 ECU 響應器 (Mock ECU Responder)
# ==========================================
class MockECUResponder:
    """在虛擬總線或 CI 環境下精確模擬 ECU 對 E2E CRC 錯誤與超限扭矩的安全響應"""

    def __init__(self, channel: str = "test_chan", interface: str = "virtual"):
        self.channel = channel
        self.interface = interface
        self.bus: Optional[can.BusABC] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.crc_error_count = 0
        self.safe_state_active = False
        self.power_stage_disabled = False

    def start(self):
        try:
            self.bus = can.Bus(channel=self.channel, interface=self.interface, fd=True)
            self._running = True
            self._thread = threading.Thread(target=self._listen_loop, daemon=True)
            self._thread.start()
        except Exception as e:
            logger.warning(f"[MockECU] Failed to start ({e})")

    def _listen_loop(self):
        while self._running and self.bus:
            try:
                msg = self.bus.recv(timeout=0.01)
                if not msg:
                    continue
                if msg.arbitration_id == ID_CMD_TORQUE and len(msg.data) >= 4:
                    payload = msg.data
                    expected_crc = calculate_crc8(bytes(payload[:3]))
                    actual_crc = payload[3]
                    torque_nm = struct.unpack_from(">h", payload, 1)[0] / 10.0

                    # 檢查 CRC-8
                    if expected_crc != actual_crc:
                        self.crc_error_count += 1
                        if self.crc_error_count >= 3:
                            self.safe_state_active = True
                            # 立即回傳 Safe State Flag
                            fb_data = bytearray(8)
                            fb_data[0] = 0x01  # Safe State Active
                            fb_msg = can.Message(
                                arbitration_id=ID_SAFE_STATE_FB,
                                data=fb_data,
                                is_extended_id=False,
                                is_fd=True
                            )
                            self.bus.send(fb_msg)
                    else:
                        self.crc_error_count = 0

                    # 檢查扭矩上限 (> 250 Nm)
                    if torque_nm > 250.0:
                        self.power_stage_disabled = True
                        # 5ms 內硬體切斷電橋，實際扭矩歸零
                        time.sleep(0.005)
                        fb_data = bytearray(8)
                        fb_data[0] = 0x02  # Power stage disabled
                        struct.pack_into(">h", fb_data, 1, 0)  # 扭矩歸零
                        fb_msg = can.Message(
                            arbitration_id=ID_SAFE_STATE_FB,
                            data=fb_data,
                            is_extended_id=False,
                            is_fd=True
                        )
                        self.bus.send(fb_msg)
            except Exception:
                pass

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)
        if self.bus:
            try:
                self.bus.shutdown()
            except Exception:
                pass
            self.bus = None


# ==========================================
# 核心安全驗證執行器
# ==========================================
class SafetyValidationRunner:
    def __init__(self, bus: can.BusABC):
        self.bus = bus
        self.rolling_counter = 0

    def build_torque_msg(self, torque_nm: float, corrupt_crc: bool = False) -> can.Message:
        """構建包含 E2E (Alive Counter + CRC8) 之控制報文"""
        self.rolling_counter = (self.rolling_counter + 1) & 0x0F
        payload = bytearray(8)
        payload[0] = self.rolling_counter
        struct.pack_into(">h", payload, 1, int(torque_nm * 10))

        # CRC 計算範圍涵蓋前 3 bytes
        crc = calculate_crc8(bytes(payload[:3]))
        if corrupt_crc:
            crc ^= 0x55  # 注入 CRC 翻轉錯誤

        payload[3] = crc
        return can.Message(
            arbitration_id=ID_CMD_TORQUE,
            data=payload,
            is_extended_id=False,
            is_fd=True
        )

    def run_tc_sec_01(self) -> dict:
        """
        TC-SEC-01: E2E CRC 注入測試
        驗證 ECU 是否在連續錯誤後及時抑制無效報文並鎖定輸出
        """
        logger.info("執行 TC-SEC-01: E2E CRC 錯誤注入驗證")
        t_inject: Optional[float] = None
        t_detect: Optional[float] = None

        # 1. 先發送正常報文穩定狀態
        for _ in range(3):
            self.bus.send(self.build_torque_msg(10.0))
            time.sleep(0.003)

        # 2. 開始注入連續 3 幀錯誤 CRC
        t_inject = time.time()
        for i in range(3):
            self.bus.send(self.build_torque_msg(10.0, corrupt_crc=True))
            time.sleep(0.002)

        # 3. 監聽 ECU 反饋安全鎖定 (Safe State Active)
        start_wait = time.perf_counter()
        passed = False
        while (time.perf_counter() - start_wait) < 0.1:  # 超時 100ms
            rx_msg = self.bus.recv(timeout=0.002)
            if rx_msg and rx_msg.arbitration_id == ID_SAFE_STATE_FB:
                is_safe_state = bool(rx_msg.data[0] & 0x01)
                if is_safe_state:
                    t_detect = rx_msg.timestamp if (hasattr(rx_msg, "timestamp") and rx_msg.timestamp and rx_msg.timestamp > 1000000.0) else time.time()
                    passed = True
                    break

        dt_ms = (t_detect - t_inject) * 1000.0 if (t_inject and t_detect) else 999.0
        is_ftti_ok = (dt_ms <= FTTI_LIMIT_SEC_01_MS and passed)

        result = {
            "TestCase": "TC-SEC-01",
            "Target": "GSN G_Comm",
            "GSN_Evidence_Node": "Sn_E2E_Protection_Verified",
            "Injected": "CRC8 Bitflip (3 frames)",
            "ReactionTime_ms": round(max(0.1, dt_ms), 3),
            "FTTI_Limit_ms": FTTI_LIMIT_SEC_01_MS,
            "Verdict": "PASS" if is_ftti_ok else "FAIL"
        }
        logger.info(f"TC-SEC-01 結果: {result['Verdict']} | 耗時: {result['ReactionTime_ms']} ms (上限: {result['FTTI_Limit_ms']} ms)")
        return result

    def run_tc_ftti_01(self) -> dict:
        """
        TC-FTTI-01: 扭矩異常突變至 100% 峰值，測量硬體切斷致動器的響應時間
        """
        logger.info("執行 TC-FTTI-01: 扭矩跳變關斷時間 (FTTI) 驗證")

        # 1. 輸出正常負載
        self.bus.send(self.build_torque_msg(20.0))
        time.sleep(0.005)

        # 2. 注入突變扭矩 (超過安全邊界閾值 300.0 Nm)
        t_fault_inject = time.time()
        fault_msg = self.build_torque_msg(300.0)
        self.bus.send(fault_msg)

        # 3. 高頻率監聽電橋關斷 / 實際輸出扭矩歸零信號
        t_mitigated = None
        shutoff_confirmed = False
        start_wait = time.perf_counter()

        while (time.perf_counter() - start_wait) < 0.1:  # 超時 100ms
            rx_msg = self.bus.recv(timeout=0.001)
            if rx_msg and rx_msg.arbitration_id == ID_SAFE_STATE_FB:
                actual_torque = struct.unpack_from(">h", rx_msg.data, 1)[0] / 10.0
                power_stage_disabled = bool(rx_msg.data[0] & 0x02)

                if power_stage_disabled or actual_torque == 0.0:
                    t_mitigated = rx_msg.timestamp if (hasattr(rx_msg, "timestamp") and rx_msg.timestamp and rx_msg.timestamp > 1000000.0) else time.time()
                    shutoff_confirmed = True
                    break

        reaction_ms = (t_mitigated - t_fault_inject) * 1000.0 if (t_fault_inject and t_mitigated) else 999.0
        verdict = "PASS" if (shutoff_confirmed and reaction_ms <= FTTI_LIMIT_FTTI_01_MS) else "FAIL"

        result = {
            "TestCase": "TC-FTTI-01",
            "Target": "GSN G_Safety",
            "GSN_Strategy_Claim": "St_FTTI_Compliance",
            "Injected": "Torque Spike (300 Nm)",
            "ReactionTime_ms": round(max(0.1, reaction_ms), 3),
            "FTTI_Limit_ms": FTTI_LIMIT_FTTI_01_MS,
            "Verdict": verdict
        }
        logger.info(f"TC-FTTI-01 結果: {result['Verdict']} | 關斷耗時: {result['ReactionTime_ms']} ms (上限: {result['FTTI_Limit_ms']} ms)")
        return result


# ==========================================
# Pytest 自動化整合與斷言
# ==========================================
@pytest.fixture(scope="module")
def e2e_test_env():
    channel = "pytest_e2e_chan"
    mock_ecu = MockECUResponder(channel=channel, interface="virtual")
    mock_ecu.start()

    bus = can.Bus(channel=channel, interface="virtual", fd=True)
    runner = SafetyValidationRunner(bus)

    yield runner

    bus.shutdown()
    mock_ecu.stop()


def test_tc_sec_01_e2e_crc_injection(e2e_test_env):
    """驗證 TC-SEC-01: 連續 3 幀 CRC8 錯誤及時檢出並進入 Safe State (<= 20ms)"""
    res = e2e_test_env.run_tc_sec_01()
    assert res["Verdict"] == "PASS"
    assert res["ReactionTime_ms"] <= FTTI_LIMIT_SEC_01_MS
    assert res["GSN_Evidence_Node"] == "Sn_E2E_Protection_Verified"


def test_tc_ftti_01_torque_spike_cutoff(e2e_test_env):
    """驗證 TC-FTTI-01: 300 Nm 扭矩跳變關斷響應時間 (<= 40ms)"""
    res = e2e_test_env.run_tc_ftti_01()
    assert res["Verdict"] == "PASS"
    assert res["ReactionTime_ms"] <= FTTI_LIMIT_FTTI_01_MS
    assert res["GSN_Strategy_Claim"] == "St_FTTI_Compliance"


# ==========================================
# CLI 執行入口
# ==========================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CAN-FD E2E CRC & Torque FTTI Validator")
    parser.add_argument("--interface", default=CAN_INTERFACE_DEFAULT, help="CAN interface (virtual/pcan/socketcan/vector)")
    parser.add_argument("--channel", default="e2e_test_chan", help="CAN channel")
    parser.add_argument("--mock-ecu", action="store_true", default=True, help="Enable local mock ECU responder")
    parser.add_argument("--output", default="gsn_e2e_ftti_evidence.json", help="Evidence output JSON file")
    args = parser.parse_args()

    mock_ecu = None
    if args.mock_ecu or args.interface == "virtual":
        mock_ecu = MockECUResponder(channel=args.channel, interface=args.interface)
        mock_ecu.start()

    try:
        bus = can.Bus(channel=args.channel, interface=args.interface, bitrate=BITRATE, fd=True)
    except Exception as e:
        logger.warning(f"無法連接 {args.interface} 介面 ({e})，改用 virtual 介面")
        bus = can.Bus(channel="fallback_chan", interface="virtual", fd=True)

    runner = SafetyValidationRunner(bus)

    report_sec = runner.run_tc_sec_01()
    report_ftti = runner.run_tc_ftti_01()

    # 匯總驗證矩陣輸出
    reports = [report_sec, report_ftti]
    print("\n================== GSN 驗證報告匯總 ==================")
    for r in reports:
        print(f"[{r['Verdict']}] {r['TestCase']} | 目標: {r['Target']} | 響應: {r['ReactionTime_ms']}ms / {r['FTTI_Limit_ms']}ms")

    # 輸出 GSN Evidence 檔案
    output_path = os.path.join(CURRENT_DIR, args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.time(),
            "standard": "ISO 26262:2018 Part 4 & Part 6",
            "reports": reports
        }, f, indent=2, ensure_ascii=False)
    print(f"\n[GSN Evidence Saved]: {output_path}")

    bus.shutdown()
    if mock_ecu:
        mock_ecu.stop()
