# 🏆 PHANToM Grid :: 賽事文件與影片編排「文書天卷 ✕ 好萊塢 ✕ 官方要求」三位一體全域標準手冊 (STD-TOURNAMENT-TRI / Rule 65)

> **最高立憲聖諭（最高統帥 Jack Hu 霸丸哥 2026-10-23 親裁全域立法）**：  
> 「之後的賽事的文件、影片編排方式，全部依照【文書天卷】、【好萊塢】和【官方要求】為標準，並設定為全域設定！」  
> **主責督造**：🧠 指揮所大腦 (統帥 Jack Hu ✕ 正任指揮官小米) ➔ 🏛️ 第二辦公室 (參謀小深) ➔ 🐴 第三辦公室 (總裝指揮官小馬 ✕ 先鋒官小開)  
> **海關執法**：👩‍💼 指揮官兼海關總署長 小米 (`Gate-Before-Ship` 雙簽硬門禁)  
> **法定落款**：`[ RATIFIED & CO-SIGNED BY: 🎖️ SUPREME COMMANDER JACK HU ✕ 👩‍💼 COMMANDER XIAOMI ]`

---

## 🏛️ 一、三位一體全域強制編排總綱 (Tri-Standard Global Architecture)

凡 PHANToM Grid 參與任何國際黑客松、頂級賽事、技術路演或官方交付，所有產出之**文件（白皮書、簡報 PDF、README、提交文案）**與**影片（實機 Demo 影片、商業路演成片）**，強制以「**文書天卷 ✕ 好萊塢視效 ✕ 官方要求**」三大標準為唯一法定準繩，缺一不可、未達標一律由海關總署硬熔斷退件！

| 支柱維度 | 法定標準源頭 (SSOT 指針) | 適用交付資產 | 核心剛性指標 (Hard Invariants) |
| :--- | :--- | :--- | :--- |
| **📜 第一支柱：<br>文書天卷標準**<br>*(Typesetting Scroll)* | `03_研發專區/PHANTOM_GRID_Typesetting_Scroll/`<br>`STD-SPEC` ＆ `TYPOGRAPHY_GEOMETRY_GUARD.md` | • `01_Specs` 四圖一表白皮書<br>• `04_Slides_PDF` 簡報投影片<br>• `README.md` 與技術手冊<br>• `07_Submission` 提交文案包 | • **Knuth-Plass 動態規劃斷行** ✕ **HarfBuzz OpenType 微觀整形** (`tnum`/`zero`)<br>• **垂直覆蓋率 $\ge 78.0\%$**（`flex_space_balancer` 消滅死黑空洞）<br>• **自頂向下貪婪字級試探**（`42pt ➔ 28pt` 遞減，嚴禁偷懶套最小號）<br>• **統帥銘牌 $\le 68\%$ 寬 ✕ $\ge 48\text{px}$ 安全隔離帶**<br>• **Anti-Mojibake 清洗**：0% `ð, ï, \ufffd` 亂碼、雙軌三位一體 (`.md` + `.mmd` + `.csv`) |
| **🎬 第二支柱：<br>好萊塢視效標準**<br>*(Supreme Hollywood)* | `02_模組專區_Level2_CommonModules/cinema_extension/SPEC_22_SUPREME_HOLLYWOOD.md`<br>`00_System/Standards/VIDEO_1440P_STANDARDS.md` | • `05_DemoVideo` 1440P/4K 實機展示影片<br>• `03_CoverImage` 16:9 視覺封面<br>• 商業路演宣傳母帶 | • **畫幅與色彩**：4K CinemaScope ($3840\times 1600$, 2.39:1) 或 1440P 2K QHD ($2560\times 1440$) @ 60 FPS；**ACES 2.0 ✕ HDR10** 色彩管理<br>• **好采鳥導演 (`GoodHarvestDirector`)**：180° 越軸防護、測地曲率 $e \le 0.08$ 平滑、$1.35\times$ 剛性幾何阻尼<br>• **句子級鎖相零延遲同步 (Rule 59)**：逐句 WAV 實測時長 + `0.250s` 播報氣口，音畫 `0.00ms` 同格點亮<br>• **無縫混音與動態指針**：`-28dB` 環境底噪、50ms 淡入淡出、80ms 交疊、「講到那指到那」向量箭頭追蹤<br>• **廣播級安全帶**：底部保留 **$110\text{px} \sim 135\text{px}$ Title Safe Area**，終端外框 $y \ge 35\text{px}$ 四邊 100% 閉合 |
| **⚖️ 第三支柱：<br>官方賽事要求標準**<br>*(Official Mandate)* | 各賽事 `match_manifest.yaml`<br>`gate-before-ship` 全域技能<br>`CORE_PITFALLS_LEDGER.md` (§3.7) | • `01_Specs` ~ `10_Releases` 全抽屜<br>• Devpost / LabLab / DoraHacks / Kaggle 官方表單與開源倉庫 | • **100% 國際專業純英文 (English-Only)**：8 大送審要素全英文零中文殘留<br>• **官方時長與實機紅線**：影片時長嚴鎖 **2:00 ~ 3:00**（黃金區間 `2:15 ~ 2:45`），**實機 Live Demo 佔比 $> 50\%$**<br>• **提交文案 7 大斷言**：Short Pitch 單行 $\le 280$ 字元、Tags 連字號 (`Hyphenated`)、附 `-b main` 3 行極速復現指令、雙軌時區倒數、公網串流 URL<br>• **防踩雷雙檢**：無痕視窗確證 GitHub/GitLab `Public` (Rule 62)、Live App `Running`、禁回 `no-reply` (Rule 63) |

