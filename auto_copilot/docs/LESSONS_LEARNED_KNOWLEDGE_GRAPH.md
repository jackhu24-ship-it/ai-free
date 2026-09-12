# 車規級失效案例知識圖譜與經驗庫 (Lessons Learned Knowledge Graph)

> **編譯時間**：2026-09-12T21:20:26  
> **收錄案例**：4 類核心車規失效模式  
> **價值**：組織級安全資產沉澱，反哺下一代全地形無人車與具身智駕研發。  

---

### [FAIL-CRC-001] 高壓逆變器 IGBT 開關引發之 CAN-FD 總線位元翻轉 (Bit-Flip)
- **根本原因類別**：`ROOT_ELECTRICAL_NOISE`
- **失效現象**：連續 2~3 幀 CRC-8 校驗失敗，Alive Counter 丟失
- **深層根因 (Root Cause)**：雙絞線遮蔽層接地阻抗不良，高頻 PWM 電磁脈衝耦合至通訊線束
- **固化防禦對策 (Countermeasure)**：AUTOSAR E2E Profile 1 演算法三級抑制 + 產線 60Ω 終端阻抗校驗
- **實證支撐**：TC-SEC-01 (4.78ms 抑制) & EOL Step 3

### [FAIL-TIM-002] Linux/RTOS 多任務調度引發之看門狗逾時抖動 (Timing Jitter)
- **根本原因類別**：`ROOT_TIMING_JITTER`
- **失效現象**：週期性遙測心跳間隔由 50ms 突增至 210ms，觸發安全降級
- **深層根因 (Root Cause)**：日誌記錄未採用非同步 I/O，阻塞主調度任務時間片
- **固化防禦對策 (Countermeasure)**：遷移至硬體計時器 (Windowed Watchdog) + 微秒級中斷服務常式 (MCAL ISR)
- **實證支撐**：TC-HIL-03 (200ms 剛性關斷)

### [FAIL-THM-003] 長爬坡重載工況冷卻水溫突破 105°C 熱失控邊界
- **根本原因類別**：`ROOT_THERMAL_DRIFT`
- **失效現象**：電機溫度達到 108°C，駕駛員持續深踩油門
- **深層根因 (Root Cause)**：散熱風扇繼電器作動延遲，單純依賴儀表警示不足以防範熱衰竭
- **固化防禦對策 (Countermeasure)**：雙軌影子模式檢出 Discrepancy ➔ 100ms 內強制作動限扭 (DEGRADED_WARN)
- **實證支撐**：TC-HIL-05 (動態實證沉澱)

### [FAIL-AI-004] 端到端神經網絡輸出超越物理極限之急暴衝指令
- **根本原因類別**：`ROOT_AI_HALLUCINATION`
- **失效現象**：AI 模組在障礙物逼近時突然輸出 +5.8 m/s^2 加速度請求
- **深層根因 (Root Cause)**：視覺盲區與神經網絡分佈外數據 (OOD) 引發權重激活值異常
- **固化防禦對策 (Countermeasure)**：部署 ASIL-D Safe AI Cage 護欄，3.2 微秒內強制限幅於安全動態包絡線
- **實證支撐**：SafeAICageSupervisor.arbitrate_ai_command

