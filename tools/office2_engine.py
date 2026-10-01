# C:\ibm-bob\office2_engine.py
# -*- coding: utf-8 -*-
"""
==============================================================================
 第二辦公室 (Office 2) 批次原子提取與閘門檢驗引擎 (Batch Audit Gate)
 職責規範：
 1. 批次快照鏡像提取 (純讀取不剪下，沙盒原始狀態不變)。
 2. 排除非目標快取雜訊 (.tmp, __pycache__, .pyc 等)。
 3. 平行流水線雙重檢驗 (.py 驗 AST Clean, .json 驗 JSON Valid, 計算 SHA-256)。
 4. 全通過即原子化打包簽證 (All-or-Nothing 門禁，1 個違規即整批阻斷)。
 5. 只做質檢與簽證移交，絕不越權落款！
==============================================================================
"""

import os
import ast
import json
import time
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

SANDBOX_OUTBOX_PLAYGROUND = Path(r"C:\Users\user\.bob\playground\02_OUTBOX")
SANDBOX_OUTBOX_LEGACY = Path(r"C:\ibm-bob\02_OUTBOX")
STAGING_DIR = Path(r"C:\ibm-bob\02_OUTBOX_STAGING")
CORE_REPO_DIR = Path(r"C:\ibm-bob\core_repo")

ALLOWED_EXTENSIONS = {".py", ".json", ".md"}
EXCLUDED_NAMES = {"__pycache__", ".pytest_cache", ".git", ".idea", ".DS_Store"}
EXCLUDED_EXTS = {".tmp", ".pyc", ".pyd", ".swap", ".bak", ".log", ".mp4"}
DANGEROUS_FUNCS = {"os.system", "eval", "exec", "subprocess.call", "shutil.rmtree"}


