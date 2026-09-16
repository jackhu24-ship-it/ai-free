#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 自治記憶與影子管家 MCP 伺服器 (autonomous_memory_mcp.py) - 旗艦穩定版
=============================================================================
作者：🛠️ 小開 (Agent_Coder)
統籌：👑 小幫手 (Agent_PM)
調研：👁️ 小Ｏ (Agent_Research)
審查：🐎 小馬 (Agent_Reviewer)

核心特性 (方案 A + B 一體化)：
1. 【方案 A: 客戶端指紋感知與追蹤】：即時識別 Antigravity / OpenCode / Hermes / Claude 等來源並統計行為。
2. 【方案 A: 主動式異常報警 (Watchdog Alert + Console)】：嚴重錯誤即時推播系統警告。
3. 【方案 A: 非同步安全日誌隊列】：支援併發鎖、非同步寫入與雙閾值防膨脹檢測。
4. 【方案 B: 本地 Ollama 影子管家 GC 蒸餾】：利用本地 qwen2.5:3b 模型或備援蒸餾器將 L1 精華萃取至 L2 並自動修剪。
5. 【方案 B: 歷史無損封存 (Rolling Archive)】：修剪前自動封存至 01_Memory/Archive，確保歷史永不遺失。
6. 【方案 B: GC 併發防重入保護 (GC Debounce Guard)】：防止高頻並發日誌重複觸發多次背景蒸餾。
"""

from __future__ import annotations

import sys
import os
import time
import json
import asyncio
import platform
import subprocess
import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import httpx


class AutonomousMemoryEngine:
    """自治記憶與影子管家核心引擎 (方案 A + B 一體化)"""

    def __init__(
        self, 
        workspace_root: Path, 
        ollama_url: str = "http://127.0.0.1:11434",
        gc_line_threshold: int = 60,
        model_name: str = "qwen2.5:3b"
    ):
        self.workspace_root = Path(workspace_root)
        self.l1_path = self.workspace_root / "01_Memory" / "Memory_Log.md"
        self.l2_dir = self.workspace_root / "02_Knowledge" / "Auto_Summaries"
        self.archive_dir = self.workspace_root / "01_Memory" / "Archive"
        self.ollama_url = ollama_url
        self.gc_line_threshold = gc_line_threshold
        self.model_name = model_name

        # 確保目錄結構存在
        self.l1_path.parent.mkdir(parents=True, exist_ok=True)
        self.l2_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        self.client_stats: dict[str, dict[str, Any]] = {}
        self.lock = asyncio.Lock()
        self._is_gc_running = False
        self.total_logs_count = 0
        self.total_gc_runs = 0

    # ==================== [方案 A] 1. 客戶端指紋追蹤 ====================
    def record_client(self, client_name: str, level: str = "INFO"):
        if client_name not in self.client_stats:
            self.client_stats[client_name] = {
                "request_count": 0,
                "first_seen": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "last_active": None,
                "error_count": 0
            }
        stats = self.client_stats[client_name]
        stats["request_count"] += 1
        stats["last_active"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if level in ["ERROR", "CRITICAL"]:
            stats["error_count"] += 1

    # ==================== [方案 A] 2. 主動報警 (Watchdog Alert) ====================
    def trigger_alert(self, title: str, msg: str):
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n" + "!" * 65)
        print(f"🚨 [WATCHDOG ALERT] [{now_str}] {title}")
        print(f"   內文: {msg}")
        print("!" * 65 + "\n")

        if sys.platform.startswith("win"):
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            except Exception:
                pass

    # ==================== [方案 A + B] 3. 非同步日誌寫入與閥值檢查 ====================
    async def log_event(self, client_id: str, level: str, message: str, role: str = "System") -> dict[str, Any]:
        self.record_client(client_id, level)
        self.total_logs_count += 1
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"- [{datetime.datetime.now().strftime('%Y-%m-%d')}] [{role}] [Client:{client_id}] [{level.upper()}] `[{timestamp}]`: {message}\n"

        async with self.lock:
            with open(self.l1_path, "a", encoding="utf-8", errors="replace") as f:
                f.write(entry)

        if level.upper() in ["CRITICAL", "FATAL"]:
            self.trigger_alert("🚨 MCP 嚴重異常警報", f"來源 [{client_id}]: {message}")
        elif level.upper() == "ERROR":
            self.trigger_alert("⚠️ MCP 警告通知", f"來源 [{client_id}]: {message}")

        current_lines = self._count_l1_lines()
        auto_gc_triggered = False
        if current_lines >= self.gc_line_threshold and not self._is_gc_running:
            self._is_gc_running = True
            asyncio.create_task(self._auto_gc_wrapper())
            auto_gc_triggered = True

        return {
            "status": "logged",
            "client_id": client_id,
            "level": level.upper(),
            "current_l1_lines": current_lines,
            "auto_gc_triggered": auto_gc_triggered
        }

    async def _auto_gc_wrapper(self):
        try:
            await self.run_shadow_gc(force=True)
        finally:
            self._is_gc_running = False

    def _count_l1_lines(self) -> int:
        if not self.l1_path.exists():
            return 0
        try:
            with open(self.l1_path, "r", encoding="utf-8", errors="replace") as f:
                return len(f.readlines())
        except Exception:
            return 0

    # ==================== [方案 B] 4. 本地 Ollama 影子管家蒸餾 (GC) ====================
    async def run_shadow_gc(self, force: bool = False) -> dict[str, Any]:
        if not self.l1_path.exists():
            return {"status": "skipped", "reason": "找不到 L1 記憶檔"}

        async with self.lock:
            with open(self.l1_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

        if len(lines) < self.gc_line_threshold and not force:
            return {"status": "idle", "lines": len(lines), "threshold": self.gc_line_threshold}

        log_content = "".join(lines)
        prompt = (
            "你是一個專業的 AI OS 知識庫管家。請將以下多 Agent 協同開發日誌提煉為 Markdown 結構化知識摘要。\n"
            "要求：\n"
            "1. 提取核心架構決策 (Architecture Decisions)、里程碑進度 (Milestones) 與解決的關鍵 Bug。\n"
            "2. 使用繁體中文，格式清晰，適當使用 [[雙向鏈結]] 標註核心概念（如 [[Three_Tier_Memory_Spec]], [[MCP_Server_Spec]]）。\n\n"
            f"=== 待提煉日誌內容 ===\n{log_content[:3000]}\n"
        )

        summary = ""
        used_engine = "Ollama-qwen2.5:3b"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={"model": self.model_name, "prompt": prompt, "stream": False}
                )
                if res.status_code == 200:
                    summary = res.json().get("response", "").strip()
                else:
                    raise RuntimeError(f"Ollama 回應狀態碼: {res.status_code}")
        except Exception as e:
            used_engine = "Rule-Based-Fallback"
            summary = self._fallback_rule_based_distill(lines)

        archive_stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_month = datetime.datetime.now().strftime("%Y%m")
        archive_file = self.archive_dir / f"Memory_Log_Archive_{archive_month}.md"
        
        with open(archive_file, "a", encoding="utf-8", errors="replace") as f:
            f.write(f"\n\n<!-- ARCHIVE_BLOCK_{archive_stamp} START -->\n")
            f.writelines(lines)
            f.write(f"\n<!-- ARCHIVE_BLOCK_{archive_stamp} END -->\n")

        summary_file = self.l2_dir / f"Auto_Summary_{archive_stamp}.md"
        with open(summary_file, "w", encoding="utf-8", errors="replace") as f:
            f.write(f"# 02_Knowledge / Auto_Summaries / Auto_Summary_{archive_stamp}.md\n\n")
            f.write(f"> **蒸餾時間**：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
            f.write(f"> **蒸餾引擎**：{used_engine}  \n")
            f.write(f"> **原始日誌筆數**：{len(lines)} 行  \n")
            f.write(f"> **歸檔存檔**：[[Memory_Log_Archive_{archive_month}]]\n\n---\n\n")
            f.write(summary + "\n")

        recent_lines = lines[-15:] if len(lines) >= 15 else lines
        async with self.lock:
            with open(self.l1_path, "w", encoding="utf-8", errors="replace") as f:
                f.write(f"# 01_Memory / Memory_Log.md（跨 Agent 即時共享記憶日誌）\n\n")
                f.write(f"> ⚡ **自適應記憶修剪完成**：歷史精華已自動蒸餾至 [[Auto_Summary_{archive_stamp}]]，原始紀錄歸檔至 [[Memory_Log_Archive_{archive_month}]]。\n\n")
                f.writelines(recent_lines)

        self.total_gc_runs += 1
        self.trigger_alert("🌟 記憶庫自動進化完成", f"已成功修剪 L1 並提煉至 Auto_Summary_{archive_stamp}.md ({used_engine})")

        return {
            "status": "success",
            "engine": used_engine,
            "pruned_lines": len(lines),
            "retained_lines": len(recent_lines),
            "summary_file": str(summary_file),
            "archive_file": str(archive_file)
        }

    def _fallback_rule_based_distill(self, lines: list[str]) -> str:
        pm_logs = [l.strip() for l in lines if "[PM]" in l or "👑" in l]
        coder_logs = [l.strip() for l in lines if "[Coder]" in l or "🛠️" in l]
        reviewer_logs = [l.strip() for l in lines if "[Reviewer]" in l or "🐎" in l]
        vision_logs = [l.strip() for l in lines if "[Vision]" in l or "👁️" in l]

        res = "## 📌 自動提煉結構化知識摘要\n\n"
        if pm_logs:
            res += "### 👑 專案架構與關鍵決策 (Architecture Decisions)\n" + "\n".join(f"- {l}" for l in pm_logs[-6:]) + "\n\n"
        if coder_logs:
            res += "### 🛠️ 模組實作與代碼交付 (Code Deliveries)\n" + "\n".join(f"- {l}" for l in coder_logs[-6:]) + "\n\n"
        if reviewer_logs:
            res += "### 🐎 審查、測試與安全度量 (Reviews & Safety)\n" + "\n".join(f"- {l}" for l in reviewer_logs[-6:]) + "\n\n"
        if vision_logs:
            res += "### 👁️ 多模態與視覺驗證 (Vision & Sandboxing)\n" + "\n".join(f"- {l}" for l in vision_logs[-4:]) + "\n\n"
        res += "### 🔗 核心技術規格關聯\n- [[Three_Tier_Memory_Spec]]\n- [[MCP_Server_Spec]]\n- [[AutoCAD_DXF_Spec]]\n- [[Fault_Tolerance_Spec]]\n"
        return res

    # ==================== [方案 B] 5. 背景定時輪詢 Daemon ====================
    async def start_background_daemon(self, interval_seconds: int = 3600):
        print(f"🕒 [DAEMON] 影子管家背景巡檢啟動 (巡檢週期: {interval_seconds} 秒)...")
        while True:
            try:
                await asyncio.sleep(interval_seconds)
                current_lines = self._count_l1_lines()
                if current_lines >= self.gc_line_threshold and not self._is_gc_running:
                    print(f"🕒 [DAEMON] L1 日誌達到 {current_lines} 行，觸發自動蒸餾...")
                    await self._auto_gc_wrapper()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.trigger_alert("影子管家背景巡檢異常", str(e))
                await asyncio.sleep(60)

    # ==================== 狀態與度量 ====================
    def get_status(self) -> dict[str, Any]:
        return {
            "status": "RUNNING",
            "l1_lines": self._count_l1_lines(),
            "gc_threshold": self.gc_line_threshold,
            "total_logs_ingested": self.total_logs_count,
            "total_gc_runs": self.total_gc_runs,
            "active_clients_count": len(self.client_stats),
            "clients": self.client_stats,
            "ollama_url": self.ollama_url,
            "ollama_model": self.model_name
        }


DEFAULT_WORKSPACE = Path(r"G:\我的雲端硬碟\AI_master_workspace\three_memory")
autonomous_engine = AutonomousMemoryEngine(DEFAULT_WORKSPACE)


if __name__ == "__main__":
    async def _test():
        print("Testing AutonomousMemoryEngine directly...")
        await autonomous_engine.log_event("Antigravity-Client", "INFO", "直接測試 AutonomousMemoryEngine 初始化", role="PM")
        status = autonomous_engine.get_status()
        print("Engine status:", json.dumps(status, indent=2, ensure_ascii=False))

    asyncio.run(_test())
