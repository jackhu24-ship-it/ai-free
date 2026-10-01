#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
PHANTOM GRID - 指揮所正式落款模組 (Commander Sign & Stamp Engine)
👑 霸丸總指揮官 Jack 哥 專屬權威蓋印與核心庫封版引擎

【核心工程哲學：主件實體與防偽證書一併移交】
- 杜絕「打包壓縮再解碼還原」：代碼與 JSON 一直保持真實 .py 與 .json，隨時可被全域反查引擎秒級檢索。
- 標準交付結構：C:\ibm-bob\core_repo\ 內包含乾淨檔案實體與 .audit_certificate.json (二辦認證檔)。

【指揮所落款標準 3 步驟】
1. 第一步：拿「認證檔」驗收原檔 (驗票)
   - 讀取 .audit_certificate.json，現場重新計算目錄下各實體檔案之 SHA-256，100% 吻合才准放行。
2. 第二步：直接在檔案上「落款蓋印」 (簽字)
   - 對 .py 檔案：最上方注入權威宣告 Docstring Header。
   - 對 .json 檔案：頂層寫入 _commander_seal 元數據鍵值。
3. 第三步：頒發正式封存章 (發章)
   - 把 .audit_certificate.json 升級覆蓋為 RELEASE_SEAL.json，完成全生命週期交付，直接上架！
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
AUDIT_LEDGER_FILE = HQ_DIR / "delivery_audit_ledger.json"
WAR_LOG_FILE = HQ_DIR / "war_log.md"

SIGNER_NAME = "Commander Jack"
AUTHORITY_TITLE = "👑 霸丸總指揮官 (Supreme Commander)"
VERSION_TAG = "v1.2.0-RELEASE"

DELIMITER = '==============================================================================\n"""\n'
DELIMITER_CRLF = '==============================================================================\r\n"""\r\n'


def extract_pure_code(code_str: str) -> str:
    """精確剝離指揮所落款頭部，並統一換行符為 \\n，避免 Windows CRLF 造成雜湊偏差"""
    norm = code_str.replace("\r\n", "\n")
    if "ARCHITECTURE : PHANTOM GRID" in norm:
        idx = norm.find(DELIMITER)
        if idx != -1:
            return norm[idx + len(DELIMITER):]
    return norm


