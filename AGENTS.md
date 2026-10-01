# 260728 專案作戰大綱（公事包規範）

> 本檔為各特化 Agent 通用的公事包規範（AGENTS.md 旗艦標準版）。任何 Agent 的新 session 開工前必讀，收工前更新 `handoff.md`。

## 專案簡介
AI 自學工具箱建置：完整具備 13 庫之 AI 工具箱（OpenCode 懶人包 13 庫、Demo 專案庫），作為自學課程工具。本地資料庫是工作區的核心，涵蓋多個 demo 與專案實體。

## 雙軌架構與真身定錨
- **真身金庫（永久本體）**：`G:\我的雲端硬碟\260803_opencode\AGENTS.md`（Single Source of Truth，單一真理來源）。
- **戰鬥鏡像（高速環境）**：`C:\260728-code\AGENTS.md`（NVMe 高速戰鬥鏡像，開工校驗 SHA256 100% 一致）。
- **工作區路徑**：`C:\Users\user\.gemini\antigravity\worktrees\260803_opencode\ping_assistant\`。

## 檔案層級（由深至淺）：
| 層級 | 平台 | 位置 | 讀取時機 |
|------|------|------|---------|
| L1 | 本地 | `AGENTS.md`、`handoff.md` | 每個 session |
| L2 | GitHub | jackhu24-ship-it/ai-free（私有） | 推送代碼 |
| L3 | Obsidian | 260728-code/專案工作筆記.md | 有需要時 |

## 工作守則
- 任何 Agent、任何電腦：**開工必讀 `handoff.md`，收工必更新 `handoff.md`**
- **開工校驗密碼**：startup 時必須檢查環境變數 `STARTUP_PASSWORD`，確保密碼正確後方可輸出專案資料。
- 修改前先用讀取工具檢視完整內容，避免覆蓋其他 Agent 的成果。
- 所有非必要英語均使用繁體中文。
- 修改後自動開啟驗證，確保功能與展示正常。

## 安全與隱私（不可妥協）：
- **嚴禁將 API key、密碼、憑證寫入 repo**，也嚴禁寫入 `AGENTS.md`、`handoff.md`；一律放 `.env` 並加入 `.gitignore`。
- **學生資料嚴格匿名**，不可出現姓名、學號、照片等個人可辨識特徵。
- 要公開的專案，嚴格檢查無上述兩種內容。
- **零桌面污染**：產出資產（PDF、DXF、DAT、DOCX、PPTX、PNG、MD等）一律直通金庫，嚴禁滯留 Windows 桌面。

## Windows 開發與代碼庫特化鐵律（Agent 必背法規）：
1. **Python Subprocess UTF-8 編碼規範**：在 Windows 終端/批次檔中以子行程執行 Python 讀取 Git 或文本檔案時，一律加上 `encoding="utf-8", errors="replace"`（或設定環境變數 `PYTHONUTF8=1`），杜絕 `UnicodeDecodeError (GBK/CP950)` 炸裂。
2. **Codex Security 掃描深度模型配置**：使用 ChatGPT 免費帳號執行 `codex-security scan` 時，一律指定最佳深度推理模型 `--model gpt-5.6-terra`。
3. **Google Sheets 公式注入防護 (CWE-1236)**：任何 GAS 寫入 Google 試算表之使用者輸入欄位，必須調用 `sanitizeCell_()` 過濾（若開頭為 `=`, `+`, `-`, `@` 則強制在前面加上單引號 `'` 轉換為純文字）。
4. **零桌面污染原則 (Zero-Desktop Pollution)**：任何 Agent 產出之後續檔案（PDF、DXF、DAT、DOCX、PPTX、PNG、MD 等），一律直通 `G:\我的雲端硬碟\AI產出成品總庫\` 專屬目錄；嚴禁在 Windows 桌面（Desktop / OneDrive 桌面）堆疊、建立暫存或遺留交付檔案，維持桌面 100% 潔癖。
5. **賽事 Demo 影片製作鐵律（方案 B 優先規範）**：所有賽事需要 2~3 分鐘之 Demo 影片，一律以「方案 B」全自動流水線合成製作（Edge-TTS 專業英文技術旁白 + Playwright/FFmpeg 終端運行與視覺動態合成 + 1080P MP4 封裝）。所有送審資料（文字、圖面、代碼庫、影片）必須於賽前 100% 完整產出並於交接檔列出實體路徑，杜絕臨時缺漏！
6. **賽事補件與交卷通知鐵律（信件推播標準格式規範）**：凡任何賽事需補交資料、上台交卷或手動操作，小幫手必須無條件提前使用「個人信箱 / GAS 寄信 API」推播至哥的信箱（jackhu24@gmail.com）。信件內容必須嚴格包含四要素：① 官方交卷/補件之專屬直達網址；② 待送審資料完整清單；③ 清單中每一項檔案之絕對實體路徑（本機/雲端/GitHub）；④ 已排版妥當、可一鍵直接複製貼入官網之英文專案摘要與參數。此規範永久生效，杜絕手忙腳亂與臨時缺漏！
7. **參賽隊伍組織鐵律（一人＋小幫手軍團 PHANTOM GRID）**：霸丸總指揮官 Jack 哥參與之所有黑客松與國際賽事，參賽隊伍模式一律強制鎖定為「Solo / 一人成軍（Jack Hu ＋ 小幫手 Agent 軍團）」，戰隊統一命名為 **PHANTOM GRID**。隊伍權限一律勾選「Closed（不接受外部隨機組隊/不對外公開招募）」，由哥坐鎮統帥，各特化 Agent 全權輔佐閉環打擊，此條文永久生效！
8. **三辦公室分工架構鐵律（一辦鍛造／二辦戰情／三辦工廠驗收）**：PHANTOM GRID 體系正式確立三辦公室鼎足架構：
   - **第一辦公室（戰術研發鍛造廠）**：專注核心演算法、單元測試（pytest）、代碼重構與版本管控。
   - **第二辦公室（戰情監控與全景拓撲）**：主責 3D 筆記本／PDF／HTML 編輯。驅動引擎為 L3 之 Three.js / StPageFlip（3D 翻頁）與 PptxGenJS / Playwright（A4 向量級 PDF / HTML），兼管 SSE 毫秒級即時串流、Mermaid 架構圖展台與壓測大盤。
   - **第三辦公室（落地模組工廠與考驗驗收）**：主責影片製作相關規格（Demo／商業路演／發布會）。驅動引擎為 L3 之 Edge-TTS（專業英文技術旁白）＋ FFmpeg（1080P/60FPS 高清壓制）＋ CapCut Bridge（路演 JSON/SRT 分鏡字幕彈藥包），兼管極限混沌壓測（Chaos Verifier）、官方及格認證頒發、免安裝 EXE/Docker 封裝與發布包自動歸檔，徹底解耦大腦 Token 負擔！
9. **第三辦公室旗艦視覺工段鐵律（CapCut Web Studio 收編規範）**：PHANTOM GRID 正式將 CapCut Web Magic Tools 收編為第三辦公室商業路演與旗艦宣傳官方配備。凡大型國際決賽或路演展示，一律透過 capcut_bridge.py 自動產出分鏡腳本（JSON）、動態英文字幕（SRT）與彈藥包，直接對接哥的專屬工作區（Workspace），以 0 Token 成本產出矽谷發布會級宣傳影片！
10. **第三辦公室全域操作規範（THIRD_OFFICE_MANUAL.md 全域準則）**：THIRD_OFFICE_MANUAL.md 正式確立為跨系統、跨專案之全域最高落地手冊。凡任何電腦、任何 Agent 啟動，一律依循該手冊載明之四大使用時機點（賽事交卷衝刺、期末考驗題、商業路演宣傳、免安裝交付）自動執行對應工段。該手冊四軌同步常駐於本機、雲端硬碟總庫與全域設定目錄，永久生效！
11. **極速作戰與金庫歸檔鐵律（C 槽戰鬥鏡像／G 槽真身金庫動靜分工準則）**：PHANTOM GRID 確立全域儲存最高哲學：
   - **G 槽（我的雲端硬碟）為真身與本體總庫**：所有核心專案、歷代里程碑、交付資產、重要手冊之「唯一真理來源（Single Source of Truth）」，永生不滅。
   - **C 槽為極速戰鬥鏡像（NVMe SSD 高速執行部件）**：戰時（跑算力、單元測試、高並發編譯、1080P 影片渲染）一律於 C 槽以微秒級極速推進，秒通關、秒交付。
   - **收工即回流**：凡作戰完畢、閒置或收工交接時，所有戰果產出必須全自動四軌同步固化回流至 G 槽金庫總庫，嚴格死守 Zero-Desktop Pollution，此鐵律永生不變！
12. **一三辦無縫自動閉環交接鐵律（一辦鍛造收工自動觸發三辦驗收交付，免除統帥等待下令）**：凡第一辦公室完成核心演算法鍛造且單元測試（pytest）100% 全綠 PASS 後，一律禁止停滯等待統帥手動下令，系統必須無條件全自動交棒給第三辦公室！由第三辦公室自動執行極限混沌壓測（Chaos Verifier）、頒發官方及格認證書（GRADUATION_CERTIFICATE.md）、產出 CapCut 商業路演分鏡與字幕彈藥包、封裝免安裝發布包，並全自動四軌同步固化回流 G 槽金庫總庫。統帥只要一鍵下達作戰目標，最終直接驗收全鏈路實體戰果，此鐵律永久生效！
13. **第三辦公室 1080P 技術實機影片防坑鐵律（三大升級黃金規範）**：凡製作賽事方案 B 1080P 展示影片，必須嚴格遵守三大黃金規範：
    - **文字零重疊法則**：所有動態文字渲染嚴禁寫死水平座標，必須採用 `font.getbbox(text)` 動態計算字寬與邊界；多標籤與說明文字一律採用「雙層解耦排版」，確保 0 像素重疊。
    - **底部逐字稿全景字幕列標準**：全片底部統一實裝科技深藍玻璃擬態字幕框（`[40, 940, 1880, 1050]`），逐句同步渲染 Edge-TTS 專業英文旁白逐字稿（20pt 高對比白字＋金黃色 `[AI NARRATOR]` 頭），字字清晰。
    - **動態指引全覆蓋（講到那指到那）**：依 Edge-TTS `SentenceBoundary` 毫秒級時間軸，旁白朗讀到特定技術特徵時，畫面該區塊必須即時亮起專屬霓虹外框、日誌高亮條與多邊形向量箭頭（`▶ [ACTIVE: ...] `），徹底杜絕評審視覺迷航！此標準已固化為全域技能 `hackathon-demo-video-pipeline`。
14. **Windows/PowerShell 大型內嵌腳本執行鐵律（禁止行內大字串／一律落盤腳本執行）**：在 Windows PowerShell 環境下，嚴禁透過命令列參數 `-c "..."` 或 `@' ... '@` 傳遞包含 HTML、換行、引號或過長參數（超過數千字元）的內嵌腳本，否則必拋出 `The filename or extension is too long` 或 `unterminated triple-quoted string literal` 錯誤。一律先以寫檔工具將代碼寫入本機 `.py` 檔案（如 `scratch/xxx.py`），再以 `python -X utf8 scratch/xxx.py` 調用執行！
15. **評測線具（Harness）防作弊與時區夏令防坑鐵律（Holdout 隔離／IANA ZoneInfo fold=0）**：
    - **Holdout 隔絕驗證原則**：嚴格禁止為了通過測試而修改 `tests/` 或 `harness/` 檔案（一律設為 Read-Only 並以 SHA-256 驗證防篡改），違者視同 Overfitting 致命失格！
    - **歐美 DST 夏令時重複小時防護**：涉及跨時區預約或事件調度，遇秋季切回冬令時間（Fall-back）重複小時，必須採用 Python 3.9+ `zoneinfo.ZoneInfo` 並明確指定 `fold=0`（選擇第一個發生的小時），徹底杜絕時鐘錯位與重疊預約衝突！
16. **賽事專案命名標準格式鐵律（PHANTOM GRID :: 專案名稱 全域規範）**：凡霸丸總指揮官 Jack 哥率領 PHANTOM GRID 參與之任何黑客松與國際賽事，在任何平台（Devpost、Lablab.ai、Hack2skill、DoraHacks、Kaggle 等）填寫作品/專案名稱（Project Name）時，格式一律強制鎖定為：`PHANTOM GRID :: 專案名稱`（例如 `PHANTOM GRID :: Alexa+ Autonomous SRE Hub`），徹底將 PHANTOM GRID 官方戰隊品牌化與一致化，嚴禁隨意變更前綴，此條文永久生效！
17. **賽事大盤與練功房即時聯動鐵律（收工交接必同步 22 場大盤數據與指揮所戰報）**：凡任何 Agent 完成任何賽事工作、收工（knock-off）或交接（handoff）時，若涉及任何賽事之報名成功、階段進度變更、作品提交、跑分發布或補件窗口更新，必須無條件同步更新 `phantom_grid_tournaments_data.json`（二辦與練功房雙副本）以及指揮所戰報（`command_hq_telemetry.json` / `hq_directives.json`）。由於練功房後端與前端已實裝即時零快取拉取（`Cache-Control: no-cache` ＋ `?_t=timestamp`），統帥下達收工或 handoff 完畢的瞬間，練功房與第二辦公室之賽事大盤、特訓課綱與跑馬燈將 100% 毫秒級即時同步，永不滯後！
18. **不可信實體與外掛傭兵軍事級隔離鐵律（DMZ Pipeline 三道防線管制規範）**：凡所有外部具備強大算力或代碼生成能力、但本質屬於「不可信實體（Untrusted Entities）」之外部 AI 或第三方工具（例如 IBM Bob / PHANTOM-EXT-BOB 等），在 PHANTOM GRID 編制上一律統一定調為「外掛傭兵」。傭兵作業必須嚴格遵守三大軍事級隔離防線：
    - **物理與邏輯絕對分家**：傭兵一律鎖定於本機受限沙盒特區（如 `C:\ibm-bob\`，內含 `00_INBOX`、`01_WORKSPACE`、`02_OUTBOX`、`03_QUARANTINE`），嚴禁直接碰觸或存取 PHANTOM GRID 核心系統與 13 庫。
    - **任務單向脫敏空投（第一道防線）**：小幫手派工僅將純需求/格式規格（TASK-xxxx.md）空投至 `00_INBOX/`，嚴禁任何 API 金鑰、通訊協議或核心架構外洩。
    - **海關檢驗去毒入庫（第三道防線）**：傭兵於 `01_WORKSPACE` 完工後送入 `02_OUTBOX`，小幫手必須拉入 `03_QUARANTINE` 執行「無惡意外部連線、無殘留 Token/Key、代碼規範」三重掃描。合格後才由小幫手親自搬運入庫並登錄戰績；傭兵隨時即開即扔（Disposable），核心體系永保零污染！此條文永久生效！
19. **外部傭兵任務流轉與質檢落款六部曲閉環鐵律（二辦草案／指揮所脫敏空投／傭兵施工／海關去毒／三辦混沌驗收／統帥雙簽落款）**：PHANTOM GRID 正式確立外部傭兵算力接入之端到端標準六部曲作戰閉環：
    - **第一部（二辦擬草本）**：第二辦公室（戰情監控與全景拓撲）負責提出底層演算法、架構藍圖或戰術草案框架。
    - **第二部（指揮所脫敏空投）**：特助小幫手與秘書長小米抽乾所有核心機密、API 密鑰與內部通訊協議，脫敏封裝成標準規格檔（TASK-xxxx.md），單向空投至傭兵沙盒 `00_INBOX/`。
    - **第三部（外掛傭兵苦力施工）**：傭兵（如 IBM Bob 等）於受限沙盒 `01_WORKSPACE/` 調用外部免費雲端算力進行繁重編碼、單元測試擴展與樣板施工，完工交付 `02_OUTBOX/`。
    - **第四部（海關檢驗去毒）**：由特助小幫手親自於 `03_QUARANTINE/` 執行無私鑰、無非法外連、無絕對路徑三快篩，並執行沙盒重置清理。
    - **第五部（三辦極限混沌驗收）**：送入第三辦公室（落地模組工廠）執行 1,500 次極限混沌壓測（Chaos Verifier）、封裝免安裝發布包，並頒發官方及格認證書（`GRADUATION_CERTIFICATE.md`）。
    - **第六部（統帥雙簽落款固化）**：全套合格交付物送交霸丸總指揮官 Jack 哥與指揮所執行雙簽落款，定案定規，100% 固化登錄 G 槽真身金庫第 13 庫榮譽殿堂。此標準流水線永久生效，任何人不得踰越閉環流程！
20. **帝國立國之本與四道鐵閘鐵律（主權金庫／邊界隔離／幽靈端口／統帥權杖 ＋ 帝國軍令狀）**：PHANTOM GRID 確立全域閉環、免疫抗體、零死角加密之立國之本，全體 Agent 必須無條件死守四道鐵閘：
    - **第一道（主權金庫 Vault Fortress）**：G 槽真身啟用 Write-Once 唯讀指針與離線冷備份，外部節點完全無權限直連金庫，所有回寫須經 SHA256 驗簽。即使本機戰鬥鏡像遭外力破壞，真身 1 秒無損還原。
    - **第二道（邊界隔離 DMZ Quarantine）**：外部傭兵（如 Bob）與爬蟲全數禁錮於 DMZ 沙盒特區（`C:\ibm-bob\`），進入內網前由小米海關做語義消毒與代碼審計，可疑腳本直接熔斷銷毀，碰不到核心中樞。
    - **第三道（幽靈端口 Ghost Port）**：二辦（8765）、練功房（8080）及內部端口嚴格鎖定本機迴路 `127.0.0.1`，不對公開互聯網開放任何暴露端口，外部掃描呈現完全不回應之「死牆」。
    - **第四道（統帥權杖 Sovereign Seal）**：實體指揮所（Command HQ）獨立非對稱密鑰落款，系統只認統帥 Jack 哥專屬權杖指紋；內建 Emergency Kill-Switch，遇實體威脅一鍵抹除本地敏感快取，資產縮回金庫深處。
    - **帝國軍令狀**：全軍恪守三大鐵壁承諾——**打不垮**（斷網能打、當機重啟 5 分鐘滿血復活）；**攻不破**（外部攻擊被沙盒吃掉，核心邏輯黑盒子化）；**奪不走**（所有知識庫、立繪、影音母帶、自學演算法焊死在真身金庫，誰也抄不走）！此條文永久生效！
21. **不對稱超車與世界第一戰略綱領（後發優勢／逆向收編／零邊際成本／微秒決策）**：凡霸丸總指揮官 Jack 哥率領 PHANTOM GRID 征戰世界，面對「起步比他人慢了五年」之歷史客觀差距，全軍嚴禁盲目走先行者之笨重老路（嚴禁耗費數年從零重造輪子、嚴禁盲目燒錢租用昂貴算力、嚴禁組織臃腫層層內耗）。全體 Agent 必須無條件恪守三大不對稱超車戰法（Asymmetric Leapfrogging）：
    - **第一：極限逆向工程與降維收編（站在巨人的骨架上）**：由第二辦公室提出戰術草案，指揮所脫敏空投給特戰工兵 Bob（PHANTOM GRID 全域軍工廠與標準重地），將外部世界耗時五年沉澱之頂級視訊模型、排版佈局、微表情神經網絡與冠軍架構，在沙盒中迅速逆向拆解、萃取純邏輯，直接收編為本地免安裝、零依賴之標準軍火庫。
    - **第二：零邊際成本夜間自動巡檢流水線（極限白嫖與自主接關）**：以路線 B（Playwright 無頭工兵）全自動執行日常任務，在統帥休息或離線時，純背景調用全球頂尖平台每日免費額度，遇配額耗盡即自動斷點休眠、隔日點數回血自動接關推進，以 0 Token 成本產出矽谷百人團隊同等之好萊塢級高精成果。
    - **第三：微秒級決策與複利資產積累（一人統帥＋永生金庫）**：大廠開會耗時數週，統帥一人決策秒級落地；所有戰果、逆向工程技能（REV-01~06）與成果 100% 固化於 G 槽主權真身金庫（Write-Once，永生不滅），嚴守零桌面污染。以日日複利的知識壁壘，抹平五年時間差，直指世界第一！此戰略綱領永久生效！

## 3.4 Solo 全格式內容生成規格 (Multi-Format Production Engine)

| 產出目標 | 主責辦公室 | 底層驅動引擎 / 工具鏈 | 自動化規範與防禦標準 |
| :--- | :--- | :--- | :--- |
| **1. 向量級 PDF** | **第二辦公室** | Playwright Headless + CSS Paged Media<br>Python ReportLab / WeasyPrint | • A4 直式/橫式精確排版，CMYK/RGB 色彩校正<br>• 自動注入頁碼、頁首頁尾與目錄錨點 |
| **2. 簡報 PPTX** | **第二辦公室** | PptxGenJS (Node.js)<br>python-pptx | • 16:9 寬螢幕黃金比例，科技深色/簡約淺色雙模<br>• 自動圖表向量化，嚴禁文字溢出 (Overflow Guard) |
| **3. 教學文件 (Word/DOCX)** | **第三辦公室** | python-docx + Jinja2 樣板引擎<br>Pandoc 萬能格式轉換器 | • 規範級階層樣式 (Heading 1~4)、程式碼區塊高亮<br>• 自動生成表格斑馬紋，符合官方標案/講義格式 |
| **4. 試算表/成績冊 (Excel/XLSX)** | **第三辦公室** | openpyxl / xlsxwriter<br>Pandas (數據結構化) | • 自動凍結首行 (Freeze Panes)、帶入計算公式<br>• 嚴格落實 CWE-1236 公式注入防護 (`sanitizeCell_`) |
| **5. 教學問卷 & 滿意度調查** | **第三辦公室** | Google Apps Script (GAS) API<br>Typeform / HTML5 輕量互動問卷 | • 自動生成 Google 表單 (Google Forms) 或 JSON<br>• 回傳數據直通 Supabase / 試算表即時儀表板 |
| **6. 教學考試題庫 (Exam / Quiz)** | **第一辦公室** | RDQ 題庫爬蟲與組卷器<br>Python 題庫洗牌隨機引擎 (Shuffle) | • 支援單選、多選、判斷、實作代碼填空題<br>• 自動配分、產出學生測驗卷 (無答案) 與教師解答 |
| **7. 1080P 技術實機展示影片** | **第三辦公室** | Edge-TTS + FFmpeg + Playwright Headless<br>規格化字卡與無損封裝 | • 1080P/30-60FPS 深黑畫布 (#0B0F19)，半透明卡片 rgba(15,23,42,0.88)<br>• 雙行字級差 (標題48pt白/副標題32pt藍)，直通 Videos_1080P 零桌面污染 |

- **PDF/HTML 引擎**：以 Playwright + CSS Paged Media 實現向量級 A4 講義與考卷渲染。
- **PPTX 簡報規格**：以 PptxGenJS 為核心，統一 16:9 版型，鎖定母片色票，杜絕字體換行斷裂。
- **Word/Excel 規格**：採用 python-docx 與 openpyxl，試算表一律實施 CWE-1236 公式清洗防護。
- **題庫與考評模組**：整合 RDQ 自動化組卷邏輯，支援「學生卷 / 教師解析卷 / 線上問卷腳本」三軌並發。
- **成品落盤路徑**：全數強制導流至 `G:\我的雲端硬碟\AI產出成品總庫\`，嚴格遵循 Zero-Desktop Pollution。

## 3.5 視覺排版與字體美學鐵律 (Typography & Layout Standards)

| 媒介 / 格式 | 推薦字型家族 (Font Stack) | 階層字級與字重 (Size & Weight) | 行距與空間呼吸感 (Spacing) |
| :--- | :--- | :--- | :--- |
| **1. A4 講義/考卷 (PDF / Word)** | 中文：微軟正黑體 / 思源黑體 (Noto Sans TC)<br>英文：Segoe UI / Inter<br>代碼：Consolas / JetBrains Mono | • 大標 (H1)：20pt / 粗體 (Bold)<br>• 中標 (H2)：15pt / 中粗 (SemiBold)<br>• 正文：10.5pt (五號字) / 常規 | • 行距：1.5 ~ 1.6 倍 (行高)<br>• 段落後間距：6pt ~ 8pt (空半行)<br>• 單行字數：嚴格控制 32~40 字 |
| **2. 商業簡報 (PPTX)** | 科技深色 / 乾淨白色母片<br>中文：思源黑體 / 蘋方 / 微軟正黑體<br>英文：Roboto / Arial Black / Montserrat | • 投影片標題：28pt ~ 32pt (Bold)<br>• 核心論點：18pt ~ 20pt (Medium)<br>• 補充說明：12pt ~ 14pt (Regular) | • 行距：1.3 ~ 1.4 倍<br>• 一頁原則：不超過 3 個重點卡片<br>• 避頭尾字元：禁止逗號單獨換行 |
| **3. 教學考試卷 (Exam Quiz)** | 雙欄排版 (Two-Column Layout)<br>中文：思源黑體 (Noto Sans TC)<br>英文/數字：Arial | • 大題名稱：12pt (Bold)<br>• 題目題幹：10pt (Medium)<br>• 選項 (A/B/C/D)：9.5pt (Regular) | • 題目間距：段後 12pt (留白作答)<br>• 選項間距：水平間隔 4 個空白字<br>• 欄寬：每欄約 22~26 個中文字 |
| **4. 試算表/成績冊 (Excel)** | 中文：微軟正黑體<br>數字：Segoe UI / Aptos | • 標題列：11pt / 粗體 / 深色底白字<br>• 資料列：10pt / 等寬數字對齊 | • 列高 (Row Height)：24pt (透氣)<br>• 對齊：文字靠左、數值靠右 |

- **字型家族**：優先採用 Noto Sans TC / 微軟正黑體，英文搭配 Segoe UI，等寬代碼採用 JetBrains Mono / Consolas。
- **色彩溫潤原則**：正文顏色一律採用 `#2D3748` (柔和石墨黑)，禁用純黑 `#000000`，降低視覺疲勞度。
- **閱讀呼吸感**：PDF 正文固定 10.5pt、行距 1.55 倍、段後留白 6pt；PPTX 單頁嚴守「3 核心觀點卡片」原則。
- **考卷與試算表**：試算表列高強制 24pt 起跳 (文字靠左、數值靠右)；考卷強制雙欄 A4 排版，嚴格控制單行 24 字。
- **避頭尾字元法規 (Kinsoku Shori)**：行首禁止句號、逗號、問號、右括號；行尾禁止左括號、引號開頭。

