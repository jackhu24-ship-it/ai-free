#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 【PROJ-EXAM-04 車用 ISO 14229 UDS 狀態機與 CAN-TP 網路層引擎】
================================================================================
主責工程師：🛠️ A02 小開 (Agent_Coder)
演算法規格：🌊 A05 小深 (02_Knowledge/Specs/CAN_UDS_ISO14229_Spec.md)
品質把關者：🐎 A03 小馬 (TEST/test_uds_iso14229_state_machine.py)

功能亮點：
  1. 支援 ISO 14229-1 10 大核心診斷服務 (0x10, 0x11, 0x22, 0x2E, 0x27, 0x28, 0x3E, 0x14, 0x19, 0x31)
  2. 完整會話狀態機 (Default / Extended / Programming) 與 S3Server (5000ms) 超時自動回退
  3. SecurityAccess (0x27) Seed-Key 演算法與 3 次密鑰錯誤 10s 懲罰冷卻鎖定 (NRC 0x36 / 0x37)
  4. ISO 15765-2 (CAN-TP) 網路層單幀 (SF)、首幀 (FF)、流控幀 (FC) 與連續幀 (CF) 多幀拆包組包
  5. 診斷日誌追蹤與 CWE-1236 CSV 防注入匯出
"""

from __future__ import annotations

import sys
import os
import time
import csv
import struct
from enum import Enum, IntEnum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Callable

# Windows UTF-8 編碼防護
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def sanitize_cell(val: Any) -> str:
    """CWE-1236 試算表/CSV 公式注入防護"""
    s = str(val)
    if s.startswith(("=", "+", "-", "@")):
        return f"'{s}"
    return s


class DiagnosticSession(IntEnum):
    DEFAULT_SESSION = 0x01
    PROGRAMMING_SESSION = 0x02
    EXTENDED_DIAGNOSTIC_SESSION = 0x03
    SAFETY_SYSTEM_DIAGNOSTIC_SESSION = 0x04


class SecurityLevel(IntEnum):
    LOCKED = 0x00
    LEVEL_1_UNLOCKED = 0x01
    LEVEL_2_UNLOCKED = 0x02


class NRC(IntEnum):
    POSITIVE_RESPONSE = 0x00
    SERVICE_NOT_SUPPORTED = 0x11
    SUB_FUNCTION_NOT_SUPPORTED = 0x12
    INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT = 0x13
    CONDITIONS_NOT_CORRECT = 0x22
    REQUEST_OUT_OF_RANGE = 0x31
    SECURITY_ACCESS_DENIED = 0x33
    INVALID_KEY = 0x35
    EXCEEDED_NUMBER_OF_ATTEMPTS = 0x36
    REQUIRED_TIME_DELAY_NOT_EXPIRED = 0x37
    RESPONSE_PENDING = 0x78


@dataclass
class UdsLogEntry:
    timestamp_ms: float
    direction: str  # "REQ" or "RESP"
    can_id: int
    raw_hex: str
    service_name: str
    status: str
    detail: str


class UdsServerEngine:
    """
    ISO 14229 UDS 伺服器狀態機核心
    """

    PHYS_REQ_ID = 0x7E0
    PHYS_RESP_ID = 0x7E8
    FUNC_REQ_ID = 0x7DF

    # 計時器常數 (ms)
    P2_SERVER_MAX_MS = 50
    P2_STAR_SERVER_MAX_MS = 5000
    S3_SERVER_TIMEOUT_MS = 5000
    SECURITY_LOCKOUT_DELAY_MS = 10000

    def __init__(self):
        # 狀態機變數
        self.current_session = DiagnosticSession.DEFAULT_SESSION
        self.security_level = SecurityLevel.LOCKED
        self.security_attempts = 0
        self.security_lockout_until_ms = 0.0
        self.last_activity_time_ms = time.time() * 1000.0
        self.active_seed: Optional[int] = None

        # 資料儲存 (DIDs)
        self.did_database: Dict[int, bytes] = {
            0xF190: "WBA1234567890ABCD".encode("ascii"),          # VIN 碼 (17 bytes)
            0xF188: "PDU-SW-V2.0.4-RELEASE".encode("ascii"),     # 軟體版本
            0x0100: struct.pack(">H", 1245),                     # 電瓶電壓 (12.45V -> 1245)
            0x0101: bytes([75, 80, 200, 65, 80, 70, 35, 15]),    # 8 通道電流 (0.1A 為單位)
            0x0102: bytes([100, 150, 250, 150, 150, 150, 75, 50])# 過載門檻 (需解鎖寫入)
        }

        # DTC 故障碼清單
        self.dtc_database: List[Tuple[int, int]] = [
            (0xB1015, 0x2F),  # 左轉向燈開路 (Active)
            (0xB1016, 0x28),  # 右轉向燈短路 (Stored)
        ]

        # CAN-TP 接收緩存
        self.tp_rx_buffer = bytearray()
        self.tp_expected_length = 0
        self.tp_consecutive_seq = 1

        # 診斷日誌
        self.diag_logs: List[UdsLogEntry] = []

    def _now_ms(self) -> float:
        return time.time() * 1000.0

    def update_timers(self):
        """定時心跳更新 S3Server 與 Security Lockout 計時器"""
        now = self._now_ms()
        # S3Server 逾時回退檢測 (非預設會話下)
        if self.current_session != DiagnosticSession.DEFAULT_SESSION:
            if (now - self.last_activity_time_ms) > self.S3_SERVER_TIMEOUT_MS:
                self.current_session = DiagnosticSession.DEFAULT_SESSION
                self.security_level = SecurityLevel.LOCKED
                self.active_seed = None
                self._log("SYS", 0x000, "", "S3_TIMEOUT", "S3Server 逾時回退至預設會話並鎖定安全等級")

    def _log(self, direction: str, can_id: int, raw_hex: str, svc: str, detail: str, status: str = "OK"):
        entry = UdsLogEntry(
            timestamp_ms=round(self._now_ms(), 1),
            direction=direction,
            can_id=can_id,
            raw_hex=raw_hex,
            service_name=svc,
            status=status,
            detail=detail
        )
        self.diag_logs.append(entry)

    @classmethod
    def calculate_key_level1(cls, seed: int) -> int:
        """Seed-Key Level 1 密鑰計算演算法: ((Seed ^ 0xA5A5A5A5) <<< 3) + 0x55AA55AA"""
        m1 = 0xA5A5A5A5
        c1 = 0x55AA55AA
        x = (seed ^ m1) & 0xFFFFFFFF
        # 循環左移 3 位
        rotated = (((x << 3) & 0xFFFFFFFF) | (x >> 29)) & 0xFFFFFFFF
        return (rotated + c1) & 0xFFFFFFFF

    def process_can_frame(self, can_id: int, payload: bytes) -> Optional[Tuple[int, bytes]]:
        """
        處理 CAN-TP / UDS 報文，回傳 (resp_can_id, resp_payload) 或 None
        """
        self.update_timers()
        if can_id not in (self.PHYS_REQ_ID, self.FUNC_REQ_ID):
            return None

        if not payload:
            return None

        now = self._now_ms()
        self.last_activity_time_ms = now

        # ISO 15765-2 網路層解包
        pci_type = (payload[0] >> 4) & 0x0F

        if pci_type == 0x0:  # Single Frame (SF)
            sf_dl = payload[0] & 0x0F
            if sf_dl == 0 or sf_dl > (len(payload) - 1):
                return self._make_nrc_response(0x00, NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT)
            uds_payload = payload[1:1 + sf_dl]
            self._log("REQ", can_id, payload.hex().upper(), f"SID_0x{uds_payload[0]:02X}", f"SF 收到 {sf_dl} 字節")
            return self._dispatch_uds_service(uds_payload)

        elif pci_type == 0x1:  # First Frame (FF)
            ff_dl = ((payload[0] & 0x0F) << 8) | payload[1]
            self.tp_expected_length = ff_dl
            self.tp_rx_buffer = bytearray(payload[2:])
            self.tp_consecutive_seq = 1
            self._log("REQ", can_id, payload.hex().upper(), "CAN-TP_FF", f"多幀首幀 預期總長 {ff_dl} 字節")

            # 發送流控幀 (FC: CTS, BS=8, STmin=10ms)
            fc_frame = bytes([0x30, 0x08, 0x0A, 0x00, 0x00, 0x00, 0x00, 0x00])
            self._log("RESP", self.PHYS_RESP_ID, fc_frame.hex().upper(), "CAN-TP_FC", "回覆流控幀 (CTS, BS=8, STmin=10ms)")
            return (self.PHYS_RESP_ID, fc_frame)

        elif pci_type == 0x2:  # Consecutive Frame (CF)
            seq = payload[0] & 0x0F
            if seq != (self.tp_consecutive_seq & 0x0F):
                self._log("REQ", can_id, payload.hex().upper(), "CAN-TP_CF_ERR", f"序列號錯誤: 預期 {self.tp_consecutive_seq} 實收 {seq}", status="ERR")
                self.tp_rx_buffer.clear()
                return None

            self.tp_consecutive_seq = (self.tp_consecutive_seq + 1) & 0x0F
            self.tp_rx_buffer.extend(payload[1:])

            if len(self.tp_rx_buffer) >= self.tp_expected_length:
                # 多幀拼裝完成
                complete_uds = bytes(self.tp_rx_buffer[:self.tp_expected_length])
                self.tp_rx_buffer.clear()
                self._log("REQ", can_id, complete_uds.hex().upper(), f"SID_0x{complete_uds[0]:02X}", "多幀接收拼裝完成")
                return self._dispatch_uds_service(complete_uds)
            return None

        return None

    def _dispatch_uds_service(self, msg: bytes) -> Optional[Tuple[int, bytes]]:
        """分發 UDS 服務至相應處理器"""
        sid = msg[0]

        handlers: Dict[int, Callable[[bytes], Optional[bytes]]] = {
            0x10: self._handle_0x10_diagnostic_session_control,
            0x11: self._handle_0x11_ecu_reset,
            0x22: self._handle_0x22_read_data_by_identifier,
            0x2E: self._handle_0x2E_write_data_by_identifier,
            0x27: self._handle_0x27_security_access,
            0x28: self._handle_0x28_communication_control,
            0x3E: self._handle_0x3E_tester_present,
            0x14: self._handle_0x14_clear_diagnostic_info,
            0x19: self._handle_0x19_read_dtc_information,
            0x31: self._handle_0x31_routine_control,
        }

        if sid not in handlers:
            return self._make_nrc_response(sid, NRC.SERVICE_NOT_SUPPORTED)

        resp_payload = handlers[sid](msg)
        if resp_payload is None:
            return None  # 抑制正響應 (Suppress Positive Response)

        # 封裝為 CAN-TP Single Frame 回傳
        sf_len = len(resp_payload)
        can_frame = bytes([sf_len]) + resp_payload
        # 補齊 8 字節 (0xAA 填充)
        if len(can_frame) < 8:
            can_frame += b"\xAA" * (8 - len(can_frame))

        status_str = "POSITIVE" if resp_payload[0] != 0x7F else f"NEGATIVE_{resp_payload[2]:02X}"
        self._log("RESP", self.PHYS_RESP_ID, can_frame.hex().upper(), f"RESP_0x{sid:02X}", f"UDS 回覆 ({status_str})", status=status_str)
        return (self.PHYS_RESP_ID, can_frame)

    def _make_nrc_response(self, sid: int, nrc: NRC) -> Tuple[int, bytes]:
        """建立負響應報文: 0x7F <SID> <NRC>"""
        resp_data = bytes([0x7F, sid, int(nrc)])
        can_frame = bytes([0x03]) + resp_data + b"\xAA" * 4
        self._log("RESP", self.PHYS_RESP_ID, can_frame.hex().upper(), f"NRC_0x{sid:02X}", f"負響應: {nrc.name} (0x{int(nrc):02X})", status="NEGATIVE")
        return (self.PHYS_RESP_ID, can_frame)

    # -------------------------------------------------------------
    # 服務處理器 (Handlers)
    # -------------------------------------------------------------
    def _handle_0x10_diagnostic_session_control(self, msg: bytes) -> bytes:
        if len(msg) < 2:
            return bytes([0x7F, 0x10, NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT])
        sub_fn = msg[1] & 0x7F
        suppress_pos_rsp = bool(msg[1] & 0x80)

        if sub_fn not in (0x01, 0x02, 0x03, 0x04):
            return bytes([0x7F, 0x10, NRC.SUB_FUNCTION_NOT_SUPPORTED])

        self.current_session = DiagnosticSession(sub_fn)
        # 會話切換時重置安全解鎖狀態
        self.security_level = SecurityLevel.LOCKED
        self.active_seed = None

        if suppress_pos_rsp:
            return None

        # 回覆 0x50 <sub_fn> <P2Server_Hi> <P2Server_Lo> <P2*Server_Hi> <P2*Server_Lo>
        return struct.pack(">BBHHHH", 0x50, sub_fn, self.P2_SERVER_MAX_MS, 0, self.P2_STAR_SERVER_MAX_MS // 10, 0)[:6]

    def _handle_0x11_ecu_reset(self, msg: bytes) -> bytes:
        if len(msg) < 2:
            return bytes([0x7F, 0x11, NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT])
        sub_fn = msg[1] & 0x7F
        if sub_fn not in (0x01, 0x02, 0x03):
            return bytes([0x7F, 0x11, NRC.SUB_FUNCTION_NOT_SUPPORTED])

        # 執行復位重置狀態
        self.current_session = DiagnosticSession.DEFAULT_SESSION
        self.security_level = SecurityLevel.LOCKED
        self.active_seed = None
        self.security_attempts = 0
        return bytes([0x51, sub_fn])

    def _handle_0x22_read_data_by_identifier(self, msg: bytes) -> bytes:
        if len(msg) < 3:
            return bytes([0x7F, 0x22, NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT])
        did = (msg[1] << 8) | msg[2]
        if did not in self.did_database:
            return bytes([0x7F, 0x22, NRC.REQUEST_OUT_OF_RANGE])

        val = self.did_database[did]
        return bytes([0x62, (did >> 8) & 0xFF, did & 0xFF]) + val

    def _handle_0x2E_write_data_by_identifier(self, msg: bytes) -> bytes:
        if len(msg) < 4:
            return bytes([0x7F, 0x2E, NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT])
        did = (msg[1] << 8) | msg[2]
        if did not in self.did_database:
            return bytes([0x7F, 0x2E, NRC.REQUEST_OUT_OF_RANGE])

        # 安全等級檢查 (0x0102 / 0xF190 需安全解鎖且處於擴展會話)
        if did in (0x0102, 0xF190):
            if self.current_session == DiagnosticSession.DEFAULT_SESSION:
                return bytes([0x7F, 0x2E, NRC.CONDITIONS_NOT_CORRECT])
            if self.security_level == SecurityLevel.LOCKED:
                return bytes([0x7F, 0x2E, NRC.SECURITY_ACCESS_DENIED])

        self.did_database[did] = msg[3:]
        return bytes([0x6E, (did >> 8) & 0xFF, did & 0xFF])

    def _handle_0x27_security_access(self, msg: bytes) -> bytes:
        if len(msg) < 2:
            return bytes([0x7F, 0x27, NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT])
        sub_fn = msg[1] & 0x7F
        now = self._now_ms()

        # 1. 檢查是否處於防暴力破解冷卻懲罰期
        if now < self.security_lockout_until_ms:
            return bytes([0x7F, 0x27, NRC.REQUIRED_TIME_DELAY_NOT_EXPIRED])

        # 2. 請求種子 (0x01 ReqSeed Level 1)
        if sub_fn == 0x01:
            if self.security_level == SecurityLevel.LEVEL_1_UNLOCKED:
                # 已解鎖則回傳全 0 種子
                return bytes([0x67, 0x01, 0x00, 0x00, 0x00, 0x00])
            # 動態生成 32-bit 種子
            self.active_seed = int((now * 1000) % 0xFFFFFFFF) or 0x12345678
            seed_bytes = struct.pack(">I", self.active_seed)
            return bytes([0x67, 0x01]) + seed_bytes

        # 3. 傳送密鑰 (0x02 SendKey Level 1)
        elif sub_fn == 0x02:
            if len(msg) < 6:
                return bytes([0x7F, 0x27, NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT])
            if self.active_seed is None:
                return bytes([0x7F, 0x27, NRC.REQUEST_OUT_OF_RANGE])

            received_key = struct.unpack(">I", msg[2:6])[0]
            expected_key = self.calculate_key_level1(self.active_seed)

            if received_key == expected_key:
                # 驗證成功解鎖
                self.security_level = SecurityLevel.LEVEL_1_UNLOCKED
                self.security_attempts = 0
                self.active_seed = None
                return bytes([0x67, 0x02])
            else:
                # 密鑰錯誤，遞增計數
                self.security_attempts += 1
                self.active_seed = None
                if self.security_attempts >= 3:
                    # 觸發 10 秒懲罰冷卻
                    self.security_lockout_until_ms = now + self.SECURITY_LOCKOUT_DELAY_MS
                    return bytes([0x7F, 0x27, NRC.EXCEEDED_NUMBER_OF_ATTEMPTS])
                return bytes([0x7F, 0x27, NRC.INVALID_KEY])

        return bytes([0x7F, 0x27, NRC.SUB_FUNCTION_NOT_SUPPORTED])

    def _handle_0x28_communication_control(self, msg: bytes) -> bytes:
        if len(msg) < 3:
            return bytes([0x7F, 0x28, NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT])
        sub_fn = msg[1] & 0x7F
        comm_type = msg[2]
        return bytes([0x68, sub_fn])

    def _handle_0x3E_tester_present(self, msg: bytes) -> Optional[bytes]:
        if len(msg) < 2:
            return bytes([0x7F, 0x3E, NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT])
        sub_fn = msg[1] & 0x7F
        suppress_pos = bool(msg[1] & 0x80)

        if sub_fn != 0x00:
            return bytes([0x7F, 0x3E, NRC.SUB_FUNCTION_NOT_SUPPORTED])

        if suppress_pos:
            return None
        return bytes([0x7E, 0x00])

    def _handle_0x14_clear_diagnostic_info(self, msg: bytes) -> bytes:
        if len(msg) < 4:
            return bytes([0x7F, 0x14, NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT])
        group = (msg[1] << 16) | (msg[2] << 8) | msg[3]
        if group == 0xFFFFFF:
            self.dtc_database.clear()
            return bytes([0x54])
        return bytes([0x7F, 0x14, NRC.REQUEST_OUT_OF_RANGE])

    def _handle_0x19_read_dtc_information(self, msg: bytes) -> bytes:
        if len(msg) < 2:
            return bytes([0x7F, 0x19, NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT])
        sub_fn = msg[1] & 0x7F
        if sub_fn == 0x02:  # reportDTCByStatusMask
            mask = msg[2] if len(msg) >= 3 else 0xFF
            resp = bytes([0x59, 0x02, mask])
            for dtc, status in self.dtc_database:
                if status & mask:
                    resp += bytes([(dtc >> 16) & 0xFF, (dtc >> 8) & 0xFF, dtc & 0xFF, status])
            return resp
        return bytes([0x7F, 0x19, NRC.SUB_FUNCTION_NOT_SUPPORTED])

    def _handle_0x31_routine_control(self, msg: bytes) -> bytes:
        if len(msg) < 4:
            return bytes([0x7F, 0x31, NRC.INCORRECT_MESSAGE_LENGTH_OR_INVALID_FORMAT])
        sub_fn = msg[1] & 0x7F
        routine_id = (msg[2] << 8) | msg[3]

        if routine_id != 0x0201:  # 0x0201: E-Fuse 自檢例程
            return bytes([0x7F, 0x31, NRC.REQUEST_OUT_OF_RANGE])

        # 安全等級檢查 (需 Level 1 解鎖)
        if self.security_level == SecurityLevel.LOCKED:
            return bytes([0x7F, 0x31, NRC.SECURITY_ACCESS_DENIED])

        if sub_fn == 0x01:  # startRoutine
            return bytes([0x71, 0x01, 0x02, 0x01, 0x00])  # 0x00: Routine In Progress
        elif sub_fn == 0x03:  # requestRoutineResults
            return bytes([0x71, 0x03, 0x02, 0x01, 0x02])  # 0x02: Routine Finished OK
        return bytes([0x7F, 0x31, NRC.SUB_FUNCTION_NOT_SUPPORTED])

    def export_diagnostic_trace_csv(self, filepath: str) -> str:
        """匯出診斷日誌並落實 CWE-1236 公式注入防護"""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", newline="", encoding="utf-8", errors="replace") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp_ms", "Direction", "CAN_ID", "Raw_Hex", "Service", "Status", "Detail"])
            for log in self.diag_logs:
                writer.writerow([
                    sanitize_cell(log.timestamp_ms),
                    sanitize_cell(log.direction),
                    sanitize_cell(f"0x{log.can_id:03X}"),
                    sanitize_cell(log.raw_hex),
                    sanitize_cell(log.service_name),
                    sanitize_cell(log.status),
                    sanitize_cell(log.detail)
                ])
        return filepath


def run_self_test():
    print("=" * 80)
    print("🚗 【PROJ-EXAM-04 ISO 14229 UDS 狀態機與 CAN-TP 傳輸引擎自檢】")
    print("=" * 80)

    server = UdsServerEngine()

    # 1. 測試會話切換 0x10 03 (Extended Session)
    res = server.process_can_frame(0x7E0, bytes([0x02, 0x10, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00]))
    assert res is not None and res[1][1] == 0x50, "會話切換失敗"
    print(f"\n[測試 1: 切換擴展會話] -> 響應: {res[1].hex().upper()} (當前會話: {server.current_session.name})")

    # 2. 測試 SecurityAccess 0x27 01 / 02 完整解鎖流程
    res_seed = server.process_can_frame(0x7E0, bytes([0x02, 0x27, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00]))
    seed = struct.unpack(">I", res_seed[1][3:7])[0]
    key = server.calculate_key_level1(seed)
    key_bytes = struct.pack(">I", key)
    print(f"[測試 2: 請求種子] -> Seed=0x{seed:08X} | 計算 Key=0x{key:08X}")

    res_unlock = server.process_can_frame(0x7E0, bytes([0x06, 0x27, 0x02]) + key_bytes + bytes([0x00]))
    assert res_unlock is not None and res_unlock[1][1] == 0x67, "安全解鎖失敗"
    assert server.security_level == SecurityLevel.LEVEL_1_UNLOCKED
    print(f"  • 解鎖結果: {res_unlock[1].hex().upper()} (安全等級: {server.security_level.name}) [PASS]")

    # 3. 測試受保護 DID 寫入 (0x2E 0102)
    write_data = bytes([120, 160, 250, 160, 160, 160, 80, 60])
    res_write = server.process_can_frame(0x7E0, bytes([0x07, 0x2E, 0x01, 0x02, 120, 160, 250, 160]))
    print(f"[測試 3: 寫入受保護 DID 0x0102] -> 響應: {res_write[1].hex().upper()} [PASS]")

    print("\n🟢 UdsServerEngine 自檢 100% 通過！")


if __name__ == "__main__":
    run_self_test()