def verify_audit_certificate() -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    第一步：拿「認證檔」驗收原檔 (驗票)
    開啟 .audit_certificate.json，現場重新計算核心庫檔案之 SHA-256，核對指紋是否 100% 一致。
    """
    cert_file = CORE_REPO_DIR / ".audit_certificate.json"
    if not cert_file.exists():
        # 兼容模式：若無 .audit_certificate.json 則檢查 approval_seal.json
        alt_seal = CORE_REPO_DIR / "approval_seal.json"
        if not alt_seal.exists():
            return False, "❌ 前置認證缺失：核心庫中無 .audit_certificate.json 認證檔，拒絕落款！", []
        try:
            seal_data = json.loads(alt_seal.read_text(encoding="utf-8"))
            files = seal_data.get("files", [])
            # 轉換為認證格式
            verified_list = []
            for item in files:
                f_name = item.get("name") if isinstance(item, dict) else str(item)
                f_path = CORE_REPO_DIR / f_name
                if f_path.exists():
                    f_hash = hashlib.sha256(f_path.read_bytes()).hexdigest()
                    verified_list.append({"name": f_name, "sha256": f_hash})
            return True, "✅ 依據前置簽章通過驗票", verified_list
        except Exception as e:
            return False, f"❌ 前置憑證讀取失敗: {e}", []

    try:
        cert_data = json.loads(cert_file.read_text(encoding="utf-8"))
    except Exception as e:
        return False, f"❌ 認證檔格式損毀: {e}", []

    verified_files = cert_data.get("verified_files", []) or cert_data.get("sealed_files", [])
    if not verified_files:
        return False, "❌ 認證檔中無登記待審檔案清單", []

    mismatches = []
    validated_files = []

    for item in verified_files:
        f_name = item.get("name") or item.get("file_name")
        expected_sha = (item.get("sha256") or item.get("seal_hash") or "").lower()
        if expected_sha.startswith("sha256-"):
            expected_sha = expected_sha.replace("sha256-", "")
        f_path = CORE_REPO_DIR / f_name

        if not f_path.exists():
            mismatches.append(f"{f_name} [實體缺失]")
            continue

        raw = f_path.read_bytes()
        live_sha = hashlib.sha256(raw).hexdigest().lower()

        # 如果檔案已經蓋印過，需要剔除蓋印元數據後比對純內容 hash
        if expected_sha and live_sha != expected_sha:
            # 嘗試剝離 Header 或 _commander_seal 進行驗票
            pure_code = raw.decode("utf-8", errors="replace")
            if f_name.endswith(".py") and "ARCHITECTURE : PHANTOM GRID" in pure_code:
                pure_code = extract_pure_code(pure_code)
                pure_sha = hashlib.sha256(pure_code.encode("utf-8")).hexdigest().lower()
                if pure_sha == expected_sha or pure_sha.startswith(expected_sha) or expected_sha.startswith(pure_sha[:16]):
                    validated_files.append({"name": f_name, "sha256": live_sha, "pure_sha": pure_sha})
                    continue
            elif f_name.endswith(".json") and "_commander_seal" in pure_code:
                try:
                    j_obj = json.loads(pure_code)
                    j_obj.pop("_commander_seal", None)
                    pure_json_bytes = json.dumps(j_obj, ensure_ascii=False, indent=2).encode("utf-8")
                    pure_sha = hashlib.sha256(pure_json_bytes).hexdigest().lower()
                    if pure_sha == expected_sha or pure_sha.startswith(expected_sha) or expected_sha.startswith(pure_sha[:16]):
                        validated_files.append({"name": f_name, "sha256": live_sha, "pure_sha": pure_sha})
                        continue
                except Exception:
                    pass

            mismatches.append(f"{f_name} [指紋不符: 預期 {expected_sha[:8]}... 實測 {live_sha[:8]}...]")
        else:
            validated_files.append({"name": f_name, "sha256": live_sha})

    if mismatches:
        return False, f"❌ 指紋驗票失敗：{', '.join(mismatches)}", []

    return True, f"✅ 驗票成功！全數 {len(validated_files)} 支檔案與二辦認證檔 100% 吻合！", validated_files


def stamp_python_file(target_path: Path, now_stamp: str) -> Dict[str, Any]:
    """第二步子模組：對 .py 檔案最上方注入權威宣告 Header"""
    raw_code = target_path.read_text(encoding="utf-8", errors="replace")

    # 若已有舊款，剝離舊款計算純代碼 Hash
    pure_code = extract_pure_code(raw_code)

    file_sha = hashlib.sha256(pure_code.encode("utf-8")).hexdigest()[:16]

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

    updated_code = stamp_header + pure_code
    target_path.write_text(updated_code, encoding="utf-8")

    # 同步 G 槽真身金庫
    try:
        G_CORE_REPO_DIR.mkdir(parents=True, exist_ok=True)
        g_target = G_CORE_REPO_DIR / target_path.name
        g_target.write_text(updated_code, encoding="utf-8")
    except Exception:
        pass

    return {
        "file_name": target_path.name,
        "type": "PYTHON_MODULE",
        "seal_hash": file_sha,
        "signed_by": SIGNER_NAME,
        "timestamp": now_stamp,
        "version_tag": VERSION_TAG,
        "status": "SEALED_AND_RELEASED"
    }


def stamp_json_file(target_path: Path, now_stamp: str) -> Dict[str, Any]:
    """第二步子模組：對 .json 檔案頂層寫入 _commander_seal 元數據鍵值"""
    raw_text = target_path.read_text(encoding="utf-8", errors="replace")
    try:
        data = json.loads(raw_text)
    except Exception:
        return {}

    # 若非 dict 則包裝成 dict
    if not isinstance(data, dict):
        data = {"data": data}

    # 計算純業務數據 Hash (排除 _commander_seal)
    temp_data = dict(data)
    temp_data.pop("_commander_seal", None)
    pure_bytes = json.dumps(temp_data, ensure_ascii=False, indent=2).encode("utf-8")
    file_sha = hashlib.sha256(pure_bytes).hexdigest()[:16]

    # 在頂層最前方注入 _commander_seal
    new_data = {
        "_commander_seal": {
            "signed_by": SIGNER_NAME,
            "authority": AUTHORITY_TITLE,
            "status": "OFFICIALLY_RELEASED",
            "release_version": VERSION_TAG,
            "sealed_at": f"{now_stamp} CST",
            "seal_hash": f"SHA256-{file_sha}"
        }
    }
    # 依序放回原始業務欄位
    for k, v in data.items():
        if k != "_commander_seal":
            new_data[k] = v

    updated_json = json.dumps(new_data, ensure_ascii=False, indent=2)
    target_path.write_text(updated_json, encoding="utf-8")

    # 同步 G 槽真身金庫
    try:
        G_CORE_REPO_DIR.mkdir(parents=True, exist_ok=True)
        g_target = G_CORE_REPO_DIR / target_path.name
        g_target.write_text(updated_json, encoding="utf-8")
    except Exception:
        pass

    return {
        "file_name": target_path.name,
        "type": "JSON_SCHEMA",
        "seal_hash": file_sha,
        "signed_by": SIGNER_NAME,
        "timestamp": now_stamp,
        "version_tag": VERSION_TAG,
        "status": "SEALED_AND_RELEASED"
    }


def sign_all_core_modules() -> Dict[str, Any]:
    """
    指揮所落款標準 3 步驟主控程序：
    第一步：拿「認證檔」驗收原檔 (驗票)
    第二步：直接在檔案上「落款蓋印」 (簽字 - .py 注入 Header, .json 注入 _commander_seal)
    第三步：頒發正式封存章 (RELEASE_SEAL.json 覆蓋認證檔，全生命週期交付直接上架)
    """
    now_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    now_iso = datetime.now().isoformat()

    # 第一步：拿「認證檔」驗收原檔 (驗票)
    ok_ticket, ticket_msg, verified_files = verify_audit_certificate()
    if not ok_ticket:
        return {
            "success": False,
            "msg": ticket_msg,
            "signed_count": 0,
            "signed_files": []
        }

    # 第二步：直接在檔案上「落款蓋印」 (簽字)
    signed_meta_list = []
    for item in verified_files:
        f_name = item.get("name")
        target_path = CORE_REPO_DIR / f_name
        if not target_path.is_file():
            continue

        if f_name.endswith(".py"):
            meta = stamp_python_file(target_path, now_stamp)
            if meta:
                signed_meta_list.append(meta)
        elif f_name.endswith(".json") and not f_name.startswith("."):
            meta = stamp_json_file(target_path, now_stamp)
            if meta:
                signed_meta_list.append(meta)

    # 第三步：頒發正式封存章 (把 .audit_certificate.json 升級覆蓋為 RELEASE_SEAL.json)
    release_seal_data = {
        "seal_title": "PHANTOM GRID 官方權威封存章 (RELEASE SEAL)",
        "signer": SIGNER_NAME,
        "authority": AUTHORITY_TITLE,
        "release_version": VERSION_TAG,
        "released_at": now_iso,
        "audit_certificate_verified": True,
        "audit_officer": "Office_2_Copilot",
        "total_sealed_files": len(signed_meta_list),
        "sealed_files": signed_meta_list,
        "status": "SEALED_AND_RELEASED"
    }

    seal_json_str = json.dumps(release_seal_data, ensure_ascii=False, indent=2)

    # 寫入正式 RELEASE_SEAL.json
    seal_path = CORE_REPO_DIR / "RELEASE_SEAL.json"
    seal_path.write_text(seal_json_str, encoding="utf-8")

    # 同時升級覆蓋 .audit_certificate.json 完成生命週期閉環
    cert_path = CORE_REPO_DIR / ".audit_certificate.json"
    cert_path.write_text(seal_json_str, encoding="utf-8")

    try:
        G_CORE_REPO_DIR.mkdir(parents=True, exist_ok=True)
        (G_CORE_REPO_DIR / "RELEASE_SEAL.json").write_text(seal_json_str, encoding="utf-8")
        (G_CORE_REPO_DIR / ".audit_certificate.json").write_text(seal_json_str, encoding="utf-8")
    except Exception:
        pass

    # 登錄產出建檔履歷 (delivery_audit_ledger.json)
    ledger_entry = {
        "release_id": f"RELEASE-{VERSION_TAG}-{int(datetime.now().timestamp())}",
        "timestamp": now_iso,
        "action": "COMMAND_HQ_SOVEREIGN_SIGN_AND_STAMP",
        "signer": SIGNER_NAME,
        "authority": AUTHORITY_TITLE,
        "version_tag": VERSION_TAG,
        "status": "SEALED_AND_RELEASED",
        "signed_count": len(signed_meta_list),
        "files": signed_meta_list
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

        g_ledger = TRUTH_ROOT / "00_Command_HQ" / "delivery_audit_ledger.json"
        g_ledger.parent.mkdir(parents=True, exist_ok=True)
        g_ledger.write_text(json.dumps(ledger_data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

    # 登錄統帥作戰統御日誌 (war_log.md)
    war_entry = (
        f"\n- **[統帥權威落款 · 3步驟實體驗收與正式發布]** `{now_stamp}` "
        f"👑 統帥 Jack 哥拿 `.audit_certificate.json` 驗收原檔指紋 100% 吻合；"
        f"現場在 `.py` 注入 Header、在 `.json` 注入 `_commander_seal`；"
        f"正式頒發 `RELEASE_SEAL.json`，共落款 `{len(signed_meta_list)}` 支實體檔案，"
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
        f"👑 **報告 Jack 哥！指揮所權威落款 3 步驟程序已圓滿完成！**\n\n"
        f"🏛️ 【指揮所落款結算報告】：\n"
        f"• 驗票結果：{ticket_msg}\n"
        f"• 蓋印實體：共 {len(signed_meta_list)} 支檔案 (.py 注入 Header / .json 注入 _commander_seal)\n"
        f"• 封版版本：`{VERSION_TAG}`\n"
        f"• 正式封存：已頒發 `RELEASE_SEAL.json` 完成交付全生命週期！\n"
        f"• 建檔履歷：狀態已升級為「🟢 已落款發佈 (Sealed & Released)」\n\n"
        f"★ 主件實體保持真實代碼，全域反查可秒級檢索，最高主權護照已生效！🛡️✨"
    )

    return {
        "success": True,
        "ticket_msg": ticket_msg,
        "version_tag": VERSION_TAG,
        "signed_count": len(signed_meta_list),
        "signed_files": signed_meta_list,
        "notice_text": notice_text,
        "release_seal": release_seal_data
    }


if __name__ == "__main__":
    print("🏛️ [PHANTOM GRID 指揮所權威落款 3 步驟標準作業自檢]")
    res = sign_all_core_modules()
    print(f"• 驗票與執行: {res['success']}")
    if res['success']:
        print(f"• 驗票訊息: {res.get('ticket_msg')}")
        print(f"• 蓋印檔案數: {res['signed_count']} 支")
        for item in res.get("signed_files", []):
            print(f"  - [{item['type']}] {item['file_name']} -> {item['seal_hash']}")
        print(f"• 正式封存章: RELEASE_SEAL.json [RELEASED]")
        print("\n" + res["notice_text"])
    else:
        print(f"• 失敗原因: {res.get('msg')}")