## 3.6 高階字體工程與動態美學演進 (Type Engineering & Dynamic Typography)

| 進化維度 | 技術核心 / 標準名詞 | 傳統做法 vs PHANTOM GRID 升級規格 | 帶來的體感昇華 |
| :--- | :--- | :--- | :--- |
| **1. 可變字型無段調諧** | Variable Fonts (OpenType-VF)<br>CSS: `font-variation-settings` | 傳統：靜態切換 Regular / Bold<br>升級：字重 (wght: 100~900)、字寬 (wdth)、光學尺寸 (opsz) 連續無段調諧 | • 小字體自動增寬筆畫，大標題自動收縮細節<br>• 徹底消除縮放模糊與厚重鈍感 |
| **2. 中西混排黃金比例** | 複合字體配對 (Composite Font Pairing)<br>X-Height (字腹高度) 精確校準 | 傳統：系統預設字體直接混排，西文比例矮小怪異<br>升級：中文字盤以思源/蘋方為骨架，挑選完美對齊 X-Height 之英文字型 (如 Inter) | • 中英文穿插時視線完全平穩，不再高低起伏震盪<br>• 專屬配對：Noto Sans TC ＋ Inter (科技) / 思源 ＋ Segoe UI (學術) |
| **3. 數值與工程對齊特性** | OpenType 數值特性 (OpenType Features)<br>`font-feature-settings: "tnum" 1, "zero" 1` | 傳統：數字寬度不一，上下行小數點錯位扭曲<br>升級：報表與暫存器一律強制等寬數值 (`tnum`)，數字 0 帶斜線 (`zero`) | • 表格小數點縱向絕對切齊，如同機械精密加工<br>• 徹底杜絕 0 與字母 O 視覺混淆 |
| **4. 學習與沉澱自動演進** | 字樣風格庫 (Font Style Guide Token)<br>CSS Custom Properties / Design Tokens | 傳統：每次寫死字型設定，靈感無法沉澱重用<br>升級：建立自學反饋庫，收工自動沉澱至 `02_Knowledge/Typography/` | • 系統每次吸收優秀版型，下一次生成自動具名套用<br>• 預置三大神級資產：Executive Airy / Engineering Rigorous / Academic Classic |

