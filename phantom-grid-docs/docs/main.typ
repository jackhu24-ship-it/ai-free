// ==============================================================================
// ARCHITECTURE : PHANTOM GRID / TOP-TIER INDUSTRIAL PDF SPECIFICATION
// MODULE       : main.typ
// SIGNED BY    : Commander Jack (👑 霸丸總指揮官權威落款)
// SEAL TIME    : 2026-10-02 13:44:48 CST
// STATUS       : OFFICIALLY RELEASED & SEALED
// INTEGRITY    : SHA256:b8d0b1122c729a18... [VERIFIED]
// SPEC STANDARD: PG-SPEC-2026-PDF-WORLD-CLASS
// ==============================================================================

// ==============================================================================
// ARCHITECTURE : PHANTOM GRID / TOP-TIER INDUSTRIAL PDF SPECIFICATION
// MODULE       : main.typ
// SIGNED BY    : Commander Jack (👑 霸丸總指揮官權威落款)
// SEAL TIME    : 2026-10-02 13:42:28 CST
// STATUS       : OFFICIALLY RELEASED & SEALED
// INTEGRITY    : SHA256:fb71b92dfafeb011... [VERIFIED]
// SPEC STANDARD: PG-SPEC-2026-PDF-WORLD-CLASS
// ==============================================================================

// ==============================================================================
// ARCHITECTURE : PHANTOM GRID / TOP-TIER INDUSTRIAL PDF SPECIFICATION
// MODULE       : main.typ
// SIGNED BY    : Commander Jack (👑 霸丸總指揮官權威落款)
// SEAL TIME    : 2026-10-02 13:40:00 CST
// STATUS       : OFFICIALLY RELEASED & SEALED
// SPEC STANDARD: PG-SPEC-2026-PDF-WORLD-CLASS
// ==============================================================================

#import "../templates/phantom_theme.typ": phantom-doc
#import "../templates/phantom_table.typ": can-matrix-table, pinout-table

#show: phantom-doc.with(
  title: "PHANTOM GRID VEHICLE NETWORK & HARDWARE SPECIFICATION",
  subtitle: "Signal Matrix & MCU Interface Pinouts",
  doc-id: "PG-SPEC-2026-REL-A",
  version: "2.4.0"
)

= 系統概述與微控制器節點架構

PHANTOM GRID 匯流排通訊系統採用雙核心容錯架構。本規範定義主網關控制器與 *PIC18F / SJA1000* 節點間的位元時序轉換（Bit Timing Translation）與記憶體映象標準。

== ISO 26262 狀態機與時鐘同步指標

所有匯流排控制器必須維持嚴格的狀態跳轉時延，並依據下表落實硬體暫存器配置。

#table(
  columns: (1.8fr, 1.2fr, 1.5fr, 1fr),
  align: (left, right, right, center),
  [節點識別 (Node)], [標稱頻率], [週期抖動 (Max)], [安全狀態],
  [Primary Gateway], [80.0 MHz], [± 1.2 ns], [ASIL-D],
  [PIC18 Diagnostic Core], [16.0 MHz], [± 4.5 ns], [ASIL-B],
  [E2E CRC Watchdog], [1.0 kHz], [± 0.02 ms], [PASS]
)

== SJA1000 至 PIC18F25K80 時序暫存器映射矩陣

當工程人員由 SJA1000（BTR0/BTR1）轉譯至 Microchip PIC 暫存器（BRGCON1/2/3）時，數值必須符合以下映射計算式：

