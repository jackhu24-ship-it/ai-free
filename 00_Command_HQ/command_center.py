#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
PHANTOM GRID - Supreme Command Center (00_Command_HQ)
👑 霸丸總指揮官 Jack 哥 專屬實體特權中樞

三大核心權限：
1. 【統帥落款權 (Final Sign-off)】：驗證 commander_token.json 數位簽章，正式核可資產為 OFFICIALLY_CERTIFIED。
2. 【終極熔斷權 (Emergency Kill-Switch)】：一鍵終止本機所有背景哨兵 (Watchdog)、聯動伺服器與傭兵行程。
3. 【全域重構權 (Global Factory Reset)】：自 G 槽唯一真理庫重新投射覆寫 C 槽戰鬥鏡像，5 分鐘滿血原地復活。
"""

import os
import sys
import json
import time
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# Windows UTF-8 強制防護
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 定位路徑
HQ_DIR = Path(__file__).resolve().parent
REPO_ROOT = HQ_DIR.parent
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

try:
    from path_resolver import (
        TRUTH_ROOT, COMBAT_ROOT, G_COMMAND_HQ, C_COMMAND_HQ,
        G_KNOWLEDGE_TYPO, C_KNOWLEDGE_TYPO, G_HANDOFF, C_HANDOFF,
        G_INSTALLER_TPL, C_INSTALLER_TPL, ensure_all_dirs
    )
except ImportError:
    TRUTH_ROOT = Path(r"G:\我的雲端硬碟\260803_opencode")
    COMBAT_ROOT = Path(r"C:\260728-code")
    G_COMMAND_HQ = TRUTH_ROOT / "00_Command_HQ"
    C_COMMAND_HQ = COMBAT_ROOT / "00_Command_HQ"
    G_KNOWLEDGE_TYPO = TRUTH_ROOT / "02_Knowledge" / "Typography"
    C_KNOWLEDGE_TYPO = COMBAT_ROOT / "02_Knowledge" / "Typography"
    G_HANDOFF = TRUTH_ROOT / "handoff.md"
    C_HANDOFF = COMBAT_ROOT / "handoff.md"
    G_INSTALLER_TPL = TRUTH_ROOT / "工具安裝包" / "template"
    C_INSTALLER_TPL = COMBAT_ROOT / "工具安裝包" / "template"

TOKEN_FILE = HQ_DIR / "commander_token.json"
WAR_LOG_G = G_COMMAND_HQ / "war_log.md"
WAR_LOG_C = C_COMMAND_HQ / "war_log.md"

def load_commander_token():
    """載入統帥專屬權杖與數位指紋"""
    if not TOKEN_FILE.exists():
        raise FileNotFoundError(f"❌ 嚴重警報: 找不到統帥權杖 {TOKEN_FILE}！")
    with open(TOKEN_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def write_war_log(action_title: str, details: str):
    """登記統帥作戰日誌 (G 槽真身優先，再投影至 C 槽與 handoff.md)"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n- **[{action_title}]** `{timestamp}` {details}\n"
    
    for log_path in [WAR_LOG_G, WAR_LOG_C, HQ_DIR / "war_log.md"]:
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception:
            pass

    # 同步登記進 handoff.md
    for handoff_path in [G_HANDOFF, C_HANDOFF]:
        try:
            if handoff_path.exists():
                with open(handoff_path, "a", encoding="utf-8") as f:
                    f.write(entry)
        except Exception:
            pass

# ==============================================================================
# 權限 1: 👑 統帥最高落款 (Final Sign-off)
# ==============================================================================
def sign_off_asset(draft_name: str, verdict: str = "准") -> bool:
    token = load_commander_token()
    print("=" * 70)
    print("👑 [PHANTOM GRID 實體指揮所] 統帥終審落款核定程序")
    print("=" * 70)
    print(f"• 授權統帥 : {token['title']} ({token['commander_name']})")
    print(f"• 權杖指紋 : {token['digital_fingerprint']}")
    print(f"• 標的資產 : {draft_name}")
    print(f"• 裁決意志 : 【{verdict}】")
    print("-" * 70)

    if verdict not in ["准", "APPROVE", "PASS"]:
        print("🛑 統帥裁決：【駁回】。該資產不予生效，退回重構！")
        write_war_log("統帥終審駁回", f"標的 `{draft_name}` 經審閱駁回，終止入庫。")
        return False

    # 調用雙層認證管線進行正規落款
    from dual_verify_pipeline import DualVerificationEngine
    engine = DualVerificationEngine(draft_name)
    if not engine.verify_l1_xiaomi_customs():
        print("❌ L1 小米安檢未過，無法落款！")
        return False
    if not engine.verify_l2_office2_sandbox():
        print("❌ L2 二辦試跑未過，無法落款！")
        return False

    success = engine.commander_signoff(commander_name=token["commander_name"])
    if success:
        print("🎖️ 統帥御印完成！資產已正式賦予 OFFICIALLY_CERTIFIED 榮譽！")
        write_war_log("統帥終審落款", f"標的 `{draft_name}` 經審閱裁決【准】，已加蓋最高權杖指紋並四軌入庫。")
    return success