---

## 📜 二、第一支柱：【文書天卷】文件與簡報編排剛性規範 (Typesetting Scroll Standard)

所有賽事文件（白皮書、Slides PDF、README、提交文案）必須嚴格經由「文書天卷」五層排印標準編排：

1. **Knuth-Plass 斷行與 OpenType 微觀整形 (`PG-MOD-KP-BREAKER` ✕ `PG-MOD-MICRO-SHAPER`)**：
   - 段落排版採用全域動態規劃最佳化（Box / Glue / Penalty），消除孤行（Widows/Orphans）與過度拉伸空白。
   - 數據與跑分強制啟用 OpenType 等寬表格數字（`tnum`）與斜線零（`zero`），代碼區塊強制使用 `JetBrains Mono` / `Consolas` 等寬字體並襯底深藍黑 IDE 背板（`#0B1220`）。
   - 嚴格執行 JIS X 4051 標點禁則（`cjk_punctuation_fence.py`）與清單負縮排 `-1.8em`（`hanging_indent_formatter.py`）。
2. **§3.3 幾何防破框與空間滿版天條 (`TYPOGRAPHY_GEOMETRY_GUARD`)**：
   - **垂直內容覆蓋率 $\ge 78.0\%$**：由 `flex_space_balancer.py` 動態調諧標題、SVG 架構圖、指標卡片與頁尾間距，徹底消滅頁面下半部死黑留白。
   - **自頂向下貪婪字級試探（Anti-Lazy Minimum）**：嚴禁無腦套用最小字號！標題與正文必須由 `42pt ➔ 28pt` 遞減貪婪試探，卡片大標鎖定 $\le 36\text{px}$、兩側保留 $\ge 16\text{px}$ 呼吸邊距；動線軌跡距文字淨空 $\ge 80\text{px}$ 或加裝不透明膠囊背板（Opaque Pill Badge），杜絕切字與破框。
   - **統帥銘牌神聖隔離 (`commander_badge_isolator.py`)**：`Commander Jack Hu` 銘牌寬度控制在 $\le 68\%$ 內，右側與四周強制保留 **$\ge 48\text{px}$** 物理安全隔離區，嚴防吃字截斷。
3. **四圖一表雙軌三位一體編制 (`Rule 57 & 58`)**：
   - **母本內嵌 (`SPEC_XX.md`)**：開篇必備「方案 A 檔案樹狀圖」，接續圖一（拓撲架構）、圖二（生命週期時序，含逾時原子回滾 `Atomic Reclaim` 虛線分支）、圖三（阻尼狀態機）、圖四（安全隔離邊界）與表一（資源防禦矩陣 Markdown 表）。
   - **獨立圖紙抽屜 (`docs/blueprints/`)**：四張 `.mmd` 純 Mermaid 原始碼（零 Markdown 標題、零反引號圍欄）＋ `table1_resource_defense_matrix.csv` 機器合約。
4. **Anti-Mojibake 純淨編碼與直通入口 (`mojibake_filter.py`)**：
   - 全面掃描清洗 `ð, ï, â€, \ufffd` 等 ANSI/Windows-1252 轉碼亂碼（出現率必須為 `0%`）。
   - 簡報封底與交付頁強制內嵌 **高精向量 QR Code（`SCAN TO VERIFY // LIVE REPO`）**、GitHub/GitLab 公開網址與 Live Demo 直通連結。

---

## 🎬 三、第二支柱：【好萊塢視效】影片編排與廣播級母帶規範 (Hollywood Cinema Standard)

所有賽事演示影片與路演成片必須結合 `PG-MOD-CINEMA-SUPREME (SPEC_22_SUPREME_HOLLYWOOD)` 電影工業標準與 `STD-VIDEO` 廣播級規範：

