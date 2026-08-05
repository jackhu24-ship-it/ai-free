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
  - [x] #09 Groq 金鑰（GROQ_API_KEY 已設，語音轉字幕 demo 完成）
  - [x] #10 用途 B：Functions 藏金鑰後端（ask-ai 函式已上線）
  - [x] extras firebase login（已登入，projects:list 驗證通過）
  - [x] extras chezmoi（dotfiles 管理，已建 dotfiles 私有 repo 並推送）
- [ ] 階段二：Demo 作品（GAS 課堂回饋、Supabase 文字雲、Groq 語音字幕、Netlify 網頁部署）
  - [x] Netlify 網頁部署（用途 A＋用途 B）
  - [x] GAS 課堂回饋（已部署上線，Web App 網址見 handoff）
  - [x] Supabase 文字雲（專案＋建表＋RLS＋keep-alive 全完成；前端頁面待做）
  - [x] Groq 語音字幕（edge-tts 測試音→SRT 完成）
- [x] 階段二附加：Supabase 文字雲前端頁面（學生輸入＋文字雲，可部署 Netlify）
- [x] 階段二附加：Netlify 兩站公開設定（class-wordcloud＋class-demo-jackhu24 皆無登入可訪問）
- [x] 階段二附加：Netlify QR Code（qr-codes\ 兩站 SVG＋A4 列印頁）
- [x] 階段二附加：GAS 試算表測試資料清理（只剩標題列）
- [x] 階段二附加：Padlet 免費帳戶申請（jackhu24@gmail.com，免費版 3 板限制；評估學生免帳號即可貼）
- [x] 階段二附加：簡報技能集安裝（opencode-presentation-skills 5 個技能：SOIL/PPTX/HTML/圖片式；Python 3.12＋PptxGenJS＋Playwright 依賴備齊）
- [x] 階段二附加：Wordwall CLI 安裝＋登入（wordwall-cli-opencode，本機 C:\wordwall-cli-opencode；可建活動/發作業/讀成績）
- [x] 階段二附加：RDQ 技能安裝（需求探索四象限，clone 至 ~/.config/opencode/skills\rdq，chezmoi 納管）
- [x] 階段二附加：簡報技能實作一（Agent 工具鏈現況報告 21 頁，PPTX＋PDF 交付簡報作品\；修復 pptxgenjs 負寬度坑）
- [x] 階段二附加：Obsidian MCP 配置完成（mcpvault 全域安裝＋opencode.json 改用 node 直連 server.js，消除 npx 下載延遲；L3 層級正式啟用）
- [ ] 階段二附加：codex-security 掃描工作區（openai/codex-security 已裝＋登入＋中文路徑編碼修補；三路線全卡額度：ChatGPT 帳號 8/20 重置、OpenAI API 需充值、OpenRouter 免費 50 請求/日 8/6 08:00 重置；已建 8/6 排程提醒＋縮範圍策略 sheets-gas-demo）
- [x] 階段二附加：簽呈 Word/PDF 模板製作（A4 直向標準格式已重製完成，同步 G:\我的雲端硬碟\簽呈表單\）
- [x] 階段二附加：全域技能 web-study-manual-builder 與 auto-approve-command-guide 建立與 chezmoi 同步
- [x] 階段二附加：opencode-draw-free 部件歸檔與本機安裝比對
- [x] 階段二附加：《極光下的父愛》1 分鐘繪本短片音畫同步與風吹草動 GIF 實作
- [ ] 階段三：實際運用於教學備課

## 資料夾結構
<!-- 初始化時自動掃描生成，之後新增檔案要更新 -->
```
G:\我的雲端硬碟\260803_opencode\    ← 工作區根目錄（git repo，私有；由 C:\260728-code 全量複製，SHA256 驗證完整）
├── .gitignore                 ← 敏感資料防護（信用卡/API key/PDF/PPT/大檔）
├── .githooks\pre-commit       ← 2MB 上限＋檔案類型擋檔
├── .github\workflows\         ← supabase-keep-alive.yml（每日 21:00 UTC ping）
├── groq-demo\                 ← Groq 語音轉字幕 demo（edge-tts 測試音、SRT）
├── netlify-demo\              ← Netlify 部署 demo（class-demo-jackhu24，含 ask-ai 函式）
├── padlet-assets\             ← clone 自 mathruffian-dot/padlet-assets（圖床 repo，已 gitignore 排除）
├── qr-codes\                  ← 兩站 QR Code（SVG＋print.html A4 列印頁）
├── sheets-gas-demo\           ← Google Apps Script 課堂回饋 demo（獨立 repo，已推 GitHub）
├── supabase-demo\             ← Supabase 文字雲 demo（建表SQL、keep-alive、.env 金鑰）
├── wordcloud-app\             ← 文字雲前端頁面（Supabase＋WordCloud2，可部署 Netlify）
├── 簡報作品\                  ← 簡報技能成品輸出（Agent工具鏈現況報告.pptx＋.pdf，gitignore 排除不推 GitHub）
└── 安裝資料\                  ← 使用者自建暫存（含 wordwall-cli-opencode、codex-security 副本，已 gitignore 排除）
```
> ⚠️ Wordwall 工具執行主位置在 **C:\wordwall-cli-opencode**（本機，已裝環境＋已登入），不在工作區內；雲端硬碟對 git repo 同步不穩，勿把工具放工作區
> ⚠️ codex-security 執行主位置在 **C:\codex-security**（本機，已 build＋npm link 全域＋登入），工作區內只有乾淨副本

## 同步層級（本專案初始化至第 3 層級）

| 層級 | 平台 | 位置 | 讀取時機 |
|------|------|------|---------|
| L1 | 本地 | `AGENTS.md`＋`handoff.md` | 每個 session |
| L2 | GitHub | jackhu24-ship-it/ai-free（私有） | 指定時 |
| L3 | Obsidian | 260728-code/專案工作流程.md | 有需要時 |

## 工作約定
- 任何 Agent、任何電腦：**開工先讀 `handoff.md`，收工必更新 `handoff.md`**
- **開工需驗證密碼**：startup 技能會先檢查環境變數 `STARTUP_PASSWORD`，正確才輸出專案資訊；密碼本身絕不寫進任何 repo／檔案（只存環境變數，跨電腦各自設定）
- 修改共用檔案前先讀最新內容，避免覆蓋其他 Agent 的變更
- 所有回應與文件使用繁體中文
- 修改前先確認計畫，優先保留原有資料結構

## 安全與隱私（不可違反）
- **不把 API key、密碼、憑證寫進 repo**，也不要貼進 `AGENTS.md`／`handoff.md`；一律放 `.env` 並列入 `.gitignore`
- **學生資料只用座號**，不出現姓名、學號、班級以外的個資、照片或聯絡方式
- 要公開分享前，先確認檔案裡沒有上述兩類內容
- 信用卡／金融資料、PDF、簡報、試算表、影像、音樂檔、大於 2MB 的檔案**一律不上傳 GitHub**（`.gitignore`＋`pre-commit` hook 雙重防護）
