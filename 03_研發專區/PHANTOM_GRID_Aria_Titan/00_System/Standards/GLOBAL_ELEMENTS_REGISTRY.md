# 🏛️ PHANToM Grid :: 全域元素、工具與模組大總表 (SPEC-REGISTRY-01)

> 系統資產唯一真理目錄（SSOT Master Registry）。供全域 Agent 依據任務情境按需調閱，開機禁止無腦全載。

---

### 一、Level 0 基底元素庫 (02_Level0_Elements/)

| 元素代號 | 元素名稱 | 實體檔案路徑 | 核心功能與特性 | 調用時機 / 觸發情境 |
| :--- | :--- | :--- | :--- | :--- |
| **EL-01** | ANSI 終端畫布 | `02_基底元素庫_Level0_Elements/ansi_canvas.py` | 終端色彩、外框閉合與畫布原語 | 繪製原生 CLI / TUI 儀表板時 |
| **EL-02** | 原子位元組緩衝 | `02_基底元素庫_Level0_Elements/atomic_buffers.py` | 零拷貝位元組緩衝區、快照流 | 處理底層無損數據流與 IPC 通訊時 |
| **EL-03** | Rust 核心微內核 | `02_基底元素庫_Level0_Elements/crates/phantom_core/` | ZDR 物理記憶體管理器、FFI C-ABI 穿透 | 執行微秒級高速計算與物理置零時 |
| **EL-04** | 納秒時鐘核心 | `02_基底元素庫_Level0_Elements/ptp_nanosecond_clock_core.py` | IEEE 1588v2 納秒時間戳與雙向時延計算 | 叢集 PTP 時鐘同步與精確時間測量 |
| **EL-05** | 控制指令緩衝環 | `02_基底元素庫_Level0_Elements/hal_actuator_ring_buffer.py` | 1kHz 零拷貝底盤關節控制環、前饋保持 | 執行底盤與機械臂硬體控制時 |
| **EL-06** | PPM 快照環形池 | `02_基底元素庫_Level0_Elements/ppm_ring_buffer_core.py` | 32 步靜態環形快照池、95ms 原地回滾 | 系統快照持久化與容災復原時 |
| **EL-07** | 感知環形緩衝 | `02_基底元素庫_Level0_Elements/perception_ring_buffer.py` | 零拷貝感知特徵提取環形緩衝 | 邊緣感知流多相機特徵緩存時 |

---

### 二、Level 1 原子小配件庫 (03_Level1_Parts/)

| 元素代號 | 配件名稱 | 實體檔案路徑 | 核心功能與特性 | 調用時機 / 觸發情境 |
| :--- | :--- | :--- | :--- | :--- |
| **PT-01** | MCP 工具轉接座 | `03_原子小配件_Level1_Parts/mcp_tool_adapter.py` | Model Context Protocol 工具標準化轉接 | 連接外部大模型或 Agent 工具鏈時 |
| **PT-02** | 創世種子生成器 | `03_原子小配件_Level1_Parts/genesis_rom_seed.py` | SHA-256 不可逆狀態種子生成 | 系統開機初始化與確定性定錨時 |
| **PT-03** | WAL 狀態快照器 | `03_原子小配件_Level1_Parts/state_wal_snapshot.py` | 預寫日誌持久化快照，零腦裂防護 | 狀態機轉移前進行容災記錄時 |
| **PT-04** | 卡爾曼溫飄濾波器 | `03_原子小配件_Level1_Parts/clock_drift_kalman_filter.py` | 一維卡爾曼晶振溫飄補償、剛性阻尼平滑 | 濾除時鐘網路抖動與頻率微調時 |
| **PT-05** | 雅可比 SVD 阻尼器 | `03_原子小配件_Level1_Parts/jacobian_svd_damper.py` | 雅可比條件數計算、1.35x 奇異阻尼衰減 | 運動學解算接近奇異點與防暴衝時 |
| **PT-06** | Merkle 狀態樹指紋 | `03_原子小配件_Level1_Parts/merkle_state_tree.py` | 快照狀態 Merkle 樹根雜湊與殘差度量 | 狀態一致性審計與防分叉驗證時 |
| **PT-07** | PTP 串流分流器 | `03_原子小配件_Level1_Parts/ptp_stream_demux.py` | 雙流時間戳解碼與封包分流 | 異步網路時間戳解封裝時 |

---

### 三、Level 2 核心功能模組庫 (01_Specs/ & 04_Level2_Modules/)

