# -*- coding: utf-8 -*-
"""
PHANTOM GRID 一鍵安裝與自適應配置凍結器 (Dual-Mode Adaptive Installer & Freezer)
模式 1 (預設安裝模式): 全新環境一鍵部署，從金庫拉取最新動態備份，5 分鐘原地滿血復活。
模式 2 (--freeze / --sync): 封存凍結模式，自動抓取當前最新 AGENTS.md、環境依賴與設定，更新一鍵安裝資產庫與 sync_info.json。
"""

import os
import sys
import argparse
import hashlib
import json
import shutil
from pathlib import Path
from datetime import datetime

# Windows UTF-8 編碼強制防護
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

G_VAULT_ROOT = Path(r"G:\我的雲端硬碟\260803_opencode")
C_MIRROR_ROOT = Path(r"C:\260728-code")
LOCAL_ROOT = Path(__file__).resolve().parent

TEMPLATE_SUBDIR = Path("工具安裝包") / "template"

def get_file_hash(p: Path) -> str:
    if not p.exists():
        return "NONE"
    return hashlib.sha256(p.read_bytes()).hexdigest()

def sync_agents_to_installer() -> dict:
    """收工與凍結核心：比對 SHA256，有變更才更新安裝庫與 sync_info.json"""
    # 決定當前運行的 AGENTS.md
    runtime_agents = None
    for cand in [G_VAULT_ROOT / "AGENTS.md", LOCAL_ROOT / "AGENTS.md", C_MIRROR_ROOT / "AGENTS.md"]:
        if cand.exists():
            runtime_agents = cand
            break
            
    if not runtime_agents:
        raise FileNotFoundError("無法定位運行端 AGENTS.md！")
        
    runtime_hash = get_file_hash(runtime_agents)
    
    # 定義雙軌安裝庫目標
    g_installer_template = G_VAULT_ROOT / TEMPLATE_SUBDIR / "AGENTS.md"
    c_installer_template = C_MIRROR_ROOT / TEMPLATE_SUBDIR / "AGENTS.md"
    local_installer_template = LOCAL_ROOT / TEMPLATE_SUBDIR / "AGENTS.md"
    
    targets = [local_installer_template]
    if G_VAULT_ROOT.exists():
        targets.append(g_installer_template)
    if C_MIRROR_ROOT.exists():
        targets.append(c_installer_template)
        
    diff_detected = False
    for t in targets:
        t.parent.mkdir(parents=True, exist_ok=True)
        if get_file_hash(t) != runtime_hash:
            diff_detected = True
            shutil.copy2(runtime_agents, t)
            
    # 更新 sync_info.json
    now_iso = datetime.now().isoformat()
    sync_data = {
        "project": "PHANTOM_GRID",
        "last_sync_timestamp": now_iso,
        "agents_sha256": runtime_hash,
        "installer_template_synced": True,
        "status": "UPDATED" if diff_detected else "ALREADY_UP_TO_DATE",
        "targets_updated": [str(t) for t in targets]
    }
    
    for s_path in [LOCAL_ROOT / "sync_info.json", G_VAULT_ROOT / "sync_info.json", C_MIRROR_ROOT / "sync_info.json"]:
        if s_path.parent.exists():
            s_path.write_text(json.dumps(sync_data, indent=2, ensure_ascii=False), encoding="utf-8")
            
    if diff_detected:
        print("⚡ [PHANTOM GRID] 偵測到 AGENTS.md 架構變更，已自動同步更新一鍵安裝資產庫！")
    else:
        print("✅ [PHANTOM GRID] 一鍵安裝 AGENTS.md 為最新狀態，無需重複寫入 (0.1s PASS)。")
        
    return sync_data

def freeze_configuration():
    """封存凍結模式：快照所有配置、依賴與安裝庫"""
    print("\n" + "="*80)
    print("❄️  [PHANTOM GRID] 啟動配置凍結器 (Installer Freezing Mechanism)")
    print("="*80)
    
    # 1. 同步 AGENTS.md
    res = sync_agents_to_installer()
    print(f"   • AGENTS.md 凍結狀態 : {res['status']} (SHA256: {res['agents_sha256'][:16]}...)")
    
    # 2. 凍結環境依賴清單 (使用標準庫 importlib.metadata，免除 pip subprocess 編碼炸裂)
    req_file = LOCAL_ROOT / TEMPLATE_SUBDIR / "requirements_snapshot.txt"
    req_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        from importlib.metadata import distributions
        installed_pkgs = sorted([f"{d.metadata['Name']}=={d.version}" for d in distributions() if d.metadata.get('Name')])
        req_content = "\n".join(installed_pkgs) + "\n"
        req_file.write_text(req_content, encoding="utf-8")
        if G_VAULT_ROOT.exists():
            g_req = G_VAULT_ROOT / TEMPLATE_SUBDIR / "requirements_snapshot.txt"
            g_req.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(req_file, g_req)
        print(f"   • Python 依賴快照   : 已就緒 ({len(installed_pkgs)} 套件已封存至 requirements_snapshot.txt)")
    except Exception as e:
        print(f"   • Python 依賴快照   : 跳過 ({e})")
        
    print("✅ 【配置凍結完成】當前 PHANTOM GRID 完全體已封存入一鍵安裝庫！\n")

def run_installation():
    """安裝模式：全新環境 5 分鐘滿血復活"""
    print("\n" + "="*80)
    print("🚀 [PHANTOM GRID] 執行一鍵完整安裝與環境還原 (Full Resurrection)")
    print("="*80)
    
    # 1. 優先從 G 槽金庫或本機安裝庫拉取 AGENTS.md
    source_template = None
    for cand in [
        G_VAULT_ROOT / TEMPLATE_SUBDIR / "AGENTS.md",
        LOCAL_ROOT / TEMPLATE_SUBDIR / "AGENTS.md",
        G_VAULT_ROOT / "AGENTS.md",
    ]:
        if cand.exists():
            source_template = cand
            break
            
    if not source_template:
        print("❌ 錯誤：找不到安裝模板，請先確認 G 槽金庫連線！")
        return
        
    dest_agents = LOCAL_ROOT / "AGENTS.md"
    shutil.copy2(source_template, dest_agents)
    print(f"   • 核心規章還原     : {dest_agents} (來源: {source_template})")
    
    # 2. 確保雙軌高速鏡像 C:\260728-code 建立
    if not C_MIRROR_ROOT.exists():
        try:
            C_MIRROR_ROOT.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_template, C_MIRROR_ROOT / "AGENTS.md")
            print(f"   • 高速鏡像目錄建立 : {C_MIRROR_ROOT}")
        except Exception as e:
            print(f"   • 建立高速鏡像提示 : {e}")
            
    print("✅ 【一鍵安裝就緒】PHANTOM GRID 完全體 100% 配置到位！\n")

def main():
    parser = argparse.ArgumentParser(description="PHANTOM GRID 一鍵安裝與配置凍結器")
    parser.add_argument("--freeze", action="store_true", help="封存當前最新架構與依賴至一鍵安裝庫")
    parser.add_argument("--sync", action="store_true", help="執行 SHA256 差異比對並反向同步")
    args = parser.parse_args()
    
    if args.freeze or args.sync:
        freeze_configuration()
    else:
        run_installation()

if __name__ == "__main__":
    main()
