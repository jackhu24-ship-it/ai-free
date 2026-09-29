# 🛠️ WeAreDevelopers x BAND: Dark Factory — 今日踩坑與實戰經驗全景手冊
> **專案**：PHANTOM DARK FACTORY (Lights-Out Software Building Engine)  
> **日期**：2026-09-28  
> **統帥**：霸丸總指揮官 Jack Hu  
> **特化支援**：特助小幫手軍團 ＋ 小米審查標準  
> **交接代號**：Milestone 243  
> **本地存檔**：`dark_factory_delivery/PITFALLS_AND_LESSONS_LEARNED.md`  
> **金庫總庫**：`G:\我的雲端硬碟\AI產出成品總庫\AI_DARK_FACTORY_DELIVERY\PITFALLS_AND_LESSONS_LEARNED.md`  

---

## 🎯 總覽：九大實戰踩坑病灶與根治解法

在本次 WeAreDevelopers x BAND: Dark Factory 國際黑客松從無到有、超前一週滿分交卷的極限推進過程中，我們遭遇並徹底攻克了涵蓋 **系統終端、影音合成、排版渲染、官方評測線具、失格防線與平台表單** 等 9 大層面的深度技術陷阱。

為貫徹統帥指示：**「把今天的踩坑多記錄起來，下次賽事就不會犯同樣的錯了」**，以下整理全景踩坑診斷書與全域標準解法，供全體 Agent 與未來所有黑客松永久恪守！

---

### 坑 1：Windows PowerShell 命令列過長截斷與多行引號溢出

* **【病灶現象】**：
  在 Windows PowerShell 環境下，當試圖透過 `python -c "..."` 或 `@' ... '@` 傳遞包含 HTML 標籤、換行符號、單雙引號混合或超過數千字元的多行腳本時，PowerShell 會丟出：
  * `The filename or extension is too long`（命令列參數超出 Windows 8,191 字元上限）。
  * `SyntaxError: unterminated triple-quoted string literal`（換行符被截斷導致字串未閉合）。
  * `MissingExpressionAfterToken`（PowerShell 特殊符號如 `$`, `,`, `()` 被誤解析）。
* **【根治解法】**：
  * **嚴禁命令列直傳大段代碼**：任何超過 10 行或帶有 HTML/CSS/JSON 的腳本，**一律先使用檔案寫入工具落盤為本機 `.py` 檔案**（如 `scratch/xxx.py`）。
  * **標準調用方式**：落盤後，僅透過 `python -X utf8 scratch/xxx.py` 調用執行，徹底隔離終端引號解析陷阱！

---

### 坑 2：1080P 技術展示影片文字水平重疊（PIL Font Bounding Box）

* **【病灶現象】**：
  在第一代動態影片影格合成中，Act 3 頂部狀態標題 `[HOLDOUT PRINCIPLE ENFORCED]` 與右側標籤 `STRICT READ-ONLY SANDBOX` 直接在畫面上打架、重疊在一起，導致評審完全無法閱讀。
  * **原因**：開發者習慣寫死固定像素座標（如 `x = 800`），但動態內容的字數與字型度量不同，一旦字型略大或文字增長，直接發生幾何撞車。
* **【根治解法】**：
  * **動態長度計算**：全面改用 `font.getbbox(text)` 精確計算文字寬度：
    ```python
    bbox = font.getbbox(label_text)
    text_width = bbox[2] - bbox[0]
    next_x = start_x + text_width + PADDING
    ```
  * **雙層解耦排版法則**：當單行訊息包含「狀態核心」與「防禦說明（如 SHA-256）」時，嚴禁強塞在同一行！強制拆為雙層：
    * **第一層**：`[HOLDOUT PRINCIPLE ENFORCED]` ＋ 金黃色標籤 `STRICT READ-ONLY SANDBOX`。
    * **第二層**：`SHA-256 IMMUTABILITY SEAL VERIFIED` 獨立下移 `y + 28px`，達到 **0 像素重疊、字字分明**！

---

### 坑 3：影片旁白與字幕脫節（Edge-TTS SentenceBoundary 毫秒級對齊）

* **【病灶現象】**：
  傳統影片常使用獨立 SRT 字幕或靜態字幕，但在快節奏的 2 分鐘技術展示中，若旁白與終端畫面切換存在 0.5 秒以上的延遲，評審的大腦就會產生認知失調，甚至看不懂日誌在跑什麼。