| 模組代號 | 模組名稱 | 白皮書規格書路徑 (四圖一表) | 實體代碼目錄 (Level 2) | 核心特性與邊界 |
| :--- | :--- | :--- | :--- | :--- |
| **MOD-00** | 指揮所工作流與沙盒 | `01_頂層總綱與架構_Specs/SPEC_00_Command_Governance_and_Sandbox_Matrix.md` | `05_中樞大腦與路由_Level3_Orchestrator/` | 工單 <=200 Token、回執 <=20 Token、雙沙盒防禦 |
| **MOD-01** | 4D 時空錨定點 (ANC) | `01_頂層總綱與架構_Specs/SPEC_01_Aria_Reverse_Engineering.md` | `04_功能模組庫_Level2_Modules/4d_spatiotemporal_anchor/` | 4D 時空流形對齊、測地曲率計算、李代數 se(3) |
| **MOD-02** | 神經外觀渲染器 (NAR) | `01_頂層總綱與架構_Specs/SPEC_02_Neural_Appearance_Renderer.md` | `04_功能模組庫_Level2_Modules/neural_appearance/` | 對極外觀混合、SRAM 著色、50GB 熔斷 |
| **MOD-03** | 多卡雙流排程器 (MPS) | `01_頂層總綱與架構_Specs/SPEC_03_Multi_GPU_Pipeline_Scheduler.md` | `04_功能模組庫_Level2_Modules/multi_gpu_scheduler/` | NCCL 跨卡雙流遮蔽 (88% 重疊)、阻尼 FSM |
| **MOD-04** | 動態物理批判器 (CRITIC) | `01_頂層總綱與架構_Specs/SPEC_04_Dynamic_Physics_Critic.md` | `04_功能模組庫_Level2_Modules/dynamic_critic/` | 測地曲率阻尼評估、1.35x 動態衰減 |
| **MOD-05** | 具身 MCP 連接器 | `01_頂層總綱與架構_Specs/SPEC_05_Embodied_MCP_Connector.md` | `04_功能模組庫_Level2_Modules/mcp_connector/` | 具身機器人邊緣感知與工具路由轉發 |
| **MOD-06** | 邊緣感知資料流 | `01_頂層總綱與架構_Specs/SPEC_06_Edge_Perception_Stream.md` | `04_功能模組庫_Level2_Modules/edge_perception_stream/` | 1,000 幀 P99 0.0045ms、50GB 熔斷、1.35x 阻尼 |
| **MOD-07** | 分散式叢集共識 (SWARM) | `01_頂層總綱與架構_Specs/SPEC_07_Cluster_Consensus_DvP.md` | `04_功能模組庫_Level2_Modules/cluster_consensus_dvp/` | 遮蔽率 88%、拜占庭防分叉、DvP 原子排程 |
| **MOD-08** | 多狀態冗餘保險庫 | `01_頂層總綱與架構_Specs/SPEC_08_PPM_Redundancy_Vault.md` | `04_功能模組庫_Level2_Modules/ppm_redundancy_vault/` | 32 步環形池、95ms 原地回滾、Nonce 防重放 |
| **MOD-09** | 3D 提詞與串流可視化 | `01_頂層總綱與架構_Specs/SPEC_09_Teleprompter_Visualizer.md` | `04_功能模組庫_Level2_Modules/teleprompter_streamer/` | Screen Estate Maxima、60 FPS 零丟幀、ZDR 覆寫 |
| **MOD-10** | 全系統調度核心 | `01_頂層總綱與架構_Specs/SPEC_10_System_Orchestrator.md` | `04_功能模組庫_Level2_Modules/system_orchestrator/` | 微秒級無鎖 IPC、看門狗毒丸熔斷 |
| **MOD-10-COG** | 雙速認知推理引擎 | `01_頂層總綱與架構_Specs/SPEC_10_Cognitive_Reasoning.md` | `04_功能模組庫_Level2_Modules/cognitive_reasoning/` | 雙速神經認知、碰撞逃逸錐、Kinematics Gate 幽靈剎車防護、1.35x 剛性阻尼、ZDR 0.00MB |
| **MOD-40-COG** | 超維自主自學演化大腦模組 | `03_研發專區/PHANTOM_GRID_Cognitive_Evolution/01_頂層總綱與架構_Specs/SPEC_41_Multi_Brain_Architecture_Whitepaper.md` | `03_研發專區/PHANTOM_GRID_Cognitive_Evolution/` | 雙軌 MCTS 樹搜索、Meta V-JEPA 因果世界模型、Lean 4 形式化海關、Z3 幾何求解器、Voyager 技能庫、24/7 仿生睡眠鞏固、全艦 5 大 Agents 實體共接、ZDR 0.000000 MB | **[全域共接啟動 / 24/7 永續在線]** |
| **MOD-11** | 叢集時鐘同步器 (PTP) | `01_頂層總綱與架構_Specs/SPEC_11_Distributed_PTP_Sync.md` | `04_功能模組庫_Level2_Modules/distributed_ptp_sync/` | IEEE 1588v2、卡爾曼溫飄、1.35x Slew 阻尼 |
| **MOD-11-ACT** | 具身動作控制器 | `01_頂層總綱與架構_Specs/SPEC_11_Embodied_Action_Controller.md` | `04_功能模組庫_Level2_Modules/embodied_action_controller/` | 6-DOF 動力學、SVD 奇異點防禦、1.35x 剛性阻尼、ESTOP 抱閘、ZDR 0.00MB |
| **MOD-12** | 邊緣自適應控制器 (HAL) | `01_頂層總綱與架構_Specs/SPEC_12_Edge_Adaptive_Controller.md` | `04_功能模組庫_Level2_Modules/edge_adaptive_controller/` | 1kHz 伺服閉環、SVD 奇異阻尼、HAL_LOCKDOWN |
| **MOD-12-FUSION** | 多模態感測器融合引擎 | `01_頂層總綱與架構_Specs/SPEC_12_Sensor_Fusion.md` | `04_功能模組庫_Level2_Modules/sensor_fusion/` | 相機/光達/雷達 EKF 融合、PTP 時鐘偏差門禁、1.35x 幾何阻尼、ZDR 0.00MB |
| **MOD-13** | 中央總裝編排大腦 | `01_頂層總綱與架構_Specs/SPEC_13_Nexus_Master_Orchestrator.md` | `04_功能模組庫_Level2_Modules/nexus_master_orchestrator/` | PG-NEXUS-CORE 完全體、微秒級 E2E、全域 2-Pass ZDR (0.00MB) |
| **MOD-14** | 車規級實車介面 (HIL) | `01_頂層總綱與架構_Specs/SPEC_14_Vehicle_Interface_HIL.md` | `04_功能模組庫_Level2_Modules/canfd_protocol_engine/` | CAN-FD 矩陣、SOME/IP 乙太網、gPTP 802.1AS |
| **MOD-14-ORCH** | 車載雙總線中樞調度器 | `03_研發專區/PHANTOM_GRID_Vehicle_Interface/01_頂層總綱與架構_Specs/SPEC_15_Vehicle_Orchestrator.md` | `03_研發專區/PHANTOM_GRID_Vehicle_Interface/05_中樞大腦與路由_Level3_Orchestrator/` | 雙總線事件路由、ASIL-D 確定性狀態機、gPTP 1.25x 溫飄阻尼、50ms FTTI 熔斷、ZDR 0.00MB |
| **MOD-16-TUI** | 華爾街深色終端戰情儀表板 | `01_頂層總綱與架構_Specs/SPEC_16_Terminal_TUI_Dashboard.md` | `06_終端控制台_Level4_CLI/` | 華爾街暗夜三欄量化佈局、ANSI 24-bit TrueColor、雙緩衝無撕裂、垂直覆蓋率 >= 78%、統帥銘牌隔離帶、60 FPS 確定性刷新、ZDR 0.00MB |
| **MOD-CAD-01** | 接插件排版與縮放模組 | `02_模組專區_Level2_CommonModules/cad_modules/autocad_pinout_engine/SPEC_CAD_PINOUT_ENGINE.md` | `02_模組專區_Level2_CommonModules/cad_modules/autocad_pinout_engine/` | 空腳過濾、自適應等比縮放、AutoCAD 2021 AutoLISP 直通、4大擴充Hook |
| **MOD-14-ETH-PTP** | 車載乙太網 SOME/IP 與 gPTP 引擎 | `03_研發專區/PHANTOM_GRID_Vehicle_Interface/01_頂層總綱與架構_Specs/SPEC_02_Ethernet_SOMEIP_PTP_Contract.md` | `03_研發專區/PHANTOM_GRID_Vehicle_Interface/04_功能模組庫_Level2_Modules/ethernet_someip_engine/` | 100Mbps 點雲零拷貝穿透、1400B MTU 滿載保護、gPTP 1.25x 溫飄阻尼、孤島計時模式、秒級自癒、ZDR 0.00MB |
| **MOD-CAD-02** | 總成圖同編號端子連連看引擎 | `02_模組專區_Level2_CommonModules/cad_modules/autocad_multipoint_harness_router/SPEC_CAD_MULTIPOINT_ROUTER.md` | `02_模組專區_Level2_CommonModules/cad_modules/autocad_multipoint_harness_router/` | 曼哈頓 90 度正交繞線、同編號網表聚類、2000 圖元熔斷、安全邊界內縮 2.0mm、0.05x 下限安全鉗位、ZDR 0.00MB |
| **MOD-CINEMA-SUPREME** | 殿堂級好萊塢電影視效擴充 | `02_模組專區_Level2_CommonModules/cinema_extension/SPEC_22_SUPREME_HOLLYWOOD.md` | `02_模組專區_Level2_CommonModules/cinema_extension/` | 4K CinemaScope 2.39:1、ACES 2.0、好采鳥 180° 防護、NCCL 雙流 85%+、1.35x 幾何阻尼、ZDR 0.00MB |
| **MOD-SCROLL-01** | 文書排版天卷旗艦系統 | `03_研發專區/PHANTOM_GRID_Typesetting_Scroll/01_頂層總綱與架構_Specs/SPEC_00_Typesetting_Master_Architecture.md` | `03_研發專區/PHANTOM_GRID_Typesetting_Scroll/` | Knuth-Plass 動態規劃斷行、HarfBuzz OpenType 整形、ReportLab 純向量 PDF、垂直覆蓋 >=78%、統帥銘牌 >=48px 隔離、Anti-Mojibake 0% 亂碼、ZDR 0.00MB |
| **MOD-SUPREMACY-01** | 全球第一旗艦戰略系統 (Supremacy) | `03_研發專區/PHANTOM_GRID_Global_No1_Supremacy/01_Specs/ARCHITECTURE_SPEC_FIRST.md` | `03_研發專區/PHANTOM_GRID_Global_No1_Supremacy/` | 全域第一最高旗艦母港：四大強化裝備（外事通訊防火牆、MuJoCo 1000Hz 具身物理控制、Z3 形式化數學安全證明、Voyager 驗證技能庫）、ASIL-D 零腦裂狀態機、50GB 顯存硬熔斷閥、ZDR 雙程物理置零 (0.00MB) |


