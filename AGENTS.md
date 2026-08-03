# 260728 程式工作區（專案藍圖）

> 本檔為跨 Agent 通用的專案藍圖（AGENTS.md 開放標準）。任何 Agent 的每個 session 都應先讀本檔＋`handoff.md`。

## 專案簡介
AI 教學工具鏈建置：安裝並熟悉 AI 工具鏈（OpenCode 懶人包 13 包＋Demo 作品），作為教學備課工具。本資料夾是工作區根目錄，包含多個 demo 與子專案。

## 關鍵時程
<!-- 格式：- 事件名稱：日期（說明）；沒有就留白 -->

## 目標與路線圖
<!-- 用 checklist 追蹤，收工技能會更新這裡 -->
- [x] 階段一：完成 OpenCode 懶人包安裝（#00-#10＋extras）
  - [x] #00-#08（環境/模型/工具/NotebookLM/Obsidian/GAS/GitHub/工作流程技能）
  - [x] #10 用途 A：Netlify 部署（class-demo-jackhu24.netlify.app，正式網址已發布）
  - [x] extras：browser（Playwright＋open-computer-use）、firebase CLI
  - [ ] #09 Groq 金鑰（待使用者申請 → GROQ_API_KEY 環境變數）
  - [ ] #10 用途 B：Functions 藏金鑰後端（待 Groq 金鑰）
  - [ ] extras firebase login（待使用者執行）
- [ ] 階段二：Demo 作品（GAS 課堂回饋、Supabase 文字雲、Groq 語音字幕、Netlify 網頁部署）
  - [x] Netlify 網頁部署（用途 A）
  - [ ] GAS 課堂回饋（待瀏覽器手動部署）
  - [ ] Supabase 文字雲（待註冊建專案）
  - [ ] Groq 語音字幕（待金鑰）
- [ ] 階段三：實際運用於教學備課

## 資料夾結構
<!-- 初始化時自動掃描生成，之後新增檔案要更新 -->
```
C:\260728-code\                ← 工作區根目錄（git repo，私有）
├── .gitignore                 ← 敏感資料防護（信用卡/API key/PDF/PPT/大檔）
├── .githooks\pre-commit       ← 2MB 上限＋檔案類型擋檔
├── ai-agent-ep03\             ← AI Agent 練習專案（verify_core.py、.venv）
├── netlify-demo\              ← Netlify 部署 demo（class-demo-jackhu24）
├── sheets-gas-demo\           ← Google Apps Script 課堂回饋 demo（獨立 repo，已推 GitHub）
└── supabase-demo\             ← Supabase 文字雲 demo（建表SQL、keep-alive）
```

## 同步層級（本專案初始化至第 3 層級）

| 層級 | 平台 | 位置 | 讀取時機 |
|------|------|------|---------|
| L1 | 本地 | `AGENTS.md`＋`handoff.md` | 每個 session |
| L2 | GitHub | jackhu24-ship-it/ai-free（私有） | 指定時 |
| L3 | Obsidian | 260728-code/專案工作流程.md | 有需要時 |

## 工作約定
- 任何 Agent、任何電腦：**開工先讀 `handoff.md`，收工必更新 `handoff.md`**
- 修改共用檔案前先讀最新內容，避免覆蓋其他 Agent 的變更
- 所有回應與文件使用繁體中文
- 修改前先確認計畫，優先保留原有資料結構

## 安全與隱私（不可違反）
- **不把 API key、密碼、憑證寫進 repo**，也不要貼進 `AGENTS.md`／`handoff.md`；一律放 `.env` 並列入 `.gitignore`
- **學生資料只用座號**，不出現姓名、學號、班級以外的個資、照片或聯絡方式
- 要公開分享前，先確認檔案裡沒有上述兩類內容
- 信用卡／金融資料、PDF、簡報、試算表、影像、音樂檔、大於 2MB 的檔案**一律不上傳 GitHub**（`.gitignore`＋`pre-commit` hook 雙重防護）