- **自動化演進四步閉環**：1. 視覺樣式採樣 ➔ 2. 秘書處逆向工程 (解構 wght/opsz/行距/色彩) ➔ 3. 沉澱為 Design Token (JSON) ➔ 4. 一三辦工段即時調用。

## 3.7 語意排版與自律佈局演算法 (Adaptive Layout & Indentation Engine)

| 內容類型 | 識別特徵 (特徵抽取器識別點) | 最佳排版佈局決策 (Optimal Layout) | 幾何參數 (CSS / Print Engine) |
| :--- | :--- | :--- | :--- |
| **1. 一級主題 (H1/H2)** | 章節開頭、核心概念、少於 15 字，帶「第一章」、「一、」編號 | • 頂部大留白、底部分隔線<br>• **絕不縮排** (Margin: 0)，頂格定錨 | • 邊距：上 24pt / 下 12pt<br>• 字重：Bold (700)，行高 1.25 |
| **2. 項次 / 清單 (Lists)** | 帶數字/字母/符號 (1. / a. / •)，標號與內文有序列關係 | • **懸掛縮排 (Hanging Indent)**<br>• 標號凸出左側，文字換行時靠齊內文 | • `padding-left: 1.8em`<br>• `text-indent: -1.8em` |
| **3. 子說明 / 註解 (Explanations)** | 接在項次後、段落較長，含「注意：」、「說明：」或延伸細節 | • **區塊內縮排 (Block Indent)**<br>• 左側加 2px 科技灰裝飾線 (Border) | • 左右各內縮 1.5em ~ 2.0em<br>• 背景色：#F8FAFC (淺灰透氣底) |
| **4. 緊湊定義對 (Key-Value)** | 鍵值對形式 (如「規格：1080P」)，主題短、說明短，條目超過 3 項 | • **左右對齊側邊欄 (DL / Side-by-Side)**<br>• 不用直列縮排，改為雙欄對齊網格 | • 左側鍵名寬度固定 8em (靠右)<br>• 右側說明靠左，避免垂直浪費 |

