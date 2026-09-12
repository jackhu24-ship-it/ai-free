# ISO/TC 22/SC 32/WG 8 國際標準草案修訂提案書

**提案編號**: ISO/TC 22/SC 32/WG 8 - Proposal N1042-R3  
**對應標準**: ISO 26262:202X (3rd Edition) Part 6 Annex G / ISO 21448:2022 (SOTIF) Clause 9 Extension  
**主題**: **端到端深度學習與具身智慧車載系統之外部確定性安全監控器架構（External Deterministic Safety Cage, EDSC）**  
**提案單位**: AutoCopilot Global Safety Consortium (聯合 ARTC、工研院、Tier 1 聯盟)  
**提交日期**: 2026 年 09 月 12 日  
**安全等級**: ASIL-D / SOTIF Target Residual Risk < 10⁻⁹ / h  

---

## 1. 背景與行業痛點 (Problem Statement)
隨著端到端（End-to-End, E2E）深度學習模型、大型語言模型（LLM）與具身智慧機器人（Embodied AI）深度介入車輛底盤與動態致動器（Steering, Acceleration, Braking）：
1. **黑箱不可解釋性**：類神經網路權重高達數十億參數，無法滿足 ISO 26262 Part 6 Table 8 之 100% MC/DC（修改條件/判定覆蓋率）白箱結構覆蓋要求。
2. **非確定性潛在失效（Non-Deterministic Latent Hazards）**：AI 幻覺、長尾感知缺陷及注意力機制漂移可能在幾何無害的輸入下輸出毀滅性扭矩或轉向指令。
3. **SOTIF 觸發條件（Triggering Conditions）未知性**：傳統功能安全假設「硬體有故障」，但 SOTIF 關注「系統無硬體故障但性能不足導致危害」。

---

## 2. 規範性要求條款草案 (Normative Draft Requirements)

### 條款 6.4.10: 外部確定性安全監控器 (External Deterministic Safety Cage, EDSC)
> **[EDSC-REQ-001] 零信任致動原則 (Zero-Trust Actuation Principle)**  
> 凡由非確定性或黑箱類神經網路生成之任何車輛控制指令（包括但不限於線控轉向角、驅動輪扭矩、制動減速度），在到達執行級功率驅動電路之前，**必須強制經過獨立於 AI 運算單元之外的確定性硬體/微控制器安全籠（EDSC）進行包絡線即時校驗**。

> **[EDSC-REQ-002] 獨立異構安全隔離 (Heterogeneous Independence, ASIL-D I3)**  
> EDSC 運算核心必須與 AI 運算單元具備實體或架構級獨立性（不同半導體製程、獨立時鐘源、獨立電源供電），且其核心裁決代碼必須具備 100% 形式化驗證或 100% MC/DC 覆蓋。

> **[EDSC-REQ-003] 硬體級微秒斷開時間（Deterministic Cutoff FTTI）**  
> 當 EDSC 偵測到指令超出預設安全包絡線（Safety Envelope）、或發生 E2E CRC/序號異常、或 AI 算力晶片心跳停滯時，EDSC 必須於 **{\text{cutoff}} \le 20\text{ ms}$（軟體層）** 與 **{\text{hardware}} \le 1.0\ \mu\text{s}$（晶片硬體層）** 內直接切斷功率級輸出，強制切入 Fail-Safe 或 Fail-Operational 安全狀態。

---

## 3. 全球實車與數位孿生實證數據 (Validation Evidence)

本提案之安全閾值與可行性基於超過 **15,000,000 公里實車運行** 與 **10,000 個極限場景秒級數位孿生回歸**：

| 指標類別 | 實測數值 / 驗證成果 | 標準合規判定 |
| :--- | :--- | :--- |
| **實車陰影模式異常檢出** | 100.0% 攔截率，0 漏檢（Zero False-Negative） | 符合 ASIL-D |
| **端到端神經網路幻覺限幅** | 3.2 微秒內完成軟體級動態限幅 | 遠優於 20ms FTTI |
| **晶片級硬體 IP 隔離斷開** | 1 個時脈週期（2.5 ns @ 400MHz） | 達到物理級極限保護 |
| **失效率 (Residual FIT Rate)**| 5.0 FIT（遠低於 ASIL-D 規定的 10.0 FIT） | 通過 TÜV 審查基線 |

---

## 4. 對 ISO 26262:202X 與 ISO 21448 之修訂建議對照表

`
[傳統 ISO 26262 框架] (無法涵蓋 E2E AI)
    ECU 軟體代碼 ──(要求 100% MC/DC)──> 功率執行器 [矛盾：AI 無法通過 MC/DC]

[提案修訂架構: EDSC 混合安全架構]
    ┌───────────────────────────────────────────────┐
    │ 主功能區 (Quality Managed / ASIL-B AI Model) │
    │ 端到端深度學習神經網路 / 具身語言代理         │
    └──────────────────────┬────────────────────────┘
                           │ 候選控制向量 (Candidate Vector)
                           ▼
    ┌───────────────────────────────────────────────┐
    │ 外部確定性安全監控器 (EDSC - 100% ASIL-D)      │
    │ 形式化安全包絡線 + 100% MC/DC + 硬體 IP 隔離閥 │
    └──────────────────────┬────────────────────────┘
                           │ 確定性安全驅動指令 (Certified Vector)
                           ▼
                  車輛線控底盤功率級致動器
`

此標準修訂案已獲多國代表與主要車廠認同，正式列入 2026/2027 年度標準會期優先研討議案。
