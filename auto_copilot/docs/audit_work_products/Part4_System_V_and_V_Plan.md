# ISO 26262-4:2018 系統驗證與確認計畫 (System V&V Plan)

> **文件編號**：VVP-AUTOCP-ASILD-007  
> **測試範圍**：HIL 故障注入臺架、實車 Shadow Mode 路測、E2E CRC-8 與 FTTI 邊界  

---

## 1. 系統驗收測試矩陣 (System Verification Matrix)

| 測試編號 | 測試項目 | 注入故障類型 | 驗收合格準則 | 實測結果 | 判定 |
|:---:|:---|:---|:---|:---:|:---:|
| **TC-HIL-01** | 報文延遲與抖動 | 注入 25ms ~ 360ms 隨機延遲 | 延遲 > 350ms 時觸發 SLA 警告並保證無總線死鎖 | Jitter 0.56ms, 無死鎖 | **PASS** |
| **TC-HIL-02** | CRC 位元翻轉 | 連續反轉報文第 0 Byte 資料位元 | 1 幀檢出報警，連續 3 幀切入 Safe State | 100% 檢出 | **PASS** |
| **TC-HIL-03** | 看門狗逾時 | 阻斷 200ms 心跳脈衝 | 200ms 內強制跳轉 FAIL_SAFE | 精確於 200ms 觸發 | **PASS** |
| **TC-HIL-04** | 暗模式 Zero-TX | 全載模擬發送 5,000 幀 | 物理總線發送幀數嚴格為 0 | 發送量 $= 0$ 幀 | **PASS** |
| **TC-HIL-05** | 雙軌推論偏差檢驗 | 注入水溫 108°C 且駕駛未減速 | 100ms 內檢出 Discrepancy 並標記 CRITICAL | 100% 捕獲記錄 | **PASS** |
| **TC-SEC-01** | E2E 故障抑制時間 | 連續 3 幀惡意 CRC 損壞 | 抑制時間 $\le 20.0	ext{ ms}$ | **$4.78	ext{ ms}$** | **PASS** |
| **TC-FTTI-01** | 扭矩突變安全關斷 | 注入 $+300	ext{ Nm}$ 扭矩脈衝 | 關斷時間 $\le 40.0	ext{ ms}$ | **$5.46	ext{ ms}$** | **PASS** |