* **【根治解法】**：
  * **逐句時間戳提取**：利用 Edge-TTS 原生提供的 `SentenceBoundary` 事件，將整篇旁白的每一句話精確擷取到微秒級 `offset` 與 `duration`。
  * **底部逐字稿全景字幕列（Verbatim Subtitle Bar）**：
    * 在畫面底部 `[40, 940, 1880, 1050]` 劃定深科技藍玻璃擬態框。
    * 每一影格依當前播放時間 `t`，精確匹配並渲染當前那一句話（20pt 粗體白字＋金黃色 `[AI NARRATOR]` 標籤），達到電視新聞級的字音同步！

---

### 坑 4：資訊過載導致視覺迷航（「講到那指到那」動態指引全覆蓋）

* **【病灶現象】**：
  1080P 技術展示影片資訊密度極高（左有即時終端輸出、右有架構卡片與評測指標）。如果旁白講到「120/120 通過」，評審的眼睛還在看左側終端的程式碼，就會錯過核心戰果。
* **【根治解法】**：
  * **焦點動態矩陣（Focus Mapping）**：依時間軸將旁白提到的關鍵特徵與畫面區域綁定：
    * 念到「DAG 任務拆解」➔ 架構師卡片外框發光（Cyan Neon）。
    * 念到「FastAPI 端點並行」➔ 終端日誌亮起高光綠條。
    * 念到「120/120 官方全綠」➔ 右側評測大盤全亮，並動態繪製多邊形向量箭頭 `▶ [ACTIVE: 120/120 PASS]` 緊緊指向戰果！
  * 此規範已正式沉澱為全域技能 `hackathon-demo-video-pipeline`。

---

### 坑 5：16:9 賽事封面圖全平台裁切與文字溢出

* **【病灶現象】**：
  原始封面圖的綠色按鈕 `STATUS: 100% READY FOR REVIEW` 字體過大且未經邊界校驗，文字右端直接衝破綠色線框外；且在 Lablab.ai 等賽事平台的手機版或瀑布流卡片中，靠近邊緣的字容易被裁切。
* **【根治解法】**：
  * **安全裁切區（Safe Margin）**：距離四周邊緣保留至少 60px 安全空白。
  * **精確程式化置中（Programmatic Centering）**：
    ```python
    btn_w = bbox[2] - bbox[0]
    btn_h = bbox[3] - bbox[1]
    text_x = box_left + (box_width - btn_w) // 2
    text_y = box_top + (box_height - btn_h) // 2
    ```
  * 將按鈕字體設定為 24pt Arial Bold，副標題設定為 20pt Bold，保證左右各預留 54px 安全空間，在任何平台縮圖下均 100% 完美置中！

---

### 坑 6：Playwright 轉 A4 橫式無損 PDF 之分頁斷裂

* **【病灶現象】**：
  使用 HTML/CSS 生成簡報 PDF 時，若未嚴格約束 CSS 分頁屬性，瀏覽器渲染器會隨機將對開頁切成上下半張，或者在末端產生多餘空白頁。
* **【根治解法】**：
  * **精確 `@page` 宣告**：
    ```css
    @page {
      size: 297mm 210mm; /* A4 橫向 */
      margin: 0;
    }
    .sheet {
      width: 297mm;
      height: 210mm;
      page-break-after: always;
      box-sizing: border-box;
      overflow: hidden;
    }
    ```
  * **Playwright 渲染參數**：必須傳入 `prefer_css_page_size=True, print_background=True`，確保背景深色漸層與金屬扣環 100% 原汁原味輸出為向量無損 PDF！

---

### 坑 7：Tablekeeper Stage 1 官方 Harness 深度陷阱（DST 夏令時與型別嚴檢）

* **【病灶現象】**：
  官方評測線具（`harness`）在 Stage 1 安排了極為嚴苛的邊界陷阱，稍有不慎即會被扣分或整組報錯：
  * **夏令時切換重複小時（Fall-back DST Ambiguity）**：秋季時間回撥 1 小時，同一個本機時間（如 02:00）會出現兩次！若未處理，預約時間戳會發生漂移或衝突。
  * **查詢參數弱型別注入**：`/availability` 端點若傳入 `party_size=2.5` 或字串，未嚴格校驗會引發內部 500。
  * **批次搬移原子性**：`/reservation-moves` 搬移 1~8 筆預約時，只要有 1 筆在目標時段無座位，必須全量 rollback，不可局部搬移。