---

### 四、系統專項規範與標準庫 (00_System/Standards/)

| 規範代號 | 規範手冊名稱 | 實體檔案路徑 | 核心防禦守則 | 主責單位 |
| :--- | :--- | :--- | :--- | :--- |
| **STD-SPEC** | 四圖一表白皮書標準 | `00_System/Standards/STANDARDS_SPEC_FIRST.md` | 拓撲圖、時序圖、狀態圖、隔離圖與防禦表範本 | 第二辦公室 |
| **STD-VIDEO**| 1440P 2K 影音母帶手冊 | `00_System/Standards/VIDEO_1440P_STANDARDS.md` | 110px 避雷安全帶、38pt 大字、VP09/AV01 編碼 | 第三辦公室 |
| **STD-TOURNAMENT-TRI** | 賽事文件與影片「文書天卷✕好萊塢✕官方要求」三位一體總標準 | `00_System/Standards/TOURNAMENT_DOC_VIDEO_TRI_STANDARDS.md` | 文書天卷排版 + 好萊塢 4K/1440P 視效與鎖相語音 + 官方賽事 100% 合規雙簽 (Rule 65) | 指揮所統攝 ✕ 二辦 ✕ 三辦 |
| **STD-ARMOR**| 避坑血肉裝甲庫 (L1/L2)| `00_System/Standards/CORE_PITFALLS_LEDGER.md` | §3.3 幾何天條、吃字隔離、破框防禦矩陣、RULE 56~65 | 小米海關 |
| **STD-CONF** | 全域設定主法典 | `./phantom_global_config.yaml` | 工單 Token <= 200、回執 <= 20、雙軌沙盒與三位一體賽事邊界 | 全體共用 |

