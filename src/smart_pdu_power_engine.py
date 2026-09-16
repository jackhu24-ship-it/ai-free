#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 【PROJ-EXAM-03 車用智慧配電盒 (Smart PDU) 電力預算與壓降引擎】
================================================================================
主責工程師：🛠️ A02 小開 (Agent_Coder)
演算法規格：🌊 A05 小深 (02_Knowledge/Specs/Smart_PDU_Wiring_Topology_Spec.md)
品質把關者：🐎 A03 小馬 (TEST/test_smart_pdu_power_topology.py)

功能亮點：
  1. 8 通道電力負載平衡、同時係數 (Diversity Factor) 與總功率計算
  2. 高溫 85°C 銅阻率迴路壓降計算 (車規極限 Delta V <= 0.50V)
  3. 保險絲持續負載 75% 降額安全係數校驗
  4. 智慧 E-Fuse 固態驅動器過載/短路 (<5ms) 跳脫模擬與 CWE-1236 CSV 匯出
"""

from __future__ import annotations

import sys
import os
import csv
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Any, Optional, Tuple

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


class DriverType(Enum):
    E_FUSE_PROFET = "Smart E-Fuse (PROFET)"
    MICRO_RELAY = "Micro Relay"


class ChannelState(Enum):
    OFF = auto()
    NORMAL_ON = auto()
    OVERLOAD_TRIPPED = auto()
    SHORT_CIRCUIT_TRIPPED = auto()


@dataclass
class PDUChannelConfig:
    channel_id: int
    name: str
    driver_type: DriverType
    nominal_current_a: float
    fuse_rating_a: float
    wire_gauge_mm2: float
    wire_length_m: float
    feed_rail: str  # "KL30" or "KL15"


@dataclass
class ChannelSimulationResult:
    channel_id: int
    name: str
    feed_rail: str
    driver_type: str
    nominal_current_a: float
    actual_current_a: float
    fuse_rating_a: float
    derating_ratio_pct: float       # actual_current / fuse_rating %
    derating_safe: bool             # <= 75.0%
    loop_resistance_ohm: float      # R_loop @ 85°C
    voltage_drop_v: float           # Delta V
    voltage_drop_ok: bool           # <= 0.50V
    power_loss_w: float             # I^2 * R
    state: ChannelState
    trip_time_ms: float             # 0 if normal, >0 if tripped


@dataclass
class PowerBudgetSummary:
    total_active_channels: int
    sum_nominal_current_a: float
    diversity_factor: float
    steady_state_total_current_a: float
    total_power_consumption_w: float
    total_harness_loss_w: float
    kl30_main_load_ratio_pct: float
    kl30_main_safe: bool
    channels_results: List[ChannelSimulationResult]


class SmartPDUEngine:
    """
    車用智慧配電盒 (Smart PDU) 電力預算與壓降引擎
    """

    # 高溫 85°C 銅導線電阻率 (Ohm * mm2 / m)
    RHO_85C = 0.0220

    # 預設 8 大標準通道配置 (PROJ-EXAM-03 規格)
    DEFAULT_CONFIGS: List[PDUChannelConfig] = [
        PDUChannelConfig(1, "近光頭燈 (Low Beam)", DriverType.E_FUSE_PROFET, 7.5, 10.0, 2.00, 2.5, "KL15"),
        PDUChannelConfig(2, "遠光頭燈 (High Beam)", DriverType.E_FUSE_PROFET, 8.0, 15.0, 2.00, 2.5, "KL15"),
        PDUChannelConfig(3, "散熱風扇 (Cooling Fan)", DriverType.MICRO_RELAY, 20.0, 30.0, 4.00, 1.5, "KL15"),
        PDUChannelConfig(4, "燃油泵 (Fuel Pump)", DriverType.MICRO_RELAY, 6.5, 15.0, 2.50, 3.5, "KL15"),
        PDUChannelConfig(5, "雨刷馬達 (Wiper Motor)", DriverType.E_FUSE_PROFET, 8.0, 15.0, 2.00, 1.8, "KL15"),
        PDUChannelConfig(6, "汽車喇叭 (Horn Module)", DriverType.MICRO_RELAY, 7.0, 15.0, 1.50, 2.0, "KL30"),
        PDUChannelConfig(7, "車身控制器 (BCM & Cabin)", DriverType.E_FUSE_PROFET, 3.5, 7.5, 0.75, 1.5, "KL30"),
        PDUChannelConfig(8, "儀表板與診斷 (Cluster)", DriverType.E_FUSE_PROFET, 1.5, 5.0, 0.50, 1.2, "KL30"),
    ]

    def __init__(self, configs: Optional[List[PDUChannelConfig]] = None, kl30_main_fuse_a: float = 100.0):
        self.configs = configs or self.DEFAULT_CONFIGS
        self.kl30_main_fuse_a = kl30_main_fuse_a

    def calculate_loop_resistance(self, length_m: float, gauge_mm2: float) -> float:
        """計算雙程迴路電阻 (供電線 + 接地線, 2L @ 85°C)"""
        return (2.0 * self.RHO_85C * length_m) / gauge_mm2

    def simulate_power_flow(
        self,
        active_channels: Optional[Dict[int, bool]] = None,
        overload_injections: Optional[Dict[int, float]] = None
    ) -> PowerBudgetSummary:
        """
        模擬多通道電力負載、壓降、發熱損耗與 E-Fuse 跳脫
        """
        active_map = active_channels or {cfg.channel_id: True for cfg in self.configs}
        injections = overload_injections or {}

        results: List[ChannelSimulationResult] = []
        total_nom_a = 0.0
        total_actual_a = 0.0
        total_harness_loss = 0.0
        active_count = 0

        for cfg in self.configs:
            is_active = active_map.get(cfg.channel_id, False)
            if not is_active:
                results.append(ChannelSimulationResult(
                    channel_id=cfg.channel_id,
                    name=cfg.name,
                    feed_rail=cfg.feed_rail,
                    driver_type=cfg.driver_type.value,
                    nominal_current_a=cfg.nominal_current_a,
                    actual_current_a=0.0,
                    fuse_rating_a=cfg.fuse_rating_a,
                    derating_ratio_pct=0.0,
                    derating_safe=True,
                    loop_resistance_ohm=round(self.calculate_loop_resistance(cfg.wire_length_m, cfg.wire_gauge_mm2), 4),
                    voltage_drop_v=0.0,
                    voltage_drop_ok=True,
                    power_loss_w=0.0,
                    state=ChannelState.OFF,
                    trip_time_ms=0.0
                ))
                continue

            active_count += 1
            total_nom_a += cfg.nominal_current_a

            # 實際電流 (支援過載注入)
            current_a = injections.get(cfg.channel_id, cfg.nominal_current_a)

            # 計算迴路電阻與壓降
            r_loop = self.calculate_loop_resistance(cfg.wire_length_m, cfg.wire_gauge_mm2)
            v_drop = current_a * r_loop
            p_loss = (current_a ** 2) * r_loop
            derating_pct = (current_a / cfg.fuse_rating_a) * 100.0
            derating_safe = derating_pct <= 75.0
            v_drop_ok = v_drop <= 0.50

            # E-Fuse 與過載保護判定
            state = ChannelState.NORMAL_ON
            trip_time = 0.0
            if current_a > (3.0 * cfg.fuse_rating_a):
                state = ChannelState.SHORT_CIRCUIT_TRIPPED
                trip_time = 3.5  # < 5ms 極速跳脫
                current_a = 0.0  # 切斷後無電流
            elif current_a > (1.5 * cfg.fuse_rating_a):
                state = ChannelState.OVERLOAD_TRIPPED
                trip_time = 450.0  # 反時限跳脫
                current_a = 0.0

            total_actual_a += current_a
            total_harness_loss += p_loss

            results.append(ChannelSimulationResult(
                channel_id=cfg.channel_id,
                name=cfg.name,
                feed_rail=cfg.feed_rail,
                driver_type=cfg.driver_type.value,
                nominal_current_a=cfg.nominal_current_a,
                actual_current_a=round(current_a, 2),
                fuse_rating_a=cfg.fuse_rating_a,
                derating_ratio_pct=round(derating_pct, 2),
                derating_safe=derating_safe,
                loop_resistance_ohm=round(r_loop, 4),
                voltage_drop_v=round(v_drop, 3),
                voltage_drop_ok=v_drop_ok,
                power_loss_w=round(p_loss, 2),
                state=state,
                trip_time_ms=trip_time
            ))

        diversity_factor = 0.75
        steady_state_total_a = total_actual_a * diversity_factor
        total_power_w = 12.0 * steady_state_total_a
        kl30_ratio = (steady_state_total_a / self.kl30_main_fuse_a) * 100.0

        return PowerBudgetSummary(
            total_active_channels=active_count,
            sum_nominal_current_a=round(total_nom_a, 2),
            diversity_factor=diversity_factor,
            steady_state_total_current_a=round(steady_state_total_a, 2),
            total_power_consumption_w=round(total_power_w, 1),
            total_harness_loss_w=round(total_harness_loss, 2),
            kl30_main_load_ratio_pct=round(kl30_ratio, 2),
            kl30_main_safe=kl30_ratio <= 75.0,
            channels_results=results
        )

    def export_power_budget_csv(self, summary: PowerBudgetSummary, filepath: str) -> str:
        """匯出智慧配電盒電力報告並落實 CWE-1236 公式注入防護"""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", newline="", encoding="utf-8", errors="replace") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Channel_ID", "Load_Name", "Feed_Rail", "Driver_Type", "Nominal_Current_A",
                "Actual_Current_A", "Fuse_Rating_A", "Derating_Pct", "Derating_Safe",
                "Loop_Resistance_Ohm", "Voltage_Drop_V", "Voltage_Drop_OK", "Power_Loss_W",
                "State", "Trip_Time_ms"
            ])
            for r in summary.channels_results:
                writer.writerow([
                    sanitize_cell(r.channel_id),
                    sanitize_cell(r.name),
                    sanitize_cell(r.feed_rail),
                    sanitize_cell(r.driver_type),
                    sanitize_cell(r.nominal_current_a),
                    sanitize_cell(r.actual_current_a),
                    sanitize_cell(r.fuse_rating_a),
                    sanitize_cell(r.derating_ratio_pct),
                    sanitize_cell(r.derating_safe),
                    sanitize_cell(r.loop_resistance_ohm),
                    sanitize_cell(r.voltage_drop_v),
                    sanitize_cell(r.voltage_drop_ok),
                    sanitize_cell(r.power_loss_w),
                    sanitize_cell(r.state.name),
                    sanitize_cell(r.trip_time_ms)
                ])
        return filepath


def run_self_test():
    print("=" * 80)
    print("⚡ 【PROJ-EXAM-03 智慧配電盒 (Smart PDU) 電力預算與壓降引擎自檢】")
    print("=" * 80)

    engine = SmartPDUEngine()

    # 1. 滿載常規模擬
    summary = engine.simulate_power_flow()
    print(f"\n[測試 1: 全通道常規滿載模擬]")
    print(f"  • 啟動通道數: {summary.total_active_channels} / 8")
    print(f"  • 標稱總電流: {summary.sum_nominal_current_a} A | 穩態平均電流: {summary.steady_state_total_current_a} A (同時係數 {summary.diversity_factor})")
    print(f"  • 整車總功耗: {summary.total_power_consumption_w} W | 線束總損耗: {summary.total_harness_loss_w} W")
    print(f"  • KL30 主保險絲負載率: {summary.kl30_main_load_ratio_pct}% (安全裕度: {'🟢 安全' if summary.kl30_main_safe else '🔴 過載'})")

    for ch in summary.channels_results:
        print(f"  • [{ch.channel_id}] {ch.name:22s} | I={ch.actual_current_a:4.1f}A | 壓降={ch.voltage_drop_v:.3f}V ({'PASS' if ch.voltage_drop_ok else 'FAIL'}) | 降額={ch.derating_ratio_pct:4.1f}%")
        assert ch.voltage_drop_ok, f"通道 {ch.name} 壓降超標: {ch.voltage_drop_v}V > 0.50V"
        assert ch.derating_safe, f"通道 {ch.name} 降額超標: {ch.derating_ratio_pct}% > 75%"

    # 2. 測試過載與短路跳脫注入
    print(f"\n[測試 2: 注入 CH-01 短路 (40A) 與 CH-05 過載 (25A)]")
    trip_summary = engine.simulate_power_flow(overload_injections={1: 40.0, 5: 25.0})
    ch1 = trip_summary.channels_results[0]
    ch5 = trip_summary.channels_results[4]
    print(f"  • CH-01 (近光燈短路 40A): 狀態={ch1.state.name} | 跳脫時間={ch1.trip_time_ms} ms | 切斷後電流={ch1.actual_current_a} A")
    print(f"  • CH-05 (雨刷過載 25A): 狀態={ch5.state.name} | 跳脫時間={ch5.trip_time_ms} ms | 切斷後電流={ch5.actual_current_a} A")
    assert ch1.state == ChannelState.SHORT_CIRCUIT_TRIPPED and ch1.trip_time_ms < 5.0, "短路應在 5ms 內跳脫"
    assert ch5.state == ChannelState.OVERLOAD_TRIPPED, "過載應觸發反時限保護"

    print("\n🟢 SmartPDUEngine 電力計算引擎自檢 100% 通過！")


if __name__ == "__main__":
    run_self_test()
