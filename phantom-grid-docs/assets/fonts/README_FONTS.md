# 🔤 PHANTOM GRID :: 字型依賴與目錄結構 (Assets / Fonts)

本目錄存放 PHANTOM GRID 核心工程字型檔案：
- **英數/符號**：`Inter`、`Roboto`、`SF Pro`
- **繁體中文**：`Noto Sans TC`（思源黑體）、`PingFang TC`（蘋方）
- **代碼/矩陣/等寬**：`JetBrains Mono`、`Roboto Mono`

Tinymist Typst 編譯器與 VS Code 外掛會自動讀取本目錄字型（透過 `--font-path ./assets/fonts`），並內嵌至輸出之向量 PDF 中。
若本機系統已安裝對應字型，Typst 亦會直接自系統字庫調用渲染。
