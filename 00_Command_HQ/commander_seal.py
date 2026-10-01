# C:\ibm-bob\commander_seal.py
# -*- coding: utf-8 -*-
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

CORE_REPO_DIR = Path(r"C:\ibm-bob\core_repo")
COMMANDER_NAME = "Commander Jack"

DELIMITER = '==============================================================================\n"""\n'


def extract_pure_code(code_str: str) -> str:
    """精確剝離舊款頭部，並統一換行符為 \n，避免 Windows CRLF 雜湊偏差"""
    norm = code_str.replace("\r\n", "\n")
    if "ARCHITECTURE : PHANTOM GRID" in norm:
        idx = norm.find(DELIMITER)
        if idx != -1:
            return norm[idx + len(DELIMITER):]
    return norm


class CommanderSealer:
    @classmethod
    def verify_and_stamp(cls) -> Dict[str, Any]:
        cert_file = CORE_REPO_DIR / ".audit_certificate.json"
        if not cert_file.exists():
            return {"success": False, "msg": "核心庫無審查認證檔，指揮所拒絕落款"}

        try:
            cert_data = json.loads(cert_file.read_text(encoding="utf-8"))
        except Exception as e:
            return {"success": False, "msg": f"認證檔解析失敗: {e}"}

        verified_files = cert_data.get("verified_files", []) or cert_data.get("sealed_files", [])
        if not verified_files:
            return {"success": False, "msg": "認證檔無待審檔案"}

        # 1. 驗票階段：逐一比對檔案指紋
        for record in verified_files:
            f_name = record.get("name") or record.get("file_name")
            target_path = CORE_REPO_DIR / f_name
            if not target_path.exists():
                return {"success": False, "msg": f"驗票失敗：檔案遺失 {f_name}"}

            expected_sha = (record.get("sha256") or record.get("seal_hash") or "").lower().replace("sha256-", "")
            current_raw = target_path.read_bytes()
            current_hash = hashlib.sha256(current_raw).hexdigest().lower()

            if expected_sha and current_hash != expected_sha:
                # 容錯處理：若檔案已落款過，剝離 Header / _commander_seal 後核驗
                pure_str = current_raw.decode("utf-8", errors="replace")
                if f_name.endswith(".py") and "ARCHITECTURE : PHANTOM GRID" in pure_str:
                    pure_code = extract_pure_code(pure_str)
                    pure_sha = hashlib.sha256(pure_code.encode("utf-8")).hexdigest().lower()
                    if pure_sha == expected_sha or pure_sha.startswith(expected_sha) or expected_sha.startswith(pure_sha[:16]):
                        continue
                elif f_name.endswith(".json") and "_commander_seal" in pure_str:
                    try:
                        j_data = json.loads(pure_str)
                        j_data.pop("_commander_seal", None)
                        pure_sha = hashlib.sha256(json.dumps(j_data, ensure_ascii=False, indent=2).encode("utf-8")).hexdigest().lower()
                        if pure_sha == expected_sha or pure_sha.startswith(expected_sha) or expected_sha.startswith(pure_sha[:16]):
                            continue
                    except Exception:
                        pass
                return {"success": False, "msg": f"安全告警：檔案指紋不吻合，疑似被篡改 {f_name}"}

        # 2. 原位落款階段
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sealed_records = []

        for record in verified_files:
            f_name = record.get("name") or record.get("file_name")
            target_path = CORE_REPO_DIR / f_name
            base_sha = (record.get("sha256") or record.get("seal_hash") or "")[:16]

            if target_path.suffix.lower() == ".py":
                # 對 .py 檔案原位注入 Header Docstring
                raw_text = target_path.read_text(encoding="utf-8", errors="replace")
                pure_code = extract_pure_code(raw_text)
                header_stamp = (
                    '"""\n'
                    '==============================================================================\n'
                    f' ARCHITECTURE : PHANTOM GRID / BOB CORE SYSTEM\n'
                    f' MODULE       : {target_path.name}\n'
                    f' SIGNED BY    : {COMMANDER_NAME} (指揮所權威落款)\n'
                    f' SEAL TIME    : {now_str} CST\n'
                    f' INTEGRITY    : SHA256:{base_sha} [OFFICIALLY SEALED]\n'
                    '==============================================================================\n'
                    '"""\n\n'
                )
                target_path.write_text(header_stamp + pure_code, encoding="utf-8")

            elif target_path.suffix.lower() == ".json":
                # 對 .json 檔案原位注入 _commander_seal
                try:
                    data = json.loads(target_path.read_text(encoding="utf-8", errors="replace"))
                except Exception:
                    data = {}
                if not isinstance(data, dict):
                    data = {"data": data}
                data.pop("_commander_seal", None)
                seal_node = {
                    "_commander_seal": {
                        "signed_by": COMMANDER_NAME,
                        "seal_time": now_str,
                        "base_sha256": base_sha,
                        "status": "OFFICIALLY_RELEASED"
                    }
                }
                # 確保印章位於頂部
                sealed_data = {**seal_node, **data}
                target_path.write_text(json.dumps(sealed_data, indent=2, ensure_ascii=False), encoding="utf-8")

            sealed_records.append(f_name)

        # 3. 升級簽證單為發佈封印憑證 (RELEASE_SEAL.json)
        release_seal = {
            "seal_status": "OFFICIALLY_RELEASED",
            "commander": COMMANDER_NAME,
            "sealed_at": now_str,
            "total_sealed": len(sealed_records),
            "sealed_files": sealed_records
        }
        seal_json_str = json.dumps(release_seal, indent=2, ensure_ascii=False)
        (CORE_REPO_DIR / "RELEASE_SEAL.json").write_text(seal_json_str, encoding="utf-8")

        # 4. 同步至履歷登記簿與 G 槽金庫
        try:
            g_dest = Path(r"G:\我的雲端硬碟\260803_opencode\02_Knowledge\Bob_Verified")
            g_dest.mkdir(parents=True, exist_ok=True)
            (g_dest / "RELEASE_SEAL.json").write_text(seal_json_str, encoding="utf-8")
            for sf in sealed_records:
                src_p = CORE_REPO_DIR / sf
                if src_p.exists():
                    shutil.copy2(src_p, g_dest / sf)
        except Exception:
            pass

        return {
            "success": True,
            "msg": f"落款完成！已正式蓋印封存 {len(sealed_records)} 份模組，並簽發 RELEASE_SEAL.json",
            "signed_count": len(sealed_records),
            "sealed_files": sealed_records
        }
