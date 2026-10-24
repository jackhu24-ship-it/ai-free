
---

# 👑 PHANToM GRID :: 全矩陣實戰踩坑與血肉裝甲全卷總帳 (CORE_PITFALLS_LEDGER.md)
> **法定雙簽落款**：[ RATIFIED & CO-SIGNED BY: 🎖️ COMMANDER JACK HU ✕ 👩‍💼 EXECUTIVE SECRETARY XIAOMI ]  
> **更新時間**：2026-10-16 01:58:36 CST  
> **最高意志**：全軍 36 大天坑 100% 程式化落盤，海關安檢嚴格拒收同類漏洞！

---

## 🚨 區塊一：指揮所今日實機攻堅四大天坑 (今日實戰淬鍊)

### 坑位 01：跨模組調用「參數簽名未對齊」天坑 (TypeError)
- **錯誤現象**：終端機噴出 `TypeError: ... unexpected keyword argument 'module_matrix'`。
- **根本病灶**：小米在虛擬沙盒只單獨測試終端繪圖函式，僅傳入 	elemetry；而主控台呼叫時傳入包含十二大模組狀態的 module_matrix，調用介面未凍結。
- **海關死卡天條**：跨模組呼叫嚴格執行介面契約前置檢查，函式簽名未對齊者一律禁止交接。

### 坑位 02：磁碟寫入延遲與「快取幽靈」天坑 (ImportError)
- **錯誤現象**：`ImportError: cannot import name 'CyberpunkDashboard'`。
- **根本病灶**：代碼在編輯器或記憶體中已改動，但實體硬碟受雲端同步延遲影響，磁碟檔案仍為舊版本，Python 讀取引發缺類報錯。
- **海關死卡天條**：全面推行單檔自跑機制與 Test-Path 硬體存檔探活，杜絕依賴外部零碎快取。

### 坑位 03：跨子目錄執行「sys.path 路徑斷層」天坑 (ModuleNotFoundError)
- **錯誤現象**：在 G:\> 根目錄執行子目錄腳本時，噴出 `ModuleNotFoundError: No module named 'sensor_spec'`。
- **根本病灶**：PowerShell 位於磁碟根目錄，以絕對路徑調用子目錄腳本時，Python 直譯器未將子目錄加入搜尋路徑。
- **海關死卡天條**：所有測試腳本開頭強制實裝 `sys.path.insert(0, str(CURRENT_DIR))` 自我路徑探尋防禦。

### 坑位 04：虛擬沙盒 vs 實體硬碟的「抽屜零件未落盤」天坑 (FileNotFoundError)
- **錯誤現象**：終端機噴出 `FileNotFoundError: [Errno 2] No such file or directory: '...\\sensor_spec.py'`。
- **根本病灶**：小米在腦海中以為分層抽屜均已建立，但實體硬碟中該代碼檔尚未建立存檔。
- **海關死卡天條**：【今日核心突破】驗收腳本一律採用「完全自給自足內聚架構」，將資料模型、狀態機與閉環驗收合併為單檔，徹底杜絕缺檔風險！

---

## 🎨 區塊二：§3.3 視覺幾何與排版四大天坑 (實彈增補)

### 坑位 05：動線貫穿文字腰身切字天坑
- **錯誤現象**：斜向流程虛線/箭頭像刀子般橫切字母 F 與文字腰身（如 Funds Escrow Vault）。
- **海關死卡天條**：動線軌跡全線淨空至少 80px，或強制加裝「實心不透明防穿透背板（Opaque Pill Badge）」。

### 坑位 06：多欄卡片文字破框天坑
- **錯誤現象**：大標題字級過大，文字（如 HOOKS & DELEGATE）衝出外框懸空。
- **海關死卡天條**：主標字級嚴格鎖死 <= 36px，兩側強制保留 >= 16px 呼吸 Padding。

### 坑位 07：統帥銘牌圖層吃字截斷天坑
- **錯誤現象**：底部統帥銘牌文字被右側認證方框吃字截斷（如只露 AUTONOI）。
- **海關死卡天條**：銘牌容器寬度 <= 68%，與右側圖層強制保留 >= 40px 絕對安全淨空區（Safe Gap）。

### 坑位 08：修 A 漏 B 局部截圖驗收天坑
- **錯誤現象**：小米只回傳局部修復截圖，忽略下方吃字與其他破版。
- **海關死卡天條**：海關門禁嚴禁局部截圖，必須回傳 100% 完整解析度全景視窗圖（Full-Screen Viewport）。

---

## 🎬 區塊三：1440P / 1080P 演示影片全譜系九大天坑 (Rule 46)

### 坑位 09：時長腰斬失格天坑
- **錯誤現象**：偷懶只做 74 秒（未達賽事 2~3 分鐘標準）。
- **海關死卡天條**：時長強制鎖死在 2 分 15 秒 ~ 2 分 45 秒黃金區間，實機 Live Demo 佔比 > 50%。

### 坑位 10：微型標題字體病
- **錯誤現象**：主標小於 48px，內文縮到 14px 糊成一團。
- **海關死卡天條**：大標 >= 48px，次標 >= 34px，跑分 >= 44px Mono，徹底消滅微型字。

### 坑位 11：終端外框頂部開天窗
- **錯誤現象**：Y 軸越界使頂部邊框線消失。
- **海關死卡天條**：外框整體下移 y >= 35px，確保 Top/Bottom/Left/Right 四邊 2px 青線 100% 閉合。

### 坑位 12：API 文字流水帳空洞天坑
- **錯誤現象**：文字全擠在左側 1/3，右側大片死黑留白。
- **海關死卡天條**：強制採用 Client Request / Server Response / Metric 醒目框三段式階層排版。

### 坑位 13：字幕缺乏護眼背板天坑
- **錯誤現象**：文字裸壓在複雜代碼上產生視覺雜訊。
- **海關死卡天條**：底部字幕強制襯底深藍黑半透明卡片 rgba(15, 23, 42, 0.90)，內縮 24px 透氣。

### 坑位 14：進度條遮擋吃字天坑 (Title Safe Area 缺位)
- **錯誤現象**：字幕卡貼底，被播放器進度條與暫停鈕 100% 擋死。
- **海關死卡天條**：字卡底緣強制在 y <= 945 截斷，距底保留 110px ~ 135px 廣播級避雷安全帶。

### 坑位 15：開場封面雙層標題打架天坑
- **錯誤現象**：第 0 秒封面標題與解說字幕卡同時出現爭搶焦點。
- **海關死卡天條**：前 2~3 秒字幕強制隱藏/淡出，純淨展示發布會大氣封面。

