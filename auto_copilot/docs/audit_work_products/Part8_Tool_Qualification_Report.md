# ISO 26262-8:2018 軟體工具資格認證報告 (Tool Qualification Report)

> **文件編號**：TQR-AUTOCP-ASILD-011  
> **適用標準**：ISO 26262-8:2018 Clause 11 (Confidence in the Use of Software Tools)  

---

## 1. 軟體工具分類與評估準則 (Tool Classification)
依據工具對軟體產生缺陷的可能性（Tool Impact, TI）與工具缺陷被檢出的可能性（Tool Error Detection, TD），判定工具置信度等級（Tool Confidence Level, TCL）：
- **TI1**：工具失效不可能在安全相關系統中引入或遺漏錯誤。
- **TI2**：工具失效可能引入或遺漏錯誤。
- **TD1**：具有高度信心能檢出錯誤。
- **TD2 / TD3**：中度/低度信心能檢出錯誤。

## 2. 工具清單與 TCL 定級評估表

| 工具名稱 (Tool Name) | 用途描述 (Usage) | TI 等級 | TD 等級 | TCL 定級 | 資格鑑定方法 (Qualification Method) | 認證結論 |
|:---|:---|:---:|:---:|:---:|:---|:---:|
| **Python 3.12 執行環境** | 安全狀態機與診斷腳本執行 | TI2 | TD1 | **TCL2** | 廣泛使用的成熟執行環境 (Use of validated tool) + 自動化測試用例驗收 | **QUALIFIED** |
| **python-can 驅動庫** | CAN / CAN-FD 物理與虛擬匯流排通訊 | TI2 | TD1 | **TCL2** | 搭配 Vector / PCAN 硬體回環測試 (Loopback) 與 100% 斷言驗證 | **QUALIFIED** |
| **pytest 測試框架** | 單元測試與 100% MC/DC 覆蓋率驗證 | TI2 | TD1 | **TCL2** | 交叉比對標準測試輸出與獨立覆蓋率報告 | **QUALIFIED** |
| **Flake8 / Bandit** | 靜態代碼檢查與資安掃描 | TI1 | TD1 | **TCL1** | 直接採用，無需額外鑑定 (TCL1 exempt) | **QUALIFIED** |
| **Vector CANoe / VN16xx** | 實車/臺架微秒級時間戳與總線分析 | TI2 | TD1 | **TCL2** | Vector 官方 ISO 26262 ASIL-D 資格認證證書 (Vendor Qualification) | **QUALIFIED** |
