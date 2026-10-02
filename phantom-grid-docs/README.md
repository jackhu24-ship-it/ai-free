# 📄 PHANTOM GRID :: 世界級標準化 PDF 工程排版系統

> **標準規範**：PG-SPEC-2026-PDF-WORLD-CLASS  
> **排版核心**：Typst 向量微排版引擎 ＋ Python Matplotlib 向量 SVG 引擎  
> **適用範圍**：技術白皮書、車載架構規範書、競賽交付件與商業路演講義  

---

## 🚀 開箱即用 (Quick Start)

### 1. VS Code 即時預覽 (推薦模式)
- 安裝 VS Code 官方擴充套件 **Tinymist Typst**。
- 開啟 `docs/main.typ`，點擊編輯器右上角「預覽」按鈕，即可享受毫秒級熱重載預覽。
- 按 `Ctrl + S` 儲存時，自動於同目錄匯出高品質 PDF！

### 2. 命令列一鍵建置
- **Windows**：雙擊或在終端機執行 `scripts\build.bat`。
- **Linux / macOS**：執行 `make all` 或 `./scripts/build.sh`。

### 3. 品質檢核驗收
執行以下命令，自動驗證六大維度標準：
```bash
python check_standards.py
```

---

## 📂 專案目錄結構

```plaintext
phantom-grid-docs/
├── .vscode/                   # VS Code 與 Tinymist 延伸模組配置
│   ├── settings.json          # 字型路徑與儲存時自動匯出 PDF 設定
│   └── tasks.json             # 一鍵編譯與自檢任務
├── templates/
│   └── phantom_theme.typ      # PHANTOM GRID 核心設計系統 (8pt Grid / A4 / tnum)
├── docs/
│   └── main.typ               # 主要編排文件入口 (訊號矩陣與圖表引用)
├── assets/
│   ├── fonts/                 # 字型檔目錄 (Inter, Noto Sans TC, JetBrains Mono)
│   └── images/                # 向量圖庫 (latency_benchmark.svg)
├── scripts/
│   ├── generate_charts.py     # PG-SPEC-2026 向量圖表生成器 (Direct Labeling)
│   ├── build.bat              # Windows 一鍵自動編譯腳本
│   └── build.sh               # Linux / macOS 自動建置腳本
├── Makefile                   # 跨平台一鍵建置目標
├── .github/workflows/
│   └── build-docs.yml         # GitHub Actions CI/CD 工作流
├── CHECKLIST_WORLD_CLASS_PDF.md # 發布前 6 大維度品質零瑕疵檢核清單
├── check_standards.py         # 依據檢核清單自動掃描之品質閘門腳本
└── README.md
```
