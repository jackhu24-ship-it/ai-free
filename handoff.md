# 交接檔（handoff.md）

> 任何 Agent、任何電腦接手前**必讀**；收工時**必更新**。本檔只放交接必需的精簡資訊，詳細脈絡放 Obsidian（若有 L3）。

## ⏯️ 目前做到哪
#00-#10＋extras 全部完成；簡報技能集與 Wordwall CLI 已安裝上線：
- **開工密碼已啟用**：startup 技能新增 L0 密碼關卡（環境變數 `STARTUP_PASSWORD`，已設於本機 User 層級）；未設密碼的電腦會先被要求設定、密碼錯誤則停止
- **#05 GAS 已部署上線**：Web App 網址見 Obsidian 或先前記錄（專案「課堂回饋」，試算表測試資料已清空）
- **#06 Supabase 文字雲完成**：後端＋前端 wordcloud-app 已部署 `https://class-wordcloud.netlify.app`（公開）；class-demo-jackhu24 也已公開
- **Padlet 免費帳戶**：jackhu24@gmail.com（免費 3 板）；學生免帳號即可貼
- **簡報技能集已安裝**：opencode-presentation-skills 5 技能（soil-teaching-deck／pptx-teaching-deck／html-slide-deck／soil-image-deck／yaml-image-deck）裝進 `~/.config/opencode/skills/`，chezmoi 納管（dotfiles repo）
- **Wordwall CLI 已安裝＋登入**：工具在 **`C:\wordwall-cli-opencode`**（本機執行主位置，已裝環境＋已登入，`doctor --login --pdf` 全過）；skill 已裝 `~/.config/opencode/skills\wordwall`（chezmoi 納管）

## 🚦 目前狀態
- 可運行。#00-#10＋extras＋簡報技能＋Wordwall CLI 全部完成。
- **Wordwall**：`~/.wordwall/state.json` 已存登入狀態；`python wordwall.py` 系列指令可用（create／assign／results 等）
- **簡報技能**：重開 opencode 後才載入新技能；PPTX 產出需 PptxGenJS（已全域裝）
- **登入 session**：Wordwall 登入存在本機 `~/.wordwall/state.json`（grab-session 抓的），跨電腦要各自登入

## ➡️ 下一步
1. 階段三：實際運用於教學備課（Wordwall 活動、文字雲課堂使用、Padlet 板子）
2. 用 Wordwall 建第一個活動（`python wordwall.py create --content 內容.json --dry-run` → `--editor-check` → 正式建立）
3. （可選）簡報技能試做一份教材 PPTX；chezmoi 補充納管 PowerShell `$PROFILE`

## ⚠️ 注意事項
- **開工密碼**：密碼只存環境變數（不進任何 repo/檔案），跨電腦要各自 `setx STARTUP_PASSWORD "密碼"` 重設；改 startup/shutdown 技能後需重開 opencode 才生效
- **兩個 git repo 分開管理**：工作區 ai-free 與 dotfiles（`~/.local/share/chezmoi`）是獨立 repo，收工/開工要各自處理
- **chezmoi**：改動 `~/.config/opencode/` 後用 `chezmoi re-add` 同步 source repo，再 commit＋push dotfiles repo
- **Wordwall 工具位置**：執行主位置 **`C:\wordwall-cli-opencode`**（已裝 Python 3.12＋Playwright＋Chromium＋PDF 元件）。雲端硬碟對 git repo 同步不穩（本次 clone 曾被 Google Drive 檔案串流回滾），勿把工具放雲端硬碟。工作區「安裝資料\」副本已 gitignore 排除
- **grab-session 的坑**：Chrome 運作中會刪除 DevToolsActivePort 檔，grab-session 直接跑會報「找不到有效 DevToolsActivePort」；改用 `python wordwall.py grab-session --cdp-url http://127.0.0.1:9333`（先確認 9333 在監聽）
- **登入流程**：`python wordwall.py chrome-login`（專用 Chrome 埠 9333）→ 本人登入 → `grab-session`；不可代填帳密
- **簡報技能依賴**：Python 3.12.10（winget 已裝）＋ PyYAML/Pillow/python-pptx ＋ npm pptxgenjs/playwright（全域）
- **draw skill 未裝**：圖片式簡報（soil-image-deck/yaml-image-deck）與 Level 3 生圖需要 `draw` skill，本機目前沒有
- **setup.ps1 有 bug**：PowerShell 5.1 執行 setup.ps1 第 42 行 inline Python 會 parser 錯誤；改用 `python -m pip install -r requirements.txt`＋`python -m playwright install chromium` 手動安裝
- GAS 操作技巧、Supabase 金鑰位置、Netlify 點數等見先前注意事項（AGENTS.md 與 Obsidian 有完整版）

## 🕐 最後更新
- 時間：2026-08-05
- 更新者：opencode @ LAPTOP-C47IT9US
- Git push：待推
- 本次完成：簡報技能集安裝（5 技能＋依賴備齊）；Wordwall CLI 安裝＋登入（工具在 C:\wordwall-cli-opencode，skill 納管 dotfiles）；Python 3.12.10 補裝取代 Store stub