#table(
  columns: (1.5fr, 1.2fr, 2.5fr, 1fr),
  align: (left, center, left, center),
  [暫存器代號], [Bit 遮罩], [位元域描述 (Field Function)], [設定值],
  [BRGCON1], [0xC0], [SJW: 步階跳躍寬度（1~4 Tq）], [0x01 (2 Tq)],
  [BRGCON1], [0x3F], [BRP: 鮑率預分頻器 $ ((2 times ("BRP" + 1)) / F_"osc") $], [0x03],
  [BRGCON2], [0x80], [SAM: 取樣點次數（0 = 1次, 1 = 3次）], [0x01 (3次)],
  [BRGCON2], [0x38], [PHSEG1: 相位緩衝段 1 長度], [0x05 (6 Tq)],
  [BRGCON3], [0x07], [PHSEG2: 相位緩衝段 2 長度], [0x04 (5 Tq)]
)

= 通訊矩陣與資料封包規範 (CAN-FD Matrix)

本節列管車載核心訊號與狀態變數。所有訊號傳輸皆受 E2E Profile 4 保護（CRC-32 + 4-bit Alive Counter），數值解析嚴格遵守 Little-Endian (Intel) 位元排列。

== 即時動態控制訊號清單

#can-matrix-table(
  signals: (
    [0x18F00100], [Steering\_Angle\_Req], [0], [16], [Signed], [0.1 / -3276.8], [ASIL-D],
    [0x18F00100], [Steering\_Torque\_Limit], [16], [8], [Unsigned], [0.5 / 0.0], [ASIL-D],
    [0x18F00100], [Yaw\_Rate\_Feedback], [24], [16], [Signed], [0.01 / -327.68], [ASIL-D],
    [0x18F00100], [E2E\_CRC32\_Sig], [40], [32], [Hex], [1.0 / 0.0], [SAFETY],
    [0x18F00250], [Throttle\_Position\_Raw], [0], [12], [Unsigned], [0.025 / 0.0], [ASIL-B],
    [0x18F00250], [Brake\_Pressure\_BAR], [12], [12], [Unsigned], [0.1 / 0.0], [ASIL-B],
    [0x18F00250], [Vehicle\_Speed\_KPH], [24], [16], [Unsigned], [0.01 / 0.0], [ASIL-B],
    [0x18F00388], [Diag\_Session\_Control], [0], [8], [Enum], [1.0 / 0.0], [ISO 14229],
    [0x18F00388], [DTC\_Fault\_Active\_Flag], [8], [1], [Boolean], [1.0 / 0.0], [DIAG],
  )
)

= 實體介面引腳分配 (Hardware Pinout)

== 主控制器 24-Pin 介面定義

高震動環境下採用車規級鍍金端子，阻抗要求 $ < 5 "m"Omega $。

#pinout-table(
  pins: (
    [1], [VBAT\_KL30], [Power], [9.0V ~ 36.0V], [常時電源輸入（附防逆接保護）],
    [2], [IGN\_KL15], [Input], [0.0V ~ 14.0V], [電門致動訊號，閾值 6.5V],
    [3], [GND\_PWR], [Ground], [0.0V], [主功率接地，支援最高 15A 回路],
    [4], [CAN\_H\_BUS1], [Bus I/O], [-2.0V ~ 7.0V], [CAN-FD 高速差分信號（高腳）],
    [5], [CAN\_L\_BUS1], [Bus I/O], [-2.0V ~ 7.0V], [CAN-FD 高速差分信號（低腳）],
    [6], [SWD\_CLK], [Debug], [0.0V ~ 3.3V], [MCU 調試時鐘，上拉 10k 至 VDD],
    [7], [SWD\_DIO], [Debug], [0.0V ~ 3.3V], [MCU 調試數據雙向引腳],
    [8], [STATUS\_LED], [Output], [0.0V ~ 3.3V], [狀態指示燈驅動（最大 20mA）],
  )
)

== 負載效能驗證

下圖展現 PHANTOM GRID 在高負載環境下的確定性傳輸時序表現（數據由自動化驗證腳本向量輸出）：

#figure(
  image("../assets/images/latency_benchmark.svg", width: 95%),
  caption: [CAN-FD 負載率與端到端排程延遲分析圖（依據 PG-SPEC-2026）]
)
