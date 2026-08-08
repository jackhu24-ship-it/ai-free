# 交接檔（handoff.md）

> 任何 Agent、任何電腦接手前**必讀**；收工時**必更新**。本檔只放交接必需的精簡資訊，詳細脈絡放 Obsidian（若有 L3）。

## ⏯️ 目前做到哪
- **Ollama 資料夾搬遷**（完成）：從 `C:\Users\user\.ollama` 搬到 `C:\Users\user\ollama`，環境變數 `OLLAMA_MODELS` 已設定
- **OI Project Manager 工具包**（完成）：`C:\Users\user\oi-project-manager.py`，支援自然語言操作 init/startup/shutdown
- **Ollama 雲端模型重新授權**（完成）：已重新登入，雲端模型正常運作

## 🚦 目前狀態
- **Ollama 本地模型**：qwen2.5:14b 正常運作
- **Ollama 雲端模型**：nemotron-3-super:cloud 正常運作
- **OI Project Manager**：工具包已建立並載入成功
- **Git 狀態**：工作區乾淨

## ➡️ 下一步
1. **在 OI 中測試工具包**：啟動 OI，執行 `exec(open(r'C:\Users\user\oi-project-manager.py').read())`
2. **用自然語言測試**：說「幫我建立一個專案叫做 hello」
3. **開始實際專案**：用工具包管理教學備課專案

## ⚠️ 注意事項
- **Ollama 資料夾已搬遷**：`OLLAMA_MODELS=C:\Users\user\ollama\models`，新開 PowerShell 需確認環境變數
- **OI 工具包位置**：`C:\Users\user\oi-project-manager.py`，不在 git repo 中
- **雲端模型授權連結**：`https://ollama.com/connect?name=LAPTOP-C47IT9US&key=c3NoLWVkMjU1MTkg...`（已過期需重新產生）
- **開工密碼**：密碼只存環境變數，跨電腦要各自 `setx STARTUP_PASSWORD "密碼"`
- **API key 不進 repo**：OpenRouter key 僅放 session 環境變數，收工後即消失
- **兩個 git repo 分開管理**：工作區 ai-free 與 dotfiles 是獨立 repo
- **Wordwall 工具位置**：執行主位置 **`C:\wordwall-cli-opencode`**，勿放雲端硬碟
- **媒體與產出影片不推 GitHub**：`.gitignore` 已自動排除所有 mp4/gif/jpg

## 🕐 最後更新
- 時間：2026-08-07 17:30
- 更新者：opencode @ LAPTOP-C47IT9US
- Git push：待推
- 本次完成：雲端模型授權完成、工具包載入測試成功
