# ISO 26262-6:2018 軟體架構設計規範 (Software Architecture Design)

> **文件編號**：SWAD-AUTOCP-ASILD-008  
> **符合標準**：ISO 26262-6:2018 Clause 7  

---

## 1. 軟體分層與防禦性架構 (Layered Architecture)
- **Layer 1: 應用與推論層 (Application Layer - QM)**：語音特徵提取、自然語言大模型、LangGraph 多代理人協同。
- **Layer 2: 安全監督層 (Safety Supervisor Layer - ASIL-D)**：決定性狀態機、雙重口語確認握手、FTTI 計時器。
- **Layer 3: 抽象與通信層 (CAN/CAN-FD Adapter Layer - ASIL-D)**：DBC 物理編解碼、AUTOSAR E2E Profile 1 CRC-8、UDS 封包器。
- **Layer 4: 驅動與硬體抽象層 (HAL Layer - ASIL-D)**：Zero-TX 聽證閘門、硬體微秒級時間戳、Blackbox FIFO 環形緩衝區。

## 2. 關鍵車規軟體設計準則 (Design Guidelines)
1. **禁止運行時動態記憶體分配 (No Dynamic Memory Allocation)**：
   - 嚴格禁止在安全關鍵控制迴路中使用 `malloc()` / `free()`。
   - 所有緩衝區（如 200ms Blackbox）採用編譯期靜態分配或固定長度環形陣列。
2. **無死循環與有界執行時間 (Bounded Execution Time)**：
   - 所有迴圈必須具備剛性上限（如 `for i in range(MAX_RETRIES)`），禁止 `while True:` 無退出超時之設計。
3. **防禦性默認切入 Safe State (Fail-Safe Default)**：
   - 狀態機所有未定義狀態、未知列舉值或例外異常（Exception），預設 handler 一律引導跳轉至 `EMERGENCY_SAFE`。
