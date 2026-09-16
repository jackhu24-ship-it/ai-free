#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 【PROJ-18 旗艦開發核心引擎】：coder_dev_core.py
========================================================================================
角色定位：🛠️ 小開 (Agent_Coder) 專用全自動化開發與自癒修復核心引擎
三大核心組件：
  1. DiffPatcher     : 多層容錯微創搜尋替換、Unified Diff 解析、歧義熔斷 (AmbiguousPatchError) 與原子寫入
  2. DevRunner       : 非同步 TDD 執行、環境變數隔離 (PYTHONUTF8=1)、超時死鎖熔斷與結構化自癒反饋 (SelfHealingReport)
  3. ModuleScaffolder: 符合 Base_Rules.md 之工業級標準模組骨架生成 (支援 EventBus / 01_Memory 動態 Hooks)

三層記憶架構整合：
  - 00_System   : Base_Rules.md / Agent_Coder.md
  - 01_Memory   : Memory_Log.md / Dynamic Event Logging
  - 02_Knowledge: Coder_Dev_Core_Spec.md
"""

from __future__ import annotations

import os
import sys

# Windows UTF-8 編碼防護
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import time
import json
import re
import difflib
import asyncio
import shutil
import subprocess
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Literal
from dataclasses import dataclass, asdict, field


# ============================================================================
# 自訂異常定義 (Custom Exceptions)
# ============================================================================

class CoderDevError(Exception):
    """PROJ-18 開發核心引擎基礎異常"""
    pass


class PatchError(CoderDevError):
    """補丁套用基礎異常"""
    pass


class AmbiguousPatchError(PatchError):
    """歧義補丁異常：在目標檔案中比對到多處相似代碼，為防止打錯區塊強制熔斷"""
    pass


class TargetNotFoundError(PatchError):
    """目標代碼不存在異常：在檔案中找不到可匹配之目標區塊"""
    pass


class PatchVerificationError(PatchError):
    """補丁寫入或驗證失敗異常"""
    pass


class DevRunnerTimeoutError(CoderDevError):
    """測試執行超時熔斷異常"""
    pass


# ============================================================================
# 數據結構定義 (Data Models)
# ============================================================================

@dataclass
class SelfHealingReport:
    """結構化自癒診斷報告資料契約"""
    status: Literal["PASSED", "FAILED", "TIMEOUT", "ERROR"]
    exit_code: int
    duration_ms: float
    error_type: Optional[str] = None
    failed_file: Optional[str] = None
    failed_line: Optional[int] = None
    failed_snippet: Optional[str] = None
    root_cause_analysis: Optional[str] = None
    suggested_patch: Optional[Dict[str, str]] = None
    raw_stdout: str = ""
    raw_stderr: str = ""
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


# ============================================================================
# 核心組件一：DiffPatcher (多層容錯局部精準補丁引擎)
# ============================================================================

class DiffPatcher:
    """
    微創手術式代碼補丁引擎
    特點：
      - 多層容錯策略（100% 精確 -> 空白/縮排容錯 -> 滑動窗口模糊比對）
      - 歧義自動偵測與 AmbiguousPatchError 安全熔斷
      - Unified Diff 解析與套用
      - Dry-run 預檢與安全原子寫入 / 備份回滾
    """

    @staticmethod
    def _normalize_line(line: str) -> str:
        """去除前後空白以進行縮排容錯比對"""
        return line.strip()

    @classmethod
    def apply_search_replace(
        cls,
        file_content: str,
        target_content: str,
        replacement_content: str,
        tolerance: Literal["auto", "exact", "whitespace", "fuzzy"] = "auto",
        fuzzy_threshold: float = 0.85
    ) -> Tuple[str, str]:
        """
        對字串內容進行多層容錯替換
        回傳: (替換後的新內容, 採用的匹配策略名稱)
        """
        if not target_content:
            raise PatchError("目標代碼 (target_content) 不能為空。")

        target_clean = target_content.replace("\r\n", "\n")
        content_clean = file_content.replace("\r\n", "\n")
        replacement_clean = replacement_content.replace("\r\n", "\n")

        # -------------------------------------------------------------
        # Tier 1: 100% 精確比對 (Exact Match)
        # -------------------------------------------------------------
        if tolerance in ("auto", "exact"):
            occurrences = [m.start() for m in re.finditer(re.escape(target_clean), content_clean)]
            if len(occurrences) == 1:
                idx = occurrences[0]
                new_content = content_clean[:idx] + replacement_clean + content_clean[idx + len(target_clean):]
                return new_content, "exact"
            elif len(occurrences) > 1:
                raise AmbiguousPatchError(
                    f"[歧義熔斷] 目標代碼在檔案中精確出現 {len(occurrences)} 次，無法唯一判定替換位置。"
                    f"請提供包含更多上下文字文 (Context) 的 target_content。"
                )
            elif tolerance == "exact":
                raise TargetNotFoundError("[精確比對失敗] 檔案中未找到完全一致的目標代碼區塊。")

        # -------------------------------------------------------------
        # Tier 2: 空白與縮排容錯比對 (Whitespace / Indentation Tolerant)
        # -------------------------------------------------------------
        content_lines = content_clean.split("\n")
        target_lines = target_clean.split("\n")
        target_norm = [cls._normalize_line(l) for l in target_lines if cls._normalize_line(l)]
        k = len(target_norm)

        if k > 0 and tolerance in ("auto", "whitespace"):
            matched_indices: List[Tuple[int, int]] = []
            for i in range(len(content_lines)):
                # 收集非空白行
                sub_lines = []
                sub_indices = []
                for j in range(i, len(content_lines)):
                    norm_j = cls._normalize_line(content_lines[j])
                    if norm_j:
                        sub_lines.append(norm_j)
                        sub_indices.append(j)
                    if len(sub_lines) == k:
                        break

                if sub_lines == target_norm:
                    start_idx = sub_indices[0]
                    end_idx = sub_indices[-1] + 1
                    matched_indices.append((start_idx, end_idx))

            if len(matched_indices) == 1:
                start_l, end_l = matched_indices[0]
                # 偵測原始起始行縮排
                orig_leading = ""
                if start_l < len(content_lines):
                    m = re.match(r"^(\s*)", content_lines[start_l])
                    if m:
                        orig_leading = m.group(1)

                # 套用縮排調整
                rep_lines = replacement_clean.split("\n")
                if orig_leading and rep_lines:
                    first_rep_m = re.match(r"^(\s*)", rep_lines[0])
                    first_rep_leading = first_rep_m.group(1) if first_rep_m else ""
                    if not first_rep_leading and orig_leading:
                        rep_lines = [orig_leading + l if l.strip() else l for l in rep_lines]

                new_lines = content_lines[:start_l] + rep_lines + content_lines[end_l:]
                return "\n".join(new_lines), "whitespace"
            elif len(matched_indices) > 1:
                raise AmbiguousPatchError(
                    f"[歧義熔斷] 縮排容錯比對在檔案中發現 {len(matched_indices)} 處匹配區塊，無法唯一判定替換位置。"
                )
            elif tolerance == "whitespace":
                raise TargetNotFoundError("[縮排容錯比對失敗] 檔案中未找到符合的目標代碼區塊。")

        # -------------------------------------------------------------
        # Tier 3: 滑動窗口局部模糊比對 (Context Fuzzy Matching)
        # -------------------------------------------------------------
        if tolerance in ("auto", "fuzzy") and len(content_lines) >= len(target_lines):
            t_len = len(target_lines)
            best_ratio = 0.0
            fuzzy_matches: List[Tuple[int, int, float]] = []

            for i in range(len(content_lines) - t_len + 1):
                window_lines = content_lines[i:i + t_len]
                window_str = "\n".join(window_lines)
                ratio = difflib.SequenceMatcher(None, target_clean, window_str).ratio()

                if ratio >= fuzzy_threshold:
                    fuzzy_matches.append((i, i + t_len, ratio))
                if ratio > best_ratio:
                    best_ratio = ratio

            if len(fuzzy_matches) == 1:
                start_l, end_l, score = fuzzy_matches[0]
                rep_lines = replacement_clean.split("\n")
                new_lines = content_lines[:start_l] + rep_lines + content_lines[end_l:]
                return "\n".join(new_lines), f"fuzzy (score: {score:.2f})"
            elif len(fuzzy_matches) > 1:
                raise AmbiguousPatchError(
                    f"[歧義熔斷] 模糊比對發現 {len(fuzzy_matches)} 處高度相似區塊 (相似度 >= {fuzzy_threshold})，無法唯一判定。"
                )

        raise TargetNotFoundError(
            f"[目標未找到] 無法在目標檔案中找到匹配的代碼區塊 (已嘗試精確、縮排容錯與模糊搜尋，最高相似度: {best_ratio:.2f})。"
        )

    @classmethod
    def apply_unified_diff(cls, file_content: str, patch_diff: str) -> str:
        """解析並套用標準 Unified Diff (Git 格式) 補丁"""
        content_lines = file_content.replace("\r\n", "\n").split("\n")
        diff_lines = patch_diff.replace("\r\n", "\n").split("\n")

        hunk_re = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
        hunks = []
        current_hunk = None

        for line in diff_lines:
            m = hunk_re.match(line)
            if m:
                if current_hunk:
                    hunks.append(current_hunk)
                old_start = int(m.group(1))
                old_count = int(m.group(2)) if m.group(2) else 1
                new_start = int(m.group(3))
                new_count = int(m.group(4)) if m.group(4) else 1
                current_hunk = {
                    "old_start": old_start,
                    "old_count": old_count,
                    "new_start": new_start,
                    "new_count": new_count,
                    "lines": []
                }
            elif current_hunk is not None:
                current_hunk["lines"].append(line)

        if current_hunk:
            hunks.append(current_hunk)

        if not hunks:
            raise PatchError("Unified Diff 格式無效，未偵測到任何 @@ -x,y +x,y @@ hunk 區塊。")

        # 由後往前套用 hunk 以保持行號偏移正確
        result_lines = list(content_lines)
        for hunk in reversed(hunks):
            old_start = hunk["old_start"] - 1  # 轉為 0-indexed
            old_count = hunk["old_count"]
            hunk_lines = hunk["lines"]

            new_block = []
            expected_old_block = []

            for hl in hunk_lines:
                if not hl:
                    continue
                prefix = hl[0]
                line_val = hl[1:]
                if prefix == " ":
                    new_block.append(line_val)
                    expected_old_block.append(line_val)
                elif prefix == "-":
                    expected_old_block.append(line_val)
                elif prefix == "+":
                    new_block.append(line_val)

            # 驗證上下文 (Context Verification)
            actual_old = result_lines[old_start:old_start + old_count]
            if actual_old != expected_old_block:
                # 縮排微幅容錯驗證
                actual_norm = [cls._normalize_line(l) for l in actual_old]
                exp_norm = [cls._normalize_line(l) for l in expected_old_block]
                if actual_norm != exp_norm:
                    raise PatchError(
                        f"Unified Diff Context 驗證失敗 (行號 {old_start+1})。\n"
                        f"預期舊代碼:\n{chr(10).join(expected_old_block)}\n"
                        f"實際檔案內容:\n{chr(10).join(actual_old)}"
                    )

            result_lines[old_start:old_start + old_count] = new_block

        return "\n".join(result_lines)

    @classmethod
    def patch_file(
        cls,
        file_path: Union[str, Path],
        patch_content: str,
        mode: Literal["search_replace", "unified"] = "search_replace",
        target_content: Optional[str] = None,
        dry_run: bool = False,
        backup: bool = True
    ) -> Dict[str, Any]:
        """
        對實際檔案進行原子性安全補丁
        """
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"目標檔案不存在: {path}")

        # 讀取原始檔案 (強制 UTF-8)
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            original_content = f.read()

        # 執行記憶體補丁
        strategy = mode
        if mode == "search_replace":
            if target_content is not None:
                new_content, strategy = cls.apply_search_replace(
                    original_content, target_content, patch_content
                )
            else:
                # 嘗試解析 <<<<<<< SEARCH / ======= / >>>>>>> REPLACE 格式
                pattern = r"<<<<<<< SEARCH\r?\n(.*?)\r?\n=======\r?\n(.*?)\r?\n>>>>>>> REPLACE"
                m = re.search(pattern, patch_content, re.DOTALL)
                if m:
                    t_block = m.group(1)
                    r_block = m.group(2)
                    new_content, strategy = cls.apply_search_replace(
                        original_content, t_block, r_block
                    )
                else:
                    raise PatchError(
                        "在 search_replace 模式下，請提供 target_content 或使用 SEARCH/REPLACE 標記格式。"
                    )
        elif mode == "unified":
            new_content = cls.apply_unified_diff(original_content, patch_content)
        else:
            raise ValueError(f"不支援的補丁模式: {mode}")

        # Dry-run 預檢
        if dry_run:
            diff = difflib.unified_diff(
                original_content.splitlines(),
                new_content.splitlines(),
                fromfile=f"a/{path.name}",
                tofile=f"b/{path.name}",
                lineterm=""
            )
            return {
                "status": "dry_run_success",
                "file_path": str(path),
                "strategy": strategy,
                "diff_preview": "\n".join(diff)
            }

        # 建立備份檔 (.bak)
        bak_path = path.with_suffix(path.suffix + ".bak")
        if backup:
            shutil.copyfile(path, bak_path)

        # 原子性寫入 (先寫臨時檔再 replace)
        tmp_path = path.with_suffix(path.suffix + f".tmp_{int(time.time()*1000)}")
        try:
            with open(tmp_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(new_content)

            # 原子置換
            os.replace(tmp_path, path)

            # 驗證寫入成功
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                verified_content = f.read()

            if verified_content != new_content:
                raise PatchVerificationError("寫入後驗證失敗，代碼內容不相符。")

        except Exception as e:
            # 發生任何異常，立即從備份回滾
            if backup and bak_path.exists():
                shutil.copyfile(bak_path, path)
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            raise PatchVerificationError(f"原子寫入失敗，已自動回滾至原始狀態: {str(e)}") from e

        # 計算 diff 統計
        diff_lines = list(difflib.unified_diff(
            original_content.splitlines(),
            new_content.splitlines(),
            lineterm=""
        ))
        added = sum(1 for l in diff_lines if l.startswith("+") and not l.startswith("+++"))
        removed = sum(1 for l in diff_lines if l.startswith("-") and not l.startswith("---"))

        return {
            "status": "applied",
            "file_path": str(path),
            "backup_path": str(bak_path) if backup else None,
            "strategy": strategy,
            "diff_stat": f"+{added} / -{removed} lines"
        }


# ============================================================================
# 核心組件二：DevRunner (TDD 非同步測試與自癒反饋引擎)
# ============================================================================

class DevRunner:
    """
    小開專屬非同步測試執行與自癒診斷引擎
    特點：
      - 非同步子行程執行 (asyncio)
      - 環境變數嚴格隔離 (PYTHONUTF8=1, PYTHONIOENCODING=utf-8)
      - 超時死鎖優雅熔斷 (SIGTERM -> SIGKILL)
      - 深度 Traceback 過濾與結構化自癒反饋
    """

    @classmethod
    def _clean_traceback(cls, raw_stderr: str) -> Tuple[Optional[str], Optional[str], Optional[int], Optional[str]]:
        """
        過濾系統內部冗餘堆疊，精確提煉出錯誤類型、出錯檔案、行號與語句
        """
        if not raw_stderr:
            return None, None, None, None

        # 匹配常見 Exception: ...
        error_type_match = re.search(r"([A-Za-z_][A-Za-z0-9_]*Error|Exception|AssertionError): (.*)", raw_stderr)
        error_type = error_type_match.group(1) if error_type_match else None
        if not error_type and "AssertionError" in raw_stderr:
            error_type = "AssertionError"

        # 匹配 File "...", line X, in ...
        file_matches = list(re.finditer(r'File "([^"]+)", line (\d+)(?:, in (.*))?\r?\n\s*(.*)', raw_stderr))
        failed_file = None
        failed_line = None
        failed_snippet = None

        if file_matches:
            # 優先選取最後一個非標準庫的用戶代碼 frame
            for m in reversed(file_matches):
                f_path = m.group(1)
                if not ("lib" in f_path.lower() and "python" in f_path.lower()):
                    failed_file = f_path
                    failed_line = int(m.group(2))
                    failed_snippet = m.group(4).strip()
                    break

            if not failed_file:
                # 退回最後一個 frame
                last_m = file_matches[-1]
                failed_file = last_m.group(1)
                failed_line = int(last_m.group(2))
                failed_snippet = last_m.group(4).strip()

        return error_type, failed_file, failed_line, failed_snippet

    @classmethod
    def _diagnose_root_cause(
        cls,
        error_type: Optional[str],
        failed_file: Optional[str],
        failed_line: Optional[int],
        failed_snippet: Optional[str],
        raw_stderr: str
    ) -> Tuple[str, Optional[Dict[str, str]]]:
        """
        啟發式根因分析 (Root Cause Analysis) 與自癒修復建議生成
        """
        if not error_type:
            return "測試未通過，但未偵測到明確的 Python 例外堆疊。", None

        root_cause = f"偵測到 {error_type} 異常。"
        suggested_patch = None

        if error_type == "AssertionError":
            root_cause = "斷言檢驗失敗：函數回傳值或系統狀態未達預期，請檢查邏輯邊界條件或回傳格式。"
        elif error_type in ("NameError", "UnboundLocalError"):
            m = re.search(r"name '([^']+)' is not defined", raw_stderr)
            var_name = m.group(1) if m else "變數"
            root_cause = f"變數或函數 `{var_name}` 未定義，可能缺少 import 或拼寫錯誤。"
        elif error_type == "TypeError":
            root_cause = "型別不相符：傳入參數型別或數量與函數簽名不符，或對 NoneType 進行了屬性存取。"
        elif error_type == "ZeroDivisionError":
            root_cause = "除以零錯誤：分母運算結果為 0，請加入分母非零之安全防禦判斷。"
        elif error_type == "SyntaxError":
            root_cause = f"語法錯誤：在第 {failed_line} 行附近存在無效語法或缺少冒號/括號。"
        elif error_type == "UnicodeDecodeError":
            root_cause = "Windows 編碼錯誤：請確認檔案讀寫均加上 encoding='utf-8', errors='replace'。"
        elif error_type == "IndexError":
            root_cause = "索引超出邊界：清單或字串長度不足，請檢查邊界條件。"
        elif error_type == "KeyError":
            m = re.search(r"KeyError: (.*)", raw_stderr)
            k = m.group(1) if m else "鍵值"
            root_cause = f"字典鍵值 {k} 不存在，建議改用 `.get()` 提供預設值防護。"

        if failed_snippet:
            suggested_patch = {
                "target_content": failed_snippet,
                "replacement_content": f"# [自癒提示] 請修復此行 ({error_type}): {failed_snippet}"
            }

        return root_cause, suggested_patch

    @classmethod
    async def run_test(
        cls,
        target_path: Union[str, Path],
        timeout: int = 15,
        runner_type: Literal["self_test", "pytest", "unittest", "command"] = "self_test",
        custom_cmd: Optional[List[str]] = None,
        cwd: Optional[Union[str, Path]] = None
    ) -> SelfHealingReport:
        """
        非同步執行測試，具備超時熔斷與自癒報告生成
        """
        target = Path(target_path).resolve()
        work_dir = Path(cwd).resolve() if cwd else target.parent

        # 隔離環境變數 (強制 UTF-8 防 CP950)
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"

        # 準備執行指令
        if runner_type == "pytest":
            cmd = [sys.executable, "-m", "pytest", "-v", str(target)]
        elif runner_type == "unittest":
            cmd = [sys.executable, "-m", "unittest", str(target)]
        elif runner_type == "self_test":
            cmd = [sys.executable, str(target), "--self-test"]
        elif runner_type == "command" and custom_cmd:
            cmd = custom_cmd
        else:
            cmd = [sys.executable, str(target)]

        start_time = time.perf_counter()

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(work_dir),
                env=env
            )

            # 超時監控 (Timeout Protection)
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), timeout=float(timeout)
                )
            except asyncio.TimeoutError:
                # 觸發優雅終止
                try:
                    process.terminate()
                    await asyncio.sleep(0.5)
                    if process.returncode is None:
                        process.kill()
                except Exception:
                    pass

                duration = (time.perf_counter() - start_time) * 1000
                return SelfHealingReport(
                    status="TIMEOUT",
                    exit_code=-1,
                    duration_ms=round(duration, 2),
                    error_type="DevRunnerTimeoutError",
                    failed_file=str(target),
                    root_cause_analysis=f"測試執行超過 {timeout} 秒限制，疑似死迴圈或阻塞式 IO，已被強制熔斷回收。",
                    summary=f"⏱️ 測試超時 ({timeout}s) 熔斷保護生效"
                )

            duration = (time.perf_counter() - start_time) * 1000
            stdout_text = stdout_bytes.decode("utf-8", errors="replace")
            stderr_text = stderr_bytes.decode("utf-8", errors="replace")
            exit_code = process.returncode if process.returncode is not None else 1

            if exit_code == 0:
                return SelfHealingReport(
                    status="PASSED",
                    exit_code=0,
                    duration_ms=round(duration, 2),
                    raw_stdout=stdout_text,
                    raw_stderr=stderr_text,
                    summary=f"🟢 測試全數通過 (耗時 {duration:.1f}ms)"
                )
            else:
                err_type, f_file, f_line, f_snippet = cls._clean_traceback(stderr_text or stdout_text)
                root_cause, suggested_patch = cls._diagnose_root_cause(
                    err_type, f_file, f_line, f_snippet, stderr_text or stdout_text
                )
                return SelfHealingReport(
                    status="FAILED",
                    exit_code=exit_code,
                    duration_ms=round(duration, 2),
                    error_type=err_type or "NonZeroExitCode",
                    failed_file=f_file or str(target),
                    failed_line=f_line,
                    failed_snippet=f_snippet,
                    root_cause_analysis=root_cause,
                    suggested_patch=suggested_patch,
                    raw_stdout=stdout_text,
                    raw_stderr=stderr_text,
                    summary=f"🔴 測試失敗: {err_type or 'ExitCode ' + str(exit_code)} (行號: {f_line or '未知'})"
                )

        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000
            return SelfHealingReport(
                status="ERROR",
                exit_code=1,
                duration_ms=round(duration, 2),
                error_type=type(e).__name__,
                root_cause_analysis=f"執行測試引擎時發生未預期異常: {str(e)}",
                raw_stderr=traceback.format_exc(),
                summary=f"⚠️ 測試引擎執行異常: {str(e)}"
            )


# ============================================================================
# 核心組件三：ModuleScaffolder (標準模組骨架生成器)
# ============================================================================

class ModuleScaffolder:
    """
    符合 Base_Rules.md 的工業級標準模組骨架生成器
    支援動態 Hook 選配開關 (EventBus / 01_Memory / CWE-1236)
    """

    @classmethod
    def scaffold(
        cls,
        module_name: str,
        target_dir: Union[str, Path],
        module_type: Literal["core", "tool", "spec"] = "core",
        enable_event_bus: bool = True,
        enable_three_memory: bool = True,
        enable_cwe_protection: bool = True
    ) -> Dict[str, Any]:
        """
        生成標準模組檔案
        """
        out_dir = Path(target_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        clean_name = re.sub(r"[^\w\-]", "_", module_name).lower()

        if module_type == "spec":
            file_path = out_dir / f"{module_name}_Spec.md"
            content = cls._generate_spec_template(module_name)
        elif module_type == "tool":
            file_path = out_dir / f"{clean_name}.py"
            content = cls._generate_tool_template(
                clean_name, enable_event_bus, enable_three_memory, enable_cwe_protection
            )
        else:  # core
            file_path = out_dir / f"{clean_name}.py"
            content = cls._generate_core_template(
                clean_name, enable_event_bus, enable_three_memory, enable_cwe_protection
            )

        with open(file_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)

        lines_count = len(content.splitlines())
        return {
            "status": "created",
            "file_path": str(file_path),
            "lines_generated": lines_count,
            "module_type": module_type,
            "hooks": {
                "event_bus": enable_event_bus,
                "three_memory": enable_three_memory,
                "cwe_protection": enable_cwe_protection
            }
        }

    @classmethod
    def _generate_core_template(
        cls, name: str, event_bus: bool, memory: bool, cwe: bool
    ) -> str:
        eb_import = "from event_bus import AgentEventBus\n" if event_bus else ""
        mem_hook = """
    async def log_memory(self, message: str, level: str = "INFO"):
        \"\"\"記錄至 L1 動態記憶體\"\"\"
        # [Three-Tier Memory Hook] 可串接 obsidian_mcp 或 autonomous_memory_mcp
        print(f"[{level}] [Memory Log] {message}")