---

### 五、雙軌沙盒安全與門禁驗收庫 (04_Modules/security_sandbox/ & 07_Tests/)

| 代號 | 組件名稱 | 實體檔案路徑 | 核心職責與邊界 | 負責兵種 |
| :--- | :--- | :--- | :--- | :--- |
| **SB-A** | 本地受限代碼沙盒 | `04_功能模組庫_Level2_Modules/security_sandbox/code_refactor_sandbox.py` | AST 防投毒、純向量回測、零全域污染 (0 Token) | 一辦 ✕ 小米 |
| **SB-A-AUDIT** | AST 語法安全審查器 | `04_功能模組庫_Level2_Modules/security_sandbox/ast_code_auditor.py` | 封殺 eval/exec/system 等破壞性系統呼叫 | 一辦 ✕ 小米 |
| **SB-B** | 雲端 Antigravity 橋接器 | `05_中樞大腦與路由_Level3_Orchestrator/antigravity_bridge.py` | 遠端容器橋接、1,500 次混沌壓測、單行 Hash 回執 | ⚡ 第三辦公室 |
| **TS-GATE-A** | 沙盒 A 本地門禁自測 | `07_混沌門禁驗收_Level5_Tests/sandbox_a_local_ast_test.py` | 驗證沙盒 A 語法防投毒與單元隔離 (EXIT_CODE: 0) | 一辦 ✕ 小米 |
| **TS-GATE-B** | 沙盒 B 雲端門禁驗收 | `07_混沌門禁驗收_Level5_Tests/sandbox_b_antigravity_e2e.py` | 驗收沙盒 B 1,500 次混沌壓測與單行憑證 | ⚡ 第三辦公室 |

