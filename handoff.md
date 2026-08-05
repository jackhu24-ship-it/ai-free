# 交接檔（handoff.md）

> 任何 Agent、任何電腦接手前**必讀**；收工時**必更新**。本檔只放交接必需的精簡資訊，詳細脈絡放 Obsidian（若有 L3）。

## ⏯️ 目前做到哪
- **簽呈 Word 模板製作**（進行中）：從 Excel `中控議決簽呈20260330.xls` 提取格式規範，已建立 `sign-template/` 資料夾，含 3 版 Word 模板＋格式規範文件；待使用者確認版面是否符合需求。
- **codex-security 掃描工作區**（卡額度）：工具已裝＋登入＋中文路徑編碼修補，三條 provider 路線都被額度卡住：
  - **ChatGPT 帳號**：8/20 14:40 重置（需用 `--model gpt-5.6-terra`）
  - **OpenAI API key**：帳戶無餘額，需充值
  - **OpenRouter 免費 tier**：50 請求/日已用盡，**8/6 08:00（台灣）重置**
- 其餘全部完成（階段一＋階段二＋附加項）：見 AGENTS.md 路線圖

## 🚦 目前狀態
- **Obsidian MCP**：L3 已啟用，工具可用（`read_note`、`write_note`、`patch_note`、`list_directory`、`search_notes`、`get_vault_stats`）
- **codex-security 掃描**：尚未跑出任何報告（每次都在 preflight 階段被額度擋下）
- **簽呈模板**：`sign-template/` 資料夾已建立，含 3 版 Word 檔＋格式規範；待確認版面
- **編碼修補已完成**：`C:\codex-security\` 本機修補，未回推 GitHub

## ➡️ 下一步
1. **確認簽呈模板版面**：使用者確認 `sign-template/` 內 Word 檔是否符合需求，必要時微調
2. **8/6 08:00 後**（排程會提醒），用縮範圍測試指令驗證 codex-security 能產出報告：
   ```
   $env:PYTHONUTF8="1"
   $env:OPENROUTER_API_KEY="sk-or-v1-…"
   cd G:\我的雲端硬碟\260803_opencode
   codex-security scan . --provider openrouter --model "google/gemma-4-31b-it:free" --effort high --auth api-key --headless --path sheets-gas-demo
   ```
3. 縮範圍跑通後，評估 50 請求/日是否足以全掃 18 檔；不足則分次掃或考慮 OpenRouter 加 $10

## ⚠️ 注意事項
- **開工密碼**：密碼只存環境變數，跨電腦要各自 `setx STARTUP_PASSWORD "密碼"`；改 startup/shutdown 技能後需重開 opencode
- **API key 不進 repo**：OpenRouter／OpenAI key 僅放 session 環境變數，收工後即消失
- **兩個 git repo 分開管理**：工作區 ai-free 與 dotfiles 是獨立 repo，收工/開工要各自處理
- **chezmoi**：改動 `~/.config/opencode/` 後用 `chezmoi re-add` 同步 source repo，再 commit＋push dotfiles repo
- **Wordwall 工具位置**：執行主位置 **`C:\wordwall-cli-opencode`**，勿放雲端硬碟
- **pptxgenjs 負寬度坑**：`addShape('line', { w: 負值 })` 會寫出非法 XML，PowerPoint 整檔拒開
- **簡報作品\ 不推 GitHub**：PPTX/PDF 被 .gitignore＋pre-commit 排除

## 🕐 最後更新
- 時間：2026-08-05
- 更新者：opencode @ LAPTOP-C47IT9US
- Git push：待推
- 本次完成：未完成項目記錄至 Obsidian；簽呈 Word 模板製作（sign-template/ 3 版 Word 檔＋格式規範）