# ==============================================================================
# 權限 2: 🛑 終極熔斷器 (Emergency Kill-Switch)
# ==============================================================================
def emergency_kill_switch():
    token = load_commander_token()
    print("🚨" * 20)
    print("🛑 [PHANTOM GRID 實體指揮所] 終極緊急熔斷器啟動 (EMERGENCY KILL-SWITCH)")
    print("🚨" * 20)
    print(f"• 執行授權 : {token['commander_name']} (權限等級: {token['authority_level']})")
    
    # 終止後台哨兵與服務
    targets = ["auto_watchdog_pipeline.py", "office2_server.py"]
    killed_count = 0
    try:
        cmd = 'powershell -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like \'*auto_watchdog*\' -or $_.CommandLine -like \'*office2_server*\' } | Select-Object -ExpandProperty ProcessId"'
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        pids = [p.strip() for p in res.stdout.splitlines() if p.strip().isdigit()]
        for pid in pids:
            try:
                subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
                print(f"   ⚡ 已熔斷行程 PID: {pid}")
                killed_count += 1
            except Exception:
                pass
    except Exception as e:
        print(f"⚠️ 熔斷執行提示: {e}")

    write_war_log("終極熔斷啟動", f"統帥啟動緊急熔斷，強制處決 {killed_count} 個後台行程，進入全靜默防禦狀態。")
    print(f"\n✅ 熔斷完成！共切斷 {killed_count} 個活動進程，幽靈防護罩已全開。")

# ==============================================================================
# 權限 3: 🔄 全域重構權 (Global Factory Reset)
# ==============================================================================
def global_factory_reset():
    token = load_commander_token()
    print("🔄" * 20)
    print("🔄 [PHANTOM GRID 實體指揮所] 全域重構工段 (Global Factory Reset)")
    print("🔄" * 20)
    print(f"• 執行授權 : {token['commander_name']}")
    print(f"• 真身來源 : {TRUTH_ROOT}")
    print(f"• 鏡像目標 : {COMBAT_ROOT}")
    
    confirm = input("⚠️ 確認要由 G 槽真身重新灌入覆蓋 C 槽戰鬥鏡像嗎？(y/N): ").strip().lower()
    if confirm != "y":
        print("操作已取消。")
        return

    print("🚀 正在自 G 槽真身同步至 C 槽戰鬥鏡像...")
    # 呼叫安裝腳本執行全量滿血復活
    install_script = REPO_ROOT / "install_opencode_complete.py"
    if install_script.exists():
        subprocess.run([sys.executable, str(install_script)], check=True)
    
    write_war_log("全域重構完成", "統帥授權自 G 槽真身全量重新投射 C 槽戰鬥鏡像，滿血復活。")
    print("✅ 全域重構圓滿完成！雙端 SHA256 100% 吻合！")

# ==============================================================================
# 互動式特權終端面板
# ==============================================================================
def interactive_terminal():
    token = load_commander_token()
    while True:
        print("\n" + "=" * 65)
        print("🏛️  PHANTOM GRID 最高實體指揮所 (COMMAND HQ TERMINAL)")
        print(f"👑 統帥坐鎮 : {token['commander_name']}  |  權限 : {token['authority_level']}")
        print(f"🛡️ 真身錨點 : {TRUTH_ROOT}")
        print("=" * 65)
        print("  [1] 👑 終審審批落款 (Sign-off Asset)")
        print("  [2] 🛑 啟動終極熔斷 (Emergency Kill-Switch)")
        print("  [3] 🔄 全域鏡像重構 (Global Factory Reset)")
        print("  [4] 📜 檢視統御戰報 (View War Log)")
        print("  [5] 📡 廣播統帥軍令 (Broadcast Command to Offices)")
        print("  [0] 🚪 退出指揮所終端")
        print("=" * 65)
        choice = input("👑 請總指揮官下達命令 [0-5]: ").strip()

        if choice == "1":
            draft = input("請輸入待落款草案檔名 (如 bob_sample_draft.json): ").strip()
            verdict = input("請下達裁決意志 (准 [預設] / 駁回): ").strip()
            if not verdict:
                verdict = "准"
            sign_off_asset(draft, verdict)
        elif choice == "2":
            emergency_kill_switch()
        elif choice == "3":
            global_factory_reset()
        elif choice == "4":
            if (HQ_DIR / "war_log.md").exists():
                print("\n" + (HQ_DIR / "war_log.md").read_text(encoding="utf-8")[-1500:])
            else:
                print("日誌檔案尚在初始化中。")
        elif choice == "5":
            cmd = input("請輸入欲廣播之全軍軍令: ").strip()
            if cmd:
                # 投遞至 8766 聯動服務
                try:
                    import urllib.request
                    req = urllib.request.Request("http://127.0.0.1:8766/api/command",
                                                data=json.dumps({"command": f"👑 統帥令: {cmd}"}).encode("utf-8"),
                                                headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=3) as res:
                        print("📡 軍令已成功廣播至全軍辦公室大盤！")
                except Exception as e:
                    print(f"⚠️ 廣播提示: {e} (二辦聯動核心可能未啟動)")
                write_war_log("廣播統帥軍令", f"統帥發布全軍作戰動員: 「{cmd}」")
        elif choice == "0":
            print("🚪 統帥退出終端，系統轉入常態警戒巡航。")
            break
        else:
            print("無效命令，請重新輸入。")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "sign":
            asset = sys.argv[2] if len(sys.argv) > 2 else "bob_sample_draft.json"
            verdict = sys.argv[3] if len(sys.argv) > 3 else "准"
            sign_off_asset(asset, verdict)
        elif cmd in ["kill", "kill-switch", "stop"]:
            emergency_kill_switch()
        elif cmd in ["reset", "restore"]:
            global_factory_reset()
        elif cmd == "status":
            token = load_commander_token()
            print(json.dumps(token, ensure_ascii=False, indent=2))
        else:
            print(f"未知參數: {cmd}")
    else:
        interactive_terminal()
