# PHANToM Grid: 4D 神經幾何防禦與動態顯存熔斷系統技術白皮書
**版本**: 1.0.0-PROD  
**體系**: PHANToM Grid Neural Geometric Defense Core  
**驗收狀態**: 全模組 Phase 1 ~ 4 通過 / ZDR 零殘留 / SHA-256 存證完畢  

---

## 一、系統架構總覽 (四圖一表)

### 1.1 圖一：系統總體架構與拓撲圖
- 外部生成採樣迴圈 (FlowMatch / Wan2.1) -> FlowMatchSamplerSchedulerHook
- FlowMatchSamplerSchedulerHook -> DiTGeometricGuidanceAdapter (幾何引導轉接器)
- 統一防禦引擎 (PhantomDefenseEngine SDK):
  1. VRAMGuardDynamicScheduler (50GB 熔斷守門 / 35GB 自適應分塊)
  2. SpatiotemporalAnchor4D (4D 時空特徵幾何錨定)
  3. GeodesicCurvatureEstimator (二階測地曲率平滑器)
  4. EpipolarConsistencyCritic (跨視角本質矩陣 Critic)
- Phase 4 治理審計層: ZDRAuditManager (中介張量 zero_() 物理清零 + SHA-256 日誌)

### 1.2 表一：防禦矩陣表
- VRAMGuard: <35GB 直通, 35~50GB 自適應 Chunk=2, >=50GB 熔斷拋出 MemoryBackoffReject
- 幾何阻尼: 殘差 > 0.08 啟用 1.35x 剛性收縮阻尼
- ZDR 物理銷毀: 中介暫存 zero_() 清零 (Max Abs = 0.0)
- 審計簽名: SHA-256 64-hex 指紋存證於 logs/audit/
