# 車載實體 CAN 總線通訊品質與電氣診斷分析指南
> 本指南詳細記述 `can_health_inspector.py` 的工具設計核心、底層電氣推斷原理與現場實體台架排錯標準作業程序（SOP）。

---

## 一、 工具設計核心與無示波器檢測原理

在實車維修現場、工廠調試或邊緣台架測試時，工程師往往無法隨身攜帶高頻示波器。本工具利用底層 CAN 控制器的**硬體錯誤計數器（TEC/REC）**、**錯誤訊框（Error Frame）比率**與**高頻週期性封包的時間抖動（Jitter）**，透過數學統計模型**反推實體層與電氣特性的健康度**。

```text
[實體層物理異常] (無示波器狀態)
      │
      ├──► 缺 120Ω 終端電阻 ──► 高頻信號邊緣反射 ──► CRC / ACK 錯誤 ──► 錯誤訊框暴增 ──► BUS-OFF
      ├──► 阻抗過低 (< 45Ω)  ──► 總線負載過重 ──────► 顯性差分電壓不足 ──► 節點無法採樣識別
      └──► 線束極性反接      ──► 差分電平倒置 ──────► 總線長期靜默 ──────► 0 接收幀
```

---

## 二、 終端電阻與電氣異常推斷矩陣 (Physical Layer Inference Matrix)

| 異常特徵現象 | 軟體監測特徵 | 物理層實體故障成因 | 現場檢修處置 SOP |
| :--- | :--- | :--- | :--- |
| **總線完全靜默 (No Traffic)** | `total_rx_count == 0` | 1. CAN_H 與 CAN_L 線路反接<br>2. 節點未供電或收發器待機<br>3. 波特率不匹配（如 250k 與 500k） | 1. 測量 CAN_H / CAN_L 對地電壓（正常待機隱性電平均為 2.5V 左右）。<br>2. 檢查整車電源繼電器與收發器供電 5V。<br>3. 切換波特率掃描（125k, 250k, 500k, 1M）。 |
| **高頻錯誤幀 (Error Frames)** | `error_frame_count > 10%`<br>`bus_state == ERROR-PASSIVE` | **缺少 120Ω 終端電阻**<br>信號傳播到開路端引發反射波，衝擊後續比特位，破壞 CRC 校驗。 | **斷電量測**：關閉整車電源，使用三用電表測量 CAN_H 與 CAN_L 間阻抗。<br>• 正常值：**60Ω 左右**（兩端各 120Ω 並聯）。<br>• 若測得 **120Ω**：代表有一端終端電阻斷開或未接。<br>• 若測得 **開路 (OL)**：代表兩端皆無終端電阻。 |
| **阻抗過低 (< 45Ω)** | 連續嚴重丟包<br>迅速跳入 `BUS-OFF` | **總線並聯過多終端電阻**（如 > 3 個 120Ω）或線路短路，造成差分驅動電流超載。 | 檢查並移除多餘的加裝節點內部內置電阻，維持全網僅首尾兩端各 120Ω。 |
| **偶發零星錯誤幀** | 錯誤訊框 < 2%<br>`bus_state == ERROR-ACTIVE` | 電磁干擾（EMI）、高壓逆變器諧波噪訊或接地迴路電位差。 | 檢查雙絞線絞距（標準每米 33~50 絞）、屏蔽層單端接地狀態。 |
| **通訊良好 (Healthy)** | 錯誤幀 0 幀<br>抖動 Jitter < 2.0 ms | 終端阻抗為 60Ω 匹配，電壓差分顯性 2.0V 良好。 | 系統正常，具備進入 ISO 26262 ASIL 功能安全與 UDS 診斷之條件。 |

---

## 三、 抖動（Jitter）與丟包率量測模型

針對週期性廣播封包（例如 Frame ID `0x120` 動力散熱遙測，預設週期 $T_{expected} = 50.0\text{ ms}$ / 20Hz）：

1. **時間差分數列**：
   $$\Delta t_i = t_{i+1} - t_i \quad (i = 1, 2, \dots, N-1)$$
2. **時間抖動 (Jitter)**：
   $$\text{Jitter} = \max(\Delta t) - \min(\Delta t)$$
   *車載標準：Jitter 應壓制在 2.0 ms 以內，超過 5.0 ms 代表匯流排負載率過高或高優先級 ID 搶占頻繁。*
3. **理論丟包率 (Packet Loss Rate)**：
   $$N_{expected} = \left\lfloor \frac{t_{last} - t_{first}}{T_{expected}} \right\rfloor$$
   $$\text{Loss Rate} = \max\left(0, \frac{N_{expected} - N_{actual}}{N_{expected}}\right) \times 100\%$$

---

## 四、 雙平臺實體硬體相容指令集

### 1. Linux / 工控機（SocketCAN 環境）
針對 Ubuntu / Debian / Jetson 工控機，直接與內核 CAN 模組交互：
```bash
# 監控 can0，取樣 5 秒，監控 0x120 遙測幀
python auto_copilot/can_health_inspector.py \
  --interface socketcan \
  --channel can0 \
  --bitrate 500000 \
  --duration 5.0 \
  --expected-id 0x120 \
  --expected-period 50.0
```

### 2. Windows（PCAN-Basic / PEAK-System 環境）
針對安裝 PCAN-USB 介面卡的 Windows 筆電或工程電腦：
```powershell
# 監控 PEAK PCAN-USB 通道 1，取樣 5 秒
python auto_copilot/can_health_inspector.py `
  --interface pcan `
  --channel PCAN_USBBUS1 `
  --bitrate 500000 `
  --duration 5.0
```

### 3. 單機離線自檢（流量模擬驗收）
無實體硬體接線時，一鍵啟動內建 20Hz 流量模擬驗證演算法：
```bash
python auto_copilot/can_health_inspector.py --simulate-traffic --duration 3.0
```

---

## 五、 標準輸出報告範例解讀

```text
============================================================
           CAN 總線通訊品質與電氣診斷分析報告           
============================================================
介面型態: socketcan | 通道: can0 | 波特率: 500000 bps
總線硬體狀態: ERROR-ACTIVE
總接收幀數: 100 幀
錯誤幀數量 (Error Frames): 0

[目標幀 0x120 傳輸品質分析]
  - 接收幀數: 100 幀 (估計應收: 100 幀)
  - 平均週期: 50.08 ms (預期: 50.00 ms)
  - 最大週期: 51.12 ms | 最小週期: 49.30 ms
  - 時間抖動 (Jitter): 1.82 ms
  - 估計丟包率 (Packet Loss Rate): 0.00%

[電氣與終端電阻評估 (Inference)]
  ✅ 通訊良好：無錯誤幀，CRC/ACK 檢驗正常。終端阻抗與電氣特性符合規範。
============================================================
```

> 🎯 **結語**：本套排錯工具已完全收錄於 AutoCopilot 車載工具箱，作為 Stage 3 HIL 與實車連線前**必執行的電氣與通訊體檢首道防線**。
