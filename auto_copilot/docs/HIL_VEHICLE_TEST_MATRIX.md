# AutoCopilot ISO 26262 HIL 實車測試用例矩陣 ✕ 整車暗模式規格書
**Document ID**: `AC-HIL-SPEC-20260912-V1`  
**Standard Compliance**: ISO 26262:2018 (Part 4: Product Development at System Level, Part 6: Software Integration & Testing)  
**Target ASIL**: ASIL-D (Fail-operational / Fail-safe Architecture)  
**Release Tag**: `v2.1.0-hil-shadow-mode`  
**Sign-off**: 👑 小幫手 (Agent_PM) & 🛠️ 小開 (Agent_Coder) 奉 霸丸總指揮官 統帥令發布  

---

## 1. 宗旨與架構概述 (Purpose & Architecture)

本規格書為 AutoCopilot 車載語音診斷 Copilot 建立實車在環測試（Hardware-in-the-Loop, HIL）與整車暗模式運算（Shadow Mode）標準工程指南。  
旨在透過**主動故障注入**與**非侵入式雙軌影子推論**，在實車上線前嚴格驗證 FTTI（故障容忍時間間隔）、SLA 響應延遲與系統安全降級策略，並持續沉澱 GSN（Goal Structuring Notation）所需的**動態實證（Dynamic Evidence）**。

---

## 2. HIL 實車測試用例矩陣 (HIL Vehicle Test Matrix)

| 測試編號 | 測試用例名稱 | 注入維度與方法 | 車規門檻 / SLA 邊界 | 預期安全策略 | GSN 追溯 | 驗收狀態 |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **TC-HIL-01** | 報文階梯延遲與抖動注入 | CAN 報文延遲 25ms ~ 360ms，抖動 5%~10% | $\text{Latency} \le 350\text{ms}$ (SLA)<br>超時觸發降級警告 | $\le 350\text{ms}$: NORMAL<br>$> 350\text{ms}$: FAIL_OPERATIONAL | **G4 / S4 / Sn5** | 🟢 **PASS** |
| **TC-HIL-02** | CRC 位元翻轉與訊框毀損 | 隨機翻轉 payload 1~2 位元，引發校驗錯誤 | 100% 檢出錯誤訊框，觸發控制器重傳 | 檢出錯誤: FAIL_OPERATIONAL | **G4 / S4 / Sn5** | 🟢 **PASS** |
| **TC-HIL-03** | 看門狗心跳中斷安全關斷 | 中斷 0x080 心跳幀 220ms (門檻 200ms) | $t \ge 200\text{ms}$ (FTTI 超時) 剛性切入安全態 | 超時中斷: FAIL_SAFE | **G3 / S3 / Sn4** | 🟢 **PASS** |
| **TC-HIL-04** | 暗模式 Zero-TX 廣播防禦 | 攔截內部致動節點下發之 0x210 訊號 | 實車總線發送量嚴格為 **0** (零侵入) | 阻擋發送，保持安全隔離 | **G2 / S2 / Sn1** | 🟢 **PASS** |
| **TC-HIL-05** | 實車雙軌推論與偏差比對 | 注入水溫 94°C 與 108°C，駕駛維持全載 | 水溫 > 105°C 且無減載時，觸發 Discrepancy | 標記 CRITICAL 偏差，寫入動態實證 | **G1 / C1 / Sn6** | 🟢 **PASS** |

---

## 3. 整車暗模式運算機制 (Shadow Mode Principles)

### 3.1 零侵入聽證閘門 (Zero-TX Barrier)
在實車初期測試階段，系統僅透過 CAN / CAN-FD 之 **Listen-Only** 模式旁路掛載於整車網路：
- **物理層**：禁止 ACK 顯性拉低與訊框發送（若硬體支援 Listen-Only 則啟用）。
- **驅動層**：`VehicleShadowModeEngine` 內部實作 `guarded_send` 阻絕閘門，任何內部調用 `send()` 均被強制攔截並累計 `tx_blocked_count`，保證不會對實車動力、轉向與制動網路造成任何反向干擾。

### 3.2 雙軌影子推論與偏差比對 (Dual-Track Discrepancy Analyzer)
- **真實世界軌道 (Track 1)**：即時捕捉駕駛員操作（油門開度、檔位、繼電器狀態）與實車 ECU 廣播報文。
- **影子大腦軌道 (Track 2)**：AutoCopilot 內部狀態機並行運行，基於 ISO 26262 規則庫推論當前環境的最佳安全狀態（如 `DEGRADED_WARN`）。
- **偏差判定矩陣 (Discrepancy Formula)**：
  $$\text{Discrepancy} = \mathbb{I}\left( T_{\text{coolant}} > 105.0^{\circ}\text{C} \land \text{Action}_{\text{driver}} = \text{NORMAL\_DRIVING} \right)$$
  當條件成立時，系統判定駕駛員未察覺熱失控早期徵兆，立即標記 `CRITICAL` 風險等級並觸發實證沉澱。

### 3.3 GSN 動態實證記錄格式 (Dynamic Evidence Schema)
沉澱於 `auto_copilot/shadow_dynamic_evidence.jsonl`：
```json
{
  "record_id": "EV-1789217950824-14",
  "timestamp": 1789217950.824,
  "telemetry": {
    "coolant_temp_c": 108.0,
    "bus_voltage_v": 384.5,
    "motor_rpm": 3000
  },
  "predicted_state": "SystemOperatingState.DEGRADED_WARN",
  "recommended_action": "SUGGEST_DERATING_OR_SAFE_STOP",
  "actual_driver_action": "NORMAL_DRIVING",
  "discrepancy_detected": true,
  "risk_level": "CRITICAL",
  "tx_blocked_count": 0,
  "notes": "Discrepancy: Engine coolant 108.0°C exceeds 105°C, but driver made no thermal derating action."
}
```

---

## 4. 降級策略與 FTTI 邊界定義 (Degradation & FTTI)

1. **Fail-Operational（操作降級）**：
   - 觸發條件：報文單次校驗失敗 (CRC)、偶發抖動延遲 > 350ms。
   - 系統行為：狀態機維持運行，啟動語音降級提示，限制非關鍵診斷請求頻率。
2. **Fail-Safe（安全關斷）**：
   - 觸發條件：看門狗心跳遺失逾 200ms、實體 CAN 斷線 (Bus-Off)、危險致動指令等待口語確認逾 10.0 秒。
   - 系統行為：剛性進入 `EMERGENCY_SAFE`，廣播緊急關斷命令（Shadow Mode 下僅記錄並在日誌輸出），確保車載功能安全。

---

## 5. 實體交付清單與驗證指針

- 測試腳本：[`auto_copilot/test_hil_vehicle_matrix.py`](file:///C:/Users/user/.gemini/antigravity/worktrees/260803_opencode/begin_development/auto_copilot/test_hil_vehicle_matrix.py) (5/5 綠燈)
- 注入引擎：[`auto_copilot/hil_vehicle_matrix.py`](file:///C:/Users/user/.gemini/antigravity/worktrees/260803_opencode/begin_development/auto_copilot/hil_vehicle_matrix.py)
- 暗模式引擎：[`auto_copilot/vehicle_shadow_mode.py`](file:///C:/Users/user/.gemini/antigravity/worktrees/260803_opencode/begin_development/auto_copilot/vehicle_shadow_mode.py)
- 動態實證庫：[`auto_copilot/shadow_dynamic_evidence.jsonl`](file:///C:/Users/user/.gemini/antigravity/worktrees/260803_opencode/begin_development/auto_copilot/shadow_dynamic_evidence.jsonl)
