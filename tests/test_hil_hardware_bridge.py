# -*- coding: utf-8 -*-
"""
tests/test_hil_hardware_bridge.py - 實體 HIL 硬體橋接與 CAN-FD 適配層單元測試
==============================================================================
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import unittest
from src.edge_soa.hil_hardware_bridge import PicStLinkHardwareBridge
from src.edge_soa.can_bus_hardware_adapter import HardwareCanBusAdapter


class TestHilHardwareBridge(unittest.TestCase):

    def setUp(self):
        self.bridge = PicStLinkHardwareBridge(simulation_mode=True)
        self.can_adapter = HardwareCanBusAdapter(channel="PCAN_USBBUS1")
        self.can_adapter.connect()

    def test_pickit4_and_stlink_script_generation(self):
        """測試 PICkit4 與 ST-Link CLI 自動化燒錄指令格式"""
        pk4_cmd = self.bridge.generate_pickit4_flash_script(
            device="dsPIC33CK256MP506",
            hex_path="build/firmware.hex",
            power_target=True,
            voltage=3.3
        )
        self.assertIn("ipecmd.jar", pk4_cmd)
        self.assertIn("-PdsPIC33CK256MP506", pk4_cmd)
        self.assertIn("-W3.3", pk4_cmd)

        st_cmd = self.bridge.generate_stlink_flash_script(
            hex_path="build/firmware.hex",
            address="0x08000000"
        )
        self.assertIn("STM32_Programmer_CLI.exe", st_cmd)
        self.assertIn("-w \"build/firmware.hex\" 0x08000000", st_cmd)

    def test_dual_core_takeover_latency_asild(self):
        """測試 5ms 雙核熱接管極限延遲判定"""
        # 正常 2.5ms 接管 (< 5.0ms)
        res_fast = self.bridge.measure_dual_core_takeover_latency(
            primary_alive=False,
            measured_pulse_width_us=2500.0
        )
        self.assertTrue(res_fast["asil_d_compliant"])
        self.assertEqual(res_fast["safety_state"], "SAFE_REDUNDANT_TAKEOVER")
        self.assertEqual(res_fast["active_mcu"], "MCU_SECONDARY_BACKUP")

        # 超時 6.5ms 接管 (> 5.0ms) 應判定違反 ASIL-D 安全邊界
        res_slow = self.bridge.measure_dual_core_takeover_latency(
            primary_alive=False,
            measured_pulse_width_us=6500.0
        )
        self.assertFalse(res_slow["asil_d_compliant"])
        self.assertEqual(res_slow["safety_state"], "SAFETY_VIOLATION_TIMEOUT")

    def test_analog_watchdog_interceptor(self):
        """測試類比看門狗電壓超標微秒級中斷"""
        # 正常電壓 1.8V
        res_norm = self.bridge.inject_analog_watchdog_fault(channel=1, simulated_voltage=1.8)
        self.assertFalse(res_norm["fault_triggered"])

        # 過壓 3.1V 觸發硬體截斷
        res_ov = self.bridge.inject_analog_watchdog_fault(channel=1, simulated_voltage=3.1)
        self.assertTrue(res_ov["fault_triggered"])
        self.assertEqual(res_ov["action"], "HARDWARE_INTERRUPT_PWM_CUTOFF")

    def test_can_fd_communication_and_security(self):
        """測試 CAN-FD 64-Byte 數據幀傳輸、CRC32 校驗與防重放"""
        payload = b"ASIL-D_BMS_TELEMETRY_CELL_VOLTAGE_STATUS_OK"
        frame = self.can_adapter.build_can_fd_frame(can_id=0x18F00100, payload=payload)

        self.assertEqual(frame["dlc"], 15)
        self.assertEqual(frame["length"], 64)

        # 正常接收驗證
        rx_res = self.can_adapter.receive_and_verify_frame(frame)
        self.assertTrue(rx_res["verified"])

        # 重放攻擊測試 (再次接收同一序號幀)
        replay_res = self.can_adapter.receive_and_verify_frame(frame)
        self.assertFalse(replay_res["verified"])
        self.assertEqual(replay_res["reason"], "REPLAY_ATTACK_STALE_SEQUENCE")

        # 數據篡改測試 (位元翻轉)
        corrupted_payload = bytearray(frame["payload"])
        corrupted_payload[10] ^= 0xFF
        corrupted_frame = dict(frame)
        corrupted_frame["payload"] = bytes(corrupted_payload)

        corrupt_res = self.can_adapter.receive_and_verify_frame(corrupted_frame)
        self.assertFalse(corrupt_res["verified"])
        self.assertEqual(corrupt_res["reason"], "CRC32_MISMATCH_DATA_CORRUPTION")

    def test_can_bus_off_and_recovery(self):
        """測試 Bus-Off 故障注入與自癒恢復"""
        self.assertEqual(self.can_adapter.bus_state, "BUS_ACTIVE")
        self.can_adapter.inject_bus_off()
        self.assertEqual(self.can_adapter.bus_state, "BUS_OFF")

        recovered = self.can_adapter.auto_recover_bus()
        self.assertTrue(recovered)
        self.assertEqual(self.can_adapter.bus_state, "BUS_ACTIVE")


if __name__ == "__main__":
    unittest.main()
