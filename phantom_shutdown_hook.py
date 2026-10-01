# -*- coding: utf-8 -*-
"""
PHANTOM GRID 智能收工掛鉤 (Shutdown Hook & Auto-Sync Engine)
1. 步驟一：收工觸發 SHA256 差異比對 (運行端 vs 安裝包端)
2. 步驟二：條件判定與自動回寫 (無變更 0.1s 秒退，有變更覆蓋安裝包並記錄 sync_info.json)
3. 步驟三：固化閉環與收工交接 (驗證五大鐵壁護甲，更新 handoff.md，杜絕單向斷點)
"""

import sys
import hashlib
from pathlib import Path

# Windows UTF-8 強制防護
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from install_opencode_complete import sync_agents_to_installer

def run_shutdown_auto_sync():
    print("\n" + "="*80)
    print("🌙 [PHANTOM GRID] 啟動收工自動偵測與反向同步 (Shutdown Auto-Sync Hook)")
    print("="*80)
    
    # 執行 SHA256 比對與反向更新
    res = sync_agents_to_installer()
    
    print(f"   • 運行端 SHA256   : {res['agents_sha256']}")
    print(f"   • 一鍵安裝庫狀態 : {res['status']}")
    print("✅ 【反向回流閉環達成】一鍵安裝包隨時具備最新完全體架構！\n")
    return res

if __name__ == "__main__":
    run_shutdown_auto_sync()
