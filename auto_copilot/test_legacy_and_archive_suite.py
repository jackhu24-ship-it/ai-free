# -*- coding: utf-8 -*-
"""
=============================================================================
AutoCopilot Milestone 95 Test Suite: Master Archive & Cross-Domain Legacy
=============================================================================
Covers:
1. Cross-Domain Mission-Critical Framework (Embodied Robotics, Zero-Trust Satcom)
2. Dynamic Hysteresis, Physical Interlock & Zero-Trust Protocol Validation
3. GSN Automated Compliance Tree for Cross-Industry Certification
4. Cold Vault Manifest & Deterministic 15-Min Bare-Metal Restoration
5. Reproducible Docker Sandbox Specification
6. Founder Post-Mortem Playbook Document Integrity
=============================================================================
"""

import os
import pytest
from auto_copilot.cross_domain_mission_critical_framework import (
    CrossDomainMissionCriticalFramework,
    MissionCriticalDomain,
    SystemSafetyState,
    DynamicHysteresisFilter,
    PhysicalSafetyInterlockValve,
    ZeroTrustPacketProtocol,
    GSNComplianceProofNode
)
from auto_copilot.restore_cold_vault import ColdVaultRestorer


def test_cross_domain_framework_embodied_robotics():
    """驗證跨領域具身機器人框架：遲滯防抖與微秒級物理隔離閥"""
    framework = CrossDomainMissionCriticalFramework(MissionCriticalDomain.EMBODIED_ROBOTICS)
    assert framework.state == SystemSafetyState.NOMINAL_ACTIVE

    # 1. 正常關節運行：力矩 50Nm，感測器正常 75.0
    normal_pkt = framework.protocol.encode_frame(message_id=0x101, payload=b"JOINT_CMD")
    res_norm = framework.execute_supervision_cycle(sensor_val=75.0, demand_val=50.0, raw_packet=normal_pkt)
    assert res_norm["system_state"] == SystemSafetyState.NOMINAL_ACTIVE.value
    assert res_norm["output_command"] == 50.0
    assert res_norm["interlock_tripped"] is False

    # 2. 注入極端力矩過載：力矩 180Nm (超過上限 120Nm) -> 觸發物理隔離閥
    res_over = framework.execute_supervision_cycle(sensor_val=75.0, demand_val=180.0, raw_packet=normal_pkt)
    assert res_over["system_state"] == SystemSafetyState.HARDWARE_ISOLATED.value
    assert res_over["output_command"] == 0.0
    assert res_over["interlock_tripped"] is True


def test_cross_domain_zero_trust_packet_protocol():
    """驗證零信任高雜訊通訊協議 (E2E CRC16 + 滾動序號)"""
    proto = ZeroTrustPacketProtocol()
    pkt = proto.encode_frame(message_id=0x200, payload=b"DRONE_SWARM_HEARTBEAT")
    
    # 正常解碼
    valid, payload, reason = proto.decode_and_validate(pkt)
    assert valid is True
    assert payload == b"DRONE_SWARM_HEARTBEAT"
    assert reason == "VALID"

    # 模擬強電磁干擾 (EMI) 破壞 CRC
    corrupted_pkt = bytearray(pkt)
    corrupted_pkt[3] ^= 0xFF  # 翻轉 CRC 字節
    valid_corrupt, _, reason_corrupt = proto.decode_and_validate(bytes(corrupted_pkt))
    assert valid_corrupt is False
    assert "CRC_MISMATCH" in reason_corrupt


def test_cross_domain_gsn_compliance_node():
    """驗證通用 GSN 合規證明節點 (跨醫療/航空/車載驗收)"""
    node = GSNComplianceProofNode(
        goal_id="G_MED_01",
        statement="Pacemaker Firmware Deterministic Timing Guarantee",
        target_standard="FDA_PMA_CLASS_III"
    )
    node.add_strategy("Argue timing deterministic bounds via formal verification")
    node.attach_evidence("EV_01", "Worst Case Execution Time (WCET) < 1.0ms", True, "SHA256:112233")
    node.attach_evidence("EV_02", "100% MC/DC Coverage Report", True, "SHA256:445566")

    assert node.is_claim_closed() is True


def test_cold_vault_manifest_and_restorer():
    """驗證終極冷存儲金鑰清單與 15 分鐘裸機一鍵復原器"""
    ws = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    restorer = ColdVaultRestorer(ws)
    audit = restorer.verify_vault_integrity()

    assert audit["is_intact"] is True
    assert audit["vault_id"] == "COLD-VAULT-AUTOCP-2026-FINAL"
    assert audit["release_tag"] == "v7.0.0-final-legacy-sealed"
    assert audit["rebuild_sla_minutes"] <= 15
    assert audit["checks_passed"] >= 8
    assert len(audit["violations"]) == 0


def test_reproducible_dockerfile_contents():
    """驗證確定性 Docker 構建沙盒與工具鏈版本鎖死"""
    ws = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    docker_path = os.path.join(ws, "auto_copilot", "Dockerfile.reproducible_asil_d")
    assert os.path.exists(docker_path)

    with open(docker_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "FROM python:3.12-slim-bookworm" in content
    assert "pytest==7.4.3" in content
    assert "python-can==4.3.1" in content
    assert "flake8==7.0.0" in content
    assert "bandit==1.7.7" in content


def test_founder_playbook_spec_integrity():
    """驗證技術創始人實戰覆盤與治理白皮書之完備性"""
    ws = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    playbook_path = os.path.join(ws, "auto_copilot", "docs", "POST_MORTEM_FOUNDER_PLAYBOOK.md")
    assert os.path.exists(playbook_path)

    with open(playbook_path, "r", encoding="utf-8") as f:
        text = f.read()

    assert "你是我任命的指揮官" in text
    assert "Windows 中文語系下的 Python Subprocess" in text
    assert "二重翻轉抵消" in text
    assert "外部確定性安全監控器架構（External Deterministic Safety Cage, EDSC）" in text
    assert "個人架構母版庫抽象化" in text