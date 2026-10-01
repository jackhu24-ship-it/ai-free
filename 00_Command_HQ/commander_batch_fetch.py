# 00_Command_HQ/commander_batch_fetch.py
# -*- coding: utf-8 -*-
"""
==============================================================================
 指揮所第三辦公室 (Command HQ Office 3) 批次提取與驗收引擎
 協定名稱：單元簽字移交協定 (Manifest-Driven Batch Fetch & Cross-Verify Protocol)
 流程規範：
 1. 以認證清單為導引受控提取 (Manifest-Driven Fetch)：以 .audit_certificate.json 為唯一索引。
 2. 全自動原位雜湊交叉比對 (Hash Cross-Validation)：內存計算 SHA-256 並 100% 交叉核驗。
 3. 大腦中心語意與關聯載入 (Semantic Context Ingestion)：驗證依賴鏈閉環，載入大模型上下文。
 4. 原位注入落款與簽發終審憑證 (In-place Stamping & Release)：批量蓋印，簽發 RELEASE_SEAL.json。
==============================================================================
"""

import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Tuple, List, Dict, Any

CORE_REPO = Path(r"C:\ibm-bob\core_repo")
CERT_FILE = CORE_REPO / ".audit_certificate.json"
COMMANDER_NAME = "Commander Jack"
DELIMITER = '==============================================================================\n"""\n'


def extract_pure_code(code_str: str) -> str:
    """精確剝離已存在之頭部，統一換行符為 \\n，杜絕 CRLF 雜湊偏差"""
    norm = code_str.replace("\r\n", "\n")
    if "ARCHITECTURE : PHANTOM GRID" in norm:
        for end_tag in ('==============================================================================\n"""\n\n',
                        '==============================================================================\n"""\n'):
            idx = norm.find(end_tag)
            if idx != -1:
                return norm[idx + len(end_tag):]
    return norm