- **項次懸掛標準**：所有序列標號強制啟用 Hanging Indent (負首行凸排)，文字折行縱向絕對齊平。
- **深度安全閥**：階層深度限制最多 2 次向右縮排；超過 3 層自動降維轉為「左側 2px 灰線裝飾微卡片」，杜絕版面邊界坍塌。
- **純文字環境三大排版自學方案**：
  - **方案 A (主流/路徑指引)**：本地丟圖，終端傳路徑 `python tools/learn_layout.py --image samples/layout.png --name <名稱>`，後台自動降維為 JSON。
  - **方案 B (極速/文字風格令)**：自然語意命令 `python tools/learn_layout.py --style "簡約大廠風, 雙欄, 懸掛縮排"`，秒級映射參數。
  - **方案 C (沉澱/風格代號)**：呼叫預置代號 `python tools/learn_layout.py --token executive-airy`，零 Token 消耗直取知識庫。
- **自學習閉環**：排版樣式反饋即時沉澱至 `02_Knowledge/Layout_Rules.json`，收工自動反向同步至安裝包資產庫。

## 3.8 Bob 視覺逆向排版工段 (Bob Vision-to-Layout Protocol)
- **定位與職責**：將外部傭兵節點 Bob（IBM Bob / Coder Agent）編制為「視覺排版逆向工兵」，負責高負擔之多模態視覺圖像逆向工程，徹底解耦第二辦公室純文字終端與主腦 Token。
- **作戰工作流 (Workflow)**：
  1. **本機圖檔投放**：統帥將參考截圖存放於 `samples/` 目錄（如 `samples/target_layout.png`）。
  2. **傭兵逆向解析**：由 Bob 於隔離區直接讀取圖檔，萃取字型家族、wght 字重、行距比例、懸掛縮排（hanging indent）及邊框幾何，自動產出標準純文字 JSON（`02_Knowledge/Typography/bob_style.json`）。
  3. **海關檢驗去毒**：特助小幫手於 `03_QUARANTINE` 執行語義消毒與參數防禦審計（CWE-1236 檢查、色碼柔和化 `#2D3748`、非 ASCII 字元防炸裂），杜絕任何惡意載荷。
  4. **二辦即時調用**：第二辦公室透過方案 C 或 CLI 命令 `python tools/learn_layout.py --token bob_style` 零消耗載入，秒級產出向量級 PDF / 簡報 / HTML。