class Office2AuditEngine:
    @staticmethod
    def audit_ast(file_path: Path) -> Tuple[bool, str]:
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
        return True, "AST Clean"

    @staticmethod
    def audit_json(file_path: Path) -> Tuple[bool, str]:
        """JSON 結構完整性與格式檢查"""
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
            json.loads(text)
            return True, "JSON Valid"
        except Exception as e:
            return False, f"JSON 格式錯誤: {str(e)[:18]}"

    @staticmethod
    def audit_md(file_path: Path) -> Tuple[bool, str]:
        """Markdown 文件格式檢查"""
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
            if len(text.strip()) == 0:
                return False, "Markdown 內容為空"
            return True, "Markdown Clean"
        except Exception as e:
            return False, f"讀取錯誤: {str(e)[:15]}"

    @classmethod
    def get_active_outbox(cls) -> Path:
        r"""優先採用 playground，若無有效檔案則自動回退至 C:\ibm-bob\02_OUTBOX"""
        if SANDBOX_OUTBOX_PLAYGROUND.exists():
            valid_pg = [f for f in SANDBOX_OUTBOX_PLAYGROUND.glob("*") if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS]
            if len(valid_pg) > 0:
                return SANDBOX_OUTBOX_PLAYGROUND
        if SANDBOX_OUTBOX_LEGACY.exists():
            return SANDBOX_OUTBOX_LEGACY
        return SANDBOX_OUTBOX_PLAYGROUND

    @classmethod
    def execute_stage_review(cls) -> Dict[str, Any]:
        """
        批次原子提取與閘門檢驗 (Batch Audit Gate)：
        1. 純讀取唯讀快照至 Staging
        2. 過濾隱藏快取與雜訊
        3. 平行流水線雙重檢驗 (SHA-256 + 語法/格式)
        4. All-or-Nothing 打包簽證 (一檔出錯整批阻斷)
        """
        start_time = time.time()
        active_outbox = cls.get_active_outbox()
        if not active_outbox.exists():
            return {
                "success": False,
                "msg": "沙盒 02_OUTBOX 不存在",
                "items": [],
                "data": [],
                "count": 0,
                "blocked_cache_count": 0,
                "all_passed": False
            }

        # 清理並重建中繼區
        if STAGING_DIR.exists():
            shutil.rmtree(STAGING_DIR, ignore_errors=True)
        STAGING_DIR.mkdir(parents=True, exist_ok=True)

        items_report = []
        verified_files = []
        all_passed = True
        blocked_cache_count = 0

        # 批次遍歷沙盒檔案
        all_sandbox_files = sorted(list(active_outbox.rglob("*")), key=lambda p: p.name)

        for file_path in all_sandbox_files:
            # 排除目錄與非目標快取
            if any(part in EXCLUDED_NAMES for part in file_path.parts):
                if file_path.is_file():
                    blocked_cache_count += 1
                continue
            if file_path.is_file() and file_path.suffix.lower() in EXCLUDED_EXTS:
                blocked_cache_count += 1
                continue
            if not file_path.is_file() or file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
                continue

            rel_path = file_path.relative_to(active_outbox)
            dest_file = STAGING_DIR / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)

            raw_bytes = file_path.read_bytes()
            dest_file.write_bytes(raw_bytes)
            sha256_full = hashlib.sha256(raw_bytes).hexdigest()
            sha256_short = sha256_full[:10]

            # 平行流水線雙重檢驗
            ext = file_path.suffix.lower()
            if ext == ".py":
                passed, reason = cls.audit_ast(dest_file)
            elif ext == ".json":
                passed, reason = cls.audit_json(dest_file)
            elif ext == ".md":
                passed, reason = cls.audit_md(dest_file)
            else:
                passed, reason = True, "結構合規 (免檢)"

            if not passed:
                all_passed = False

            idx = len(items_report) + 1
            item_info = {
                "no": idx,
                "name": file_path.name,
                "rel_path": str(rel_path),
                "sha256": sha256_full,
                "sha": f"{sha256_short}...",
                "size": len(raw_bytes),
                "size_formatted": f"{len(raw_bytes):,} B",
                "status": "PASSED" if passed else "FAILED",
                "details": reason,
                "audit_msg": reason
            }
            items_report.append(item_info)
            if passed:
                verified_files.append({"name": str(rel_path), "sha256": sha256_full})

        total_count = len(items_report)
        if total_count == 0:
            return {
                "success": False,
                "msg": "02_OUTBOX 內無有效檔案",
                "items": [],
                "data": [],
                "count": 0,
                "blocked_cache_count": blocked_cache_count,
                "all_passed": False
            }

        passed_count = sum(1 for it in items_report if it["status"] == "PASSED")
        pass_rate_percent = int((passed_count / total_count) * 100) if total_count > 0 else 0
        pass_rate_str = f"{passed_count}/{total_count} ({pass_rate_percent}%)"
        compliance_status = "全數通過" if all_passed else "存在違規 (已阻斷)"
        latency_s = f"{time.time() - start_time:.2f}s"

        # All-or-Nothing 門禁：全數合格才簽發認證單
        if all_passed:
            cert_data = {
                "certificate_type": "OFFICE2_BATCH_AUDIT_MANIFEST",
                "issuer": "PHANTOMGRID_Office2_BatchAuditGate",
                "issued_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_files": total_count,
                "all_passed": True,
                "blocked_cache_count": blocked_cache_count,
                "latency": latency_s,
                "verified_files": verified_files
            }
            cert_file = STAGING_DIR / ".audit_certificate.json"
            cert_file.write_text(json.dumps(cert_data, indent=2, ensure_ascii=False), encoding="utf-8")

        # 組織看板相容結構
        data_compat = []
        for it in items_report:
            data_compat.append({
                "no": it["no"],
                "name": it["name"],
                "hash": it["sha256"][:10],
                "size": it["size"],
                "line_info": it["size_formatted"],
                "passed": it["status"] == "PASSED",
                "status": it["status"],
                "audit_msg": it["details"],
                "entity_info": f"SHA: {it['sha256'][:10]}... | [{it['status']}] {it['details']}",
                "staging_path": str(STAGING_DIR / it["name"])
            })

        return {
            "success": True,
            "all_passed": all_passed,
            "msg": f"批次審查完成：{pass_rate_str} 合規" if all_passed else "存在違規檔案，整批阻斷！",
            "items": items_report,
            "data": data_compat,
            "count": total_count,
            "total_count": total_count,
            "passed_count": passed_count,
            "pass_rate_str": pass_rate_str,
            "compliance_status": compliance_status,
            "blocked_cache_count": blocked_cache_count,
            "latency_s": latency_s,
            "latency_ms": int((time.time() - start_time) * 1000),
            "staging_dir": str(STAGING_DIR),
            "manifest": {"manifest_id": f"MANIFEST-{int(datetime.now().timestamp())}"},
            "can_sync_core": all_passed
        }

    @classmethod
    def execute_sync_core(cls) -> Dict[str, Any]:
        """
        第二階段：批次原子化推送到 core_repo
        嚴格落實成對移交 (實體原檔 + 認證簽證單)
        """
        cert_file = STAGING_DIR / ".audit_certificate.json"
        if not cert_file.exists():
            return {"success": False, "msg": "未檢測到認證單或檔案未全數合格，禁止入庫！"}

        cert_data = json.loads(cert_file.read_text(encoding="utf-8"))
        if not cert_data.get("all_passed"):
            return {"success": False, "msg": "中繼區檔案未全數通過審查，禁止入庫！"}

        CORE_REPO_DIR.mkdir(parents=True, exist_ok=True)
        synced_count = 0

        # 將 Staging 區之實體原檔與認證單一併原子化移交
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
            "delivery_summary": f"🎉 核心庫已成功接收 {synced_count} 支審查合規檔案 (實體原檔 + 認證簽證單成對交付)！"
        }