* **【根治解法】**：
  * **時區防禦**：使用 Python 標準庫 `zoneinfo.ZoneInfo`，並在時鐘轉換中顯式指定 `fold=0`（選擇第一個發生的小時）：
    ```python
    dt = dt.replace(fold=0)
    ```
  * **嚴格參數校驗**：使用 Pydantic v2 `StrictInt` 與自定義正規表示式，阻斷非整數輸入。
  * **記憶體交易狀態機（Transaction Isolation）**：在執行搬移前先對記憶體狀態做 deepcopy，全部檢查通過才一次性提交，確保 120/120 測試道道秒通關！

---

### 坑 8：Dark Factory 失格檢查線（嚴禁修改 Test Harness）

* **【病灶現象】**：
  許多 AI 參賽團隊為了讓測試變綠，會讓 Agent 修改測試案例（Assertion Tampering），這在 Dark Factory 與各大賽事中屬於 **第一死罪（Immediate Disqualification）**！
* **【根治解法】**：
  * **Holdout 隔絕驗證原則（Decoupled Evaluation）**：
    * 測試集（`tests/`, `harness/`）設為唯讀沙箱，Agent 的工具權限只開放實作目錄（`src/`）。
    * 執行前後比對測試集的 SHA-256 密碼學雜湊值，若有任何 1 個 byte 被變更，立即判定為作弊失格並中止交付！

---

### 坑 9：Lablab.ai Step 3 表單字數上限截斷（2000 Characters Limit）

* **【病灶現象】**：
  在最後交卷 Step 3 of 3（Application）的 `Additional Information` 欄位中，官方設有 `0 / 2000 characters` 硬性限制。若直接將長達 5,000 字元的完整公文貼入，前端表單會直接紅字報錯或切斷後半截關鍵說明。
* **【根治解法】**：
  * **精準提煉 1,750 字元硬核短文**：
    * 將公文精煉為 4 大黃金模組：① 賽事核心願景（"Build a factory that doesn't need you"）；② 官方 Tablekeeper 120/120 測試全綠戰果；③ Holdout 防過度擬合沙箱；④ <200ms 自愈循環與開源倉庫。
    * 字數精確控制在 1,750 字元，安全保留 250 字元餘裕，一鍵複製秒通關！

---

### 坑 10：外部傭兵與第三方 IDE 預設開啟家目錄污染核心庫坑