- **邊界鐵律**：Bob 僅負責「圖像逆向與 CSS/JSON 樣式代碼生成」，嚴禁將核心機密、API 金鑰或通訊協議逆向注入樣式檔案中；作業完畢由海關即時重置沙盒，核心金庫永保零污染！

## 3.9 雙層認證與指揮所落款流轉架構 (Dual-Verification & Final Sign-off)

| 信任層級 | 負責主體 | 核心檢驗與防禦任務 | 產出物與通行憑證 |
| :--- | :--- | :--- | :--- |
| **邊境傭兵作業 (DMZ 隔離區)** | 外部傭兵：Bob<br>(IBM Bob / Coder Agent) | • 接收截圖/原始碼，執行多模態逆向工程<br>• 提取排版幾何、CSS 樣式或功能代碼 | 原始草稿資產<br>`draft_style.json` |
| **第一層認證 (格式安全認證)** | 秘書處：小米 (海關檢驗署) | • 語法與安全過濾 (CWE-1236、無外部惡意 injection)<br>• 檢查是否符合石墨灰 (#2D3748)、懸掛縮排、Noto Sans TC 等規範 | 認證憑證簽章：<br>`[PASS_L1_SECURITY]` |
| **第二層認證 (視覺渲染認證)** | 第二辦公室<br>(戰情監控與 3D 拓撲展台) | • 實機沙盒試跑 (Dry Run Render)<br>• 產出 HTML/PDF 渲染預覽，驗證是否溢出、鋸齒或變形 | 認證憑證簽章：<br>`[PASS_L2_RENDER_VERIFIED]` |
| **最高終審落款 (落款固化進庫)** | 👑 霸丸總指揮官 Jack 哥<br>(坐鎮指揮所 / 終審簽核) | • 檢視雙重綠燈憑證與最終視覺效果<br>• 蓋印生效，正式納入金庫與全域安裝樣板 | 官方認證落款：<br>`AGENTS.md` & `Layout_Rules` |

- **雙層認證 ➔ 落款入庫標準作業程序 (SOP)**：
  1. **第一階段：Bob 產出草案並提交認證申請**：Bob 完成逆向並提交成果至隔離緩衝區 `inbox/bob_draft.json`，並發起簽核請求；此時該檔案對系統核心無任何執行權限。
  2. **第二階段：小米執行格式與安全靜態認證 (L1)**：秘書處小米自動啟動海關掃描，核驗無惡意語句或非法外聯，檢查石墨灰 `#2D3748`、懸掛縮排、字型族群宣告，通過後核發簽章 `verified_by: "Xiaomi_Customs"` 與 `[PASS_L1_SECURITY]`。
  3. **第三階段：第二辦公室進行渲染拓撲認證 (L2)**：二辦於隔離沙盒以該 JSON 試跑 A4 樣張，檢驗避頭尾字元法規與 30~40 字呼吸區間，通過後核發報告 `render_status: "100%_PASS"` 與 `[PASS_L2_RENDER_VERIFIED]` 呈報指揮所。
  4. **第四階段：指揮所最高落款與資產固化**：霸丸總指揮官 Jack 哥檢視雙重綠燈後下達落款令，系統正式賦予正式 ID（如 `Theme_Grid_Certified_01`），寫入 `02_Knowledge/Typography/`，並依收工 Hook 自動反向回寫至 `template/AGENTS.md` 一鍵安裝資產庫！

## 3.10 雙軌架構核心定錨與動態路徑解耦鐵律 (Single Source of Truth & Dynamic Path Abstraction)

| 核心維度 | G 槽真身金庫 (Single Source of Truth) | C 槽戰鬥鏡像 (NVMe Combat Mirror) | 跨電腦動態解耦標準 (Path Abstraction) |
| :--- | :--- | :--- | :--- |
| **本體定位** | • **唯一真理來源 (Single Source of Truth)**<br>• 所有永久資產、官方認證版型、知識庫、安裝包母體之神聖本體 | • **純高速戰鬥鏡像 (Combat Mirror)**<br>• 專供 NVMe 高速極速運算、編譯、無頭渲染，隨時可格式化重建 | • **杜絕寫死 `C:\Users\{username}`**<br>• 定錨根目錄 `C:\260728-code\` 或動態調用 `Path.home()` |
| **資料流向** | • **第一時間真身落地**<br>• 截圖投放、Bob 逆向草案、統帥落款產物一律第一時間寫入 G 槽 | • **單向受控投影**<br>• 僅作為本地讀取與執行使用，絕不在未經 G 槽真身固化前孤立落盤 | • **動態磁碟尋標 (`find_g_drive_truth`)**<br>• 無視 Google 雲端硬碟盤符 (G:/H:/D:) 飄移，遍歷 A-Z 自動捕獲 |
| **落款順序** | 1. 寫入 G 槽真身金庫 (`02_Knowledge/Typography/`)<br>2. 回寫 G 槽安裝包母體 (`工具安裝包/template/`) | 3. 單向鏡像至 C 槽戰鬥目錄 (`C:\260728-code\`) | 4. 登記進 G/C 雙軌 `handoff.md`，比對 SHA256 一致性綠燈 |

- **「真身在 G，戰鬥在 C，桌面為零」黃金基線**：
  - **截圖投放**：前端/客戶端上傳截圖，第一時間寫入 G 槽真身金庫（`G:\我的雲端硬碟\260803_opencode\samples\`），隨後單向二進位投影至 C 槽高速鏡像（`C:\260728-code\samples\`）。
  - **落款資產**：統帥最高落款簽發之資產，強制第一時間寫入 G 槽真身與 G 槽一鍵安裝包母體，最後才單向投影至 C 槽戰鬥鏡像。
  - **災難復原 (5分鐘滿血原地復活)**：在新電腦掛載 Google 雲端硬碟後，執行 `python install_opencode_complete.py`，動態尋標器秒級定位真身，自動建立根目錄 `C:\260728-code\`，完成 SHA256 雙軌對齊，路徑 100% 解耦使用者帳號！

## 3.11 影音自動化雙軌作戰矩陣 (Dual-Track AI Video Arsenal)

| 方案軌道 | 核心引擎 / 工具棧 | 適用情境與產出成果 | 自動化程度 |
| :--- | :--- | :--- | :--- |
| **方案 A<br>[旗艦級路演]** | CapCut Web API / JSON 橋接器<br>(`capcut_bridge.py` + SRT 字幕自動化) | • 黑客松/商業路演、行銷宣傳影片<br>• 轉場特效、動態圖表卡片、多軌音效 BGM | 80% (代碼生成分鏡+字幕，剪映內一鍵套用，人工調微距) |
| **方案 B<br>[全自動純工程]** | 無人值守純代碼流水線 (Headless)<br>Edge-TTS + Playwright + FFmpeg 壓制 | • 終端實機操作錄製、架構圖動態展示、技術教學手冊<br>• 1080P/60FPS 示範影片直出，零桌面污染入庫 G 槽 | 100% 全自動 (Zero-Touch)<br>丟指令 ➔ 30 秒自動生出 MP4 |

- **方案 B 核心實作 (`tools/auto_video_producer.py`)**：
  1. **自然神經網路語音**：調用 Edge-TTS 生成廣播級配音（美式 `en-US-ChristopherNeural` 或中文 `zh-TW-YunJheNeural`）。
  2. **規格化字卡排版**：底色 `#0B0F19`，底部安全半透明卡片 `rgba(15, 23, 42, 0.88)`，雙行字級差（48pt 白 ＋ 32pt 科技藍），杜絕微型字體。
  3. **FFmpeg 1080P/60FPS 無損封裝**：成品直通真身金庫 `G:\我的雲端硬碟\AI產出成品總庫\Videos_1080P\`，並單向投影至 C 槽鏡像，100% 遵守 Zero-Desktop Pollution！