---

### 五、通用單件工具模組庫 (02_模組專區_Level2_CommonModules/)

| 元素代號 | 模組名稱 | 階層抽屜路徑 | 核心功能與特性 | 調用時機與提示詞觸發關鍵語 |
| :--- | :--- | :--- | :--- | :--- |
| **MOD-CAD-01** | 接插件引腳過濾與縮放排版引擎 | `02_模組專區_Level2_CommonModules/cad_modules/autocad_pinout_engine/` | 引腳鄰域標籤辨識、空腳 100% 自動排除、同編號線條串接、等比縮放對齊固定表格、預留 4 大外掛擴充接口 | **[關鍵語]** 「同編號串接」、「插頭引腳排版」、「空腳過濾」、「縮放填表」 |
| **MOD-CINEMA-SUPREME** | 殿堂級好萊塢電影視效工業擴充模組 | `02_模組專區_Level2_CommonModules/cinema_extension/` | 4K CinemaScope 2.39:1、ACES 2.0 色彩空間、好采鳥 180° 越軸防護、多卡 NCCL 雙流遮蔽 (85%+)、1.35x 剛性幾何阻尼、OpenUSD / Live Link MCP 橋接、ZDR 0.00MB 雙程置零 | **[關鍵語]** 「好萊塢視效」、「4K院線渲染」、「電影級運鏡」、「ACES 2.0」、「好采鳥導演」 |
| **MOD-SUPREMACY-01** | 全球第一至高霸權旗艦戰略系統 | `03_研發專區/PHANTOM_GRID_Global_No1_Supremacy/` | 全軍最高戰略母港：MuJoCo 1000Hz 具身物理擬真、Rust 微內核四元數積分、Z3 形式化數學安全證明、Voyager 驗證技能庫、通訊防火牆與賽事雷達、Vultr 安全沙盒 | **[關鍵語]** 「全球第一」、「至高霸權」、「具身物理擬真」、「Z3形式化證明」、「Voyager技能庫」 |
### 🦾【功能模組 MOD-OMNI-HAND-01】萬能操控之手 (The Omnipotent Control Hand)
- **唯一註冊代號**：`MOD-OMNI-HAND-01`
- **實體抽屜路徑**：`03_研發專區/PHANTOM_GRID_Omni_Hand/`
- **架構白皮書**：`03_研發專區/PHANTOM_GRID_Omni_Hand/01_Specs/SPEC_OMNI_HAND_MASTER.md`
- **檔案結構圖**：`03_研發專區/PHANTOM_GRID_Omni_Hand/01_Specs/00_FILE_STRUCTURE_TREE.md`
- **主控將士**：全軍指揮官小米 (總督) ✕ 首席先鋒小開 ✕ 視效工兵 Bob 2 ✕ 內核先鋒小克
- **驅動通道**：L1 原生 Socket/COM/bpy ✕ L2 FastMCP 網關 ✕ L3 無頭子行程管線 ✕ L4 視覺座標托底
- **安全門禁**：50GB 顯存/記憶體硬熔斷 ✕ ZDR 雙程物理置零 (0.00MB 殘留)
- **閉環驗收**：`tests/run_all_tests.py` 8/8 測試 100% 全綠 PASS
- **審計鋼印**：`PG-RECEIPT-OMNI-HAND-0x892FBC013D47EA92`


