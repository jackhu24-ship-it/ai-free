# 交接檔（handoff.md）

> 任何 Agent、任何電腦接手前**必讀**；收工時**必更新**。本檔只放交接必需的精簡資訊，詳細脈絡放 Obsidian（若有 L3）。

## ⏯️ 目前做到哪
專案初始化完成（L1＋L2＋L3）。AI 工具鏈：OpenCode 懶人包 #00-#08 已完成，#09 Groq 金鑰待使用者申請、#10 Netlify 已部署用途 A（class-demo-jackhu24），extras browser/firebase 已裝（firebase login 待使用者執行）。

## 🚦 目前狀態
- 可運行。opencode 已連 OpenCode Zen 與 obsidian/notebooklm MCP
- .gitignore＋pre-commit hook 防護已生效（信用卡/API key/PDF/PPT/大檔 2MB 擋檔）

## ➡️ 下一步
1. 使用者申請 Groq API key → 設 GROQ_API_KEY 環境變數 → 完成 #09 語音字幕與 #10 用途 B（Functions 藏金鑰）
2. 使用者執行 firebase login（瀏覽器授權）→ 驗證 projects:list
3. 階段二：完成各 Demo 作品的實作（GAS 課堂回饋部署、Supabase 文字雲建表）

## ⚠️ 注意事項
- PATH 沒有 `C:\Users\user\.local\bin`：nlm、edge-tts、notebooklm-mcp 要用完整路徑呼叫
- PowerShell 5.1 不支援 `&&`，用 `;` 串指令
- netlify 點數制：正式部署一次 15 點（本月 300 點），先草稿後 --prod，--prod 要問過使用者
- sheets-gas-demo 是**獨立 git repo**（已推 GitHub），不要混入根 repo 的 commit

## 🕐 最後更新
- 時間：2026-08-03
- 更新者：opencode @ LAPTOP-C47IT9US
- Git push：已推（ai-free 私有 repo，見下方）
