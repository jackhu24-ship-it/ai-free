# 交接檔（handoff.md）

> 任何 Agent、任何電腦接手前**必讀**；收工時**必更新**。本檔只放交接必需的精簡資訊，詳細脈絡放 Obsidian（若有 L3）。

## ⏯️ 目前做到哪

### 一鍵安裝腳本
- **install_opencode_complete.py**（完成）：GitHub 安裝器，自動安裝 Python、Git、Ollama、MCP、技能、環境變數
- **install_oi_complete.py**（完成）：OI 安裝器，自動安裝工具包、設定檔、config、啟動器
- **update_all.py**（完成）：Python 版雲端備份腳本，解決 Windows PowerShell 編碼問題
- **update_all.bat**：一鍵備份入口（呼叫 update_all.py）
- **位置**：`G:\我的雲端硬碟\一鍵安裝回原來agent\`
- **GitHub 安裝器位置**：`https://github.com/jackhu24-ship-it/install-opencode`

### 雲端同步系統
- **sync_manager.py**（完成）：同步狀態查詢、執行同步、歷史紀錄、切換電腦
- **oi_sync_manager.py**（完成）：OI 中文包裝（同步狀態、立即同步、同步紀錄、切換電腦）
- **oi-project-manager.py** 升級（完成）：新增 `get_computer_name()`、`is_same_computer()`、`save_sync_info()`、`get_last_sync_info()` 函式
- **電腦偵測**：透過 `$env:COMPUTERNAME` 偵測目前電腦，`sync_info.json` 記錄上次同步的電腦
- **同步規則**：
  - 首次在新電腦 → 從雲端下載
  - 同一台電腦第二次 → 跳過下載，只在收工時上傳備份

### OI 自動雲端同步
- **startup 自動執行**：`update_all_from_cloud()` → 偵測電腦 → 同一台跳過 / 不同台下載
- **shutdown 自動執行**：`shutdown()` + `update_oi_tools_from_cloud()` + `update_backup()` + 記錄 `sync_info.json`

### OpenCode 收工同步
- **Step 10**：執行 `update_all.py` 備份到雲端硬碟
- **Step 11**：記錄 `sync_info.json`（電腦名稱、時間、動作）

### 全域技能（C:\Users\user\.config\opencode\skills\）
- **cloud-sync**（新增）：同步管理技能
  - `SKILL.md` — 技能定義
  - `sync_manager.py` — 核心同步邏輯
  - `oi_sync_manager.py` — OI 包裝
  - 中文指令：`同步狀態()`、`立即同步()`、`同步紀錄()`、`切換電腦()`

