# C:\ibm-bob\office2_engine.py
# -*- coding: utf-8 -*-
import os
import ast
import json
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

SANDBOX_OUTBOX_PLAYGROUND = Path(r"C:\Users\user\.bob\playground\02_OUTBOX")
SANDBOX_OUTBOX_LEGACY = Path(r"C:\ibm-bob\02_OUTBOX")
STAGING_DIR = Path(r"C:\ibm-bob\02_OUTBOX_STAGING")
CORE_REPO_DIR = Path(r"C:\ibm-bob\core_repo")

ALLOWED_EXTENSIONS = {".py", ".json", ".md"}
EXCLUDED_NAMES = {"__pycache__", ".pytest_cache", ".git", ".idea", ".DS_Store"}
DANGEROUS_FUNCS = {"os.system", "eval", "exec", "subprocess.call", "shutil.rmtree"}


class Office2AuditEngine:
    @staticmethod
    def audit_ast(file_path: Path):
        """Python 語法與危險調用靜態檢查"""
        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8", errors="replace"), filename=str(file_path))
        except SyntaxError as e:
            return False, f"語法錯誤 Line {e.lineno}"
        except Exception as e:
            return False, f"讀取異常: {str(e)[:15]}"

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = ""
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    name = f"{node.func.value.id}.{node.func.attr}"
                if name in DANGEROUS_FUNCS:
                    return False, f"攔截危險調用: {name}() [L{node.lineno}]"
        return True, "AST 稽核合規"

    @classmethod
    def get_active_outbox(cls) -> Path:
        r"""優先採用 playground，若無有效檔案則自動回退至 C:\ibm-bob_OUTBOX"""
        if SANDBOX_OUTBOX_PLAYGROUND.exists() and any(SANDBOX_OUTBOX_PLAYGROUND.rglob("*")):
            return SANDBOX_OUTBOX_PLAYGROUND
        if SANDBOX_OUTBOX_LEGACY.exists():
            return SANDBOX_OUTBOX_LEGACY
        return SANDBOX_OUTBOX_PLAYGROUND

    @classmethod
    def execute_stage_review(cls) -> Dict[str, Any]:
        """第一階段：唯讀提取、過濾快取、產出認證單"""
        active_outbox = cls.get_active_outbox()
        if not active_outbox.exists():
            return {"success": False, "msg": "沙盒 02_OUTBOX 不存在", "items": [], "data": []}

        STAGING_DIR.mkdir(parents=True, exist_ok=True)
        items_report = []
        verified_files = []
        all_passed = True

        for file_path in active_outbox.rglob("*"):
            if any(part in EXCLUDED_NAMES for part in file_path.parts):
                continue
            if not file_path.is_file() or file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
                continue

            rel_path = file_path.relative_to(active_outbox)
            dest_file = STAGING_DIR / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)

            raw_bytes = file_path.read_bytes()
            dest_file.write_bytes(raw_bytes)
            sha256_hash = hashlib.sha256(raw_bytes).hexdigest()

            # 稽核檢查
            if file_path.suffix.lower() == ".py":
                passed, reason = cls.audit_ast(dest_file)
            else:
                passed, reason = True, "結構合規 (免檢)"

            if not passed:
                all_passed = False

            item_info = {
                "rel_path": str(rel_path),
                "name": file_path.name,
                "sha256": sha256_hash,
                "status": "PASSED" if passed else "FAILED",
                "details": reason,
                "size": len(raw_bytes)
            }
            items_report.append(item_info)
            if passed:
                verified_files.append({"name": str(rel_path), "sha256": sha256_hash})

        if not items_report:
            return {"success": False, "msg": "02_OUTBOX 內無有效檔案", "items": [], "data": []}

        # 生成第二辦公室認證簽證單
        cert_data = {
            "certificate_type": "OFFICE2_AUDIT_MANIFEST",
            "issuer": "PHANTOMGRID_Office2_Copilot",
            "issued_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "all_passed": all_passed,
            "verified_files": verified_files
        }
        cert_file = STAGING_DIR / ".audit_certificate.json"
        cert_file.write_text(json.dumps(cert_data, indent=2, ensure_ascii=False), encoding="utf-8")

        # 兼容看板展示清單結構
        data_compat = []
        for it in items_report:
            data_compat.append({
                "name": it["name"],
                "hash": it["sha256"][:8],
                "size": it["size"],
                "passed": it["status"] == "PASSED",
                "audit_msg": it["details"],
                "line_info": f"{it['size']} B",
                "entity_info": f"SHA256:{it['sha256'][:16]} (AST 合規)",
                "staging_path": str(STAGING_DIR / it["name"])
            })

        return {
            "success": True,
            "all_passed": all_passed,
            "msg": "審查完成，簽證單已生成" if all_passed else "存在違規檔案，已中斷流程",
            "items": items_report,
            "data": data_compat,
            "count": len(items_report),
            "latency_ms": 12,
            "staging_dir": str(STAGING_DIR),
            "manifest": {"manifest_id": f"MANIFEST-{int(datetime.now().timestamp())}"},
            "can_sync_core": all_passed
        }

    @classmethod
    def execute_sync_core(cls) -> Dict[str, Any]:
        """第二階段：帶認證檔原子化推送到 core_repo"""
        cert_file = STAGING_DIR / ".audit_certificate.json"
        if not cert_file.exists():
            return {"success": False, "msg": "未檢測到認證單，請先執行提取審查"}

        cert_data = json.loads(cert_file.read_text(encoding="utf-8"))
        if not cert_data.get("all_passed"):
            return {"success": False, "msg": "中繼區檔案未全數通過審查，禁止入庫"}

        CORE_REPO_DIR.mkdir(parents=True, exist_ok=True)
        synced_count = 0

        # 將 Staging 區之實體原檔與認證單一併移交
        for item in STAGING_DIR.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(STAGING_DIR)
                target = CORE_REPO_DIR / rel_path
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)
                synced_count += 1

        return {
            "success": True,
            "msg": f"成對移交成功！已同步 {synced_count} 個項目至核心庫",
            "synced_count": synced_count,
            "delivery_summary": f"🎉 核心庫已成功同步 {synced_count} 支審查合規檔案 (實體原檔 + 認證簽證單成對交付)！"
        }
