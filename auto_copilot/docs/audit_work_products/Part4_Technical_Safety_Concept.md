# ISO 26262-4:2018 技術安全概念規範 (Technical Safety Concept - TSC)

> **文件編號**：TSC-AUTOCP-ASILD-006  
> **系統架構**：異構非對稱雙核冗餘 (Asymmetric Dual-Core Diversity)  

---

## 1. 異構硬體仲裁架構與技術安全需求 (TSR)

```mermaid
graph TD
    subgraph Host MCU (Main Core - QM/ASIL-B)
        Voice["Speech Recognition & LLM"]
        AppFSM["Application Logic & Flow"]
        OutCmd["Actuation Signal Output"]
    end

    subgraph Safety MCU (Co-Processor - ASIL-D)
        CRCVerify["E2E CRC-8 / Alive Counter Check"]
        EnvelopeCheck["Torque & Temperature Safe Envelope"]
        Watchdog["Windowed Hardware Watchdog"]
    end

    subgraph Hardware Interlock & Arbitration (Physical Layer)
        HWGate["硬體 AND 閘門 / 類比互鎖開關 (Interlock)"]
        Inverter["逆變器三相電橋 PWM 驅動"]
        BusTransceiver["CAN-FD 收發器 (Listen-Only Gate)"]
    end

    OutCmd --> HWGate
    CRCVerify -->|Enable / Disable| HWGate
    EnvelopeCheck -->|Trip Signal| HWGate
    Watchdog -->|Reset / Safe State| HWGate
    HWGate --> Inverter
    HWGate --> BusTransceiver
```

- **TSR-01 (狀態機硬體互鎖)**：主核發出致動指令時，安全核必須同步校驗語音確認 Token 與時間戳，否則硬體閘門維持下拉。
- **TSR-02 (AUTOSAR E2E Profile 1 演算法)**：
  - 多項式：$C(x) = x^8 + x^4 + x^3 + x^2 + 1$ (`0x1D`)
  - 初始值：`0xFF`，異或值：`0xFF`
  - 滾動計數器：$0 \sim 15$ 步進循環。連續 3 幀錯誤抑制響應時間實測 **$4.78	ext{ ms}$**。
- **TSR-03 (硬體關斷迴路 FTTI 保證)**：
  - 功率級電橋驅動信號由硬體 AND Gate 物理控制，斷電延遲 $\le 5.46	ext{ ms} \ll 40	ext{ ms}$。
- **TSR-04 (電源突降防護)**：
  - 具備板載儲能電容與低壓檢測（BOD），在整車跌電時仍保證安全核持續運算至少 $50	ext{ ms}$ 完成安全停機。