""" if memory else ""

        cwe_hook = """
def sanitize_cell(val: Any) -> Any:
    \"\"\"CWE-1236 公式注入防禦過濾器\"\"\"
    if isinstance(val, str) and val.startswith(("=", "+", "-", "@")):
        return f"'{val}"
    return val
""" if cwe else ""

        return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 模組：{name}.py
========================================================================================
角色：🛠️ 小開 (Agent_Coder)
規範：符合 Base_Rules.md (Python 3.12+, UTF-8, CWE-1236, 異步狀態機)
"""

from __future__ import annotations

import sys
import os
import time
import json
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

{eb_import}{cwe_hook}

class {name.title().replace("_", "")}Engine:
    """核心業務引擎實作"""

    def __init__(self):
        self.is_running = False
{mem_hook}
    async def initialize(self) -> bool:
        """非同步初始化"""
        self.is_running = True
        return True

    async def execute_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """執行核心任務"""
        if not self.is_running:
            await self.initialize()
        return {{"status": "success", "result": payload}}


async def run_self_test():
    """標準自檢測試入口 (DevRunner 相容)"""
    print(f"🧪 開始執行 {name} 核心引擎自檢...")
    engine = {name.title().replace("_", "")}Engine()
    init_ok = await engine.initialize()
    assert init_ok is True, "初始化失敗"
    
    res = await engine.execute_task({{"test_key": "test_val"}})
    assert res["status"] == "success", "任務執行失敗"
    print("🟢 所有自檢項目 100% 通過！")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        asyncio.run(run_self_test())
    else:
        print("請使用 --self-test 參數執行自檢測試。")
