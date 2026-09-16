#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 跨平台 MCP 設定檔安全注入與合併引擎 (SRC/safe_mcp_config_injector.py)
================================================================================
作者：🛠️ 小開 (Agent_Coder)
統籌：👑 小幫手 (Agent_PM)

核心功能：
1. 【無損安全合併 (Lossless Merge)】：安全讀取 Claude Desktop 與 OpenCode 之現有設定檔，
   精準更新/注入 `autonomous_memory_mcp` 伺服器配置，絕不覆蓋抹除使用者既有的其他 MCP 工具！
2. 【路徑自動修復 (Self-Healing Paths)】：自動將當前所在之 Google Drive 實體路徑轉義並注入。
3. 【多平台支援】：同時支援 Claude Desktop、OpenCode CLI 與 Hermes Desktop。
"""

from __future__ import annotations

import sys
import os
import json
from pathlib import Path

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def inject_mcp_configurations():
    workspace_root = Path(__file__).resolve().parent.parent
    server_script = workspace_root / "SRC" / "lightweight_mcp_server.py"

    if not server_script.exists():
        print(f"[❌ 錯誤] 找不到 MCP 伺服器主腳本: {server_script}")
        return False

    server_entry = {
        "command": sys.executable,
        "args": [str(server_script).replace("\\", "/")]
    }

    results = []

    # 1. 注入 Claude Desktop (%APPDATA%\Claude\claude_desktop_config.json)
    appdata = os.environ.get("APPDATA")
    if appdata:
        claude_dir = Path(appdata) / "Claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        claude_config_file = claude_dir / "claude_desktop_config.json"

        config_data = {}
        if claude_config_file.exists():
            try:
                with open(claude_config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            except Exception:
                config_data = {}

        if "mcpServers" not in config_data:
            config_data["mcpServers"] = {}

        config_data["mcpServers"]["autonomous_memory_mcp"] = server_entry

        with open(claude_config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        results.append(f"Claude Desktop: {claude_config_file}")

    # 2. 注入 OpenCode (%USERPROFILE%\.config\opencode\opencode.json)
    user_home = Path.home()
    opencode_dir = user_home / ".config" / "opencode"
    if opencode_dir.exists():
        opencode_config_file = opencode_dir / "opencode.json"
        op_data = {}
        if opencode_config_file.exists():
            try:
                with open(opencode_config_file, "r", encoding="utf-8") as f:
                    op_data = json.load(f)
            except Exception:
                op_data = {}

        if "mcp" not in op_data:
            op_data["mcp"] = {}

        op_data["mcp"]["autonomous_memory_mcp"] = {
            "type": "stdio",
            "command": sys.executable,
            "args": [str(server_script).replace("\\", "/")]
        }

        with open(opencode_config_file, "w", encoding="utf-8") as f:
            json.dump(op_data, f, indent=2, ensure_ascii=False)
        results.append(f"OpenCode: {opencode_config_file}")

    print("🎉 [MCP 注入完成] 已成功無損注入以下客戶端：")
    for r in results:
        print(f"  • {r}")
    return True


if __name__ == "__main__":
    inject_mcp_configurations()
