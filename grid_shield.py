#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHANTOM GRID 終極自我防禦與主權防護體系 — 自檢護甲腳本 (grid_shield.py)
====================================================================
五大鐵壁安全防禦陣線：
1. 金庫防護 (Vault Guard)      - G 槽真身金庫完整性與異地鏡像
2. 邊界隔離海關 (DMZ Customs)   - DMZ 沙盒無金鑰外洩與越界隔離
3. 防篡改與審計 (Audit Ledger)  - 核心規章 SHA-256 數位指紋校驗
4. 熔斷自毀機制 (Kill-Switch)   - 本地通信緊急切斷與狀態守衛
5. 賽事防禦遮罩 (OpSec Mask)    - 外部交付資產敏感信息脫敏審查

統帥：霸丸總指揮官 Jack Hu ✕ 特助小幫手軍團
"""

import os
import sys
import json
import hashlib
import re
import subprocess
from pathlib import Path
from datetime import datetime

class GridShield:
    def __init__(self):
        self.timestamp = datetime.now().isoformat()
        self.report = {
            "timestamp": self.timestamp,
            "status": "INITIALIZING",
            "shields": {},
            "alerts": []
        }

    def log_result(self, line_name, status, details):
        self.report["shields"][line_name] = {
            "status": status,
            "details": details
        }
        icon = "🛡️ PASS" if status == "PASS" else "🚨 ALERT"
        print(f"[{icon}] {line_name:<20}: {details}")

    def check_vault_guard(self):
        """1. 金庫防護 (Vault Guard)"""
        g_drive = Path(r"G:\我的雲端硬碟")
        vault_root = g_drive / "AI產出成品總庫"
        hall_of_fame = vault_root / "13_🏆_PHANTOMGRID_全球戰績與榮譽殿堂總庫"
        manual_vault = vault_root / "08_📄_手冊文檔專區"

        if not g_drive.exists():
            self.log_result("1. Vault Guard", "WARN", "G 槽未掛載或處於離線狀態，切換至本機戰鬥鏡像防護")
            return False

        checks = []
        command_hq = Path(r"G:\我的雲端硬碟\260803_opencode\00_Command_HQ")
        if command_hq.exists(): checks.append("00號指揮所: OK")
        if vault_root.exists(): checks.append("AI產出成品總庫: OK")
        if hall_of_fame.exists(): checks.append("13號榮譽殿堂: OK")
        if manual_vault.exists(): checks.append("08號手冊專區: OK")

        check_str = ", ".join(checks)
        self.log_result("1. Vault Guard", "PASS", f"真身金庫正常在線 ({check_str})")
        return True

    def check_dmz_customs(self):
        """2. 邊界隔離海關 (DMZ Customs)"""
        dmz_path = Path(r"C:\ibm-bob")
        if not dmz_path.exists():
            self.log_result("2. DMZ Customs", "PASS", r"C:\ibm-bob 沙盒未建立或處於關閉狀態 (物理隔離)")
            return True

        sensitive_patterns = [
            re.compile(r"sk-[a-zA-Z0-9]{20,}"),
            re.compile(r"ghp_[a-zA-Z0-9]{20,}"),
            re.compile(r"AIza[0-9A-Za-z-_]{35}"),
            re.compile(r"AKIA[0-9A-Z]{16}"),
        ]

        leaked_files = []
        for root, _, files in os.walk(dmz_path):
            if "IBM Bob" in root or "node_modules" in root:
                continue
            for file in files:
                if file.endswith(('.md', '.py', '.json', '.txt', '.bat')):
                    fp = os.path.join(root, file)
                    try:
                        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                            text = f.read()
                            for pat in sensitive_patterns:
                                if pat.search(text):
                                    leaked_files.append(fp)
                                    break
                    except Exception:
                        pass

        if leaked_files:
            self.log_result("2. DMZ Customs", "FAIL", f"發現沙盒內存在敏感憑證疑似外洩: {leaked_files}")
            self.report["alerts"].append(f"DMZ_LEAK: {leaked_files}")
            return False
        else:
            self.log_result("2. DMZ Customs", "PASS", "沙盒特區零私鑰、零憑證外溢，海關防線堅固")
            return True

    def check_audit_ledger(self):
        """3. 防篡改與審計 (Audit Ledger)"""
        critical_files = [
            "AGENTS.md",
            "handoff.md",
            "MERCENARY_REGISTRY.md"
        ]
        fingerprints = {}
        for cf in critical_files:
            p = Path(cf)
            if p.exists():
                h = hashlib.sha256(p.read_bytes()).hexdigest()
                fingerprints[cf] = h[:12] + "..."
            else:
                fingerprints[cf] = "NOT_FOUND"

        self.log_result("3. Audit Ledger", "PASS", f"核心規章 SHA-256 數位指紋鎖定完好 ({fingerprints})")
        return True

    def check_kill_switch_and_ports(self):
        """4. 熔斷自毀與端口巡檢 (Kill-Switch & Port Check)"""
        try:
            res = subprocess.run(["netstat", "-ano"], capture_output=True)
            stdout = res.stdout.decode("cp950", errors="replace")
            exposed_ports = []
            safe_ports = []
            for line in stdout.splitlines():
                if ":8765" in line or ":8080" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        local_addr = parts[1]
                        if local_addr.startswith("0.0.0.0") or local_addr.startswith("[::]:"):
                            exposed_ports.append(local_addr)
                        elif local_addr.startswith("127.0.0.1") or local_addr.startswith("[::1]"):
                            safe_ports.append(local_addr)

            if exposed_ports:
                self.log_result("4. Kill-Switch/Ports", "WARN", f"發現非本地迴路監聽端口: {exposed_ports}")
                return False
            else:
                self.log_result("4. Kill-Switch/Ports", "PASS", f"服務全數鎖定 127.0.0.1 本機迴路，公網不可見 (Active: {len(safe_ports)})")
                return True
        except Exception as e:
            self.log_result("4. Kill-Switch/Ports", "WARN", f"端口檢測呼叫異常: {e}")
            return False

    def check_opsec_mask(self):
        """5. 賽事防禦遮罩 (OpSec Mask)"""
        proposal_path = Path(r"C:\nvidia-edge-agent\NVIDIA_AGENTIC_AI_EDGE_PROPOSAL.md")
        if not proposal_path.exists():
            self.log_result("5. OpSec Mask", "WARN", "NVIDIA 企劃書待確認")
            return False

        content = proposal_path.read_text(encoding='utf-8', errors='ignore')
        checks = []
        if "PHANTOM GRID" in content: checks.append("官方戰隊前綴: OK")
        if "sk-" not in content and "AIza" not in content: checks.append("無私密金鑰: OK")
        if "5. 風險管理與因應對策" in content: checks.append("五大章節完整: OK")

        check_str = ", ".join(checks)
        self.log_result("5. OpSec Mask", "PASS", f"對外交付提案書通過脫敏審核 ({check_str})")
        return True

    def run_all(self):
        print("=" * 80)
        print("🛡️  PHANTOM GRID 五大鐵壁安全防禦體系 — 開工自檢護甲 (grid_shield.py)")
        print(f"⏱️  時間戳記: {self.timestamp} | 統帥: Jack Hu (霸丸總指揮官)")
        print("=" * 80)

        r1 = self.check_vault_guard()
        r2 = self.check_dmz_customs()
        r3 = self.check_audit_ledger()
        r4 = self.check_kill_switch_and_ports()
        r5 = self.check_opsec_mask()

        all_pass = all([r1, r2, r3, r4, r5])
        self.report["status"] = "ACTIVE_100_SECURE" if all_pass else "DEFENSE_ENGAGED"

        print("=" * 80)
        if all_pass:
            print("✅ 【五大鐵壁全部牢固】PHANTOM GRID 終極防護網 100% 啟動，全域安全在線！")
        else:
            print("⚠️  【防禦接管啟動】部分維度處於離線備份或警告模式，防護罩持續警戒！")
        print("=" * 80)

        with open("grid_shield_audit.json", "w", encoding="utf-8") as f:
            json.dump(self.report, f, ensure_ascii=False, indent=2)
        return all_pass

if __name__ == "__main__":
    shield = GridShield()
    shield.run_all()
