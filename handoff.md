# 交接檔（handoff.md）

> 任何 Agent、任何電腦接手前**必讀**；收工時**必更新**。本檔只放交接必需的精簡資訊，詳細脈絡放 Obsidian（若有 L3）。

## ⏯️ 目前做到哪
- **Ollama 資料夾搬遷**（完成）：從 `C:\Users\user\.ollama` 搬到 `C:\Users\user\ollama`，環境變數 `OLLAMA_MODELS` 已設定
- **OI Project Manager 工具包**（完成）：`C:\Users\user\oi-project-manager.py`，支援自然語言操作 init/startup/shutdown
- **Ollama 雲端模型重新授權**（完成）：已重新登入，雲端模型正常運作
- **OI Model Switcher**（完成）：`C:\Users\user\oi_switcher.py`，支援 3 個模型配置檔切換
- **OI 工作區選單**（完成）：`C:\Users\user\Desktop\OI-Menu.bat`，一鍵選模型 + 啟動 OI
- **MiniMax-M3 配置修正**（完成）：移除工具包指令，避免身分衝突，改為純長文件分析模式

## 🚦 目前狀態
- **Ollama 本地模型**：qwen2.5:14b 正常運作
- **Ollama 雲端模型**：nemotron-3-super/ultra:cloud、minimax-m3:cloud 正常運作
- **OI 工作流**：選模型 → 啟動 OI → 載入工具（1-2）或直接工作（3）
- **Git 狀態**：工作區乾淨

## ➡️ 下一步
1. **使用 OI 進行教學備課**：實際運用於課堂準備
2. **繼續開發專案**：使用 OI 工具包管理專案流程
3. **優化工作流**：根據實際使用情況調整模型配置

## ⚠️ 注意事項
- **OI 自動載入限制**：`custom_instructions` 只是文字指示，不會自動執行程式碼
- **MiniMax-M3 限制**：不載入工具包，避免身分衝突；僅用於長文件分析
- **Ollama 資料夾已搬遷**：`OLLAMA_MODELS=C:\Users\user\ollama\models`
- **OI 工具包位置**：`C:\Users\user\oi-project-manager.py`，不在 git repo 中
- **開工密碼**：密碼只存環境變數，跨電腦要各自 `setx STARTUP_PASSWORD "密碼"`
- **API key 不進 repo**：OpenRouter key 僅放 session 環境變數，收工後即消失
- **兩個 git repo 分開管理**：工作區 ai-free 與 dotfiles 是獨立 repo
- **Wordwall 工具位置**：執行主位置 **`C:\wordwall-cli-opencode`**，勿放雲端硬碟
- **媒體與產出影片不推 GitHub**：`.gitignore` 已自動排除所有 mp4/gif/jpg

## 🕐 最後更新
- 時間：2026-08-08 18:30
- 更新者：opencode @ LAPTOP-C47IT9US
- Git push：✅ 已推（無新變動）
- 本次完成：OI 狀態檢查、OI-Menu 啟動測試
