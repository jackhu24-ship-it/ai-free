# 交接檔（handoff.md）

> 任何 Agent、任何電腦接手前**必讀**；收工時**必更新**。本檔只放交接必需的精簡資訊，詳細脈絡放 Obsidian（若有 L3）。

## ⏯️ 目前做到哪
#05 GAS 課堂回饋與 #06 Supabase 文字雲後端全部完成；文字雲前端頁面已完成並上線；Padlet 免費帳戶已申請；chezmoi dotfiles 管理已上線：
- **#05 GAS 已部署上線**：Web App 網址 `https://script.google.com/macros/s/AKfycbx9fG6GRbTHRuphY-cI0_zqjVoENVM4f3f5gE1XHpHrvaQBs_Mg-iGfwFYEI4oK64VF/exec`（專案「課堂回饋」，Code.gs＋index.html 已儲存，實測送出正常；試算表測試資料已清空，只剩標題列）
- **#06 Supabase 後端完成**：專案 class-wordcloud（東京）、建表 SQL 三關（table＋RLS＋realtime）全過、金鑰三件套已存 `supabase-demo\.env`（URL＋publishable＋secret）、GitHub secrets 已設、keep-alive workflow 上線實測 PING_OK（run 30797246097）
- **文字雲前端完成＋已部署上線**：`wordcloud-app\public\index.html`（座號＋詞彙輸入、WordCloud2 文字雲、Supabase realtime 即時更新、參與人數/詞數統計），本地 8099 實測：送出/文字雲/跨分頁即時更新全通過；**已部署 Netlify 正式網址 https://class-wordcloud.netlify.app 並設為公開**（網頁載入/送出/零 console error 驗證通過）
- **class-demo-jackhu24（問問 AI）已設為公開**：dashboard overview 一鍵 Make public 完成，https://class-demo-jackhu24.netlify.app 無登入 HTTP 200 驗證通過（GROQ 金鑰藏 Netlify Functions 環境變數前端拿不到，且為免費 key，被刷僅 rate limit 無費用，公開安全性已評估）
- **Padlet 免費帳戶已申請**：以 Google 帳號 jackhu24@gmail.com 註冊（email 驗證碼建立），用途選「我是教師」、方案選「免費」（3 padlet／20MB 上傳）；已登入 dashboard 可開始製作板子；學生免帳號即可貼
- **chezmoi dotfiles 管理已上線**：chezmoi v2.72.0 已安裝（winget twpayne.chezmoi）；全域設定已納管 `~/.config/opencode/`（opencode.json、opencode.jsonc、四包 skills：audio-notes/project-init/shutdown/startup），已建私有 repo **jackhu24-ship-it/dotfiles** 並推送（commit 837e49d）；node_modules 與 package 檔由既有 `.gitignore` 排除

> ⚠️ Netlify 新站預設「Private project」（2026-07 後新團隊「Private for new projects」）— 需在 dashboard 專案 overview **Make public** 一鍵公開（會開對話框 Public 再確認）；兩個站（class-wordcloud、class-demo-jackhu24）均已公開。相關 doc：docs.netlify.com/manage/security/secure-access-to-sites/project-visibility/

## 🚦 目前狀態
- 可運行。#00-#10＋extras 全部完成。
- Supabase REST 實測：publishable key 可查/可插（RLS「任何人可加」），不可刪（符合學生用途）；wordcloud 表測試資料已全清空
- 文字雲前端已完成＋部署上線（class-wordcloud.netlify.app，已公開）；class-demo-jackhu24（問問 AI）也已公開，兩站無登入皆可訪問
- Padlet：免費個人帳戶已可登入使用（3 板額度）
- chezmoi：opencode 全域設定已納管於 dotfiles repo；換電腦同步方式 → `chezmoi init https://github.com/jackhu24-ship-it/dotfiles.git` 後 `chezmoi apply`

## ➡️ 下一步
1. 階段三：實際運用於教學備課（Padlet 板子製作、文字雲課堂使用）
2. 建立 Padlet 第一個教學板子（免費版僅 3 板，用完可刪除/匯出重用）
3. （可選）chezmoi 補充：把更多全域設定納管（如 PowerShell `$PROFILE`）；QR Code 列印 `qr-codes\print.html`

## ⚠️ 注意事項
- **chezmoi 新裝**：PATH 已由 winget 更新，但新開終端才自動生效；同一 session 內要先刷新 PATH（`$env:PATH = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")`）才能呼叫 chezmoi
- **兩個 git repo 分開管理**：工作區 ai-free（`G:\我的雲端硬碟\260803_opencode`）與 dotfiles（`~/.local/share/chezmoi`，remote 是 jackhu24-ship-it/dotfiles）是獨立 repo，收工/開工要各自處理
- **GAS 操作技巧（本次驗證有效）**：用 Playwright MCP（已登入 Google 帳號）操作 script.google.com 時，Monaco 編輯器要用 `window.monaco.editor.getEditors()[0].setValue()` 直接寫內容（Ctrl+A 會被自動完成攔截、execCommand 會產生縮排殘留）；執行函式要在「請選取要執行的函式」下拉按 Home/ArrowUp/Enter 鍵盤選（JS click 不會觸發 Angular 事件）
- Supabase 金鑰只在 `supabase-demo\.env`（gitignore 已擋）；GitHub secrets 用 `SUPABASE_URL`＋`SUPABASE_PUBLISHABLE_KEY`（keep-alive 用 publishable 就夠）
- keep-alive workflow 檔同時存在 `.github\workflows\`（作用中）與 `supabase-demo\`（備份），改動要同步兩份
- Supabase 新介面 API keys 路徑：Settings → API Keys（非舊的 settings/api）；secret key 顯示遮罩，用 Copy 按鈕取完整值
- PATH 沒有 `C:\Users\user\.local\bin`：nlm、edge-tts、notebooklm-mcp 要用完整路徑呼叫
- PowerShell 5.1 不支援 `&&` 用 `;`；原生指令 stderr 顯示紅字不代表失敗；curl 要用 `curl.exe` 避開 Invoke-WebRequest 別名（呼叫 GitHub API 引號會出問題，改用 curl.exe＋Node 解析 JSON）
- Netlify 點數制：本月已用 45/300，--prod 前必問使用者；新站對未登入者 401

## 🕐 最後更新
- 時間：2026-08-05
- 更新者：opencode @ LAPTOP-C47IT9US
- Git push：待推（L2 完成後回填）
- 本次完成：chezmoi 安裝＋opencode 全域設定納管（json＋四包 skills）＋建立 dotfiles 私有 repo 推送（837e49d）；確認無敏感資料（skills 僅環境變數名稱）