* **【病灶現象】**：
  新安裝之外部 AI 編輯器（如 IBM Bob、Cursor 等）啟動時，若直接點擊 Open Folder 或預設載入，會自動指向 `C:\Users\user\` 或打開最近使用的主專案目錄。一旦讓外部不可信 Agent 讀取整顆硬碟，極易造成私人 Key 外洩或污染核心 13 庫代碼。
* **【根治解法】**：
  * **物理 DMZ 隔離區前置**：在啟用任何外部工具前，必須先建立受限特區目錄（如 `C:\ibm-bob\`，內含 `00_INBOX`、`01_WORKSPACE`、`02_OUTBOX`、`03_QUARANTINE`）。
  * **強制路徑檢查**：開啟 IDE 第一時間必須手動執行 `File -> Open Folder` 鎖定在沙盒資料夾；嚴禁讓傭兵存取父目錄或 G 槽金庫！

---

### 坑 11：瀏覽器 OAuth 授權與本機回調連接埠（127.0.0.1:port）攔截坑

* **【病灶現象】**：
  在進行第三方平台（如 IBMid）登入授權時，瀏覽器通過驗證後會跳出「此網站試圖開啟 IBM Bob (http://127.0.0.1:xxxxx)」之系統對話框。若使用者誤按「取消」或關閉瀏覽器，本機 IDE 會無限期處於等待 Token 狀態而假死。
* **【根治解法】**：
  * **勾選一律允許並點擊開啟**：明確勾選「一律允許 http://127.0.0.1:xxxxx 在相關應用程式中開啟」，並點擊【開啟】，將 OAuth 憑證正常回傳本地監聽埠，秒級點亮 AI 面板。

---

### 坑 12：Token 消耗額度與上下文視窗容量（Context Window）混淆坑

* **【病灶現象】**：
  看到介面顯示 `17.0k / 270.0k` 時，常誤以為進度條要跑到 270k 才算完工，造成不知何時結束的焦慮。
* **【根治解法】**：
  * **正確認知容量 vs 進度**：`270.0k` 是大腦記憶體容量上限（Context Window），`17.0k` 是目前已耗用 Token。
  * **完工判斷三要素**：① 旋轉圖示停止（變成靜態或勾勾）；② 對話框輸出最後完成總結文本；③ 底部重新出現白底輸入框；此時代表本輪生成結束！

---

### 坑 13：外掛傭兵自動化頻繁卡頓與多級審批等待坑（Approve for Task）

* **【病灶現象】**：
  外部傭兵在執行任務時，每讀取一個檔案或執行一條指令（如 `Get-Content` 或 `pytest`），都會彈出授權對話框。若只點選 `Approve once`，任務中途會反覆停擺等待人工點擊，喪失自動化極速優勢。
* **【根治解法】**：
  * **沙盒內全權授權**：既然已在物理隔離沙盒（`C:\ibm-bob\`）內，直接點選 **【✓ Approve for task】**，授權該任務完整執行鏈路，讓傭兵一口氣自動完成讀取、寫檔與單元測試。

---

### 坑 14：外部傭兵代碼直入核心缺乏三辦壓測之閉環缺漏坑

* **【病灶現象】**：
  傭兵寫出的代碼雖然通過基本測試，但可能隱含記憶體洩漏、未處理之邊界異常或缺乏抗混沌能力。若直接由指揮所落款入庫，會降低核心系統之反脆弱性。
* **【根治解法】**：
  * **憲法第 19 條六部曲鐵律生效**：
    1. 二辦擬草案 ➔ 2. 指揮所脫敏空投 ➔ 3. 傭兵算力施工 ➔ 4. 海關三快篩去毒 ➔ **5. 第三辦公室 1,500 次混沌壓測與及格認證（GRADUATION_CERTIFICATE.md）** ➔ 6. 統帥雙簽落款登錄第 13 庫！全流程閉環，缺一不可！

---

## 🏆 全域十全大補防坑速查手冊（Quick Checklist for Next Hackathon）

| 環節 | 踩坑風險 | 必備防禦標準 |
| :--- | :--- | :--- |
| **終端腳本** | PowerShell 引號與換行溢出 | 嚴禁 `-c "..."` 傳長字串，一律落盤 `.py` 後調用 |
| **影片文字** | 標籤說明文字重疊碰撞 | `font.getbbox` 動態算寬 ＋ 雙層解耦排版 |
| **影片旁白** | 字幕與畫面切換脫節 | Edge-TTS `SentenceBoundary` 毫秒級底部逐字稿 |
| **視覺動態** | 評審視覺疲勞迷航 | 「講到那指到那」發光外框 ＋ 多邊形向量箭頭追蹤 |
| **賽事封面** | 各平台縮圖裁切破邊 | 預留 60px 安全區 ＋ 程式化雙向精確置中 |
| **簡報生成** | Playwright 轉 PDF 隨機斷頁 | CSS `@page { size: 297mm 210mm; margin: 0; }` ＋ `.sheet { page-break-after: always; }` |
| **評測線具** | 歐美 DST 夏令時重複小時 | Python `zoneinfo.ZoneInfo` 明確設定 `fold=0` |
| **防失格線** | 竄改測試集被判作弊 | Holdout 隔離原則：測試集 Read-Only ＋ SHA-256 密碼學核簽 |
| **表單提交** | 平台 2000 字元長度限制 | 濃縮提煉 1,500~1,800 字元四要素黃金公文 |
| **外部傭兵** | 編輯器預設開啟全硬碟污染 | 強制建立 `C:\ibm-bob\` DMZ 四特區並鎖定單一目錄 |
| **OAuth授權** | 瀏覽器回傳被攔截假死 | 勾選一律允許並點擊【開啟】，將憑證回傳 127.0.0.1 監聽埠 |
| **上下文認知** | 誤將 270k 容量當作進度條 | 認清 270k 為大腦容量上限，以旋轉停止與文字總結為完工依據 |
| **審批授權** | 頻繁 Approve once 造成停擺 | 沙盒內直接點選【Approve for task】授權全任務自動跑完 |
| **閉環交接** | 傭兵產出未經壓測直入核心 | 嚴格執行憲法第 19 條六部曲：海關去毒 ＋ 三辦混沌壓測後方可雙簽落款 |
| **技能複用** | 單機開發換環境消失 | 六大節點鋪設 ＋ chezmoi dotfiles Git 永久固化 |

---

**手冊制定**：PHANTOM GRID 總指揮官 Jack Hu ＋ 特助小幫手軍團  
**生效日期**：2026 年 09 月 29 日（全域最新增補，永久生效）