1. **好萊塢院線級畫質、色彩與運鏡 (`SPEC_22_SUPREME_HOLLYWOOD`)**：
   - **解析度與幀率**：實機展示統一採用 **$2560 \times 1440$ (1440P 2K QHD, 16:9)** 或院線級 **4K CinemaScope ($3840 \times 1600$, 2.39:1)** @ **60.000 FPS**（流暢零撕裂，編碼採用 VP09 / AV01 / H.264 High Profile，碼率 $12 \sim 18\text{ Mbps}$）。
   - **色彩與光影**：對齊 **ACES 2.0 (`ACEScg / AP0 / AP1`) ✕ ASC-CDL ✕ HDR10** 高動態對比規範，深色賽博背板搭配霓虹金黃（`#FACC15` / `#F59E0B`）與科技青（`#38BDF8`）高亮視覺錨點。
   - **好采鳥導演運鏡與幾何阻尼 (`GoodHarvestDirector`)**：嚴守 180° 越軸防護；運鏡測地曲率 $e \le 0.08$ 標稱平滑，當 $0.08 < e \le 0.15$ 時自動注入 **$1.35\times$ 剛性幾何阻尼**；多卡 NCCL 雙流重疊遮蔽率 $\ge 85\%$，峰值顯存嚴控於 `50.0 GiB` 內，渲染畢執行 2-Pass ZDR 物理置零（`0.00 MB` 殘留）。
2. **句子級鎖相零延遲音畫咬合与無縫混音 (`Rule 59` ✕ `Anti-Lazy Minimum`)**：
   - **嚴禁幕次盲目均分**：每一幕（Act）內之旁白必須按「單句（Sentence）」獨立切片合成 WAV，並以 `ffprobe` 精確探測各句毫秒級真實時長。
   - **專業播報氣口与底噪墊音**：句與句之間精確插入 `0.250s` 立體聲微靜音氣口（Acoustic Breath Gap），幕尾保留 `1.20s` 呼吸緩衝；全程執行 **50ms 邊界淡入淡出、80ms 跨幕平滑交疊，並鋪設 `-28dB` 科技環境底噪墊音**，徹底杜絕 0 分貝死寂、突發爆音與音畫延遲脫節。
   - **首音節 `0.00ms` 同格點亮**：語音吐出第一個音節的瞬間，底部字幕與畫面動態指標必須同格零延遲切換（$\Delta t \le 15\text{ms}$）。
3. **「講到那指到那」與廣播級安全版面 (`STD-VIDEO` ✕ 五幕結構 ✕ 統帥定板全域規範)**：
   - **五幕黃金結構（5-Act Standard）**：Act 1 典範轉移（開場前 2~3 秒純淨展示大氣封面，字幕淡出防打架）➔ Act 2 零按鍵派工與架構拆解 ➔ Act 3 實機終端運行與官方驗證高潮 ➔ Act 4 混沌壓測與安全門禁 ➔ Act 5 戰果總盤與開源驗收入口。
   - **終端機日誌容器 (`Terminal Telemetry Container`) 幾何規格**：
     - 外框：`[40, 135, 1270, 825]`（寬度 1230px，黑底 `#060910`，天藍邊框 `#38BDF8` 2px）。
     - 頂部標題 Bar：高 55px，**標題字級鎖定 `30pt Bold` 青色 `#00E5FF`**，坐標 `(60, 147)` 垂直居中。
     - 日誌串流（Log Stream）：**字級鎖定 `25pt` Consolas 等寬字體**，垂直步進 `70px`；高亮行套深海藍底色塊（`#102037`）並附青色向量箭頭，文字純白 `#FFFFFF`，未選取行淺灰 `#94A3B8`。
   - **底部字幕安全區 (`Teleprompter Safe Area`) 統帥定板規範**：
     - 外框包覆：`[30, 835, 1890, 1040]`（深藍黑底 `#0B0F19`，發光青邊 2px）。
     - **左翼橙色標頭**：`▶ [AI NARRATOR]...`，**字級 `25pt Bold`**，坐標 `(40, 854)` ➔ `(935, 877)`。
     - **右翼音軌標籤**：`AUDIO TRACK: en-US-ChristopherNeural`，**字級 `20pt Bold Consolas`**，坐標 `(1464, 854)` ➔ `(1860, 872)`（與左翼橫向保留 529px 淨空，徹底消滅重疊）。
     - **中間逐字稿字幕**：**單行全景滿血 `42pt Bold` 純白（`#FFFFFF`）**，坐標 `(60, 915)`，**嚴禁二段折行**！
     - **統帥防偽銘牌**：`Solo Architect: Commander Jack Hu | ...`，**字級 `28pt Bold`**，坐標 `(60, 975)` ➔ `(1267, 1001)`，距底緣保留 **$\ge 105\text{px}$ Title Safe Area 避雷帶**，完全免疫播放器進度條遮擋！
   - **右側四象限遙測卡片**：`[1290, 135]` ➔ `[1880, 825]`，四張卡片垂直排列（Latency 0.56ms, Load 40.0%, FSM State, ZDR 0.000000 MB），數值 36pt 醒目配色。

