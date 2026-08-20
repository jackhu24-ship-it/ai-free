# 交接檔（handoff.md）

> 任何 Agent、任何電腦接手前**必讀**；收工時**必更新**。本檔只放交接必需的精簡資訊，詳細脈絡放 Obsidian（若有 L3）。

## ⏯️ 目前做到哪

### 系統與儲存空間優化
- **全系統儲存優化與快取重定向**（完成）：個人檔案庫、下載區、TEMP/TMP、AI 快取（HF/Pip/npm/Playwright）全數導向 780 GB 的 E 槽，C 槽（SSD）安全釋放 18.44 GB，可用空間維持在 21.96 GB。

### 本地 AI 與大模型建置
- **Ollama 本地開源模型建置**（完成）：Ollama 0.32.14 服務啟動並設置 E 槽模型膠合點，繁中推薦模型 `qwen2.5:7b` 下載與離線測試通過；已撰寫 `ollama-operation-manual.md` 操作手冊。
- **Ollama 資料夾與模型支援**（完成）：支援本地模型 `qwen2.5:7b`、`qwen2.5:14b`、`qwen2.5:3b` 與雲端模型。
- **Hermes Agent & Desktop 桌面版建置**（完成）：Nous Research `hermes-agent` v0.20.4 與 `Hermes Desktop`（Electron GUI，214 MB）編譯安裝完成；升級全域 npm 至 v12.0.2 滿足相容需求；已在桌面與開始功能表建立 `Hermes.lnk` 捷徑，並同步 82 個原生技能庫。
- **Hermes 輕量化加速與教學手冊**（完成）：配置 `qwen2.5:3b` 輕量模型提升 CPU 推理速度；精簡核心工具集減重 70%；修復 `does not support thinking` 報錯（將 `reasoning_effort` 設為 `none`）；撰寫左側選單完整教學手冊 `HERMES.md`，已同步放置於工作區與桌面。

### 一鍵安裝與雲端同步系統
- **一鍵安裝腳本**（完成）：`install_opencode_complete.py`、`install_oi_complete.py`、`update_all.py` 位於 `G:\我的雲端硬碟\一鍵安裝回原來agent\`。
- **雲端同步系統**（完成）：`sync_manager.py`、`oi_sync_manager.py`，支援電腦偵測（`sync_info.json`）與 auto startup/shutdown 同步；修復 `update_all.py` 之 Windows CP950 編碼相容性（`errors="replace"`）與檔案佔用防護。
- **全域技能**：`cloud-sync`、`fund-analyzer`、`sign-form`、`auto-approve-command-guide`、`web-study-manual-builder`。

### 代碼安全與漏洞防護
- **Codex Security 掃描與 CWE-1236 公式注入防護**（完成）：修復 Windows Python 子行程 UTF-8 編碼問題，以 `gpt-5.6-terra` 完成 `sheets-gas-demo` 全量安全分析；在 `Code.gs` 中實作 `sanitizeCell_` 防禦公式注入並提交 Git。

### OI（Open Interpreter）環境與啟動器
- **OI 執行環境與 AutoLoad 升級**（完成）：使用 `uv` 構建 Python 3.12 獨立環境，修復 `pkg_resources` (setuptools) 依賴，升級 `OI-AutoLoad.ps1` 具備全自動動態路徑解析，並同步至雲端備份庫。
- **OI 實戰操作與專案管理**（完成）：完成 `OI-AutoLoad.bat` 實戰操作與日常專案管理輔助驗證。
- **OI 全技能工具化與 AutoLoad 旗艦升級**（完成）：將 23+ 個核心技能完整封裝為旗艦工具庫 `oi_complete_skills.py`（支援中英文雙語呼叫，如 `建立簽呈()`、`分析基金()`、`語音轉字幕()`、`免費生圖()` 等）；升級 `oi-auto-load.py` 具備啟動自動載入與提示詞注入，並全量同步至雲端備份庫。

## 🚦 目前狀態
- **系統空間**：C 槽（SSD）空間充足，所有大容量下載與快取自動落入 E 槽。
- **本地與雲端 AI**：Ollama + `qwen2.5:7b` / `qwen2.5:3b` 就緒；Open Interpreter 0.4.3 + `oi_complete_skills` 旗艦工具庫就緒；Hermes Agent v0.20.4 + Hermes Desktop 就緒。
- **雲端同步**：`update_all.py` 全量九項備份完成，`sync_info.json` 維持最新。
- **Git 狀態**：乾淨無待提交檔案。

## ➡️ 下一步
1. **Hermes Desktop 實戰與進階教學**：帶領進行實戰案例演練（Python 程式生成、檔案批次整理、定時排程自動化等）。
2. **AutoCAD MCP 串接**：在繪圖工作機上執行 `master_setup.ps1` 啟用 31 個 AutoCAD 輔助工具。
3. **教學工具與專案開發**：運用 Ollama 本地模型（`qwen2.5:7b` / `qwen2.5:3b`）或 OpenCode / OI 技能庫輔助備課與教學應用。
4. **簽呈工作流完善**：測試完整流程（建立 → 預覽 → 列印 → 複製上次）。

## ⚠️ 注意事項
- **開工密碼**：密碼只存環境變數，跨電腦要各自 `setx STARTUP_PASSWORD "密碼"`
- **API key 不進 repo**：OpenRouter / OpenAI key 僅放 session 環境變數
- **Wordwall 工具位置**：執行主位置 `C:\wordwall-cli-opencode`
- **媒體與產出影片不推 GitHub**：`.gitignore` 已自動排除所有 mp4/gif/jpg

## 🕐 最後更新
- 時間：2026-08-21 03:33
- 更新者：小幫手 @ LAPTOP-C47IT9US
- Git push：✅ 乾淨無變更
- 本次完成：將全套 23+ 項技能封裝為 Open Interpreter 旗艦工具庫 `oi_complete_skills.py`，支援中英文雙語呼叫與單元測試驗證通過。
- 本次完成：修復 `oi-auto-load.py` 啟動器字串語法問題，完成 IPython 核心全自動預載入（`00-oi-tools.py`）。
- 本次完成：優化 7 大模型 Profile 提示詞結構，解決模型代碼塊執行問題。
- 本次完成：執行 `update_all.py` 全量九項備份與雲端同步完成。