'''

    @classmethod
    def _generate_tool_template(
        cls, name: str, event_bus: bool, memory: bool, cwe: bool
    ) -> str:
        return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公用工具模組：{name}.py
========================================================================================
符合 Base_Rules.md 輕量 CLI 工具規範
"""

from __future__ import annotations

import sys
import os
import argparse
from pathlib import Path


def process_data(input_text: str) -> str:
    """核心資料處理函數"""
    return input_text.strip()


def run_self_test():
    """獨立單元自檢"""
    print(f"🧪 執行 {name} 工具自檢...")
    assert process_data("  hello world  ") == "hello world", "處理邏輯異常"
    print("🟢 工具自檢通過！")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        run_self_test()
    else:
        parser = argparse.ArgumentParser(description="{name} 工具")
        parser.add_argument("--input", type=str, help="輸入字串")
        args = parser.parse_args()
        if args.input:
            print(process_data(args.input))
        else:
            parser.print_help()
'''

    @classmethod
    def _generate_spec_template(cls, name: str) -> str:
        return f'''# 02_Knowledge / Specs / {name}_Spec.md（架構規格書）

> **關聯筆記**：[[Three_Tier_Memory_Spec]] ｜ [[Base_Rules]] ｜ [[Agent_Coder]]

---

## 🏛️ 一、架構概述

本模組由 Five-Agent AI OS 團隊設計，旨在實現高效能與高可靠性之工業級功能。

```mermaid
graph TD
    PM["👑 小幫手 (Agent_PM)"] --> Dispatch["調度器"]
    Dispatch --> Engine["{name} 核心引擎"]
    Engine --> Verification["🐎 小馬驗收"]
```

---

## 📋 二、核心功能與規格

1. **功能規範一**：說明...
2. **功能規範二**：說明...

---

## 🛠️ 三、MCP 工具介面

| 工具名稱 | 參數定義 | 功能說明 |
| :--- | :--- | :--- |
| `execute_{name.lower()}` | `payload: dict` | 執行核心任務 |

---
*維護團隊：Five-Agent AI OS*
'''


