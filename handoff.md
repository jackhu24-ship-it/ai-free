# 交接檔（handoff.md）

> 任何 Agent、任何電腦接手前**必讀**；收工時**必更新**。本檔只放交接必需的精簡資訊，詳細脈絡放 Obsidian（若有 L3）。

## ⏯️ 目前做到哪
- **codex-security 掃描工作區**（進行中，卡額度）：工具已裝＋登入＋中文路徑編碼修補，但三條 provider 路線都被額度卡住：
  - **ChatGPT 帳號**：Codex 使用上限（`gpt-5.6-sol` 不吃 ChatGPT 帳號，須 `--model gpt-5.6-terra`），**8/20 14:40 重置**
  - **OpenAI API key**（sk-proj-…，僅設於 session env，未寫檔）：帳戶**無餘額**，需 platform.openai.com 充值
  - **OpenRouter 免費 tier**（sk-or-v1-…，同上）：`free-models-per-day` 每日 50 請求已用盡，**8/6 08:00（台灣）重置**；已建 Windows 排程提醒 `CodexSecurityResetReminder`（8/6 08:00 彈窗）
- 其餘全部完成（階段一＋階段二＋附加項）：見 AGENTS.md 路線圖

## 🚦 目前狀態
- 可運行，但 codex-security 掃描**尚未跑出任何報告**（每次都在 preflight 階段被額度擋下）。
- **編碼修補已完成**：`C:\codex-security\sdk\typescript\_bundled_plugin\scripts\workbench_target.py`（git_command 加 `encoding="utf-8"`）與 `generate_rank_input.py`。全域 `codex-security` 指令讀得到修補結果。**這些修補只在本機 C:\ 安裝，未回推 GitHub**。
- **登入憑證**：`C:\Users\user\.codex\state\plugins\codex-security\codex-home\auth.json`（僅本機）。
- 掃描 partial output 殘留在 `C:\Users\user\.codex\state\plugins\codex-security\scans\260803_opencode\`（皆空/無效，可忽略）。

## ➡️ 下一步
1. **8/6 08:00 後**（排程會提醒），用縮範圍測試指令驗證掃描能產出報告：
   ```
   $env:PYTHONUTF8="1"
   $env:OPENROUTER_API_KEY="sk-or-v1-…"   ← 從本次對話或使用者取得
   cd G:\我的雲端硬碟\260803_opencode
   codex-security scan . --provider openrouter --model "google/gemma-4-31b-it:free" --effort high --auth api-key --headless --path sheets-gas-demo
   ```
2. 縮範圍跑通後，評估 50 請求/日是否足以全掃 18 檔；不足則分次掃或考慮 OpenRouter 加 $10（解鎖 1000 請求/日，`:free` 模型不扣餘額）。
3. （遠程）ChatGPT 帳號 8/20 重置後也可用 `--auth chatgpt --model gpt-5.6-terra` 免 key 掃描。

## ⚠️ 注意事項
- **開工密碼**：密碼只存環境變數，跨電腦要各自 `setx STARTUP_PASSWORD "密碼"`；改 startup/shutdown 技能後需重開 opencode
- **API key 不進 repo**：OpenRouter／OpenAI key 僅放 session 環境變數，收工後即消失；下次要用需重新設定（不可寫進 AGENTS.md/handoff.md/repo）
- **`ai-agent-ep03` 資料夾已消失**：AGENTS.md 原本有記錄，本次確認不在工作區（可能雲端硬碟同步遺漏），如需可從 GitHub ai-free repo 或 Git 歷史找回
- **兩個 git repo 分開管理**：工作區 ai-free 與 dotfiles 是獨立 repo，收工/開工要各自處理
- **chezmoi**：改動 `~/.config/opencode/` 後用 `chezmoi re-add` 同步 source repo，再 commit＋push dotfiles repo
- **Wordwall 工具位置**：執行主位置 **`C:\wordwall-cli-opencode`**。雲端硬碟對 git repo 同步不穩，勿把工具放雲端硬碟
- **pptxgenjs 負寬度坑（重要）**：`addShape('line', { w: 負值 })` 會寫出 `<a:ext cx="-NNN">` 非法 XML，PowerPoint 整檔拒開。線寬度恆為正；懷疑損壞時 dump slide XML 搜 `<a:ext cx="-`
- **PPTX 轉 PDF**：本機用 PowerPoint COM 轉（`Presentation.SaveAs(..., 32)`）；COM 開檔失敗通常是 pptx 內有非法 XML
- **簡報作品\ 不推 GitHub**：PPTX/PDF 被 .gitignore＋pre-commit 排除（安全規則）

## 🕐 最後更新
- 時間：2026-08-05
- 更新者：opencode @ LAPTOP-C47IT9US
- Git push：待推
- 本次完成：codex-security 安裝＋登入＋中文路徑編碼修補（C:\codex-security，npm link 全域）；三條 provider 路線測試（ChatGPT/OpenAI API/OpenRouter 全卡額度）；OpenRouter 免費 50 請求/日 8/6 08:00 重置＋Windows 排程提醒；縮範圍策略定案（sheets-gas-demo）
