# 交接檔（handoff.md）

> 任何 Agent、任何電腦接手前**必讀**；收工時**必更新**。本檔只放交接必需的精簡資訊，詳細脈絡放 Obsidian（若有 L3）。

## ⏯️ 目前做到哪
#05 GAS 課堂回饋與 #06 Supabase 文字雲後端全部完成；文字雲前端頁面已完成（wordcloud-app）：
- **#05 GAS 已部署上線**：Web App 網址 `https://script.google.com/macros/s/AKfycbx9fG6GRbTHRuphY-cI0_zqjVoENVM4f3f5gE1XHpHrvaQBs_Mg-iGfwFYEI4oK64VF/exec`（專案「課堂回饋」，Code.gs＋index.html 已儲存，實測送出正常；試算表留有測試資料 fff/fff/ddd/kddd/hqi/測試訊息/第二次測試 待清理）
- **#06 Supabase 後端完成**：專案 class-wordcloud（東京）、建表 SQL 三關（table＋RLS＋realtime）全過、金鑰三件套已存 `supabase-demo\.env`（URL＋publishable＋secret）、GitHub secrets 已設、keep-alive workflow 上線實測 PING_OK（run 30797246097）
- **文字雲前端完成＋已部署上線**：`wordcloud-app\public\index.html`（座號＋詞彙輸入、WordCloud2 文字雲、Supabase realtime 即時更新、參與人數/詞數統計），本地 8099 實測：送出/文字雲/跨分頁即時更新全通過；**已部署 Netlify 正式網址 https://class-wordcloud.netlify.app 並設為公開**（網頁載入/送出/零 console error 驗證通過）

> ⚠️ Netlify 新站預設「Private project」（2026-07 後新團隊「Private for new projects」）— 需在 dashboard 專案 overview **Make public** 一鍵公開（會開對話框選 Public 再確認）；class-demo-jackhu24 目前仍是 Private，若要公開同樣處理。相關 doc：docs.netlify.com/manage/security/secure-access-to-sites/project-visibility/

## 🚦 目前狀態
- 可運行。#00-#10＋extras 全部完成，剩 extras firebase login（使用者自行執行）
- Supabase REST 實測：publishable key 可查/可插（RLS「任何人可加」），不可刪（符合學生用途）；wordcloud 表測試資料已全清空
- 文字雲前端已完成＋部署上線（class-wordcloud.netlify.app，已公開）

## ➡️ 下一步
1. Netlify QR Code 產生（可印成教室 QR；也考慮把 class-demo-jackhu24 設公開）
2. extras firebase login（使用者自己執行）→ 驗證 projects:list
3. 試算表測試資料清理（使用者決定）
4. 階段三：實際運用於教學備課

## ⚠️ 注意事項
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
- Git push：待推（本次變動：文字雲前端完成＋部署上線、AGENTS/handoff 更新）