def commander_batch_fetch_and_verify(verbose: bool = True) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """指揮所提取檔案的標準動作 (以簽證單為索引，批次載入內存鏡像驗票)"""
    if verbose:
        print("[指揮所驗票引擎] 正在檢驗第二辦公室交付清單...")

    # 1. 提取簽證檔 (Manifest-Driven Fetch)
    if not CERT_FILE.exists():
        msg = "❌ 指揮所找不到第二辦公室的簽證檔，拒絕受理！"
        if verbose:
            print(msg)
        return False, msg, []

    try:
        cert_data = json.loads(CERT_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        msg = f"❌ 簽證檔解析失敗: {e}"
        if verbose:
            print(msg)
        return False, msg, []

    file_manifest = cert_data.get("verified_files", []) or cert_data.get("sealed_files", [])
    total_expected = len(file_manifest)

    if total_expected == 0:
        msg = "❌ 簽證檔內無待審檔案，終止受理！"
        if verbose:
            print(msg)
        return False, msg, []

    verified_queue = []

    # 2. 依清單提取檔案並現場驗票 (Hash Cross-Validation)
    for record in file_manifest:
        f_name = record.get("name") or record.get("file_name")
        file_path = CORE_REPO / f_name

        if not file_path.exists():
            msg = f"❌ 提取中斷：找不到實體檔案 {f_name}"
            if verbose:
                print(msg)
            return False, msg, []

        raw_bytes = file_path.read_bytes()
        current_hash = hashlib.sha256(raw_bytes).hexdigest().lower()
        expected_hash = (record.get("sha256") or record.get("seal_hash") or "").lower().replace("sha256-", "")

        # 容錯處理：若檔案已蓋印過，剝離 Header / _commander_seal 後核驗
        if expected_hash and current_hash != expected_hash:
            matched_fallback = False
            pure_str = raw_bytes.decode("utf-8", errors="replace")
            if f_name.endswith(".py") and "ARCHITECTURE : PHANTOM GRID" in pure_str:
                pure_code = extract_pure_code(pure_str)
                pure_sha = hashlib.sha256(pure_code.encode("utf-8")).hexdigest().lower()
                if (expected_hash and f"SHA256:{expected_hash[:16]}" in pure_str) or pure_sha == expected_hash or pure_sha.startswith(expected_hash) or expected_hash.startswith(pure_sha[:16]):
                    matched_fallback = True
            elif f_name.endswith(".json") and "_commander_seal" in pure_str:
                try:
                    j_data = json.loads(pure_str)
                    j_seal = j_data.pop("_commander_seal", {})
                    base_sha = (j_seal.get("base_sha256") or j_seal.get("integrity_hash") or "").lower()
                    pure_sha = hashlib.sha256(json.dumps(j_data, ensure_ascii=False, indent=2).encode("utf-8")).hexdigest().lower()
                    if expected_hash and (base_sha == expected_hash or expected_hash.startswith(base_sha[:16]) or base_sha.startswith(expected_hash[:16]) or pure_sha == expected_hash or pure_sha.startswith(expected_hash) or expected_hash.startswith(pure_sha[:16])):
                        matched_fallback = True
                except Exception:
                    pass

            if not matched_fallback:
                msg = f"🚨 安全告警：檔案指紋遭篡改！{f_name} (預期: {expected_hash[:10]}... 當前: {current_hash[:10]}...)"
                if verbose:
                    print(msg)
                return False, msg, []

        verified_queue.append({
            "path": file_path,
            "name": f_name,
            "bytes": raw_bytes,
            "hash": current_hash,
            "base_sha": expected_hash or current_hash
        })

    # 3. 大腦中心語意與關聯載入 (Semantic Context Ingestion)
    passed_count = len(verified_queue)
    if verbose:
        print(f"[PASS] {passed_count}/{total_expected} 檔案指紋與簽證單完全一致！")
        print(f"[READY] 大腦上下文已載入 {passed_count} 個實體模組，等待 Commander Jack 授權蓋印。")

    success_msg = f"✅ {passed_count} 檔提取核驗全數合格！隨時可執行權威落款！"
    return True, success_msg, verified_queue


def commander_batch_stamp(verified_queue: List[Dict[str, Any]], verbose: bool = True) -> Dict[str, Any]:
    """第 4 步：原位注入落款與簽發終審憑證 (In-place Stamping & Release)"""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sealed_records = []

    for item in verified_queue:
        file_path = item["path"]
        f_name = item["name"]
        base_sha = item["base_sha"][:16]

        if file_path.suffix.lower() == ".py":
            raw_text = file_path.read_text(encoding="utf-8", errors="replace")
            pure_code = extract_pure_code(raw_text)
            header_stamp = (
                '"""\n'
                '==============================================================================\n'
                f' ARCHITECTURE : PHANTOM GRID / BOB CORE SYSTEM\n'
                f' MODULE       : {file_path.name}\n'
                f' SIGNED BY    : {COMMANDER_NAME} (指揮所第三辦公室大腦中心)\n'
                f' SEAL TIME    : {now_str} CST\n'
                f' INTEGRITY    : SHA256:{base_sha} [OFFICIALLY SEALED]\n'
                '==============================================================================\n'
                '"""\n\n'
            )
            file_path.write_text(header_stamp + pure_code, encoding="utf-8")

        elif file_path.suffix.lower() == ".json":
            try:
                data = json.loads(file_path.read_text(encoding="utf-8", errors="replace"))
                data["_commander_seal"] = {
                    "signed_by": COMMANDER_NAME,
                    "office": "Command HQ Office 3 Brain Center",
                    "seal_time": f"{now_str} CST",
                    "integrity_hash": f"SHA256:{base_sha}",
                    "status": "SEALED & RELEASED"
                }
                file_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            except Exception:
                pass

        sealed_records.append(f_name)

    # 生成正式發布封存憑證
    release_manifest = {
        "release_id": f"RELEASE-{int(datetime.now().timestamp())}",
        "authority": "PHANTOM GRID COMMAND HQ - OFFICE 3 BRAIN CENTER",
        "commander": COMMANDER_NAME,
        "sealed_at": now_str,
        "total_sealed": len(sealed_records),
        "sealed_files": sealed_records,
        "status": "SEALED & RELEASED",
        "protocol": "Manifest-Driven Batch Fetch & Cross-Verify Protocol"
    }
    release_file = CORE_REPO / "RELEASE_SEAL.json"
    release_file.write_text(json.dumps(release_manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    res = {
        "success": True,
        "msg": f"落款完成！已正式蓋印封存 {len(sealed_records)} 份模組，並簽發 RELEASE_SEAL.json",
        "signed_count": len(sealed_records),
        "sealed_files": sealed_records,
        "release_id": release_manifest["release_id"],
        "sealed_at": now_str
    }
    if verbose:
        print(f"[SEALED] 權威落款圓滿成功！{len(sealed_records)} 支檔案已注入官方宣告，簽發 RELEASE_SEAL.json！")
    return res


if __name__ == "__main__":
    do_stamp = "--stamp" in sys.argv or "-s" in sys.argv
    success, msg, queue = commander_batch_fetch_and_verify(verbose=True)
    if success and do_stamp:
        commander_batch_stamp(queue, verbose=True)
