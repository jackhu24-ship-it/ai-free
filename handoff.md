# 交接檔（handoff.md）

> 任何 Agent、任何電腦接手前**必讀**；收工時**必更新**。本檔只放交接必需的精簡資訊，詳細脈絡放 Obsidian（若有 L3）。

## ⏯️ 目前做到哪
#09 Groq 與 #10 用途 B 完成：GROQ_API_KEY 已設（User 層級）；語音轉字幕 demo 完成（edge-tts 合成音→Whisper→demo.srt）；Netlify ask-ai 函式已正式上線（class-demo-jackhu24.netlify.app，金鑰藏 env: AI_API_KEY secret，前端無金鑰，F12 驗證通過）。

## 🚦 目前狀態
- 可運行。全部 13 包中 11 包完成（#00-#10＋extras browser），剩 extras firebase login
- 正式網址已變「問問 AI」頁面；groq-demo 資料夾新增（demo.mp3、clean.flac、chunk_000.json、demo.srt）

## ➡️ 下一步
1. extras firebase login（使用者自己執行，瀏覽器授權）→ 驗證 projects:list
2. 階段二：GAS 課堂回饋部署（瀏覽器手動）、Supabase 文字雲（註冊建專案＋建表）
3. Netlify 正式網址 QR Code 產生（可印成教室 QR）

## ⚠️ 注意事項
- PATH 沒有 `C:\Users\user\.local\bin`：nlm、edge-tts、notebooklm-mcp 要用完整路徑呼叫
- PowerShell 5.1 不支援 `&&` 用 `;`；原生指令的 stderr 顯示成紅字不代表失敗
- Netlify 點數制：本月已用 45/300（3 次 --prod），先草稿 0 點、--prod 前必問使用者
- Netlify 新站 curl 會回 401（Edge Access 保護），站主瀏覽器造訪才看得到
- netlify env:set 設 secret 要加 `--context production`；dev 測試用 .env.local（用完刪除）
- 2MB 擋檔靠 .githooks/pre-commit（git config core.hooksPath 已設）
- 改了 `~/.config/opencode/opencode.json`（playwright、open-computer-use、firebase MCP）— 不在 repo 內，換電腦要重設

## 🕐 最後更新
- 時間：2026-08-03
- 更新者：opencode @ LAPTOP-C47IT9US
- Git push：✅ 已推（ai-free 私有 repo）
