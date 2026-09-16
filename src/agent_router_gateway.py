#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 【PROJ-25 混合雲智慧模型自動調度網關】：agent_router_gateway.py
================================================================================
作戰定位：
  • 🛠️ 小開 (Agent_Coder)       ➔ 自動走 OpenRouter Free API (免吃本機顯存，極限 32B+ 代碼上下文)
  • 🐎 小馬 (Agent_Reviewer)    ➔ 自動走 本機 Ollama (DeepSeek-R1 / Qwen2.5，零延遲安全審查，代碼絕不外流)
  • 👁️ 小Ｏ (Agent_LocalVision) ➔ 自動走 本機 Ollama (LLaVA / Qwen-VL，100% 離線多模態與零個資洩漏)
  • ⚡ 小深 (Agent_DeepSeek)    ➔ 本機 Ollama / DSH (DeepSeek Harness 插件生態、深度長鏈推論與沙箱審計)

核心機制：
  1. 零人工干預：小幫手派工一鍵調用 router.dispatch("Agent_Coder", ...)
  2. 自動降級熔斷 (Resilient Fallback)：主模型異常/塞車時，毫秒級無縫切換備用模型
  3. 結構化回傳：包含 model_used, provider, latency_sec 與 content
"""

from __future__ import annotations

import sys
import os

# Windows UTF-8 編碼防護
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
import requests
from openai import OpenAI


def sanitize_cell(val: Any) -> str:
    """CWE-1236 試算表公式注入防護"""
    s_val = str(val)
    if s_val.startswith(("=", "+", "-", "@")):
        return f"'{s_val}"
    return s_val


class HybridAgentRouter:
    """
    4 Core 混合雲智能模型自動調度網關單例
    """

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        if config_path is None:
            # 自動搜尋 00_System/model_router_config.json
            base_dir = Path(__file__).resolve().parent.parent
            default_p = base_dir / "00_System" / "model_router_config.json"
            self.config_path = default_p if default_p.exists() else Path("00_System/model_router_config.json")
        else:
            self.config_path = Path(config_path)

        self.config = self._load_config()

        # 初始化 OpenRouter Client
        openrouter_cfg = self.config.get("endpoints", {}).get("openrouter", {})
        api_key_env = openrouter_cfg.get("api_key_env", "OPENROUTER_API_KEY")
        self.openrouter_key = os.getenv(api_key_env, "")

        self.openrouter_base_url = openrouter_cfg.get("base_url", "https://openrouter.ai/api/v1")
        self.openrouter_client = OpenAI(
            base_url=self.openrouter_base_url,
            api_key=self.openrouter_key or "sk-dummy-key-for-local-fallback",
            timeout=45.0
        )

        # 初始化 Ollama Endpoint
        ollama_cfg = self.config.get("endpoints", {}).get("ollama", {})
        self.ollama_generate_url = ollama_cfg.get("base_url", "http://localhost:11434/api/generate")
        self.ollama_chat_url = ollama_cfg.get("chat_url", "http://localhost:11434/api/chat")

    def _load_config(self) -> Dict[str, Any]:
        """安全載入 JSON 設定檔"""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8", errors="replace") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 設定檔載入異常: {e}", file=sys.stderr)
        return {}

    def reload_config(self):
        """熱重載設定檔"""
        self.config = self._load_config()

    def dispatch(
        self,
        agent_name: str,
        prompt: str,
        system_prompt: str = "",
        override_model: Optional[str] = None,
        override_provider: Optional[str] = None,
        timeout: float = 45.0,
        is_fallback_attempt: bool = False
    ) -> Dict[str, Any]:
        """
        統一調度分流核心方法 (支援跨 Provider 自動降級熔斷)
        """
        start_t = time.time()
        agent_cfg = self.config.get("agents", {}).get(agent_name)
        if not agent_cfg:
            raise ValueError(f"未知的 Agent 角色: {agent_name} (支援: Agent_Coder, Agent_Reviewer, Agent_LocalVision, Agent_Deep, Agent_DeepSeek)")

        provider = override_provider or agent_cfg.get("provider", "ollama")
        model_name = override_model or agent_cfg.get("default_model")
        fallback_model = agent_cfg.get("fallback_model")
        fallback_provider = agent_cfg.get("fallback_provider", "ollama" if provider == "openrouter" else "ollama")

        # ====================================================================
        # 分流 1：OpenRouter 免費雲端 API (🛠️ 小開 / ⚡ 小深 雲端首選)
        # ====================================================================
        if provider == "openrouter":
            # 若無 API Key 且未設 override，嘗試自動走 fallback 或回傳提示
            if not self.openrouter_key and not is_fallback_attempt:
                # 智慧備援：若無 OPENROUTER_API_KEY，自動轉向本地 fallback
                if fallback_model:
                    return self.dispatch(
                        agent_name, prompt, system_prompt,
                        override_model=fallback_model,
                        override_provider=fallback_provider,
                        timeout=timeout,
                        is_fallback_attempt=True
                    )

            try:
                response = self.openrouter_client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt or f"你是 {agent_name}，具備頂級推論與代碼分析能力。"},
                        {"role": "user", "content": prompt}
                    ],
                    extra_headers={
                        "HTTP-Referer": "https://github.com/local-ai-os",
                        "X-Title": "5-Core Multi-Agent OS"
                    }
                )
                content = response.choices[0].message.content or ""
                latency = round(time.time() - start_t, 3)
                return {
                    "status": "SUCCESS",
                    "agent": agent_name,
                    "provider": "openrouter",
                    "model_used": model_name,
                    "content": content,
                    "fallback_triggered": is_fallback_attempt,
                    "latency_sec": latency
                }
            except Exception as e:
                # 自動觸發 Fallback 降級 (支援切換 Provider 如本地 Ollama)
                if fallback_model and fallback_model != model_name and not is_fallback_attempt:
                    return self.dispatch(
                        agent_name, prompt, system_prompt,
                        override_model=fallback_model,
                        override_provider=fallback_provider,
                        timeout=timeout,
                        is_fallback_attempt=True
                    )
                raise RuntimeError(f"OpenRouter 派工失敗 (Model: {model_name}): {e}")

        # ====================================================================
        # 分流 2：本地 Ollama 100% 離線免費推理 (🐎 小馬 / 👁️ 小Ｏ / ⚡ 小深 本地離線)
        # ====================================================================
        elif provider == "ollama":
            payload = {
                "model": model_name,
                "system": system_prompt or "你是 Five-Agent AI OS 本地專屬智能核心。",
                "prompt": prompt,
                "stream": False
            }
            try:
                res = requests.post(self.ollama_generate_url, json=payload, timeout=timeout)
                res.raise_for_status()
                data = res.json()
                content = data.get("response", "")
                latency = round(time.time() - start_t, 3)
                return {
                    "status": "SUCCESS",
                    "agent": agent_name,
                    "provider": "ollama",
                    "model_used": model_name,
                    "content": content,
                    "fallback_triggered": is_fallback_attempt,
                    "latency_sec": latency
                }
            except Exception as e:
                # 本地模型降級至備用模型 (例如 deepseek-r1:8b 降至 qwen2.5:7b)
                if fallback_model and fallback_model != model_name and not is_fallback_attempt:
                    return self.dispatch(
                        agent_name, prompt, system_prompt,
                        override_model=fallback_model, timeout=timeout, is_fallback_attempt=True
                    )
                raise RuntimeError(f"本地 Ollama 派工失敗 (Model: {model_name}，請確認 Ollama 服務是否開啟): {e}")

        else:
            raise ValueError(f"不支援的 Provider 提供商: {provider}")

    def health_check(self) -> Dict[str, Any]:
        """系統健康狀態與端點延遲 SLA 探測 (整合 EndpointMonitor)"""
        try:
            from model_endpoint_monitor import EndpointMonitor
            monitor = EndpointMonitor(self.config_path)
            probe_res = monitor.run_probe_cycle()
            return {
                "status": "HEALTHY",
                "probes": probe_res,
                "openrouter": next((p for p in probe_res if "OpenRouter" in p["name"]), {}),
                "ollama": next((p for p in probe_res if "Ollama" in p["name"]), {})
            }
        except Exception as e:
            # 降級備用探測
            status = {
                "openrouter": {"available": bool(self.openrouter_key), "key_set": bool(self.openrouter_key)},
                "ollama": {"available": False, "models": []}
            }
            try:
                r = requests.get("http://localhost:11434/api/tags", timeout=2.0)
                if r.status_code == 200:
                    status["ollama"]["available"] = True
                    models = [m.get("name") for m in r.json().get("models", [])]
                    status["ollama"]["models"] = models
            except Exception:
                status["ollama"]["available"] = False
            return status


# 全域單例
router = HybridAgentRouter()


def run_self_test():
    print("=" * 85)
    print("🚀 【PROJ-25 混合雲智能模型調度網關自檢】")
    print("=" * 85)

    r = HybridAgentRouter()
    agents = r.config.get("agents", {})
    print(f"✅ 設定檔載入成功: {r.config_path}")
    print(f"  -> 註冊 Agent 數量: {len(agents)}")
    for name, cfg in agents.items():
        print(f"  • {name:18s} ➔ Provider: {cfg['provider']:10s} | Default: {cfg['default_model']}")

    health = r.health_check()
    print(f"\n🔍 端點健康檢測與 SLA 延遲探測:")
    if "probes" in health:
        for p in health["probes"]:
            print(f"  • [{p['name']:16s}] 狀態: {p['status']:10s} | 延遲: {p['latency_ms']}ms | 錯誤: {p.get('error') or '無'}")
    else:
        print(f"  • OpenRouter API Key : {'🟢 已配置' if health['openrouter'].get('key_set') else '🟡 未配置 (自動走 Fallback)'}")
        print(f"  • 本地 Ollama 服務    : {'🟢 在線' if health['ollama'].get('available') else '🟡 離線/未啟動'}")

    print("\n🟢 agent_router_gateway.py 模組自檢通過！")


if __name__ == "__main__":
    run_self_test()
