# 00_Command_HQ/commander_stamp_executor.py
# -*- coding: utf-8 -*-
"""
==============================================================================
 指揮所第三辦公室 (Command HQ Office 3) 權威落款執行引擎
 核心原則：原地注入印章元數據，不破壞程式原有機制，並產出最終法定憑證。
 落款三大動作：
 1. .py 檔案：原位注入「權威宣告頭部 (Official Header Stamp)」
 2. .json 檔案：頂層注入 _commander_seal 節點 (排在最上方)
 3. 核心庫根目錄：簽發全域總憑證 RELEASE_SEAL.json (發佈大印)
==============================================================================
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

try:
    from commander_batch_fetch import commander_batch_fetch_and_verify, extract_pure_code
except ImportError:
    try:
        from tools.commander_batch_fetch import commander_batch_fetch_and_verify, extract_pure_code
    except ImportError:
        from commander_batch_fetch import commander_batch_fetch_and_verify, extract_pure_code

CORE_REPO = Path(r"C:\ibm-bob\core_repo")
COMMANDER_NAME = "Commander Jack"


def execute_final_stamping(verified_queue: List[Dict[str, Any]] = None, verbose: bool = True) -> Tuple[bool, str, Dict[str, Any]]:
    """對通過驗收的 10 個檔案執行原位落款"""
    if verified_queue is None:
        # 若未傳入佇列，先呼叫提取驗票引擎進行受控驗證
        success, msg, verified_queue = commander_batch_fetch_and_verify(verbose=verbose)
        if not success:
            return False, f"落款中止：驗票未通過 ({msg})", {}

    now_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_code = datetime.now().strftime("%Y%m%d")
    release_id = f"REL-{date_code}-{int(datetime.now().timestamp()) % 1000:03d}"
    sealed_names = []

    for item in verified_queue:
        file_path = item["path"]
        raw_hash = item.get("base_sha") or item.get("hash")
        hash_16 = raw_hash[:16]
        
        # 1. 處理 Python 模組落款
        if file_path.suffix.lower() == ".py":
            code_text = file_path.read_text(encoding="utf-8", errors="replace")
            pure_code = extract_pure_code(code_text)
            header = (
                '"""\n'
                '==============================================================================\n'
                f' ARCHITECTURE : PHANTOM GRID / BOB CORE REPO\n'
                f' MODULE       : {file_path.name}\n'
                f' SIGNED BY    : {COMMANDER_NAME} (指揮所權威落款)\n'
                f' SEAL TIME    : {now_stamp} CST\n'
                f' STATUS       : OFFICIALLY RELEASED & SEALED\n'
                f' INTEGRITY    : SHA256:{hash_16}... [VERIFIED]\n'
                '==============================================================================\n'
                '"""\n\n'
            )
            # 原位注入頭部印章，保持程式碼原有機制
            file_path.write_text(header + pure_code, encoding="utf-8")
            sealed_names.append(file_path.name)

        # 2. 處理 JSON 配置落款
        elif file_path.suffix.lower() == ".json":
            try:
                json_raw = file_path.read_text(encoding="utf-8", errors="replace")
                json_obj = json.loads(json_raw)
                # 剝離舊的印章節點，避免重複嵌套
                json_obj.pop("_commander_seal", None)
                seal_data = {
                    "_commander_seal": {
                        "signed_by": COMMANDER_NAME,
                        "seal_time": f"{now_stamp} CST",
                        "status": "OFFICIALLY_RELEASED",
                        "base_sha256": raw_hash
                    }
                }
                # 確保印章排在最上方
                combined = {**seal_data, **json_obj}
                file_path.write_text(json.dumps(combined, indent=2, ensure_ascii=False), encoding="utf-8")
                sealed_names.append(file_path.name)
            except Exception as e:
                if verbose:
                    print(f"⚠️ JSON 落款處理警告: {file_path.name}: {e}")

        # 3. 處理 Markdown 文檔落款
        elif file_path.suffix.lower() == ".md":
            md_text = file_path.read_text(encoding="utf-8", errors="replace")
            if "<!-- COMMANDER_SEAL" not in md_text:
                seal_comment = (
                    f"<!-- COMMANDER_SEAL : {COMMANDER_NAME} | {now_stamp} CST | SHA256:{hash_16} | STATUS: SEALED -->\n\n"
                )
                file_path.write_text(seal_comment + md_text, encoding="utf-8")
            sealed_names.append(file_path.name)

    # 3. 產出發佈大印 (RELEASE_SEAL.json)
    release_master = {
        "release_id": release_id,
        "commander": COMMANDER_NAME,
        "seal_time": f"{now_stamp} CST",
        "status": "ALL_MODULES_SEALED",
        "total_sealed": len(sealed_names),
        "sealed_manifest": sealed_names
    }
    
    seal_file = CORE_REPO / "RELEASE_SEAL.json"
    seal_file.write_text(json.dumps(release_master, indent=2, ensure_ascii=False), encoding="utf-8")

    success_msg = f"🎖️ {len(sealed_names)} 個模組已原位注入落款印章，並簽發 RELEASE_SEAL.json 正式封版入庫！"
    if verbose:
        print(f"[SUCCESS] {success_msg}")
        print(f"[RELEASE] 憑證識別號: {release_id} | 封存模組數: {len(sealed_names)}")

    return True, success_msg, release_master


if __name__ == "__main__":
    success, msg, data = execute_final_stamping(verbose=True)
    if not success:
        sys.exit(1)
