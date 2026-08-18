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
- [x] 階段二附加：codex-security 掃描與安全加固（修復 Windows 中文編碼相容性，以 gpt-5.6-terra 完成 sheets-gas-demo 深度掃描，並實作 CWE-1236 試算表公式注入防護）
- [x] 階段二附加：簽呈 Word/PDF 模板製作（A4 直向標準格式已重製完成，同步 G:\我的雲端硬碟\簽呈表單\）
- [x] 階段二附加：全域技能 web-study-manual-builder 與 auto-approve-command-guide 建立與 chezmoi 同步
- [x] 階段二附加：opencode-draw-free 部件歸檔與本機安裝比對
- [x] 階段二附加：《極光下的父愛》1 分鐘繪本短片音畫同步與風吹草動 GIF 實作
- [x] 階段二附加：Ollama 資料夾搬遷與模型支援（環境變數 OLLAMA_MODELS 設定）
- [x] 階段二附加：OI Project Manager 與 Skills Manager 工具包建置（支援自然語言與中文指令）
- [x] 階段二附加：OI Model Switcher 與 AutoLoad 自動載入工具（支援配置檔切換）
- [x] 階段二附加：基金分析技能（fund-analyzer，四張圖表+統計，支援台股/海外 ETF）
- [x] 階段二附加：簽呈 Word/PDF 模板製作（sign-form 技能，5 指令，4 範本）
- [x] 階段二附加：一鍵安裝腳本（install_opencode_complete.py、install_oi_complete.py）
- [x] 階段二附加：雲端備份同步系統與跨電腦偵測（sync_info.json、auto startup/shutdown 同步）
- [x] 階段二附加：全系統儲存優化與快取搬移至 E 槽（個人庫/下載/TEMP/AI快取全重定向，釋放 18.44 GB，C 槽 21.96 GB）
- [x] 階段二附加：Ollama 0.32.14 啟動與 qwen2.5:7b 本地模型建置（E 槽膠合點儲存，模型 4.7 GB 離線驗證通過）
- [x] 階段二附加：三師爸工具庫 112 項目同步備份至學習手冊和安裝部件好地方
- [x] 階段二附加：Ollama 本地執行操作手冊撰寫歸檔（ollama-operation-manual.md）
- [x] 階段二附加：OI 實戰操作與專案管理驗證（OI-AutoLoad 自動化日常工作流）
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
├── generated\                 ← AI 生成內容與短片素材（含 lion_story 等）
├── ollama-operation-manual.md ← Ollama 本地模型操作手冊
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

## Windows 開發與代碼安全最佳實踐（Agent 學習記憶）
1. **Python Subprocess UTF-8 編碼防護**：在 Windows 繁體/簡體中文語系下執行 Python 子行程呼叫 Git 或讀取檔案時，一律加上 `encoding="utf-8", errors="replace"`（或設定環境變數 `PYTHONUTF8=1`），防止 `UnicodeDecodeError (GBK/CP950)` 崩潰。
2. **Codex Security 授權模型配置**：使用 ChatGPT 訂閱帳戶執行 `codex-security scan` 時，一律指定支援的深度推論模型 `--model gpt-5.6-terra`。
3. **Google Sheets 公式注入防護 (CWE-1236)**：任何 GAS 寫入 Google 試算表之使用者輸入欄位，必須先經過 `sanitizeCell_()` 過濾（若開頭為 `=`, `+`, `-`, `@` 則前置加上單引號 `'` 強制轉純文字）。