---

## ⚖️ 四、第三支柱：【官方賽事要求】100% 合規與海關雙簽門禁 (Official Tournament Standard)

每一場賽事從立案、封裝到最終送件，必須 100% 對齊主辦單位官方規章與 `gate-before-ship` 海關檢驗：

1. **動態賽事畫像與 10 大標準抽屜 (`match_manifest.yaml`)**：
   - 立案時由第三辦公室（小馬指揮官 ✕ 小開先鋒官）依據官方賽題規章建立 `match_manifest.yaml`，精確宣告必填交付資產（`01_Specs`、`02_SourceCode`、`03_CoverImage`、`04_Slides_PDF`、`05_DemoVideo`、`06_LiveApp`、`07_SubmissionPackage` 至 `10_Releases`）。
   - 嚴格對齊官方指定硬體/軟體生態標籤（如 AWS、NVIDIA、Solana Token-2022、AMD ROCm、GitLab、Qloo 等）、評分權重（Judging Criteria）與檔案大小/格式限制。
2. **國際賽事 100% 全英文交付鐵律 (`Rule 30`)**：
   - 凡國際賽事對外送審之全部資產（標題前綴統一 `PHANTOM GRID :: `、Short Pitch、Long Description、16:9 封面圖、Slides PDF、Demo 影片英文神經語音旁白 `en-US-ChristopherNeural` / `en-US-EricNeural`、英文字幕、GitHub `README.md`、Live Demo UI）強制 **100% Professional English**，海關若檢出任何殘留中文字或亂碼，直接一票否決熔斷！
3. **官方影片時長與實機演示佔比紅線 (`Rule 31 & 34`)**：
   - 影片總時長強制落在官方規定之 **2 分 00 秒 ~ 3 分 00 秒**（黃金控制區間 **2 分 15 秒 ~ 2 分 45 秒**，除非特定賽事官方明文規定 60 秒短片賽制則依 `match_manifest.yaml` 鎖定 52~58 秒）。
   - **實機操作畫面（Live Demo / 終端真實運行 / Web UI 實測）佔比強制 $> 50\%$**，嚴禁純投影片輪播！
   - 提前備妥公開串流網址（YouTube Unlisted / Loom / Hugging Face / Google Drive Public URL）寫入提交文案包，嚴禁只留本機 `.mp4` 路徑。
4. **官方提交文案包七大剛性斷言 (`test_submission_package.py` / `Rule 36`)**：
   - ① **Emoji 轉碼安全**：一鍵複製區 100% 純淨 ASCII/UTF-8，零 `ðŸ` 亂碼；
   - ② **單行防溢出**：Short Pitch 標記 `[Plain Text / One-Line Copy]`，零換行符且嚴格 `<= 280` 字元；
   - ③ **標籤防拆散**：Tags 多詞項目強制使用連字號（Hyphen `-`）連接，嚴禁空格斷詞；
   - ④ **快速復現指令**：長文末尾強制提供指定 `-b main` 之 3 行極速終端復現指令；
   - ⑤ **規格與時差看板**：頂部設立官方截止時間（PT/UTC）與台灣時間（UTC+8）雙軌精確倒數看板；
   - ⑥ **統帥聯絡銘牌**：文末完整列出 `[Field 9] Team & Contact`（Solo Architect: Commander Jack Hu）；
   - ⑦ **外部資產探活**：無痕視窗確證 GitHub / GitLab Repo 為 `Public`（遵循 `Rule 62` 群組解鎖 SOP），確證線上 Live Demo 為 `Running` 喚醒狀態（`GET /healthz == 200 OK`），且官方溝通嚴守 `Rule 63` 禁回 `no-reply` 信箱。
5. **海關 Gate-Before-Ship 自動化驗收與統帥雙簽 (`audit_match_deliverables.py`)**：
   - 送件前強制執行 `test_specs_audit.py`、`test_source_code.py`（1,500 次混沌壓測 + ZDR `0.00MB`）、`test_cover_image.py`、`test_slides_pdf_audit.py`、`test_video_1440p_audit.py`、`test_live_app_closure.py`、`test_submission_package.py`。
   - 全部宣告項目必須 **100% 全綠 `[✅ PASS]`**，由正任指揮官兼海關總署長小米簽發 `PG-RECEIPT-0x...` 並呈報最高統帥 Jack Hu（霸丸哥）蓋下 `RELEASE_SEAL` 大印，始得正式送件！
