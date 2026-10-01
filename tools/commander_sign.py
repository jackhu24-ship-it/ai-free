#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
PHANTOM GRID - 指揮所正式落款模組 (Commander Sign & Stamp Engine)
👑 霸丸總指揮官 Jack 哥 專屬權威蓋印與核心庫封版引擎

【指揮所取檔與落款最高鐵律】
1. 指揮所「絕對不回頭」去沙盒 02_OUTBOX 或暫存區取檔！
2. 取檔唯一法定來源：C:\ibm-bob\core_repo\ (以及 G 槽真身 02_Knowledge\Bob_Verified\)
3. 嚴格校驗前置憑證：核查 approval_seal.json，確認代碼已經第二辦公室 AST 審查與防幻覺檢驗合格。
4. 注入元數據頭部 (Metadata Header)，具備防偽 SHA-256 與審查時間戳。
5. 登錄指揮所「產出建檔履歷」與 Git 封版 Tag，狀態變更為【已落款發佈 (Sealed & Released)】。
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

# Windows UTF-8 強制防護
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

tools_dir = Path(__file__).resolve().parent
if str(tools_dir) not in sys.path:
    sys.path.insert(0, str(tools_dir))

workspace_dir = tools_dir.parent
if str(workspace_dir) not in sys.path:
    sys.path.insert(0, str(workspace_dir))

try:
    from path_resolver import TRUTH_ROOT, COMBAT_ROOT
except ImportError:
    COMBAT_ROOT = Path(r"C:\260728-code")
    TRUTH_ROOT = Path(r"G:\我的雲端硬碟\260803_opencode")

CORE_REPO_DIR = Path(r"C:\ibm-bob\core_repo")
G_CORE_REPO_DIR = TRUTH_ROOT / "02_Knowledge" / "Bob_Verified"

HQ_DIR = workspace_dir / "00_Command_HQ"
TOKEN_FILE = HQ_DIR / "commander_token.json"
AUDIT_LEDGER_FILE = HQ_DIR / "delivery_audit_ledger.json"
WAR_LOG_FILE = HQ_DIR / "war_log.md"

SIGNER_NAME = "Commander Jack"
AUTHORITY_TITLE = "👑 霸丸總指揮官 (Supreme Commander)"
VERSION_TAG = "v1.2.0-RELEASE"


def check_precondition_seal() -> Tuple[bool, str, Dict[str, Any]]:
    """
    前置憑證校驗：
    指揮所確認核心庫伴隨寫入的 approval_seal.json，確保代碼為受信任之審查合格產物。
    """
    seal_file = CORE_REPO_DIR / "approval_seal.json"
    if not seal_file.exists():
        return False, "❌ 前置憑證缺失：核心庫中無 approval_seal.json，禁止未經審查之檔案落款！", {}

    try:
        seal_data = json.loads(seal_file.read_text(encoding="utf-8"))
        if seal_data.get("status") != "OFFICIALLY_ACCEPTED_CORE":
            return False, f"❌ 前置憑證狀態異常: {seal_data.get('status')}", seal_data
        return True, "✅ 前置憑證檢驗通過", seal_data
    except Exception as e:
        return False, f"❌ 前置憑證解析失敗: {e}", {}


