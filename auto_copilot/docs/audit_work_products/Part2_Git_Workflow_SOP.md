# ISO 26262-2:2018 配置與變更管理規範 (Git Workflow & Baseline Tagging SOP)

> **文件編號**：CFG-AUTOCP-GIT-002  
> **適用標準**：ISO 26262-8 Clause 7 (Configuration Management) & Clause 8 (Change Management)  
> **基線標籤**：`v3.0.0-commercial-ready`  

---

## 1. Git 分支管理策略 (Branching Model)
為達成 ASIL-D 嚴苛的追溯性與可重現性要求，本專案實施三層分支策略：
1. **main (Production Baseline)**：僅存放通過第三方審查之正式量產發行版本，受分支保護禁止直接 Push。
2. **begin_development (Integration Baseline)**：每日整合主幹，需通過 GitHub Actions ASIL-D Safety Gate 22 項測試 100% 綠燈方可合併。
3. **feat/xxx & fix/xxx (Working Branches)**：功能開發與缺陷修復分支，強制關聯 Safety Goal 或 CR (Change Request) 編號。

## 2. 提交規範與簽名要求 (Commit Standard)
所有 Commit 訊息必須嚴格遵循 Conventional Commits 格式，並附帶對應之需求/缺陷追溯代號：
```text
feat(safety): [SG-02][SSR-02] implement CAN-FD E2E CRC-8 calculation
fix(ftti): [SG-01][TSR-01] shorten actuator trip threshold to 40ms
docs(audit): [SMP-01] update functional safety management plan
```

## 3. 版本凍結標籤規範 (Baseline Tagging)
重大安全里程碑達成時，必須簽發 Annotated Git Tag 並附帶校驗摘要：
- `v2.0.0-automotive-asil`: 達成 100% MC/DC 白箱覆蓋率。
- `v2.1.0-hil-shadow-mode`: 實車 HIL 矩陣與 Zero-TX 影子模式落地。
- `v2.2.0-e2e-ftti-validated`: CAN-FD E2E CRC-8 與 40ms FTTI 實測通過。
- `v2.3.0-patent-disclosure-filed`: 專利技術交底書 IDF01 凍結。
- `v3.0.0-commercial-ready`: 全套車規卷宗、FSA 報告、FTO 白皮書與黑盒子遙測落地。
- `v3.1.0-audit-dossier-ready`: 審查現場必備工作成果清單與雙向追溯矩陣全量就緒。

## 4. 變更控制流程 (Engineering Change Order - ECO)
任何涉及安全關鍵代碼（`auto_copilot/stage1_safety_supervisor.py`, `stage2_can_adapter.py`）之修改，必須啟動 ECO 流程：
1. 提交變更申請單，評估對 HARA 與 FTTI 之影響。
2. 安全經理 (FSM) 審批。
3. 執行回歸測試流水線（CI/CD ASIL-D Gate 22 項驗證）。
4. 更新雙向追溯矩陣 (`Part8_Traceability_Matrix.json`)。
