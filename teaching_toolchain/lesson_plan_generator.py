# -*- coding: utf-8 -*-
"""
teaching_toolchain/lesson_plan_generator.py - 車載功能安全與 CFD 數值模擬雙跨領域教案生成器
========================================================================================
自動化產出標準 4 節課進階實戰教案與期末認證題庫，直接支援教師備課與學生實驗指導。
"""
import os
from typing import Dict, Any


class LessonPlanGenerator:
    """雙領域進階課程教案與題庫自動生成模組"""

    @staticmethod
    def generate_lesson_plan(output_path: str) -> str:
        """生成車載 ASIL-D ✕ PHANTOM CFD 四週進階實戰教案"""
        content = """# 課程教案：車載功能安全 ASIL-D ✕ PHANTOM 重疊自適應網格實戰

> **授課對象**：高等工程研究生 / 資深車載軟體工程師  
> **課程總時數**：16 小時 (共 4 單元，每單元 4 小時)  
> **教學核心目標**：掌握 ISO 26262 ASIL-D 雙核熱接管、CAN-FD 密碼學防禦，以及動態重疊網格之度量張量與通量守恆。

---

## 📅 單元大綱與實作目標

### 第一單元：ISO 26262 ASIL-D 車載雙核冗餘與硬體看門狗
- **理論講授 (2 hrs)**：
  - 故障容許時間間隔 (FTTI) 與 5ms 雙核切換安全極限
  - 類比看門狗 (Analog Watchdog ADC_CR1) 與硬體中斷截斷機制
- **實驗實作 (2 hrs)**：
  - 透過 PICkit4 與 ST-Link CLI 進行韌體自動化刷寫
  - 實測模擬 Primary MCU 斷電時 Secondary MCU 於 2.5ms 內無縫熱接管

### 第二單元：CAN-FD 64-Byte 通訊協定與 ISO/SAE 21434 車載資安
- **理論講授 (2 hrs)**：
  - CAN-FD DLC 15 (64 位元組) 幀結構與 E2E Profile 4 守護架構
  - Freshness Value 防重放攻擊與 CRC32 完整性驗證
- **實驗實作 (2 hrs)**：
  - Peak-CAN / Vector 跨網段數據注入與位元翻轉防禦實驗
  - 實作 Bus-Off 故障注入與 128 次 11 隱性位元自癒狀態機

### 第三單元：PHANTOM 重疊網格度量張量與 NACA 貼體幾何
- **理論講授 (2 hrs)**：
  - 結構化幾何解耦契約 (`AbstractGrid`) 與 SOLID 設計原則
  - NACA 0012 解析方程式、保形極角投影與度量張量 $g^{ij}$
- **實驗實作 (2 hrs)**：
  - 任意閉合多邊形射線孔洞切割 (Ray-Casting Hole Cutting)
  - 驗證度量不變性守恆律 (GCL Error $< 10^{-16}$)

### 第四單元：Berger 守恆通量匹配與 Numba/GPU 極致算力
- **理論講授 (2 hrs)**：
  - 跨網格插值數值質量漂移機理與 Berger 邊界積分補償
  - CSR 稀疏矩陣 SpMV 預組裝與 JIT 多核並行優化
- **實驗實作 (2 hrs)**：
  - 150 時間步波前穿透質量守恆驗證 (漂移 $< 10^{-15}$)
  - 63k 節點 3.72x 加速比實測與 ParaView 多區塊 VTK 雲圖繪製

---

## 🎯 評核方式
- 平時上機實驗表現：40%
- 期末認證考卷診斷：30%
- 專案程式碼架構與 CI/CD 綠燈審查：30%
"""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_path

    @staticmethod
    def generate_question_bank(output_path: str) -> str:
        """生成跨領域標準認證題庫 (含詳解)"""
        content = """# 期末評量認證題庫：車載安全與數值計算 (含解析)

### 【第 1 題】(單選題，分值：20分)
依據 ISO 26262 ASIL-D 汽車功能安全規範，在雙核心冗餘微控制器 (Dual-MCU) 架構中，當主核 (Primary MCU) 發生硬體失效時，備用核接管並使系統進入安全狀態 (Safe State) 的最大容許延遲通常不得超過多少？
- (A) 50 ms
- (B) 5 ms (正確答案)
- (C) 1 秒
- (D) 100 ms
> **【解析】**：ASIL-D 等級要求極高的故障響應時間，雙核切換需在 5ms 內藉由硬體中斷與脈寬互鎖無縫完成，避免車輛轉向或制動失控。

---

### 【第 2 題】(單選題，分值：20分)
在 ISO 14229 UDS 車載診斷服務中，哪一項服務負責透過動態 Seed & Key 挑戰響應機制解鎖高等級刷寫權限？
- (A) 0x10 會話控制 (Session Control)
- (B) 0x22 讀取數據 (ReadDataByIdentifier)
- (C) 0x27 安全訪問 (SecurityAccess) (正確答案)
- (D) 0x34 請求下載 (RequestDownload)
> **【解析】**：UDS 0x27 服務負責 SecurityAccess，透過亂數 Seed 經由密碼學演算法計算回傳 Key，通過後方可進入 Bootloader 刷寫會話。

---

### 【第 3 題】(單選題，分值：20分)
相較於傳統古典 CAN 2.0 (最多 8 位元組)，CAN-FD (Flexible Data-rate) 標準之單一數據幀最大載荷 (Payload) 擴展至多少位元組？
- (A) 64 Bytes (正確答案)
- (B) 32 Bytes
- (C) 128 Bytes
- (D) 256 Bytes
> **【解析】**：CAN-FD 定義 DLC=15 時最大支援 64 Bytes 載荷，大幅提升車載感測器與遙測數據傳輸頻寬。

---

### 【第 4 題】(單選題，分值：20分)
在 PHANTOM 重疊自適應網格中，為了將物理空間任意曲面映射至計算空間，所引入的雅可比矩陣與度量張量必須滿足哪項定律，方能確保在均勻流場中無數值偽幾何源項？
- (A) 柯西-黎曼條件 (Cauchy-Riemann)
- (B) 傅立葉熱傳導定律
- (C) 納維-斯托克斯無滑移條件
- (D) 幾何度量不變性守恆律 (Geometric Conservation Law, GCL) (正確答案)
> **【解析】**：GCL 要求差分運算元計算的幾何度量在均勻場下閉合為零，PHANTOM 實測 GCL Invariant Error 達到 $10^{-17}$ 機器精度。

---

### 【第 5 題】(單選題，分值：20分)
傳統重疊網格若僅採用幾何雙線性插值，在長時間波動或流場穿透時會累積質量漂移。PHANTOM 採用何種機制將質量漂移壓制至雙精度浮點極限 ($< 10^{-15}$)？
- (A) 一階迎風格式強加耗散
- (B) Berger 跨邊界通量匹配與體積權重動態補償 (正確答案)
- (C) 人工添加非物理黏性係數
- (D) 忽略邊界交界處的波動傳遞
> **【解析】**：Berger 通量匹配計算進出邊界之數值通量差，並依據計算單元體積將殘差守恆性平滑補償回相鄰節點，達成嚴格守恆。
"""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_path
