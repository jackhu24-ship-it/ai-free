# 交接檔（handoff.md）

> 任何 Agent、任何電腦接手前**必讀**；收工時**必更新**。本檔只放交接必需的精簡資訊，詳細脈絡放 Obsidian（若有 L3）。

## ⏯️ 目前做到哪
專案初始化完成（L1＋L2＋L3，repo `jackhu24-ship-it/ai-free` 私有已推）。AI 工具鏈：懶人包 #00-#08＋extras 全完成；#10 用途 A 已上線（class-demo-jackhu24.netlify.app，2 次 --prod＝30 點）；敏感資料防護（.gitignore＋pre-commit hook 2MB）已生效並實測通過。

## 🚦 目前狀態
- 可運行。opencode 已連 OpenCode Zen＋obsidian/notebooklm MCP；netlify-cli 27.0.1 已登入（jackhu24@gmail.com）
- 根 repo 只含 AGENTS.md、handoff.md、.gitignore、.githooks、netlify-demo、supabase-demo；sheets-gas-demo 與 ai-agent-ep03 是獨立 repo 已排除

## ➡️ 下一步
1. 使用者申請 Groq API key 貼回 → 設 GROQ_API_KEY 環境變數 → 完成 #09 語音字幕（make_srt.py/clean.py 已備妥）
2. #10 用途 B：建 netlify/functions/ask-ai.mjs → netlify env:set AI_API_KEY → 草稿部署 → 問過使用者才 --prod
3. 使用者執行 firebase login（瀏覽器授權）→ 驗證 projects:list；#05 GAS 部署、#06 Supabase 建表皆為瀏覽器手動操作

## ⚠️ 注意事項
- PATH 沒有 `C:\Users\user\.local\bin`：nlm、edge-tts、notebooklm-mcp 要用完整路徑呼叫
- PowerShell 5.1 不支援 `&&` 用 `;`；原生指令的 stderr 顯示成紅字不代表失敗
- Netlify 點數制：正式部署 15 點/次（本月已用 30/300），先草稿 0 點、--prod 前必問使用者
- Netlify 新站 curl 會回 401（Edge Access 保護），站主瀏覽器造訪才看得到，是正常現象
- 2MB 擋檔靠 .githooks/pre-commit（git config core.hooksPath 已設），換 clone 要重設
- 改了 `~/.config/opencode/opencode.json`（playwright、open-computer-use、firebase MCP）— 不在 repo 內，換電腦要重設

## 🕐 最後更新
- 時間：2026-08-03
- 更新者：opencode @ LAPTOP-C47IT9US
- Git push：✅ 已推（ai-free 私有 repo）