### 簽呈產生器（待完善）
- **sign-form**（技能已建立）：`C:\Users\user\.config\opencode\skills\sign-form\`
  - `sign_form.py` — 核心腳本（產生 Word 簽呈）
  - `oi_sign_form.py` — OI 中文包裝
  - `template.json` — 範本格式定義（4 種範本：標準/採購/人事/財務）
  - 中文指令：`建立簽呈()`、`預覽簽呈()`、`複製上次()`、`簽呈範本()`、`簽呈範本列表()`
  - ⚠️ **待做**：完整流程測試（建立→預覽→列印→複製上次）

### Ollama
- **資料夾搬遷**（完成）：`C:\Users\user\.ollama` → `C:\Users\user\ollama`，環境變數 `OLLAMA_MODELS` 已設定
- **雲端模型重新授權**（完成）：已重新登入，雲端模型正常運作
- **本地模型**：`qwen2.5:14b`（9GB）
- **免費雲端模型**：`nemotron-3-super:cloud`、`nemotron-3-ultra:cloud`、`minimax-m3:cloud`、`gpt-oss:120b-cloud`、`gpt-oss:20b-cloud`
- **付費模型（403 錯誤，不能用）**：`glm-5.2:cloud`、`kimi-k3:cloud`、`deepseek-v4-flash:cloud`、`minimax-m2.7:cloud`
- **GitHub 安全檢查**：確認安全，沒有惡意軟體

### Open Interpreter
- **版本**：0.4.3 Developer Preview，Python 3.12.10
- **OI Project Manager 工具包**（完成）：`C:\Users\user\oi-project-manager.py`，支援自然語言操作 init/startup/shutdown
- **OI Skills Manager 工具包**（完成）：`C:\Users\user\oi-skills-manager.py`，列出 14 個技能，中文指令
- **OI Model Switcher**（完成）：`C:\Users\user\oi_switcher.py`，支援 3 個模型配置檔切換
- **OI-AutoLoad 自動載入工具**（完成）：`OI-AutoLoad.bat` + `OI-AutoLoad.ps1`，用剪貼簿+SendKeys 自動貼上工具包路徑
- **MiniMax-M3 配置修正**（完成）：移除工具包指令，避免身分衝突，改為純長文件分析模式
- **OI 自動搜尋/瀏覽器**：已開啟（`import_computer_api: True`），不需要的頁面手動關閉即可

### 基金分析技能
- **fund-analyzer**（完成）：`C:\Users\user\.config\opencode\skills\fund-analyzer\`
  - `fund_analyzer.py` — 核心腳本（產生 PowerPoint 簡報，6 張投影片）
  - `oi_fund_analyzer.py` — OI 中文包裝
  - 支援台灣 ETF（0050.TW）和海外 ETF（VOO、EWZ 等）
  - 中文指令：`分析基金("0050")`、`基金走勢("0050")`、`基金統計("0050")`

### 三個模型設定檔（`C:\Users\user\oi-profiles\`）
| 檔案 | 用途 | 特殊設定 |
|------|------|----------|
| `nemotron-super.yaml` | 日常工作 | auto_run: True，載入工具包 |
| `nemotron-ultra.yaml` | 推理/寫程式 | 同上 |
| `minimax-m3.yaml` | 多模態分析 | 不載入工具包（避免衝突） |

### 中文指令系統
在 custom_instructions 裡加了中文對應：
- 開工() → 執行 startup() + 從雲端更新所有設定
- 收工() → 執行 shutdown() + 從雲端更新工具 + 自動備份
- 收工更新() → 只執行 update_backup()（不更新 handoff）
- 從雲端更新工具() → 從雲端硬碟更新 OI 工具包
- 從雲端更新所有設定() → 從雲端硬碟更新所有設定
- 建立專案() → 執行 init_project()
- 列出專案() → 執行 list_projects()
- 技能列表() → 執行 list_skills()
- 搜尋技能() → 執行 search_skills()
- 技能資訊() → 執行 skill_info()
- 指令列表() → 執行 show_guide()
- 分析基金() → 執行 分析基金()
- 基金走勢() → 執行 基金走勢()
- 基金統計() → 執行 基金統計()
- 基金列表() → 執行 基金列表()
- 建立簽呈() → 執行 建立簽呈()
- 預覽簽呈() → 執行 預覽簽呈()
- 複製上次() → 執行 複製上次()
- 簽呈範本() → 顯示簽呈格式
- 簽呈範本列表() → 列出可用範本
- 同步狀態() → 顯示同步狀態
- 立即同步() → 立即執行雲端同步
- 同步紀錄() → 顯示同步歷史
- 切換電腦() → 切換雲端同步的電腦

### 專案管理
- 測試專案全刪了（demo、fund、long-doc-analysis 等）
- 新專案 `TEST` 已建立，startup() 驗證正常
- 專案位置：`C:\Users\user\projects\TEST\`

### 安全
- 開工密碼：`5928`（環境變數 `STARTUP_PASSWORD`，不寫進任何檔案）
- API key 不進 repo：OpenRouter key 僅放 session 環境變數，收工後即消失

## 🚦 目前狀態
- **Ollama 本地模型**：qwen2.5:14b 正常運作
- **Ollama 雲端模型**：nemotron-3-super/ultra:cloud、minimax-m3:cloud 正常運作
- **OI 工作流**：`OI-AutoLoad.bat` → 選模型 → 自動載入工具 → 中文/英文指令操作
- **OI auto_run**：已開啟，但模型偶爾會多做事情（自動建立專案、自動搜尋），已用 custom_instructions 盡量控制
- **雲端同步**：startup 自動偵測電腦並下載 / shutdown 自動備份
- **Git 狀態**：工作區乾淨

## ➡️ 下一步
1. **簽呈工作流完善**（測試完整流程：建立 → 預覽 → 列印 → 複製上次）
2. **繼續測試 OI 工作流程**，確保所有設定正常運作
3. **實際運用於教學備課**
4. **整合 Antigravity**（等另一台電腦確認設定檔路徑後）

## ⚠️ 注意事項
- **OI 自動載入限制**：`custom_instructions` 只是文字指示，不會自動執行程式碼
- **MiniMax-M3 限制**：不載入工具包，避免身分衝突；僅用於長文件分析
- **Ollama 資料夾已搬遷**：`OLLAMA_MODELS=C:\Users\user\ollama\models`
- **OI 工具包位置**：`C:\Users\user\oi-project-manager.py`、`C:\Users\user\oi-skills-manager.py`，不在 git repo 中
- **開工密碼**：密碼只存環境變數，跨電腦要各自 `setx STARTUP_PASSWORD "密碼"`
- **兩個 git repo 分開管理**：工作區 ai-free 與 dotfiles 是獨立 repo
- **Wordwall 工具位置**：執行主位置 **`C:\wordwall-cli-opencode`**，勿放雲端硬碟
- **媒體與產出影片不推 GitHub**：`.gitignore` 已自動排除所有 mp4/gif/jpg
- **雲端同步**：`sync_info.json` 在雲端備份目錄，記錄上次同步的電腦名稱
- **全域技能不在 git repo**：`~/.config/opencode/skills/` 裡的技能（cloud-sync、fund-analyzer、sign-form）不會被 push 帶走

## 🕐 最後更新
- 時間：2026-08-10 00:15
- 更新者：opencode @ LAPTOP-C47IT9US
- Git push：✅ 已推
- 本次完成：一鍵安裝腳本、雲端同步系統（電腦偵測、auto startup/shutdown 同步）、簽呈技能、全域技能 cloud-sync