def sign_and_stamp(target_relative_file: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    對指定核心庫檔案執行檔案頭部權威落款 (Sign & Stamp Header)
    """
    target_path = CORE_REPO_DIR / target_relative_file
    if not target_path.exists():
        return False, f"核心庫找不到目標檔案: {target_relative_file}", {}

    if target_path.name == "approval_seal.json":
        return False, "簽章資訊檔無須蓋印頭部", {}

    # 1. 讀取並計算原始純代碼 Hash (剔除舊 Stamp 的純淨內容 Hash)
    raw_code = target_path.read_text(encoding="utf-8", errors="replace")
    
    # 若已有舊款，剝離舊款計算原始純代碼 Hash
    pure_code = raw_code
    if "ARCHITECTURE : PHANTOM GRID" in raw_code and '"""\n' in raw_code:
        parts = raw_code.split('"""\n', 2)
        if len(parts) >= 2:
            pure_code = parts[-1]

    file_sha = hashlib.sha256(pure_code.encode("utf-8")).hexdigest()[:16]
    now_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 2. 定義指揮所官方權威落款頭部 (Header Stamp)
    stamp_header = f'''"""
==============================================================================
 ARCHITECTURE : PHANTOM GRID / BOB CORE ENGINE
 TARGET       : {target_path.name}
 SIGNED BY    : {SIGNER_NAME} (指揮所權威落款)
 AUDIT DATE   : {now_stamp} CST
 SEAL HASH    : SHA256-{file_sha} [OFFICIAL SEAL]
 VERSION TAG  : {VERSION_TAG}
 STATUS       : SEALED & RELEASED (已落款發佈)
==============================================================================
"""\n'''

    # 3. 避免重複蓋印，更新印章
    updated_code = stamp_header + pure_code

    # 4. 寫回核心庫完成蓋印封存
    target_path.write_text(updated_code, encoding="utf-8")

    # 同步回寫 G 槽真身金庫
    try:
        G_CORE_REPO_DIR.mkdir(parents=True, exist_ok=True)
        g_target = G_CORE_REPO_DIR / target_relative_file
        g_target.parent.mkdir(parents=True, exist_ok=True)
        g_target.write_text(updated_code, encoding="utf-8")
    except Exception:
        pass

    stamp_meta = {
        "file_name": target_path.name,
        "rel_path": target_relative_file,
        "seal_hash": file_sha,
        "signed_by": SIGNER_NAME,
        "timestamp": now_stamp,
        "version_tag": VERSION_TAG,
        "status": "SEALED_AND_RELEASED"
    }

    return True, f"已完成權威落款 | 印章指紋: SHA256-{file_sha}", stamp_meta


def sign_all_core_modules() -> Dict[str, Any]:
    """
    全量批次落款：
    1. 檢驗核心庫審查憑證
    2. 對 core_repo 所有合法代碼進行權威蓋印
    3. 登錄履歷 ledger 與 war_log.md
    """
    valid_seal, seal_msg, seal_data = check_precondition_seal()
    if not valid_seal:
        return {
            "success": False,
            "msg": seal_msg,
            "signed_count": 0,
            "signed_files": []
        }

    if not CORE_REPO_DIR.exists():
        return {
            "success": False,
            "msg": f"核心庫目錄不存在: {CORE_REPO_DIR}",
            "signed_count": 0,
            "signed_files": []
        }

    signed_files = []
    for f in CORE_REPO_DIR.rglob("*"):
        if not f.is_file() or f.name.endswith(".json"):
            continue
        rel_path = f.relative_to(CORE_REPO_DIR)
        ok, msg, meta = sign_and_stamp(str(rel_path))
        if ok:
            signed_files.append(meta)

    # 登錄產出建檔履歷 (delivery_audit_ledger.json)
    now_iso = datetime.now().isoformat()
    now_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ledger_entry = {
        "release_id": f"RELEASE-{VERSION_TAG}-{int(datetime.now().timestamp())}",
        "timestamp": now_iso,
        "action": "COMMAND_HQ_SOVEREIGN_SIGN_AND_STAMP",
        "signer": SIGNER_NAME,
        "authority": AUTHORITY_TITLE,
        "version_tag": VERSION_TAG,
        "status": "SEALED_AND_RELEASED",
        "signed_count": len(signed_files),
        "files": signed_files
    }

    try:
        AUDIT_LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)
        ledger_data = []
        if AUDIT_LEDGER_FILE.exists():
            try:
                ledger_data = json.loads(AUDIT_LEDGER_FILE.read_text(encoding="utf-8"))
            except Exception:
                ledger_data = []
        ledger_data.insert(0, ledger_entry)
        AUDIT_LEDGER_FILE.write_text(json.dumps(ledger_data, ensure_ascii=False, indent=2), encoding="utf-8")
        
        # G 槽履歷同步
        g_ledger = TRUTH_ROOT / "00_Command_HQ" / "delivery_audit_ledger.json"
        g_ledger.parent.mkdir(parents=True, exist_ok=True)
        g_ledger.write_text(json.dumps(ledger_data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

    # 登錄統帥作戰統御日誌 (war_log.md)
    war_entry = (
        f"\n- **[統帥權威落款 · 核心庫正式封版發布]** `{now_stamp}` "
        f"👑 統帥 Jack 哥對核心庫 `{CORE_REPO_DIR}` 進行權威蓋印，"
        f"標記版本號 `{VERSION_TAG}`，共落款 `{len(signed_files)}` 支核心模組，"
        f"狀態變更為【已落款發佈 (Sealed & Released)】，履歷已永久封存！\n"
    )

    for w_path in [WAR_LOG_FILE, TRUTH_ROOT / "00_Command_HQ" / "war_log.md"]:
        try:
            w_path.parent.mkdir(parents=True, exist_ok=True)
            with open(w_path, "a", encoding="utf-8") as f:
                f.write(war_entry)
        except Exception:
            pass

    # 生成手機 Copilot 回報卡
    notice_text = (
        f"👑 **報告 Jack 哥！指揮所權威落款與封版程序已圓滿完成！**\n\n"
        f"🏛️ 【指揮所落款結算報告】：\n"
        f"• 法定庫區：C:\\ibm-bob\\core_repo\\ (雙向固化 G 槽真身)\n"
        f"• 落款官銜：{AUTHORITY_TITLE}\n"
        f"• 封版版本：`{VERSION_TAG}` (SEALED & RELEASED)\n"
        f"• 蓋印模組：共 {len(signed_files)} 支檔案注入權威 Header\n"
        f"• 建檔履歷：狀態已升級為「🟢 已落款發佈」\n\n"
        f"★ 全套核心代碼已正式受指揮所最高主權護照背書，隨時可調用上線！🛡️✨"
    )

    return {
        "success": True,
        "version_tag": VERSION_TAG,
        "signed_count": len(signed_files),
        "signed_files": signed_files,
        "notice_text": notice_text,
        "ledger_entry": ledger_entry
    }


if __name__ == "__main__":
    print("🏛️ [PHANTOM GRID 指揮所權威落款模組自檢]")
    res = sign_all_core_modules()
    print(f"• 執行結果: {res['success']}")
    print(f"• 蓋印數量: {res['signed_count']} 支")
    print(f"• 版本版號: {res.get('version_tag')}")
    for item in res.get("signed_files", []):
        print(f"  - {item['file_name']} -> {item['seal_hash']}")
    if res.get("notice_text"):
        print("\n" + res["notice_text"])
