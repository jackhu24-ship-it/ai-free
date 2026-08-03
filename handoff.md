# 交接檔（handoff.md）

> 任何 Agent、任何電腦接手前**必讀**；收工時**必更新**。本檔只放交接必需的精簡資訊，詳細脈絡放 Obsidian（若有 L3）。

## ⏯️ 目前做到哪
#05 GAS 課堂回饋與 #06 Supabase 文字雲後端全部完成；文字雲前端頁面已完成（wordcloud-app）：
- **#05 GAS 已部署上線**：Web App 網址 `https://script.google.com/macros/s/AKfycbx9fG6GRbTHRuphY-cI0_zqjVoENVM4f3f5gE1XHpHrvaQBs_Mg-iGfwFYEI4oK64VF/exec`（專案「課堂回饋」，Code.gs＋index.html 已儲存，實測送出正常；試算表測試資料已清空，只剩標題列）
- **#06 Supabase 後端完成**：專案 class-wordcloud（東京）、建表 SQL 三關（table＋RLS＋realtime）全過、金鑰三件套已存 `supabase-demo\.env`（URL＋publishable＋secret）、GitHub secrets 已設、keep-alive workflow 上線實測 PING_OK（run 30797246097）
- **文字雲前端完成＋已部署上線**：`wordcloud-app\public\index.html`（座號＋詞彙輸入、WordCloud2 文字雲、Supabase realtime 即時更新、參與人數/詞數統計），本地 8099 實測：送出/文字雲/跨分頁即時更新全通過；**已部署 Netlify 正式網址 https://class-wordcloud.netlify.app 並設為公開**（網頁載入/送出/零 console error 驗證通過）
- **class-demo-jackhu24（問問 AI）已設為公開**：dashboard overview 一鍵 Make public 完成，https://class-demo-jackhu24.netlify.app 無登入 HTTP 200 驗證通過（GROQ 金鑰藏 Netlify Functions 環境變數前端拿不到，且為免費 key，被刷僅 rate limit 無費用，公開安全性已評估）

> ⚠️ Netlify 新站預設「Private project」（2026-07 後新團隊「Private for new projects」）— 需在 dashboard 專案 overview **Make public** 一鍵公開（會開對話框 Public 再確認）；兩個站（class-wordcloud、class-demo-jackhu24）均已處理為公開。相關 doc：docs.netlify.com/manage/security/secure-access-to-sites/project-visibility/

## 🚦 目前狀態
- 可運行。#00-#10＋extras 全部完成，剩 extras firebase login（使用者自行執行）
- Supabase REST 實測：publishable key 可查/可插（RLS「任何人可加」），不可刪（符合學生用途）；wordcloud 表測試資料已全清空
- 文字雲前端已完成＋部署上線（class-wordcloud.netlify.app，已公開）；class-demo-jackhu24（問問 AI）也已公開，兩站無登入皆可訪問

## ➡️ 下一步
1. extras firebase login（使用者自己執行）→ 驗證 projects:list
2. 階段三：實際運用於教學備課
3. （可選）QR Code 列印：`qr-codes\print.html` 已備好，可直接列印兩站 QR

## ⚠️ 注意事項
- **GAS 操作技巧（本次驗證有效）**：用 Playwright MCP（已登入 Google 帳號）操作 script.google.com 時，Monaco 編輯器要用 `window.monaco.editor.getEditors()[0].setValue()` 直接寫內容（Ctrl+A 會被自動完成攔截、execCommand 會產生縮排殘留）；執行函式要在「請選取要執行的函式」下拉按 Home/ArrowUp/Enter 鍵盤選取（JS click 不會觸發 Angular 事件）
- Supabase 金鑰只在 `supabase-demo\.env`（gitignore 已擋）；GitHub secrets 用 `SUPABASE_URL`＋`SUPABASE_PUBLISHABLE_KEY`（keep-alive 用 publishable 就夠）
- keep-alive workflow 檔同時存在 `.github\workflows\`（作用中）與 `supabase-demo\`（備份），改動要同步兩份
- Supabase 新介面 API keys 路徑：Settings → API Keys（非舊的 settings/api）；secret key 顯示遮罩，用 Copy 按鈕取完整值
- PATH 沒有 `C:\Users\user\.local\bin`：nlm、edge-tts、notebooklm-mcp 要用完整路徑呼叫
- PowerShell 5.1 不支援 `&&` 用 `;`；原生指令 stderr 顯示紅字不代表失敗；curl 要用 `curl.exe` 避開 Invoke-WebRequest 別名
- Netlify 點數制：本月已用 45/300，--prod 前必問使用者；新站對未登入者 401
- 改了 `~/.config/opencode/` 下設定 — 不在 repo 內，換電腦要重設

## 🕐 最後更新
- 時間：2026-08-03
- 更新者：opencode @ LAPTOP-C47IT9US
- Git push：✅ 已推（d97fe2c：QR Code＋試算表清理＋handoff 更新；前一筆 7535ae6 兩站公開設定）
- 本次完成：QR Code 兩站已產生（qr-codes\）；firebase login 驗證通過（projects:list 正常，無專案為預期）；GAS 試算表測試資料已清空（只剩標題列）＋Code.gs 還原乾淨＋未命名.gs 殘留檔已刪除；qr-codes 已 push