# ============================================================================
# MCP 工具介面封裝 (MCP Tool Functions)
# ============================================================================

async def apply_diff_patch(
    file_path: str,
    patch_content: str,
    mode: str = "search_replace",
    target_content: Optional[str] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """MCP 工具：對檔案套用微創補丁 (支援 search_replace / unified)"""
    try:
        return DiffPatcher.patch_file(
            file_path=file_path,
            patch_content=patch_content,
            mode=mode,  # type: ignore
            target_content=target_content,
            dry_run=dry_run,
            backup=True
        )
    except Exception as e:
        return {"status": "error", "error_type": type(e).__name__, "message": str(e)}


async def run_dev_tests(
    target_path: str,
    timeout: int = 15,
    runner_type: str = "self_test"
) -> Dict[str, Any]:
    """MCP 工具：非同步執行測試並產出自癒報告"""
    try:
        report = await DevRunner.run_test(
            target_path=target_path,
            timeout=timeout,
            runner_type=runner_type  # type: ignore
        )
        return report.to_dict()
    except Exception as e:
        return {
            "status": "ERROR",
            "error_type": type(e).__name__,
            "message": str(e),
            "summary": f"⚠️ 執行失敗: {str(e)}"
        }


async def scaffold_module(
    module_name: str,
    target_dir: str,
    module_type: str = "core",
    enable_event_bus: bool = True,
    enable_three_memory: bool = True
) -> Dict[str, Any]:
    """MCP 工具：生成標準模組骨架"""
    try:
        return ModuleScaffolder.scaffold(
            module_name=module_name,
            target_dir=target_dir,
            module_type=module_type,  # type: ignore
            enable_event_bus=enable_event_bus,
            enable_three_memory=enable_three_memory
        )
    except Exception as e:
        return {"status": "error", "error_type": type(e).__name__, "message": str(e)}


# ============================================================================
# 自我驗證入口 (Self-Test CLI Harness)
# ============================================================================

async def main():
    print("=" * 80)
    print("🚀 【PROJ-18 🛠️ 小開開發核心引擎 (coder_dev_core.py) 自檢】")
    print("=" * 80)

    # 1. 測試 DiffPatcher 精確替換
    sample_code = "def calc(a, b):\n    # TODO\n    return 0\n"
    target = "# TODO\n    return 0"
    replacement = "return a + b"
    patched, strategy = DiffPatcher.apply_search_replace(sample_code, target, replacement)
    assert "return a + b" in patched
    assert strategy == "exact"
    print("✅ DiffPatcher 精確搜尋替換驗證通過！")

    # 2. 測試歧義熔斷
    dup_code = "print('hello')\nprint('hello')\n"
    try:
        DiffPatcher.apply_search_replace(dup_code, "print('hello')", "print('world')")
        assert False, "歧義檢測未能觸發熔斷"
    except AmbiguousPatchError:
        print("✅ DiffPatcher 歧義熔斷 (AmbiguousPatchError) 驗證通過！")

    print("\n🟢 PROJ-18 核心引擎內部邏輯自檢 100% 通過！")


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        asyncio.run(main())