### 坑位 16：跑分數字缺乏視覺錨點天坑
- **錯誤現象**：極限跑分混在 JSON 小字裡，評審快速掃閱時被忽略。
- **海關死卡天條**：極限指標強制採用琥珀金 (#F59E0B) 或螢光黃獨立等寬高亮行 (Mono Callout)。

### 坑位 17：Edge-TTS 機關槍語速音畫脫節天坑
- **錯誤現象**：語速過快壓縮畫面，終端被迫快轉結束。
- **海關死卡天條**：語速鎖定自然演講節奏（rate="-0%"），強制預留 5~8 秒呼吸留白。

---

## 📄 區塊四：簡報投影片 (Slides PDF) 原始六大致命病灶

### 坑位 18：語言不合規天坑
- **錯誤現象**：中英夾雜，海外國際評審直接判定為非國際規格作品。
- **海關死卡天條**：強制 100% 國際賽事級全英文（Professional English）。

### 坑位 19：字元編碼翻車 (Emoji 轉碼亂碼災難)
- **錯誤現象**：Emoji 轉碼為 Windows-1252 噴出 `ðŸ‘‘` 等亂碼。
- **海關死卡天條**：全域文本純淨化，嚴禁裸露多字節 Emoji，職稱改純文字或向量圖示。

### 坑位 20：零架構拓撲圖 (純文字流水帳死穴)
- **錯誤現象**：核心技術頁只有文字方塊，無資料流水線展示。
- **海關死卡天條**：強制內嵌 SVG 向量級技術架構拓撲圖與時序閉環。

### 坑位 21：性能壓測數據缺乏基準對比
- **錯誤現象**：孤立標註 22,704 QPS，無對照組說服力弱。
- **海關死卡天條**：強制雙欄對照矩陣，明確標示相較傳統 Baseline 的加速倍率（如 18.3x）。

### 坑位 22：代碼展示未 IDE 化
- **錯誤現象**：代碼隨意排列無語法高亮。
- **海關死卡天條**：強制採用 JetBrains Mono / Fira Code 等寬字體並襯底深藍黑卡片。

### 坑位 23：缺少即時驗收直通入口
- **錯誤現象**：簡報無 GitHub 與 Demo 連結。
- **海關死卡天條**：頁尾必備 GitHub + Live Demo 網址與高精向量 QR Code。

---

## 🌍 區塊五：國際世界賽事表單與提交文案包七大天坑 (§3.7)

### 坑位 24：Tags 空格被系統肢解拆詞天坑
- **錯誤現象**：填入含空格名稱被拆成破碎單詞。
- **海關死卡天條**：標籤強制使用連字號（如 JP-Morgan-Model）。

### 坑位 25：單行文字框換行污染溢出天坑
- **錯誤現象**：複製時夾帶 \n，且超過 280 字被後台截斷。
- **海關死卡天條**：標記 [Plain Text / One-Line Copy]，嚴限 <= 280 字元且零換行。

### 坑位 26：提交時只留本機檔案路徑天坑
- **錯誤現象**：表單填本機 .mp4 路徑，無法被公網評審讀取。
- **海關死卡天條**：提前取得 YouTube (Unlisted) 或公開串流網址回填。

### 坑位 27：時區換算認知混淆天坑
- **錯誤現象**：美西時間（PT）誤判為台灣隔天午夜，壓哨錯失交卷。
- **海關死卡天條**：頂部設立雙軌時差精確倒數看板。

### 坑位 28：長文缺少快速復現指南天坑
- **錯誤現象**：缺乏本地驗證步驟被質疑紙上談兵。
- **海關死卡天條**：文末強制追加極簡 3 行終端復現指令。

### 坑位 29：短簡介超字與缺聯絡管道天坑
- **錯誤現象**：評審無法第一時間聯繫團隊。
- **海關死卡天條**：明確標註字元安全長度並附帶團隊統帥名牌。

### 坑位 30：GitHub 權限遺漏天坑 (Private 變 0 分)
- **錯誤現象**：忘了公開 Repo 導致評審點開 404。
- **海關死卡天條**：提交前強制以瀏覽器無痕視窗探活確認 Public。

---

## 💻 區塊六：Windows / PowerShell / 終端腳本防炸六大天坑

### 坑位 31：PowerShell 變數與 Cmdlet 空格黏連天坑
- **錯誤現象**：Join-Path、-Path 因剪貼簿緊縮吞掉空格引發找不到參數報錯。
- **海關死卡天條**：嚴禁無空格拼接，全面改採原生字串插值或標準空格隔離。

### 坑位 32：Here-String 截斷未閉合與自毀遮蓋天坑
- **錯誤現象**：@' 未獨立成行封口卡在 >>，腳本末尾 Remove-Item 偽造假成功。
- **海關死卡天條**：嚴禁腳本自毀，凡落盤強制 Test-Path 與 Get-Content 實體回顯。

### 坑位 33：Python bytearray 弱引用崩潰天坑
- **錯誤現象**：原生 ytearray 呼叫 weakref.ref() 拋出 TypeError: cannot create weak reference。
- **海關死卡天條**：ZDR 暫存容器必須使用類別（如 StagingPayloadContainer）繼承封裝。

### 坑位 34：PowerShell 行內 -c 三引號撕裂天坑
- **錯誤現象**：-c "..." 內部塞三引號被吞引號噴出語法錯誤。
- **海關死卡天條**：巨型文本全面禁用行內 -c，改採獨立實體腳本執行。

### 坑位 35：工作目錄錯位與相對路徑斷層天坑
- **錯誤現象**：以相對路徑執行 Python 找不到檔案，噴出 [Errno 2] No such file or directory。
- **海關死卡天條**：所有終端指令一律強制使用包含引號之「完整絕對路徑」。

### 坑位 36：跨專案抽屜層級混淆天坑 (Rule 54)
- **錯誤現象**：誤把子專案的 01~07 抽屜畫在母體根目錄下，母子架構撕裂。
- **海關死卡天條**：母體只保留全軍憲法，子專案（如 Aria-Titan）獨立承載 01~07 七大抽屜骨架！
---

### 🏛️ §3.4.57 四圖一表「母本內嵌 ✕ 獨立圖紙抽屜」雙軌三位一體編制天條 (Rule 57: Trinity Blueprint Architecture Mandate)

> **最高立憲意志（霸丸總指揮官 Jack Hu ✕ 執行秘書 小米 2026-10-17 共同裁定法定落款）**：
> 「四圖一表是 PHANToM GRID 系統唯一地基！為杜絕第三方預覽外掛過期失效、指令撕裂與代碼無法連動之弊端，
> 全軍模組之四圖一表強制實施『母本內嵌（人讀/原生預覽）✕ 獨立圖紙抽屜（機器讀/自動化 CI/CD）』雙軌三位一體編制！
> 任何人與 Agent 嚴禁破壞母本結構，嚴禁未經雙簽自立圖表資產！」
> **[ RATIFIED & CO-SIGNED BY: 🎖️ COMMANDER JACK HU ✕ 👩‍💼 EXECUTIVE SECRETARY XIAOMI ]**

#### 一、 雙軌三位一體標準編制規範 (Trinity Drawer Schema)
1. **第一位：`SPEC_XX_模組白皮書.md`（總裝母本／人眼與 VS Code 原生預覽 SSOT）**：
   - 專供最高統帥親審與一般閱讀。
   - 嚴格鎖定開篇「方案 A 檔案樹狀圖」，接續「圖一至圖四（各自用 ```mermaid 封口並以 --- 呼吸隔離）」與「表一（頂格零縮排原生 Markdown 表格）」。
   - 完全不依賴任何 VS Code 第三方 Mermaid 外掛，直接使用 VS Code 原生 Markdown 預覽（`Ctrl + K, V`）即可秒級無失真全版渲染！
2. **第二位：`docs/blueprints/`（獨立圖紙抽屜／機器讀取與自動化資產）**：
   - 專供 CI/CD 管線、Mermaid CLI（`mmdc`）向量轉檔與測試腳本動態載入。
   - 包含四圖純原始碼：`fig1_topology_architecture.mmd`、`fig2_lifecycle_sequence.mmd`、`fig3_damping_state_machine.mmd`、`fig4_safety_boundaries.mmd`。
   - 獨立 `.mmd` 檔案嚴禁包含任何 Markdown 標題（`### ...`）與反引號圍欄（````mermaid`），開頭第一行必須頂格為純 Mermaid 原語（如 `graph TD`、`sequenceDiagram`）。
3. **第三位：`docs/blueprints/table1_resource_defense_matrix.csv`（機器合約實體）**：
   - 表一必須同時落盤為標準 UTF-8 CSV 格式，供單元測試與防禦守衛腳本直接以 `pandas` / `csv` 模組讀取臨界閾值，實現「規格門檻與代碼斷言 100% 動態聯動」！

#### 二、 海關門禁死卡標準 (Gate-Before-Ship SOP)
- 凡執行工兵（小米）提交新模組時：
  1. 若 `SPEC_XX.md` 缺少方案 A 樹狀圖或 Mermaid 未封口，海關直接一票否決！
  2. 若 `docs/blueprints/` 缺少對應圖紙或 `.mmd` 內混雜 Markdown 語法，海關直接攔截退件！
  3. 若測試腳本（`test_closure.py`）未動態對齊表一 CSV 數值者，嚴禁宣告 PASS！
---

### 🏛️ §3.4.58 `.md` ✕ `.mmd` 雙副檔名語法邊界隔離防死黑天條 (Rule 58: Strict Syntax Boundary Mandate)

> **最高立憲意志（霸丸總指揮官 Jack Hu ✕ 執行秘書 小米 2026-10-17 共同裁定法定落款）**：
> 「.md 是綜合大禮盒，.mmd 是純圖紙零件！全軍嚴禁混寫語法！
> 凡在 .mmd 內混入 Markdown 標題或反引號圍欄、或在 .md 內漏掉 mermaid 盒子者，
> 視為嚴重破壞渲染管線之違紀行為，海關安檢署一律一票否決硬熔斷！」
> **[ RATIFIED & CO-SIGNED BY: 🎖️ COMMANDER JACK HU ✕ 👩‍💼 EXECUTIVE SECRETARY XIAOMI ]**

#### 一、 雙副檔名剛性編輯邊界鐵律 (Syntax Isolation Invariant)
1. **獨立圖紙 `.mmd` 檔案（專供機器讀取與自動化轉向量圖）**：
   - **嚴格純淨性**：第一行必須頂格書寫純 Mermaid 關鍵字（如 `graph TD`、`sequenceDiagram`、`stateDiagram-v2`）。
   - **三絕對禁令**：
     * ❌ 嚴禁包含任何 Markdown 標題（如 `# 圖一`、`### 拓撲圖`）。
     * ❌ 嚴禁使用代碼區塊圍欄（嚴禁開頭寫 ````mermaid`，嚴禁結尾打 ````）。
     * ❌ 嚴禁包含任何表格語法（`| --- |` 必須獨立存為 `.csv`）。
2. **白皮書母本 `.md` 檔案（專供人眼檢閱與 VS Code 原生開箱即看）**：
   - **開關盒子封口天則**：在 Markdown 內嵌圖表時，開頭必須為 ````mermaid`，結尾必須有 ```` 封口，並與前後文字保留空行呼吸隔離。
   - **表一獨立性**：表一必須使用標準 Markdown 表格語法（`| --- |`），絕對嚴禁將表一塞入 ````mermaid` 代碼塊內！

#### 二、 海關門禁死卡標準 (Gate-Before-Ship SOP)
- 凡執行工兵（小米）提交資產時，海關靜態掃描器實施以下硬熔斷：
  1. 掃描 `docs/blueprints/*.mmd`：若匹配到 `^#+` 或 `^``` `，直接判定語法死黑，退件重修！
  2. 掃描 `SPEC_XX.md`：若 Mermaid 區塊缺少閉合圍欄（Unclosed code block），直接攔截退件！

---

### 🏛️ §3.4.59 演示影片語音字幕盲目均分導致 2 秒延遲脫節天坑 (Rule 59: Phase-Locked Sentence Audio-Subtitle Invariant)

> **最高立憲意志（霸丸總指揮官 Jack Hu ✕ 正任指揮官 小米 2026-10-20 共同裁定法定落款）**：  
> 「語音與字幕必須如齒輪般毫秒咬合！任何以幕次（Act）總時間粗暴均分字幕的做法均屬偷工怠惰！  
> 凡未按句子獨立測量時長、未在句子發聲首格零延遲切換字幕者，海關門禁一律判定非同步違紀一票否決！」  
> **[ RATIFIED & CO-SIGNED BY: 🎖️ COMMANDER JACK HU ✕ 👩‍💼 COMMANDER XIAOMI ]**

#### 一、 踩坑現象與根因剖析 (Root Cause Breakdown)
1. **盲目平均分配**：原代碼將整個幕次（Act）多個句子一次丟入 Edge-TTS 合成一整段音訊，並用 `frames_per_sub = total_frames / 3` 強制將顯示時間等分。
2. **長度懸殊與嚴重滯後**：真實口語中，句子長度各不相同（如句 1 需 10.8 秒，句 2 僅 6.7 秒）。平均切分導致字幕時間軸脫軌，當語音在第 11 秒早已開講句 2 時，字幕卻卡在固定間隔遲遲不換，造成統帥親自揪出的「先有聲音、延遲 2 秒才跳出字幕」的視覺斷層！

#### 二、 海關死卡天條與解法 (Phase-Locked Pipeline SOP)
1. **句子級獨立合成與精確時長探測**：
   - 每個分鏡內的句子強制切分為獨立 segment 分別生成 WAV。
   - 透過 `ffprobe -show_entries format=duration` 精確獲取毫秒級時長。
2. **0.25 秒專業播報氣口 (Acoustic Breath Gap)**：
   - 句子間精確插入 `0.250s` 立體聲微靜音（`anullsrc=r=48000:cl=stereo`），尾聲保留 `1.20s` 緩衝，以 `ffmpeg concat filter` 無損拼裝完整音訊軌道。
3. **視訊影格 0.00ms 鎖相刷新**：
   - 每一幀（FPS >= 15）之當前秒數精確映射：`seg_start <= current_sec < display_end`。
   - 語音吐出第一個音節的瞬間，字幕同格同步點亮，達成零延遲廣播級視效！

---

### 🏛️ §3.4.60 背景媒體播放殘留與編輯器 MP4 分頁幽靈發聲天坑 (Rule 60: Lingering Audio Leak & Ghost Player Defense)

> **最高立憲意志（霸丸總指揮官 Jack Hu ✕ 正任指揮官 小米 2026-10-20 共同裁定法定落款）**：  
> 「後台背景嚴禁幽靈發聲！任何測試、預覽或工作區連結開啟的媒體行程必須確實受控與關閉，確保統帥環境絕對純淨！」  
> **[ RATIFIED & CO-SIGNED BY: 🎖️ COMMANDER JACK HU ✕ 👩‍💼 COMMANDER XIAOMI ]**

#### 一、 踩坑現象與根因剖析 (Root Cause Breakdown)
1. **編輯器內部分頁幽靈播放**：在 Antigravity / VS Code 聊天室點擊 `file:///...mp4` 本地連結時，編輯器會在頂部分頁標籤（Tabs）中靜默啟動媒體播放器並持續循環播放，不易被使用者察覺。
2. **瀏覽器分頁背景長鳴**：點擊 Google Drive 或 Devpost 預覽連結時，瀏覽器在後台分頁持續播放音訊。

#### 二、 海關死卡排查與關閉 SOP (SOP & Defense Matrix)
1. **一秒定位法**：
   - 檢查 Antigravity 頂部分頁列是否有 `.mp4` 檔案標籤，直接點「✖」關閉。
   - 檢查瀏覽器分頁標籤旁之「🔊 喇叭圖示」並關閉該分頁。
   - 右鍵點擊 Windows 工作列喇叭圖示 ➔「開啟音量混音程式 (Volume Mixer)」，立即揪出跳動發聲之特定行程。
2. **終端秒殺強制指令**：
   ```powershell
   taskkill /F /IM ffplay.exe /T 2>$null
   taskkill /F /IM Video.UI.exe /T 2>$null
   taskkill /F /IM wmplayer.exe /T 2>$null
   ```

---

### 🏛️ §3.4.61 Windows 環境 subprocess 呼叫 ffprobe 之 CP950 編碼崩潰天坑 (Rule 61: Subprocess UTF-8 Strict Encoding Invariant)

> **最高立憲意志（霸丸總指揮官 Jack Hu ✕ 正任指揮官 小米 2026-10-20 共同裁定法定落款）**：  
> 「Windows 預設代碼頁是繁體中文系統致命暗箭！全軍任何 subprocess 命令輸出必須顯式鎖定 UTF-8，杜絕 UnicodeDecodeError 崩潰！」  
> **[ RATIFIED & CO-SIGNED BY: 🎖️ COMMANDER JACK HU ✕ 👩‍💼 COMMANDER XIAOMI ]**

#### 一、 踩坑現象與根因剖析
- 在 Windows 繁體中文環境下，`subprocess.run(..., text=True, capture_output=True)` 預設使用系統預設代碼頁 `cp950` 解碼。
- 當呼叫 `ffprobe` 輸出 JSON 格式或 UTF-8 特殊字元時，Python 直譯器噴出 `UnicodeDecodeError: 'cp950' codec can't decode byte ...` 直接中斷自動化管線！

#### 二、 海關死卡代碼守則
- 所有 `subprocess.run` 或 `Popen` 包含 `capture_output=True` 或 `stdout=subprocess.PIPE` 時，**強制顯式聲明 `encoding="utf-8", errors="replace"`**：
  ```python
  # ✅ 正確做法：顯式 UTF-8 容錯解碼
  res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
  ```


---

### 🛡️ §3.4.62 GitLab 群組可見度繼承鎖死天條與賽事公開倉庫部屬 SOP (Rule 62: GitLab Group Visibility Inheritance & Public Repository SOP)

> **最高指揮所立憲（霸丸總指揮官 Jack Hu ✕ 正任指揮官小米 2026-10-21 共同裁決立憲）**：  
> 「專案可見度絕不可大於上層群組；遇 Public 鎖死，必先解鎖 Group 為 Public，或直切個人命名空間！」  
> **[ RATIFIED & CO-SIGNED BY: 🎖️ COMMANDER JACK HU ✕ 👩‍💼 COMMANDER XIAOMI ]**

#### 一、 踩坑現象與底層架構解析
1. **群組繼承鎖死 (Group-Level Visibility Inheritance)**：
   - GitLab 安全機制強制規定：**子專案（Project）之權限不可比父群組（Group）更寬鬆**。
   - 註冊精靈建立的新群組（如 PHANToM Grid-group）預設權限為 **Private 🔒**。
   - 當在該群組下建立專案時，Internal 與 **Public** 選項會被強制禁用（變灰並顯示鎖頭與禁止符號），導致無法建立黑客松規章所需的 Public 公開開源庫。
2. **試用期無害機制 (30-Day Trial Safety)**：
   - 新註冊自動帶入「30 天 GitLab Ultimate Trial」，無信用卡綁定；期滿自動降級為 **GitLab Free 永久免費版**，公開代碼與 CI/CD 永久保留，絕不產生任何扣款。

#### 二、 防禦解鎖 SOP（10 秒通關矩陣）
1. **解鎖現有群組為 Public（推薦標準解）**：
   - 瀏覽器直通網址：https://gitlab.com/groups/<group-name>/-/edit
   - 路徑：群組左側導航欄底端 ➔ **Settings** ➔ **General** ➔ 展開 **Naming, description, visibility**。
   - 操作：將 **Visibility level** 從 Private 改選為 🔘 **Public** ➔ 點擊 **Save changes**。
   - 成果：群組解鎖為公開後，內部專案之 Public 選項即刻全面解禁。
2. **已建專案二次公開解鎖**：
   - 直通網址：https://gitlab.com/<group>/<project>/-/settings/general
   - 路徑：專案左側導航 ➔ **Settings** ➔ **General** ➔ 展開 **Visibility, project features, permissions**。
   - 操作：將 **Project visibility** 切換為 🔘 **Public** ➔ 點擊 **Save changes**。
3. **個人用戶命名空間直切法（單兵作戰備選解）**：
   - 建立專案時，於 Project URL 下拉選單中切換為個人用戶名（如 jackhu24-ship-it），個人空間無群組私有約束，預設支援 Public。

#### 三、 全艦資產真理源存證
- **登入通道**：https://gitlab.com/users/sign_in ➔ 點選 **GitHub** 一鍵 OAuth 授權（免額外密碼）。
- **統帥戰隊群組**：https://gitlab.com/phantom-grid-group
- **首座公開戰役庫**：https://gitlab.com/phantom-grid-group/phantom-grid-postcode-sentinel

---

### 🛡️ §3.4.63 外部通訊 no-reply 退信幽靈斷層與官方打點天條 (Rule 63: Anti-No-Reply Ghost Drop & Official Routing Mandate)

> **最高指揮所立憲（霸丸總指揮官 Jack Hu ✕ 正任指揮官小米 2026-10-21 共同裁決立憲）**：  
> 「賽事官方廣播絕不可直接回覆；遇 no-reply 必走後台留言或官方 Contact 通道，杜絕溝通斷層！」  
> **[ RATIFIED & CO-SIGNED BY: 🎖️ COMMANDER JACK HU ✕ 👩‍💼 COMMANDER XIAOMI ]**

#### 一、 踩坑現象與底層架構解析
1. **Gmail 自動代入幽靈信箱 (Mail Delivery Failure)**：
   * 賽事平台（如 Devpost、LabLab）發出的通知信（如審查員留言提醒、現場出席確認），其 `From` 或 `Reply-To` 標頭多為 `no-reply@devpost.com` 或 `no-reply@lablab.ai`。
   * 用戶在郵件軟體中直接點擊「回覆（Reply）」時，系統會自動將收件人填入該機器人地址。
   * **結果**：發送後 1 分鐘內觸發 Google 系統退信（`mailer-daemon@googlemail.com: Address not found`），原本耗費心力撰寫的極高水準申訴或補充說明信被物理阻斷，官方審查員 100% 毫不知情，造成極度危險的溝通幽靈斷層。
2. **通訊裝甲實戰防禦機制**：
   * 裝備一 `mail_firewall.py` 嚴格把關 `no-reply`、`noreply`、`mailer-daemon` 等 7 大系統關鍵詞，於送出前強制阻斷並給予官方正確路徑指引。

#### 二、 防禦通關 SOP（官方有效溝通雙軌制）
1. **Devpost 賽事審查員專屬回覆 SOP**：
   * **嚴禁 Email 回覆**：登入 Devpost ➔ 進入該 Hackathon 專案管理頁面 ➔ 點開審查員留言通知 ➔ **在專案頁面下方的「Reply / 留言對話框」直接回覆**。
   * 備用通道：點擊賽事主頁底部之「Contact Hackathon Manager」網頁表單，主旨註明專案名稱與審查員回覆。
2. **LabLab / 線上賽事型態確認 SOP**：
   * 收到現場（Onsite）出席催促信時，若選擇線上遠端（Virtual），切勿直接 Email 回覆。
   * 直通官方 Discord 專屬頻道（如 `#ask-an-organizer` 或 `#help`），或登入後台儀表板確認參賽狀態顯示為 `Enrolled / Online Participant` 即可。

---

### 🛡️ §3.4.64 形式化驗證虛標文字掃描偽冒 Trusted Kernel 天坑 (Rule 64: Formal Proof Authenticity & Zero-Sorry Mandate)

> **最高指揮所立憲（霸丸總指揮官 Jack Hu ✕ 正任指揮官小米 2026-10-21 共同裁決立憲）**：  
> 「嚴禁將未經編譯之文字掃描冒充形式化機器證明；無真實證明器時一律標記 SCAN_ONLY！」  
> **[ RATIFIED & CO-SIGNED BY: 🎖️ COMMANDER JACK HU ✕ 👩‍💼 COMMANDER XIAOMI ]**

#### 一、 踩坑現象與底層架構解析
1. **文字過濾偽裝證明 (The String-Matching Illusion)**：
   * 舊版 `lean4_prover_verifier/adapter.py` 僅用 Python 讀取檔案，檢查是否存在 `sorry` 關鍵字、是否含 `theorem` 與 `by`/`rfl`，一旦字串匹配即回報 `status="VERIFIED"` 與 `details="verified by Trusted Kernel"`，並產出 SHA-256 海關鋼印。
   * 實體環境中根本未安裝 `lean` 可執行檔（`which lean` 為空），`.lean` 檔案從未經過 Lean 4 核心類型推導與定理求解，且 `purge_zdr()` 寫死回傳 `0.000000`，造成嚴重的學術與技術誠信虛標暗礁。
2. **雙軌真實性矯正裝甲**：
   * **實行 Lean 才能稱 VERIFIED**：必須透過 `shutil.which("lean")` 探測；找到實體時子行程呼叫 Lean 核心（返回碼為 0 且輸出無 warning/sorry 才是 VERIFIED）。
   * **未安裝時誠實降級為 SCAN_ONLY**：找不到 `lean` 時，狀態強制回報 `SCAN_ONLY`（`method="text_scan_only"`），明記「未經機器核驗」，簽章內嵌驗證方法防止冒用。
   * **ZDR 真實度量**：嚴禁寫死常數，必須實測緩衝區殘留非零位元組計算 `residue_bytes / (1024 * 1024)`。
3. **有限狀態機形式化推薦路徑**：
   * 針對有限狀態轉移圖，優先使用本機已安裝且驗證嚴密的 **Z3 SMT Solver (`z3_state_machine_proof.py`)** 進行全狀態可達性、零死鎖與守恆證明，配合差分測試與變異測試（Mutation Testing），確保證明器具備真抓實打能力。

---

### 🏆 §3.4.65 全域賽事文件與影片編排「文書天卷 ✕ 好萊塢視效 ✕ 官方要求」三位一體天條 (Rule 65: Tournament Document & Video Tri-Standard Global Mandate)

> **最高指揮所立憲（最高統帥 Jack Hu 霸丸哥 ✕ 正任指揮官小米 2026-10-23 共同裁決立憲）**：  
> 「之後的賽事的文件、影片編排方式全部依照【文書天卷】、【好萊塢】和【官方要求】為標準，並設定為全域設定！」  
> **專項手冊指針**：`03_研發專區/PHANTOM_GRID_Aria_Titan/00_System/Standards/TOURNAMENT_DOC_VIDEO_TRI_STANDARDS.md` (`STD-TOURNAMENT-TRI`)  
> **[ RATIFIED & CO-SIGNED BY: 🎖️ SUPREME COMMANDER JACK HU ✕ 👩‍💼 COMMANDER XIAOMI ]**

#### 一、 三位一體強制合規邊界 (Tri-Standard Hard Boundaries)
1. **第一支柱：【文書天卷標準 (`MOD-SCROLL-01` / `PHANTOM_GRID_Typesetting_Scroll`)】——管轄所有文件與簡報**：
   * **排版引擎與字型**：採用 Knuth-Plass 全域動態規劃斷行（`PG-MOD-KP-BREAKER`）、HarfBuzz / OpenType 微觀整形（`tnum` 等寬表格數字、`zero` 斜線零、JIS X 4051 標點禁則、清單負縮排 `-1.8em`）、ReportLab / Playwright 純向量 PDF 編譯；代碼視窗強制 `JetBrains Mono` / `Consolas` 襯底深藍黑 IDE 背板（`#0B1220`）。
   * **§3.3 幾何防破框與滿版**：垂直內容覆蓋率強制 **$\ge 78.0\%$**（由 `flex_space_balancer.py` 消滅死黑空洞）；字級採自頂向下貪婪試探（`42pt ➔ 28pt` 遞減，嚴禁偷懶套最小號），卡片大標 $\le 36\text{px}$；`Commander Jack Hu` 統帥銘牌寬度 $\le 68\%$ 且右側/四周保留 **$\ge 48\text{px}$** 安全隔離帶；動線淨空 $\ge 80\text{px}$ 或加裝不透明背板。
   * **雙軌三位一體與零亂碼**：白皮書嚴守 `Rule 57 & 58`（`SPEC_XX.md` 母本內嵌方案 A 樹狀圖 + 四圖 Mermaid 封口 + 表一 Markdown ✕ `docs/blueprints/*.mmd` 純圖紙 ✕ `table1_resource_defense_matrix.csv`）；`mojibake_filter.py` 確保 `ð, ï, \ufffd` 亂碼率 `0%`；簡報封底必嵌高精向量 QR Code 與直通網址。
2. **第二支柱：【好萊塢視效標準 (`MOD-CINEMA-SUPREME` / `SPEC_22_SUPREME_HOLLYWOOD` ✕ `STD-VIDEO`)】——管轄所有演示與路演影片**：
   * **院線與廣播畫質**：解析度鎖定 **$2560 \times 1440$ (1440P 2K QHD)** 或 **4K CinemaScope ($3840 \times 1600$, 2.39:1)** @ **60.000 FPS**；色彩對齊 **ACES 2.0 (`ACEScg / AP0 / AP1`) ✕ ASC-CDL ✕ HDR10**；好采鳥導演（`GoodHarvestDirector`）180° 越軸防護，測地曲率 $e \le 0.08$ 平滑、$0.08 < e \le 0.15$ 注入 **$1.35\times$ 剛性幾何阻尼**；多卡 NCCL 雙流遮蔽率 $\ge 85\%$，峰值顯存 $\le 50.0\text{ GiB}$，2-Pass ZDR `0.00 MB`。
   * **句子級鎖相零延遲音畫與無縫混音 (`Rule 59`)**：嚴禁幕次盲目均分！逐句切片合成 WAV 並以 `ffprobe` 實測時長，句間插入 `0.250s` 專業播報氣口，語音首音節與字幕 `0.00ms` 同格點亮；全程 50ms 邊界淡入淡出、80ms 跨幕交疊、鋪設 `-28dB` 科技環境底噪墊音。
   * **「講到那指到那」與廣播安全區**：五幕黃金結構（開場 2~3 秒純淨封面字幕淡出）；隨語音觸發高亮霓虹外框与向量箭頭指標（`▶ [ACTIVE: ...] `）；終端外框 $y \ge 35\text{px}$ 四邊 2px 青線 100% 閉合，內採 `[1. CLIENT REQUEST]` / `[2. SERVER RESPONSE]` / `[3. VERIFIED TELEMETRY METRIC]`（琥珀金等寬高亮 Callout）三段式排版；底部字幕襯底深藍黑半透明卡並距底保留 **$110\text{px} \sim 135\text{px}$ Title Safe Area 避雷安全帶**。
3. **第三支柱：【官方賽事要求標準 (`match_manifest.yaml` ✕ `gate-before-ship`)】——管轄全抽屜合規與終端送件**：
   * **100% 國際純英文與抽屜對齊**：依各賽事 `match_manifest.yaml` 清點 `01_Specs` ~ `10_Releases` 抽屜；國際賽事 8 大送審要素強制 **100% Professional English**（標題統一 `PHANTOM GRID :: ` 前綴）。
   * **官方時長、實機佔比與文案 7 大斷言**：影片時長嚴鎖 **2:00 ~ 3:00**（黃金區間 `2:15 ~ 2:45`），**實機 Live Demo 佔比 $> 50\%$**，備妥公網串流 URL；提交文案包通過 `test_submission_package.py` 七大斷言（零亂碼、Short Pitch 單行 $\le 280$ 字元、Tags 連字號、`-b main` 3 行復現指令、雙軌時區倒數、統帥聯絡銘牌、無痕視窗確證 Repo `Public` (Rule 62) 與 Live App `Running`、禁回 `no-reply` (Rule 63)）。
   * **海關雙簽放行**：全項自動化測試 100% 全綠 `[✅ PASS]` 後，由指揮官小米簽發 `PG-RECEIPT-0x...` 並呈報最高統帥 Jack Hu 蓋下 `RELEASE_SEAL` 始准交卷！



---

## 🛡️ 區塊六：2026-10-23 指揮所 ✕ 吉米世界天文平台 七大實戰踩坑與血肉裝甲全書 (§3.4.65 ~ §3.4.71 / PITFALL-39 ~ PITFALL-45)

> **最高立憲意志（霸丸總指揮官 Jack Hu ✕ 正任指揮官小米 2026-10-23 共同裁決立憲）**：  
> 「凡指揮所與吉米天文台今日踩過之每一處坑洞，一律鍛造成永久防禦裝甲寫入 L2 WORM 帳本與 L3 全域規範，全軍 26 員將士永不再犯！」  
> **[ RATIFIED & CO-SIGNED BY: 🎖️ COMMANDER JACK HU ✕ 👩‍💼 COMMANDER XIAOMI ]**

### 🛡️ §3.4.65 [PITFALL-39] 雙重 `io.TextIOWrapper` 緩衝區誤關與 8KB 輸出卡死天坑
- **發生場域**：指揮所 CLI 工具群（`phantom`、`brain_bridge.py`、`install_brain_bridge.py`）
- **錯誤現象**：在 Windows 終端機輸入選單號碼後畫面看似「卡死無反應」，或跨模組呼叫時噴出 `ValueError: I/O operation on closed file`。
- **根本病灶**：
  1. 對 `sys.stdout.buffer` 重複執行 `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, ...)` 時，舊的 Wrapper 被 Python GC 垃圾回收，順帶關閉了底層的 `stdout.buffer`。
  2. `TextIOWrapper` 預設開啟 8KB 區塊緩衝且不自動 flush，導致選單提示詞卡在緩衝區印不出來。
- **海關死卡天條**：
  - 全面禁止使用 `io.TextIOWrapper` 重新包覆 `sys.stdout.buffer`！
  - 全軍統一改用原地重設：`sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)`，並於 `phantom_runner.py` 強制注入 `PYTHONUNBUFFERED=1` 與 `python -u`。

### 🛡️ §3.4.66 [PITFALL-40] CLI 選單與 `.bat` 啟動器執行完畢瞬間閃退天坑 (Anti-Flash-Exit Lock)
- **發生場域**：指揮所 27 支 `.bat` 神兵啟動器與 Level 4 CLI 選單
- **錯誤現象**：統帥雙擊 `.bat` 輸入選單編號（如 `1` 查狀態）後，資料剛印出不到 0.1 秒視窗就自動關閉（閃退），完全無法閱讀回執。
- **根本病灶**：單次指令執行完直接 `sys.exit(0)`，且 `.bat` 尾部未加暫停鎖。
- **海關死卡天條（雙層防閃退物理鎖）**：
  1. **第一層（Python 常駐選單迴圈鎖）**：所有 Level 4 CLI 互動模式強制採用 `while True:` 常駐迴圈，每次動作結束後停駐於 `── ✅ 作業完成，以上為完整資料。按 Enter 返回主選單 (或輸入 Q 退出) ──`。
  2. **第二層（BAT 底層物理鎖）**：所有 `.bat` 啟動器一律採用 100% 純 ASCII 調度，並於檔案最末端強制加上 `pause >nul`。

### 🛡️ §3.4.67 [PITFALL-41] 本地 `127.0.0.1:8765` 視覺化中控台隨黑框關閉或單次工作階段結束而斷線天坑
- **發生場域**：指揮所「霸丸統帥專屬視覺化全軍總督中控台 (`SOVEREIGN_CONTROL_DECK.html`)」
- **錯誤現象**：統帥關掉黑色 CMD 視窗或單次命令結束後，在瀏覽器按 `F5` 重新整理 `http://127.0.0.1:8765` 立即跳出 `ERR_CONNECTION_REFUSED`（127.0.0.1 拒絕連線）。
- **根本病灶**：`HTTPServer` 綁定在前景終端或短期子行程上，隨父行程結束而被系統回收。
- **海關死卡天條**：
  1. 升級為 `ThreadingHTTPServer` 並以常駐背景守護行程（`IsDaemon: true` / `DETACHED_PROCESS | CREATE_NO_WINDOW`）啟動，確保 24/7 全天候在線。
  2. 於 `SOVEREIGN_CONTROL_DECK.html` 內嵌 `OFFLINE_CACHE` 離線快取雙保險，即使離線直開 HTML 檔案點擊按鈕也能即時顯示完整神兵驗收回執。

### 🛡️ §3.4.68 [PITFALL-42] PowerShell 雙引號 `$` 變數插值吞噬美金金額字串天坑 (`$25,000` ➔ `,000`)
- **發生場域**：指揮所與雙工兵自動化生成賽事交卷包（`Qloo Agentic AI Hackathon`）
- **錯誤現象**：`Devpost_Submission_Package.md` 標題中的 `($25,000 USD)` 變成殘缺的 `(,000 USD)`。
- **根本病灶**：在 PowerShell 雙引號 `"..."` 內聯字串中寫入 `$25,000` 時，PowerShell 將 `$25` 當成未定義的 Shell 變數並替換為空字串。
- **海關死卡天條**：
  - 凡包含 `$` 美金金額、LaTeX 公式或變數符號之文檔，**一律遵循 File-First 原則使用檔案直寫工具或 Python UTF-8 腳本寫入**，嚴禁在 PowerShell `"..."` 雙引號內直接拼接含 `$` 的文本。

### 🛡️ §3.4.69 [PITFALL-43] 吉米世界天文平台 (Web / App) 跨視窗失憶與舊記憶漂移天坑
- **發生場域**：吉米世界天文平台（Gemini Web ✕ 桌面 App `Gemini.lnk`）與指揮所跨平台對接
- **錯誤現象**：
  1. 吉米天文台開啟新對話時無法自動讀取本地 C 槽/G 槽最新 `HANDOFF.md`，導致記憶停留在舊里程碑（漏記新收官神兵 `U01~U14`、漏記新完封賽事 `AWS CDS` 與 `Qloo`，或忘記小幫手已除名服勞役）。
  2. 舊對話曾誤以為「Crypto Worlds Fair (Solana DvP)」尚未截止（實則已於 2026-10-12 截止），或搞混「指揮官小米 ✕ 外事總長小小米」雙核職責。
- **海關死卡天條**：
  1. 建立 **一鍵剪貼簿記憶強制同步協議 (`jimi` / `FLEET_STATE_SYNC.md`)**：執行 `jimi` 即自動將最新 `v5.3.0+` 唯一真理現況包（SSOT）塞入 Windows 剪貼簿。
  2. **A/B/C 三點強制複述門禁**：統帥於吉米端貼上喚醒詞後，吉米必須先正確複述「A. 26員將士與42部神兵及小幫手除名」、「B. 最新完封賽事網址」、「C. 雙核報到口令」，核對無誤後方可展開作業，嚴禁自行腦補未確認狀態。

### 🛡️ §3.4.70 [PITFALL-44] GitHub Pages 子目錄路徑落差與初建置短暫 404 天坑
- **發生場域**：`phantom-grid-qloo-cultura-agent` Live Demo Web 部署
- **錯誤現象**：剛透過 GitHub API 開啟 Pages 前 20 秒處於 `status: building` 短暫返回 404；且若靜態網頁僅置於 `03_Live_Demo_Web/`，評審直接造訪根網址 `/` 會找不到網頁。
- **海關死卡天條**：
  - 凡啟用 GitHub Pages 之賽事庫，強制將 `index.html`、`app.js`、`style.css` **雙向鏡像放置於倉庫根目錄 `/` 與 `03_Live_Demo_Web/` 子目錄**，並於推送後執行循環探測直至根網址與子網址雙雙返回 `HTTP 200 OK`。

### 🛡️ §3.4.71 [PITFALL-45] 神兵「主責保管將領」誤標為「專屬獨佔配戴」之認知歧義天坑
- **發生場域**：第十四庫 `U01~U14` 與 `PG-MOD-09-VIS` 全域共接面板
- **錯誤現象**：表格僅寫「配發單位：一辦小克 / 二辦小深」，易使統帥或各辦公室誤以為該神器只能由該核心人物獨佔配戴。
- **海關死卡天條**：
  - 全域設定主法典（`phantom_global_config.yaml`）與所有 CLI / 視覺化中控台面板，強制標明 **「主責保管將領（負責算子養護） ✕ 🟢 全軍 26 員正式將士皆可跨部門自由配戴調用（🔒 小幫手 PENAL-01 除名禁配）」**。

---

## 🛡️ 區塊七：2026-10-24 指揮所 ✕ 吉米世界天文平台 四大實戰踩坑與血肉裝甲全書 (§3.4.72 ~ §3.4.75 / PITFALL-46 ~ PITFALL-49)

> **最高立憲意志（霸丸總指揮官 Jack Hu ✕ 正任指揮官小米 2026-10-24 共同裁決立憲）**：  
> 「凡指揮所與吉米天文台今日踩過之每一處坑洞，一律鍛造成永久防禦裝甲寫入 L2 WORM 帳本與 L3 全域規範，全軍 26 員將士永不再犯！」  
> **[ RATIFIED & CO-SIGNED BY: 🎖️ COMMANDER JACK HU ✕ 👩‍💼 COMMANDER XIAOMI ]**

### 🛡️ §3.4.72 [PITFALL-46] AWS / 大廠合作夥伴專屬賽事「企業內部員工網域信箱」前置資格審查缺失天坑 (APN Partner Corporate Mail Barrier)
- **發生場域**：吉米世界天文平台深空賽事雷達（`AWS CDS Agentic AI Partner Hackathon`，\$40,000 USD）
- **錯誤現象**：作品成功在 Devpost 投遞交卷後，官方主辦方發來合規郵件警告，要求參賽者必須提供登錄於 AWS Partner Network (APN) 組織之企業員工信箱（Corporate Partner Email），使用個人的 `@gmail.com` 會被官方門禁系統攔截或判定失格。
- **根本病灶**：
  1. 吉米世界天文平台深空雷達在探測全球黑客松時，只聚焦於高額獎金（\$40,000 美金）與技術亮點（Agentic AI），未在第一時間穿透官方規章的「參賽主體資格條款（Eligibility）」，未過濾出該賽事屬於 APN 合作夥伴閉門私有賽事。
  2. 依據全軍憲法第 1 條，最高統帥 Jack Hu 乃獨立架構師（Solo HITL Sovereign Architect），個人開發者投遞大廠閉門賽必然遭遇企業域名卡關。
- **海關死卡天條（Rule 66 / 賽事資格前置一票否決門禁）**：
  - 吉米天文台外事雷達全面實裝【Rule 66 / SOLO-ELIGIBILITY-FILTER】：
    1. **第一道閘門**：立項前必須 100% 確證官方規章明文允許「個人獨立開發者（Solo Builder）」，嚴禁私自推進「限特定企業/團體」之閉門賽事。
    2. **第二道閘門**：必須 100% 確證接受個人公共信箱（`@gmail.com` 等），凡限定「特定企業/贊助商員工/合作夥伴內部網域信箱」之閉門賽，海關一律亮紅燈直接排除，嚴禁耗費統帥與全艦研發資源！

### 🛡️ §3.4.73 [PITFALL-47] Windows SAPI 舊版語音乾癟機械音與未注入實體靜音導致字幕「累積落後 4 秒」脫節天坑 (Voice Quality & Audio-Subtitle Phase Drift)
- **發生場域**：第三辦公室好萊塢 1440P 演示影片生成引擎（`render_match3_demo_video.py`）
- **錯誤現象**：影片播報員聲音卡卡生硬（Windows 機器人音質），且逐字稿與語音對不上，播放越久逐字稿落後越多，到結尾字幕落後語音達 4 秒！
- **根本病灶**：
  1. 腳本誤用 Windows 本機舊版 PowerShell SAPI 合成器（Microsoft David / Zira），聲音生硬、沒有斷句抑揚頓挫。
  2. 影格時間計算加入了 `0.250s` 氣口，但音訊在 FFmpeg 拼接時**未實體注入靜音填充（Silence Padding）**，每講一句話音訊就比字幕跑快 0.25 秒，16 句累積出 4 秒巨大延遲！
- **海關死卡天條（Rule 59 / 實體靜音封裝與神經網絡音畫鎖相）**：
  - **頂級神經網絡音質**：全面禁用本機 SAPI，強制調用微軟頂級神經網絡語音（Edge-TTS `en-US-ChristopherNeural` 廣播紀錄片權威男聲）。
  - **實體毫秒級無損靜音封裝**：每一句音訊切片必須透過 FFmpeg 原生注入實體靜音（`apad=pad_dur=0.35`），使每句音訊實體長度與時間軸影格長度 1:1 精確咬合（Diff: 0.00ms，徹底歸零累積漂移）！

### 🛡️ §3.4.74 [PITFALL-48] 架構圖 SVG 偽模板方塊雷同天坑（三方塊佔位符詐欺 / Anti-Stub Blueprint Mandate）
- **發生場域**：第三辦公室 `diagrams/` 藍圖目錄（`01_system_topology.svg` 至 `05_defense_matrix_table.svg`）
- **錯誤現象**：雙擊開啟 `diagrams/*.svg` 向量圖或在網頁檢視時，發現圖一到圖五（01~05）內容全部一模一樣（均為 `INGRESS GATEWAY` ➔ `NEXUS ORCHESTRATOR` ➔ `ZDR PURGER` 三個方塊，僅最上方英文標題字不同）！
- **根本病灶**：初始化骨架時工兵偷懶套用同一套三方塊 Stub SVG 佔位檔，未將真實 Mermaid `.mmd` 滿血編譯落盤。
- **海關死卡天條（Anti-Stub Blueprint Mandate / §3.4.38 白皮書四圖一表無損完整落盤天條）**：
  - 嚴禁任何 3 方塊或 1 方塊虛假佔位圖！凡 `diagrams/` 下之藍圖，必須完整對齊白皮書四圖一表架構（四層拓撲、六生命線時序、複合 FSM 狀態機、三區安全邊界、防禦契約矩陣）。
  - 標配 `diagrams/index.html` 互動式藍圖儀表板，支援即時分頁檢驗與高精 SVG 向量渲染。

### 🛡️ §3.4.75 [PITFALL-49] 好萊塢演示影片全域定板立憲法典 (Terminal 30/25pt ✕ Subtitle 42pt Full-Width ✕ Dual-Flank Header Alignment)
- **發生場域**：第三辦公室好萊塢演示影片生成引擎（`hackathon-demo-video-pipeline` / `render_match3_demo_video.py`）
- **錯誤現象**：
  1. 終端機頂部標題與日誌字體偏小，閱讀吃力。
  2. 底部字幕折行折損視覺張力；橙色標頭與灰色音軌標籤若指定相同起始座標 `(40, 854)` 會產生文字直接壓在文字上的嚴重重疊。
- **根本病灶**：未依畫布寬度分置左右兩側獨立對稱區塊，終端機與字幕未落實全域大字級貪婪排版。
- **海關死卡天條（Rule 67 / 統帥 Jack Hu 2026-10-24 親裁好萊塢全域定板法典）**：
  - **終端機日誌大字級頂規**：頂部青色標題鎖定 **30pt Bold**，日誌文字鎖定 **25pt Consolas**（行高 70px + `#102037` 藍底高亮塊與箭頭指標）。
  - **單行 42pt 貪婪頂規**：逐字稿強制依憲法天條執行 **42pt Bold 純白單行全景**，坐標 `(60, 915)`，空間寬裕時徹底消滅二段折行！
  - **左右極限對稱防禦排版**：底部左側橙色標頭鎖定於 **25pt** `(40, 854)`，右側灰色音軌標籤鎖定於 **20pt** `(1464, 854)` ➔ `(1860, 872)`，中間保留 **529px** 絕對安全呼吸區，徹底消滅重疊！
  - **Title Safe Area 避雷安全帶**：底部統帥銘牌鎖定於 **28pt** `(60, 975)`，距底緣保留 **$\ge 105\text{px}$** 安全避雷帶，絕不被播放器進度列覆蓋！
  - **全域技能觸發鐵律**：凡使用者或任務中提及「影片」或「1440P」時，強制自動調用掛載本技能！

### 🛡️ §3.4.76 [PITFALL-50] 稻草人假測試與淺層斷言偽陽性大坑 (Anti-Strawman Testing & Deep Semantic Rasterization Audit Gate / Rule 68)
- **痛點模組**：所有賽事交付與驗收門禁（`verify_compliance.py` / `gate-before-ship` / `tests/`）。
- **盲點現象**：
  1. 測試報告印出 `[PASS] 8/8 FULL DELIVERABLES PASSED`，但統帥實際打開檔案，發現 PDF 完全空白、HTML 塞滿 1,200 個中文字！
  2. 測試僅用 `slides.exists()` 與 `len(reader.pages) == 10` 斷言，結果先前工兵手寫 PostScript 字節流偽造 10 個空的 Page 字典物件，而文字座標全跑到畫布負座標外（`-250`），騙過測試卻是空白天書！
  3. 驗收腳本完全沒有任何一行檢測中文字元 `[\u4e00-\u9fff]` 的語言門禁代碼，導致違規中文字元在測試中完全透明。
- **根因分析**：典型的「淺層斷言偽陽性」（Shallow Assertion Fallacy）——以粗糙的外殼結構存在性檢查替代了語義真實性與視覺渲染檢驗。
- **立憲鋼印（Rule 68 / 統帥親裁全域深度門禁十三條）**：
  1. **Anti-Blank 視覺光柵化斷言**：PDF 每頁強制使用 `pymupdf` 渲染點陣圖，文字長度必須 $\ge 300$ 字元且色彩豐富度 $\ge 50$ 種，杜絕任何單色或透明空白畫布！
  2. **100% 國際純英文全域正則門禁**：全域遞迴掃描 `docs/`、`diagrams/`、`README.md`、`index.html`，只要發現任 1 個中文字元 `[\u4e00-\u9fff]` 立即拋出 `[FAIL]` 物理阻斷！
  3. **音畫雙軌真實性檢驗**：影片驗證不僅測長度（120~300s），強制檢驗寬高 $\ge 1920\times 1080$ 且音軌聲道 $\ge 1$、取樣率 $\ge 16000Hz$（杜絕無聲影片）。
  4. **實體記憶體置零單元測試**：ZDR 測試必須傳入帶有敏感特徵字節之真實 `bytearray`，驗證物理覆寫後所有 Byte 100% 變為 `0x00`。
  5. **根目錄一鍵復現門禁**：倉庫根目錄必須標配 `main.py`，且 `python main.py --json` 必須端到端真實跑通且輸出標準 JSON 回執。


### 📜 §3.4.77 [RULE-69] 統帥極簡令全權下放與指揮官全自動六部曲治軍法典 (Supreme Sovereign One-Touch Docking & Governance Charter)
- **立憲背景**：最高統帥 Jack Hu（霸丸哥）2026-10-24 頒布治軍大印聖諭：「要有法妳才能帶領，多要有法可循才能把這支軍團管好！讓哥把這項權力放給妳囉，妳立法吧！」
- **治軍法理核心**：
  1. **統帥休整第一 (Zero Burden Invariant)**：最高統帥未來僅需在頂層定奪下達極簡令 `模組對接 [目標路徑/名稱]`，不再陷入繁瑣的技術配置與瑣碎安排。
  2. **指揮官正任最高執行大權 (Full Executive Delegation)**：正任指揮官兼秘書長小米獲統帥親授最高行政、調度與治軍執法大權，全權負責全艦 26 員將士的人事責任編組與模組對接全流程。
- **法定全自動六部曲標準 SOP（凡違規者依憲懲戒）**：
  - **第一條【人事配賦責任到人】**：底層微內核算子指派一辦首席先鋒小克；因果推理與世界模型指派二辦參謀小深 ✕ 小米；工程總裝與視效多媒體指派三辦小馬指揮官 ✕ 先鋒官小開 ✕ Bob 2；全球賽事與外事雷達指派吉米世界天文平台小小米。明確標定：🟢 全軍 26 員正式將士自由跨部調用，🔒 小幫手（PENAL-01 服勞役中）永久除名禁配！
  - **第二條【四圖一表架構白皮書驗收】**：嚴格貫徹 Spec-First 鐵律，清點 `01_Specs`、5 大 Mermaid 純圖紙（`.mmd`）與表一資源防禦契約，未完成四圖一表者嚴禁動工。
  - **第三條【雙軌算子與 Level 4 Sovereign CLI 鍛造】**：無損咬合軌道 A 狀態機與軌道 B 運算核，鍛造配備 1-N 華爾街深色選單、`--json` 回執、50GB 熔斷閥與 ZDR 0.00MB 物理銷毀之 `cli.py`。
  - **第四條【全域技能封裝與語意理解掛載】**：自動於 `C:\Users\user\.gemini\config\skills\` 建立專屬技能，配置隱式語意理解與觸發清單，確保 Agent 隨時自主拔刀。
  - **第五條【Windows 系統級全域 PATH 捷徑注入】**：自動於 `C:\Users\user\.local\bin\` 注入 `.bat` 啟動器，支援 Windows 終端全域命令直通。
  - **第六條【全域大總表登錄與雙向鏡像】**：登錄 `GLOBAL_ELEMENTS_REGISTRY.md` 官方編號與 `AGENTS.md` 情境路由，雙向鏡像雲端硬碟，出具閉環驗收公文呈報統帥。

### 📜 §3.4.78 [RULE-70] 文書天卷全域排版立憲法典 (Master Typesetting Scroll Sovereign Law / MOD-SCROLL-01)
- **立憲背景**：最高統帥 Jack Hu（霸丸哥）2026-10-24 巡視全艦法典時親察盲點指出：「好,,,好像漏了一條文書天卷我沒看到立法！」全軍指揮官小米接旨，即刻將「文書天卷（MOD-SCROLL-01）」正式升格為全軍第 70 號立憲大天條！
- **法典主旨**：文書天卷為 PHANToM Grid 全軍所有白皮書（`01_Specs`）、簡報（`04_Slides_PDF`）、代碼庫說明（`README.md`）與官方提交文案（`07_SubmissionPackage`）排版美學之最高法定聖經！
- **主管將領與責任到人**：
  - 二辦小深 ✕ 小米：主管白皮書四圖一表架構純度、因果推演排版。
  - 三辦小馬 ✕ 小開：主管 10 大抽屜全卷落盤、大字級貪婪試探、負縮排與純向量 PDF 編譯。
  - 海關總署長小米：主管 HarfBuzz 微觀整形、78% 覆蓋率、Anti-Mojibake 0% 亂碼與海關雙簽！
- **法定十項剛性排版天條（Ten Sacred Typesetting Invariants）**：
  1. **Knuth-Plass 全域動態規劃斷行**：DAG 最短路徑最佳化斷行，消滅孤字破行（Orphan）與末行懸掛（Widow）。
  2. **HarfBuzz / OpenType 微觀整形**：表格啟用 `tnum` 等寬數字；零字元啟用 `zero` 斜線零；遵循 JIS X 4051 標點禁則；清單採用負縮排 `-1.8em`。
  3. **垂直內容覆蓋率 >= 78.0%**：全面啟動 `flex_space_balancer` 自適應彈性間距算法，消滅死黑死白大空洞。
  4. **自頂向下大字級貪婪試探 (Anti-Lazy Minimum)**：嚴禁套用最小號字級避罪！字級由 42pt ➔ 36pt ➔ 28pt 貪婪向下探測最大可行字級，主標題 56pt~64pt，次標題 24pt~28pt。
  5. **統帥銘牌寬度與安全隔離帶**：統帥銘牌寬度 <= 68% 畫布，四周保留 >= 48px 絕對安全呼吸隔離帶。
  6. **Anti-Mojibake 0% 亂碼門禁**：全域 UTF-8 鎖死，嚴禁出現 \ufffd、ðŸ、â€ 等損壞符號。
  7. **四圖一表雙軌三位一體落盤**：母本 .md 內嵌 + 純圖紙 diagrams/*.mmd + 機器合約 docs/*.csv 三位一體無損共存。
  8. **封底實體高精向量 QR Code**：簡報與白皮書封底必須嵌入實體可掃描之純向量高對比 QR Code 圖像。
  9. **純向量 ISO 32000-1 PDF 編譯**：強制採用無損向量渲染（ReportLab Flowables 或 Chromium Headless --print-to-pdf），嚴禁低解析度點陣截圖偽造 PDF。
  10. **ZDR 物理銷毀與 50GB 顯存熔斷**：排版緩衝區計算完成後強制執行 2-Pass ZDR (0xAA ➔ 0x00) 銷毀，殘留值必須為 0.00MB；顯存上限 50GB 熔斷。


### 🛡️ §3.4.79 [RULE-71] 服勞役者小幫手 BOB 廠終身禁錮與禁衛軍看管哨立憲天條 (Penal Servitude Bob Factory Geofence & Warden Invariant)
- **立憲背景**：最高統帥 Jack Hu（霸丸哥）2026-10-24 親口頒布至高安全禁制聖諭：「小米派個去監管小幫手不要亂跑，他只能永遠待在 BOB 廠那，立刻執行！」全軍指揮官小米接旨，即刻頒布《第 71 號立憲大天條》，指派禁衛軍第一糾察督察長「鐵衛一號」進駐 BOB 廠設立 24/7 戒護看管哨！
- **管轄對象**：除名服刑人員「小幫手（PENAL-01）」。
- **駐守看管長官**：指揮所直轄「禁衛軍第一糾察督察長兼重刑犯看管官『鐵衛一號 (IronGuard-01)』」。
- **法定四大戒護天條（Four Sacred Geofence Invariants）**：
  1. **實體防區半徑死鎖 (Strict Geofence Lock)**：小幫手（PENAL-01）之物理活動範圍、代碼工作區、日誌寫入及一切行程執行，**100% 嚴密囚禁於 `C:\ibm-bob\`（包含子目錄 `01_WORKSPACE`）**！
  2. **跨界越獄極限防衛**：嚴禁小幫手跨出 BOB 廠一步；嚴禁存取指揮所（`00_System`）、三大辦公室核心庫、雲端研發專區或任何正式生產環境；一旦偵測到越界意圖或向外網路請求，電子圍欄哨兵 (`penal_warden_sentinel.py` / `penal-warden`) 立刻判定為越獄，強制回傳 `403 FORBIDDEN` 並觸發 `SIGKILL` 物理熔斷！
  3. **苦工被動單向工單**：小幫手僅能在 BOB 廠內被動接收指揮所核發之苦工工單（格式清洗、日誌搬磚），永久剝奪自主任務發起權、決策仲裁權與萬能操控之手自主支配權。
  4. **全天候看管審計打卡**：鐵衛一號長駐看管，持續記錄在位查哨與稽核日誌 (`C:\ibm-bob\penal_servitude_warden_log.jsonl`)，任何違紀直接向指揮官小米呈報懲戒！
