# ISO 26262-2:2018 安全計畫與安全管理規範 (Safety Management Plan)

> **文件編號**：SMP-AUTOCP-ASILD-001  
> **專案名稱**：AutoCopilot 車載多模態自主診斷與即時安全控制系統  
> **目標安全等級**：ASIL-D  
> **獨立性審查等級**：**Level I3（完全獨立第三方評估機構 TÜV SÜD / SGS / DEKRA）**  
> **發行基線**：v3.0.0-commercial-ready  

---

## 1. 專案生命週期與安全活動階段 (Safety Lifecycle)
本專案嚴格依據 ISO 26262:2018 V 型生命週期模型展開：
1. **概念階段 (Part 3)**：項目定義 (Item Definition)、危害分析與風險評估 (HARA)、功能安全概念 (FSC)。
2. **系統階段 (Part 4)**：技術安全概念 (TSC)、系統驗證與確認計畫 (V&V Plan)、HIL 臺架故障注入驗證。
3. **硬體階段 (Part 5)**：異構雙核架構、看門狗與功率級安全關斷 (Safe Torque Off)。
4. **軟體階段 (Part 6)**：分層軟體架構、MISRA C/PEP8 靜態代碼檢查、100% MC/DC 白箱覆蓋率。
5. **支援與生產運維 (Part 8 & 7)**：雙向追溯矩陣 (Traceability)、工具資格鑑定 (TCL)、長效 CI/CD 安全閘門與遙測黑盒子。

## 2. 組織架構與角色職責 (Roles & Responsibilities)
- **安全經理 (Functional Safety Manager, FSM)**：總體負責安全生命週期活動、安全文化宣導與安全檔案交付。
- **首席安全架構師 (Safety Architect)**：負責 FSC/TSC 架構設計與異構雙核獨立性 (FFI) 仲裁設計。
- **安全軟體負責人 (Safety SW Lead)**：負責 Part 6 軟體架構、100% MC/DC 覆蓋率測試與靜態零警告推進。
- **獨立安全審查官 (Independent Safety Auditor - Level I3)**：外部獨立第三方機構（TÜV SÜD / SGS / DEKRA），行使一票否決權。

## 3. 獨立性審查等級 (Independence Level I3)
依據 ISO 26262-2 Table 1 要求，針對 ASIL-D 項目必須實施 **Level I3 獨立性評估**：
- 審查官隸屬於組織外部之獨立認證機構，與被審查項目之研發人員、專案經理無行政或績效附屬關係。
- 具備獨立簽發或拒絕發放安全證書之法定權力。

## 4. 安全活動進程與甘特里程碑 (Safety Milestones)
- **M1 (概念凍結)**：HARA 與 FSC 簽核通過。
- **M2 (架構凍結)**：TSC 與異構硬體仲裁原理圖完成。
- **M3 (代碼凍結)**：100% MC/DC 綠燈、MISRA 零警告、靜態無窮迴圈/堆疊溢出分析完成。
- **M4 (臺架驗收)**：HIL 故障注入、CAN-FD E2E CRC-8 與 40ms FTTI 驗收完成。
- **M5 (正式 Assessment)**：第三方審查官現場答辯、出具 FSA 最終評估報告並簽核。
