#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 【CAN 報文監聽器與 PIC18F25K80 ECAN 暫存器計算器】：can_sniffer_ecan_calculator.py
================================================================================================
角色分工：
  - 🛠️ 小開 (Agent_Coder)   : PIC18F25K80 ECAN 暫存器數學模型、CAN 報文產生器與解碼器
  - 👁️ 小Ｏ (Agent_Vision)  : 終端黑底矩陣綠字 (#0D1117/#00FF66) 渲染排版與十進制 HUD
  - 🐎 小馬 (Agent_Reviewer): 鮑率容錯度審計、CWE-1236 注入過濾、十進位優先 (Decimal-First) 規範審查
  - 👑 小幫手 (Agent_PM)    : 雙向反應式聯動整合

技術規範：
  1. 【PIC18F25K80 ECAN 暫存器計算】：
     - MCU 主頻 Fosc = 64 MHz, Nominal Bit Time NBT = 16 TQ (Sample Point = 75%)
     - TQ = 2 * (BRP + 1) / Fosc
     - BRGCON1: SJW & BRP 鮑率預分頻
     - BRGCON2: PropSeg (4TQ) & PhaseSeg1 (7TQ)
     - BRGCON3: PhaseSeg2 (4TQ)
  2. 【即時 CAN 報文監聽器 (CAN Raw Frame Sniffer)】：
     - 格式化展示：[RX] TIMESTAMP | ID: 0x7E0 (2016) | DLC: 8 | DATA: ... (繁中語意)
     - 十進位優先 (Decimal-First) 與 Hex/Bin 雙向對照
"""

from __future__ import annotations

import sys
import os

# Windows UTF-8 編碼防護
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import time
import random
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple


def sanitize_cell(val: Any) -> str:
    """CWE-1236 試算表公式注入防護"""
    s_val = str(val)
    if s_val.startswith(("=", "+", "-", "@")):
        return f"'{s_val}"
    return s_val


# ============================================================================
# 模組一：PIC18F25K80 ECAN 暫存器計算器 (Decimal-First)
# ============================================================================

@dataclass
class ECANRegisterConfig:
    baud_rate_kbps: float
    brgcon1_val: int
    brgcon2_val: int
    brgcon3_val: int
    sjw_tq: int
    brp_val: int
    prop_seg_tq: int
    phase_seg1_tq: int
    phase_seg2_tq: int
    sample_point_pct: float

    def format_decimal_first(self) -> Dict[str, str]:
        """產生十進位優先 (Decimal-First) 暫存器對照字串"""
        return {
            "BRGCON1": f"BRGCON1: {self.brgcon1_val} (十進制) | 0x{self.brgcon1_val:02X} (0b{self.brgcon1_val:08b}) [SJW:{self.sjw_tq}TQ, BRP:{self.brp_val+1}]",
            "BRGCON2": f"BRGCON2: {self.brgcon2_val} (十進制) | 0x{self.brgcon2_val:02X} (0b{self.brgcon2_val:08b}) [Prop:{self.prop_seg_tq}TQ, Phase1:{self.phase_seg1_tq}TQ]",
            "BRGCON3": f"BRGCON3: {self.brgcon3_val} (十進制) | 0x{self.brgcon3_val:02X} (0b{self.brgcon3_val:08b}) [Phase2:{self.phase_seg2_tq}TQ, Sample:{self.sample_point_pct:.1f}%]"
        }


class ECANBaudCalculator:
    """
    PIC18F25K80 ECAN 鮑率暫存器精確計算引擎 (Fosc = 64MHz)
    """
    F_OSC_HZ = 64_000_000  # 64 MHz 晶振 (4x PLL)
    NOMINAL_BIT_TIME_TQ = 16  # 16 TQ / bit

    @classmethod
    def calculate(cls, baud_rate_kbps: float) -> ECANRegisterConfig:
        """
        根據輸入鮑率 (kbps) 計算 PIC18F25K80 暫存器配置
        支援: 125, 250, 500, 1000 kbps 等標準車用鮑率
        """
        baud_hz = max(10_000.0, float(baud_rate_kbps) * 1000.0)
        
        # TQ = NBT / 16
        # BRP = (Fosc / (2 * 16 * baud_hz)) - 1
        brp = int(round((cls.F_OSC_HZ / (2.0 * cls.NOMINAL_BIT_TIME_TQ * baud_hz)) - 1.0))
        brp = max(0, min(63, brp))  # BRP 是 6-bit (0~63)

        # 位元時間分配 (16 TQ):
        # SyncSeg = 1 TQ (固定)
        # PropSeg = 4 TQ (PRSEG = 3)
        # PhaseSeg1 = 7 TQ (SEG1PH = 6) -> 採樣點位於 (1+4+7)/16 = 12/16 = 75.0%
        # PhaseSeg2 = 4 TQ (SEG2PH = 3)
        # SJW = 1 TQ (SJW = 0)
        sjw_tq = 1
        prop_tq = 4
        phase1_tq = 7
        phase2_tq = 4
        sample_point = ((1 + prop_tq + phase1_tq) / cls.NOMINAL_BIT_TIME_TQ) * 100.0

        # BRGCON1: SJW<1:0> (bits 7-6) | BRP<5:0> (bits 5-0)
        sjw_bits = (sjw_tq - 1) & 0x03
        brgcon1 = (sjw_bits << 6) | (brp & 0x3F)

        # BRGCON2: SEG2PHTS (bit 7=1) | SAM (bit 6=0) | SEG1PH<2:0> (bits 5-3=6) | PRSEG<2:0> (bits 2-0=3)
        prseg_bits = (prop_tq - 1) & 0x07
        seg1ph_bits = (phase1_tq - 1) & 0x07
        brgcon2 = (1 << 7) | (0 << 6) | (seg1ph_bits << 3) | prseg_bits

        # BRGCON3: WAKFIL (bit 7=0) | WAKDIS (bit 6=0) | SEG2PH<2:0> (bits 2-0=3)
        seg2ph_bits = (phase2_tq - 1) & 0x07
        brgcon3 = seg2ph_bits

        return ECANRegisterConfig(
            baud_rate_kbps=baud_rate_kbps,
            brgcon1_val=brgcon1,
            brgcon2_val=brgcon2,
            brgcon3_val=brgcon3,
            sjw_tq=sjw_tq,
            brp_val=brp,
            prop_seg_tq=prop_tq,
            phase_seg1_tq=phase1_tq,
            phase_seg2_tq=phase2_tq,
            sample_point_pct=sample_point
        )


# ============================================================================
# 模組二：即時 CAN 報文監聽器 (CAN Raw Frame Sniffer)
# ============================================================================

@dataclass
class CANRawFrame:
    timestamp_str: str
    can_id: int
    dlc: int
    data_bytes: List[int]
    meaning: str
    is_tx: bool = False

    def format_log_line(self) -> str:
        """
        輸出標準監聽終端格式 (落實十進位優先)：
        [RX] 10:48:15.120 | ID: 0x7E0 (2016) | DLC: 8 | DATA: 02 01 0D 00 00 00 00 00 (車速請求)
        """
        direction = "[TX]" if self.is_tx else "[RX]"
        data_hex = " ".join(f"{b:02X}" for b in self.data_bytes)
        clean_meaning = sanitize_cell(self.meaning)
        return (
            f"{direction} {self.timestamp_str} | "
            f"ID: 0x{self.can_id:03X} ({self.can_id:4d} 十進制) | "
            f"DLC: {self.dlc} | "
            f"DATA: {data_hex} ({clean_meaning})"
        )


class CANFrameGenerator:
    """
    CAN 報文模擬產生器 (涵蓋診斷、車身、馬達、遙測與故障注入)
    """

    PRESET_FRAMES = [
        # (ID, DLC, [Bytes], 語意說明)
        (0x7E0, 8, [0x02, 0x01, 0x0D, 0x00, 0x00, 0x00, 0x00, 0x00], "OBD-II 診斷請求 / 查詢車速 PID:0x0D"),
        (0x7E8, 8, [0x03, 0x41, 0x0D, 0x40, 0x00, 0x00, 0x00, 0x00], "ECU 診斷應答 / 車速 64 km/h (十進制 64)"),
        (0x180, 8, [0x08, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], "BCM 車身狀態 / 左方向燈開啟 閃爍中"),
        (0x280, 8, [0x04, 0xB0, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00], "馬達即時遙測 / 轉速 1200 RPM (十進制 1200)"),
        (0x380, 8, [0x02, 0x00, 0x01, 0xF4, 0x00, 0x00, 0x00, 0x00], "電源軌 ADC 採樣 / 512 LSB | 2.50V"),
        (0x480, 8, [0xAA, 0x55, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00], "TGB-745 心跳廣播 / 節點在線正常 (Keep-Alive)")
    ]

    @classmethod
    def generate_random_frame(cls) -> CANRawFrame:
        now_str = time.strftime("%H:%M:%S") + f".{int(time.time() * 1000) % 1000:03d}"
        can_id, dlc, data, meaning = random.choice(cls.PRESET_FRAMES)
        
        # 若為轉速或車速，微幅動態調整數值
        data_copy = list(data)
        if can_id == 0x280:
            rpm = random.randint(1150, 1250)
            data_copy[0] = (rpm >> 8) & 0xFF
            data_copy[1] = rpm & 0xFF
            meaning = f"馬達即時遙測 / 轉速 {rpm} RPM (十進制 {rpm})"
        elif can_id == 0x7E8:
            spd = random.randint(60, 70)
            data_copy[3] = spd
            meaning = f"ECU 診斷應答 / 車速 {spd} km/h (十進制 {spd})"

        return CANRawFrame(
            timestamp_str=now_str,
            can_id=can_id,
            dlc=dlc,
            data_bytes=data_copy,
            meaning=meaning,
            is_tx=False
        )

    @classmethod
    def generate_heartbeat_pulse(cls) -> CANRawFrame:
        """手動注入 0x7E0 心跳幀"""
        now_str = time.strftime("%H:%M:%S") + f".{int(time.time() * 1000) % 1000:03d}"
        return CANRawFrame(
            timestamp_str=now_str,
            can_id=0x7E0,
            dlc=8,
            data_bytes=[0x02, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
            meaning="🚨 [手動注入] OBD-II 診斷心跳 0x7E0 / Keep-Alive 請求",
            is_tx=True
        )


# ============================================================================
# 模組三：SJA1000 ↔ PIC18F25K80 雙向暫存器轉譯器 (SJA1000ToPICBridge)
# ============================================================================

@dataclass
class SJA1000Timing:
    """NXP SJA1000 CAN 控制器時序解碼模型 (Fosc = 16MHz, Fsys = 8MHz)"""
    btr0: int
    btr1: int

    @property
    def brp(self) -> int:
        """BRP = BTR0[5:0] + 1"""
        return (self.btr0 & 0x3F) + 1

    @property
    def sjw(self) -> int:
        """SJW = BTR0[7:6] + 1"""
        return ((self.btr0 >> 6) & 0x03) + 1

    @property
    def tseg1(self) -> int:
        """TSEG1 = BTR1[3:0] + 1 (PropSeg + PhaseSeg1)"""
        return (self.btr1 & 0x0F) + 1

    @property
    def tseg2(self) -> int:
        """TSEG2 = BTR1[6:4] + 1 (PhaseSeg2)"""
        return ((self.btr1 >> 4) & 0x07) + 1

    @property
    def sam(self) -> int:
        """SAM = BTR1[7]"""
        return (self.btr1 >> 7) & 0x01

    @property
    def total_tq(self) -> int:
        """Nominal Bit Time TQ = 1 (SyncSeg) + TSEG1 + TSEG2"""
        return 1 + self.tseg1 + self.tseg2

    @property
    def baud_rate_bps(self) -> float:
        """SJA1000 典型 F_sys = 8MHz 鮑率計算"""
        return 8_000_000.0 / (self.brp * self.total_tq)


class SJA1000ToPICBridge:
    """
    SJA1000 ↔ PIC18F25K80 雙向暫存器轉譯引擎
    支援從創芯 USB-CAN Tool 提取的 BTR0/BTR1 自動轉譯為 Microchip BRGCON1/2/3
    """

    @classmethod
    def convert_to_pic18f25k80(
        cls,
        btr0_hex: Union[str, int],
        btr1_hex: Union[str, int],
        fosc_mhz: int = 64
    ) -> Dict[str, Any]:
        """
        將 SJA1000 BTR0 / BTR1 轉譯為 PIC18F25K80 暫存器配置 (落實十進位優先)
        """
        btr0 = int(btr0_hex, 16) if isinstance(btr0_hex, str) else int(btr0_hex)
        btr1 = int(btr1_hex, 16) if isinstance(btr1_hex, str) else int(btr1_hex)

        sja = SJA1000Timing(btr0=btr0, btr1=btr1)
        baud_kbps = sja.baud_rate_bps / 1000.0

        # 計算 PIC18F25K80 ECAN 暫存器 (Fosc = 64MHz, 16TQ)
        pic_cfg = ECANBaudCalculator.calculate(baud_kbps)
        pic_fmt = pic_cfg.format_decimal_first()

        return {
            "baud_rate_kbps": round(baud_kbps, 3),
            "sja1000_decoded": {
                "btr0_hex": f"0x{btr0:02X}",
                "btr1_hex": f"0x{btr1:02X}",
                "brp": sja.brp,
                "sjw": sja.sjw,
                "tseg1": sja.tseg1,
                "tseg2": sja.tseg2,
                "sam": sja.sam,
                "total_tq": sja.total_tq
            },
            "pic18f25k80_registers": {
                "BRGCON1": f"0x{pic_cfg.brgcon1_val:02X}",
                "BRGCON2": f"0x{pic_cfg.brgcon2_val:02X}",
                "BRGCON3": f"0x{pic_cfg.brgcon3_val:02X}",
                "decimal_first": pic_fmt
            }
        }


def run_self_test():
    print("=" * 80)
    print("🚀 【CAN Sniffer & PIC18F25K80 ECAN 暫存器計算器自檢】")
    print("=" * 80)

    # 1. 驗證 500 kbps ECAN 暫存器計算
    cfg500 = ECANBaudCalculator.calculate(500.0)
    assert cfg500.brgcon1_val == 3, f"500kbps BRGCON1 應為 3, 實測 {cfg500.brgcon1_val}"
    assert cfg500.brgcon2_val == 179, f"500kbps BRGCON2 應為 179, 實測 {cfg500.brgcon2_val}"
    assert cfg500.brgcon3_val == 3, f"500kbps BRGCON3 應為 3, 實測 {cfg500.brgcon3_val}"
    fmt = cfg500.format_decimal_first()
    print(f"✅ 500 kbps: {fmt['BRGCON1']}")
    print(f"✅ 500 kbps: {fmt['BRGCON2']}")
    print(f"✅ 500 kbps: {fmt['BRGCON3']}")

    # 2. 驗證 250 kbps 與 125 kbps
    cfg250 = ECANBaudCalculator.calculate(250.0)
    assert cfg250.brgcon1_val == 7
    cfg125 = ECANBaudCalculator.calculate(125.0)
    assert cfg125.brgcon1_val == 15
    print("✅ 250 kbps 與 125 kbps BRP 預分頻計算驗證通過！")

    # 3. 驗證 CAN Sniffer 報文生成
    frame = CANFrameGenerator.generate_random_frame()
    log_line = frame.format_log_line()
    assert "ID: 0x" in log_line and "十進制" in log_line
    print(f"✅ 報文日誌輸出: {log_line}")

    print("\n🟢 can_sniffer_ecan_calculator.py 100% 自檢通過！")


if __name__ == "__main__":
    run_self_test()