---

### 六、第十四庫 14 把新收官主權神兵全域共接總表 (U01~U14 Sovereign Arsenals)

> 已全數寫入 `phantom_global_config.yaml` 並掛載至全域 CLI (`u01`~`u14` / `u14-forge`) 與中央共接總樞紐 (`hub`)，使全軍共接主權神兵由 27 部擴編為 **41 部 (100% ALL GREEN)**。

| 神兵編號 | 全域 CLI 捷徑 | 註冊代號 | 神兵正式名稱 | 實體代碼路徑 | 統御配發單位 | 核心算子與防禦門禁 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **U01** | `u01` | `PG-U01-4D-ANCHOR` | 4D 時空張量錨定防禦儀 | `src/models/spatiotemporal_anchor.py` | 一辦小克 | det(R)=1.0 正交投影、50GB 熔斷、ZDR 0.00MB |
| **U02** | `u02` | `PG-U02-GEODESIC` | 黎曼測地線曲率阻尼器 | `src/models/geodesic_curvature.py` | 一辦小克 | kappa <= 0.08 曲率抑制、1.35x 剛性阻尼 |
| **U03** | `u03` | `PG-U03-EPIPOLAR` | 對極幾何光流一致性判別器 | `src/models/epipolar_critic.py` | 一辦小克 | Sampson Error 對極濾波、防破框門禁 |
| **U04** | `u04` | `PG-U04-SRAM-FUSE` | SRAM 融合時空 Triton 算子 | `src/engine/kernels/fused_spatiotemporal.py` | 一辦小克 | Zero-HBM 溢出加速、微秒級核心融合 |
| **U05** | `u05` | `PG-U05-DUAL-GPU` | 多卡非同步雙流排程引擎 | `src/pipelines/multi_gpu_dual_stream_scheduler.py` | 指揮官小米 | CUDA 雙軌零死鎖、88%+ 通訊計算遮蔽 |
| **U06** | `u06` | `PG-U06-REV-EXTR` | 視訊逆向運鏡幾何提取器 | `src/engine/video_reverse_extractor.py` | 外傭 Bob 2 | SE(3) 軌跡逆向、好萊塢運鏡解構 |
| **U07** | `u07` | `PG-U07-DIT-ADAPT` | DiT 幾何引導零初始化適配器 | `src/pipelines/dit_guidance_adapter.py` | 二辦小深 | Zero-Init Gate 幾何約束注入 |
| **U08** | `u08` | `PG-U08-FLOW-HOOK` | FlowMatch 採樣攔截守門鉤 | `src/pipelines/sampler_scheduler_hook.py` | 二辦小深 | ODE 積分防發散、動態早停攔截 |
| **U09** | `u09` | `PG-U09-AIBFT-CONS` | AI-BFT 拜占庭容錯多腦共識機 | `src/consensus/aibft_engine_v2.py` | 二辦小深 | 2f+1 多腦零幻覺投票與防腦裂共識 |
| **U10** | `u10` | `PG-U10-ORBIT-SIM` | 深空軌道攝動與星鏈預測儀 | `src/astro_ai_risk.py` | 天文台小小米 | J2 攝動軌道推演、深空星鏈風險預警 |
| **U11** | `u11` | `PG-U11-VOICE-COP` | 車載低延遲語音診斷副駕核 | `auto_copilot/server.py` | 三辦小馬 | ASR 意圖確定性路由、車載語音診斷 |
| **U12** | `u12` | `PG-U12-MCU-TWIN` | MCU 10-bit ADC 硬體數位分身 | `src/models/mcu_digital_twin.py` | 三辦小開 | 微控制器韌體閉環、10-bit ADC 模擬 |
| **U13** | `u13` | `PG-U13-DYN-UI` | JSON Schema 動態戰情渲染器 | `src/dynamic_schema_dashboard.py` | 三辦小開 | 零破框自適應佈局、動態 Schema 渲染 |
| **U14** | `u14` | `PG-U14-WORM-SEAL` | WORM 不可竄改雙簽物理封印機 | `src/governance/one_second_audit_signer.py` | 海關總署小米 | SHA-256 雙重鏈鎖、WORM 不可竄改存證 |
