# 交接檔（handoff.md）

> 任何 Agent、任何電腦接手前**必讀**；收工時**必更新**。本檔只放交接必需的精簡資訊，詳細脈絡放 Obsidian（若有 L3）。

## ⏯️ 目前做到哪
- **全新全域技能建立與驗證**（完成）：建立並測試全域技能 `web-study-manual-builder`，統一定義獨立雲端資料夾 `G:\我的雲端硬碟\學習手冊和安裝部件好地方\<主題或網址名稱>\`，並成功實測產出 A3 橫向+新細明體 10pt 圖文並茂《全域與專案技能全攻略》學習手冊 (DOCX/PDF/MD/圖表)。
- **簽呈 Word 模板精準重製**（完成）：依據 `中控規格確認簽呈20260708.xls` 精準重製為 A4 直向標準格式 Word (`.docx`) 與 PDF 範本，已同步至 `sign-template/` 與 `G:\我的雲端硬碟\簽呈表單\`。
- **Obsidian MCP (L3) 通訊驗證**（完成）：雙向讀寫與統計工具驗證成功，`專案工作流程.md` 追加紀錄完成。
- **codex-security CLI 本機安裝**（完成）：於 `LAPTOP-BSBDEJ2Q` 完成 `C:\codex-security` 環境建置與全域 `npm link`（版本 0.1.6）。
- **codex-security 掃描工作區**（卡額度）：工具已裝＋登入＋中文路徑編碼修補，三條 provider 路線都被額度卡住：
  - **ChatGPT 帳號**：8/20 14:40 重置（需用 `--model gpt-5.6-terra`）
  - **OpenAI API key**：帳戶無餘額，需充值
  - **OpenRouter 免費 tier**：50 請求/日已用盡，**8/6 08:00（台灣）重置**
- 其餘全部完成（階段一＋階段二＋附加項）：見 AGENTS.md 路線圖

## 🚦 目前狀態
- **全域技能 `web-study-manual-builder`**：已設定於 `C:\Users\jackh\.gemini\config\skills\`，支援口述觸發、唯一獨立資料夾與 A3 講義匯出。
- **Obsidian MCP**：L3 已啟用，工具可用（`read_note`、`write_note`、`patch_note`、`list_directory`、`search_notes`、`get_vault_stats`），運作良好。
- **簽呈模板**：`sign-template/中控規格確認簽呈_標準格式.docx` 已建置，並副本至 `G:\我的雲端硬碟\簽呈表單\`。
- **codex-security CLI**：`LAPTOP-BSBDEJ2Q` 全域指令已啟用。

## ➡️ 下一步
1. **使用 `web-study-manual-builder` 技能**：未來提供任何網址或主題，說出「生成手冊」、「查閱」或「學習」即可產出獨立資料夾學習手冊。
2. **8/6 08:00 後**（排程會提醒），用縮範圍測試指令驗證 codex-security 能產出報告：
   ```
   $env:PYTHONUTF8="1"
   $env:OPENROUTER_API_KEY="sk-or-v1-…"
   cd G:\我的雲端硬碟\260803_opencode
   codex-security scan . --provider openrouter --model "google/gemma-4-31b-it:free" --effort high --auth api-key --headless --path sheets-gas-demo
   ```

## ⚠️ 注意事項
- **開工密碼**：密碼只存環境變數，跨電腦要各自 `setx STARTUP_PASSWORD "密碼"`；改 startup/shutdown 技能後需重開 opencode
- **API key 不進 repo**：OpenRouter／OpenAI key 僅放 session 環境變數，收工後即消失
- **兩個 git repo 分開管理**：工作區 ai-free 與 dotfiles 是獨立 repo，收工/開工要各自處理
- **Wordwall 工具位置**：執行主位置 **`C:\wordwall-cli-opencode`**，勿放雲端硬碟
- **簡報作品\ 不推 GitHub**：PPTX/PDF 被 .gitignore＋pre-commit 排除

## 🕐 最後更新
- 時間：2026-08-05
- 更新者：opencode @ LAPTOP-BSBDEJ2Q
- Git push：✅ 已推
- 本次完成：建置全域技能 `web-study-manual-builder` 並實測成功；Obsidian MCP (L3) 通訊測試成功；codex-security CLI 安裝；精準重製 A4 簽呈 Word/PDF 模板。


