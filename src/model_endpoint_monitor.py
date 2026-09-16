#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 【PROJ-25 混合雲模型端點可用率與延遲探測監控腳本】：model_endpoint_monitor.py
========================================================================================
職責：
  定期與即時探測本地 Ollama 與雲端 OpenRouter API 之可用性與延遲 SLA (Heartbeat & Latency SLA)
  支援單次快速探測、常駐 Daemon 輪詢模式，並與 HybridAgentRouter 深度整合實現主動預先降級。
"""

from __future__ import annotations

import os
import sys

# 設定 Windows 終端與日誌編碼安全
if sys.platform.startswith("win"):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import json
import time
import logging
import argparse
from typing import Dict, Any, List, Optional
from datetime import datetime
import urllib.request
import urllib.error
from pathlib import Path

# 路徑與日誌配置
BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "01_Memory"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "health_monitor.log"
CONFIG_PATH = BASE_DIR / "00_System" / "model_router_config.json"

# 設定 Logger
logger = logging.getLogger("EndpointMonitor")
logger.setLevel(logging.INFO)
if not logger.handlers:
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


def sanitize_cell(val: Any) -> str:
    """CWE-1236 試算表公式注入防護"""
    s_val = str(val)
    if s_val.startswith(("=", "+", "-", "@")):
        return f"'{s_val}"
    return s_val


class EndpointMonitor:
    """
    PROJ-25 模型端點可用性與 SLA 延遲探測監控器
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or CONFIG_PATH
        self.config = self._load_config()
        self.failure_counters: Dict[str, int] = {}

    def _load_config(self) -> Dict[str, Any]:
        """安全載入系統設定檔"""
        if not self.config_path.exists():
            return {
                "endpoints": {
                    "ollama": {"base_url": "http://127.0.0.1:11434/api/generate"},
                    "openrouter": {"base_url": "https://openrouter.ai/api/v1"}
                }
            }
        try:
            with open(self.config_path, "r", encoding="utf-8", errors="replace") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"⚠️ 設定檔載入異常: {e}")
            return {}

    def probe_ollama(self, base_url: str = "http://127.0.0.1:11434", timeout: float = 5.0) -> Dict[str, Any]:
        """探測本地 Ollama 服務狀態與模型清單 (輕量 /api/tags 不浪費生成 Token)"""
        clean_url = base_url.replace("/api/generate", "").replace("/api/chat", "").rstrip("/")
        target_url = f"{clean_url}/api/tags"
        start_t = time.perf_counter()
        try:
            req = urllib.request.Request(target_url, headers={"User-Agent": "AI-OS-Monitor/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                latency_ms = round((time.perf_counter() - start_t) * 1000, 2)
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    model_count = len(data.get("models", []))
                    return {
                        "name": "Local Ollama",
                        "status": "HEALTHY",
                        "http_code": 200,
                        "latency_ms": latency_ms,
                        "models_loaded": model_count,
                        "error": None
                    }
        except Exception as e:
            latency_ms = round((time.perf_counter() - start_t) * 1000, 2)
            return {
                "name": "Local Ollama",
                "status": "UNAVAILABLE",
                "http_code": None,
                "latency_ms": latency_ms,
                "models_loaded": 0,
                "error": str(e)
            }

    def probe_openrouter(self, base_url: str = "https://openrouter.ai/api/v1", timeout: float = 8.0) -> Dict[str, Any]:
        """探測雲端 OpenRouter API 端點可用性 (輕量 /models 探測)"""
        clean_url = base_url.rstrip("/")
        target_url = f"{clean_url}/models"
        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        headers = {"User-Agent": "AI-OS-Monitor/1.0"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        start_t = time.perf_counter()
        try:
            req = urllib.request.Request(target_url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                latency_ms = round((time.perf_counter() - start_t) * 1000, 2)
                return {
                    "name": "Cloud OpenRouter",
                    "status": "HEALTHY" if resp.status == 200 else "DEGRADED",
                    "http_code": resp.status,
                    "latency_ms": latency_ms,
                    "error": None
                }
        except urllib.error.HTTPError as e:
            latency_ms = round((time.perf_counter() - start_t) * 1000, 2)
            status = "HEALTHY (AUTH_READY)" if e.code in (401, 403) else "ERROR"
            return {
                "name": "Cloud OpenRouter",
                "status": status,
                "http_code": e.code,
                "latency_ms": latency_ms,
                "error": f"HTTP {e.code}: {e.reason}"
            }
        except Exception as e:
            latency_ms = round((time.perf_counter() - start_t) * 1000, 2)
            return {
                "name": "Cloud OpenRouter",
                "status": "UNAVAILABLE",
                "http_code": None,
                "latency_ms": latency_ms,
                "error": str(e)
            }

    def evaluate_sla(self, latency_ms: float) -> str:
        """SLA 延遲等級三色評定"""
        if latency_ms < 300:
            return "🟢 優秀 (Excellent <300ms)"
        elif latency_ms < 1200:
            return "🟡 正常 (Acceptable 300~1200ms)"
        else:
            return "🔴 遲緩 (Degraded >1200ms)"

    def run_probe_cycle(self) -> List[Dict[str, Any]]:
        """執行一次完整端點探測循環"""
        ollama_url = self.config.get("endpoints", {}).get("ollama", {}).get("base_url", "http://127.0.0.1:11434")
        openrouter_url = self.config.get("endpoints", {}).get("openrouter", {}).get("base_url", "https://openrouter.ai/api/v1")

        results = [
            self.probe_ollama(base_url=ollama_url),
            self.probe_openrouter(base_url=openrouter_url)
        ]

        logger.info("=" * 70)
        logger.info("📡 【PROJ-25 模型端點 Heartbeat 探測報告】")
        for res in results:
            sla = self.evaluate_sla(res["latency_ms"]) if res["status"] != "UNAVAILABLE" else "⛔ 離線"
            status_icon = "🟢" if "HEALTHY" in res["status"] else "🔴"

            logger.info(
                f"{status_icon} [{res['name']}] 狀態: {res['status']} | "
                f"延遲: {res['latency_ms']}ms ({sla}) | 錯誤: {res['error'] or '無'}"
            )

            # 故障計數與連續 3 次中斷警報
            ep_name = res["name"]
            if res["status"] == "UNAVAILABLE":
                self.failure_counters[ep_name] = self.failure_counters.get(ep_name, 0) + 1
                if self.failure_counters[ep_name] >= 3:
                    logger.error(f"🚨 [CRITICAL ALERT] {ep_name} 已連續中斷 {self.failure_counters[ep_name]} 次！建議路由器預先切換 Fallback 備援通道！")
            else:
                self.failure_counters[ep_name] = 0

        logger.info("=" * 70)
        return results

    def start_daemon(self, interval_sec: int = 60):
        """以常駐 Daemon 模式定時執行探測"""
        logger.info(f"🚀 端點探測常駐守護進程啟動 (探測間隔: 每 {interval_sec} 秒)...")
        try:
            while True:
                self.run_probe_cycle()
                time.sleep(interval_sec)
        except KeyboardInterrupt:
            logger.info("🛑 收到終止訊號，監控常駐進程已安全關閉。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PROJ-25 端點可用率與延遲探測監控器")
    parser.add_argument("--daemon", action="store_true", help="以常駐模式執行")
    parser.add_argument("--interval", type=int, default=60, help="探測週期 (秒)，預設 60 秒")
    args = parser.parse_args()

    monitor = EndpointMonitor()
    if args.daemon:
        monitor.start_daemon(interval_sec=args.interval)
    else:
        monitor.run_probe_cycle()
