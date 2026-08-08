# 交接檔（handoff.md）

> 任何 Agent、任何電腦接手前**必讀**；收工時**必更新**。本檔只放交接必需的精簡資訊，詳細脈絡放 Obsidian（若有 L3）。

## ⏯️ 目前做到哪
- **Ollama 資料夾搬遷**（完成）：從 `C:\Users\user\.ollama` 搬到 `C:\Users\user\ollama`，環境變數 `OLLAMA_MODELS` 已設定
- **OI Project Manager 工具包**（完成）：`C:\Users\user\oi-project-manager.py`，支援自然語言操作 init/startup/shutdown
- **Ollama 雲端模型重新授權**（完成）：已重新登入，雲端模型正常運作
- **OI 自動載入工具包**（部分完成）：已設定 `custom_instructions`，但 OI 不會自動執行程式碼，需手動載入

## 🚦 目前狀態
- **Ollama 本地模型**：qwen2.5:14b 正常運作
- **Ollama 雲端模型**：nemotron-3-super:cloud 正常運作
- **OI Project Manager**：工具包已建立，需手動載入
- **Git 狀態**：工作區乾淨

## ➡️ 下一步
1. **手動載入工具包**：每次開 OI 時貼上 `exec(open(r'C:\Users\user\oi-project-manager.py').read())`
2. **測試完整流程**：專案初始化 → 開工 → 收工
3. **考慮替代方案**：將工具包程式碼直接嵌入 OI 設定檔，或建立 OI 插件

## ⚠️ 注意事項
- **OI 自動載入限制**：`custom_instructions` 只是文字指示，不會自動執行程式碼
- **Ollama 資料夾已搬遷**：`OLLAMA_MODELS=C:\Users\user\ollama\models`，新開 PowerShell 需確認環境變數
- **OI 工具包位置**：`C:\Users\user\oi-project-manager.py`，不在 git repo 中
- **開工密碼**：密碼只存環境變數，跨電腦要各自 `setx STARTUP_PASSWORD "密碼"`
- **API key 不進 repo**：OpenRouter key 僅放 session 環境變數，收工後即消失
- **兩個 git repo 分開管理**：工作區 ai-free 與 dotfiles 是獨立 repo
- **Wordwall 工具位置**：執行主位置 **`C:\wordwall-cli-opencode`**，勿放雲端硬碟
- **媒體與產出影片不推 GitHub**：`.gitignore` 已自動排除所有 mp4/gif/jpg

## 🕐 最後更新
- 時間：2026-08-08 10:35
- 更新者：opencode @ LAPTOP-C47IT9US
- Git push：✅ 已推（21858e2）
- 本次完成：確認雲端授權、測試工具包自動載入（發現限制）
