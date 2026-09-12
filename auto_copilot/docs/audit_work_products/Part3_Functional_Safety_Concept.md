# ISO 26262-3:2018 功能安全概念規範 (Functional Safety Concept - FSC)

> **文件編號**：FSC-AUTOCP-ASILD-005  
> **適用等級**：ASIL-D / ASIL-B  

---

## 1. 安全目標導出之功能安全需求 (Functional Safety Requirements - FSR)

- **FSR-01 (對應 SG-01, ASIL-D)**：
  - 系統必須實作口語雙重確認（Double-Confirmation）握手協議。
  - 任何危害致動指令進入系統後，必須強制滯留於 `WAITING_CONFIRMATION` 態，且啟動 $10.0	ext{ s}$ 即時硬計時器。若超時未收到肯定答覆，自動撤回並切入安全態。
- **FSR-02 (對應 SG-02, ASIL-D)**：
  - 系統必須具備動態匯流排錯誤抑制機制。連續 3 幀 CRC-8 翻轉或滾動計數跳變時，必須在 $	ext{FTTI} \le 40	ext{ ms}$ 內強制關斷功率電橋（Safe Torque Off）。
- **FSR-03 (對應 SG-03, ASIL-B)**：
  - 系統必須實時監測整車熱力學安全包絡線。水溫 $>105^\circ	ext{C}$ 時於 $100	ext{ ms}$ 內切入 `DEGRADED_WARN` 並發出語音預警。
- **FSR-04 (對應 SG-04, ASIL-B)**：
  - 高危 UDS 常規服務執行器必須由狀態機實施互鎖，且具備 $15	ext{ ms} \sim 40	ext{ ms}$ 之工規實體回覆逾時保護。
- **FSR-05 (對應 SG-05, ASIL-D)**：
  - 實車測試模式必須啟用 Listen-Only 實體驅動隔離，保證 Zero-TX 物理發送幀數 $= 0$。
- **FSR-06 (對應 SG-06, ASIL-D)**：
  - 系統必須配備 200ms Pre-Trigger 高頻環形緩衝區，在狀態機躍遷至異常態時瞬態凍結並保全。

## 2. 安全狀態（Safe State）與轉移矩陣
- **NORMAL_RUN**：系統正常待命與常規遙測，致動器硬體閘門常閉。
- **WAITING_CONFIRMATION**：口語交握中，執行器維持當前安全負載，嚴禁執行新致動。
- **DEGRADED_WARN**：限扭運行、關閉高壓附屬設備、發出駕駛警示。
- **EMERGENCY_SAFE**：硬體仲裁器物理拉低驅動信號（Safe Torque Off），廣播 0x210 安全報文。
