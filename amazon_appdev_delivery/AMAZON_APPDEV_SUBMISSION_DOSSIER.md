# Amazon Developer Hackathon: Build, Ship, Shape (2026)
## PHANTOM GRID 全球旗艦賽事作戰公文與備戰指南

> **戰隊名稱**：PHANTOM GRID (Closed Solo Mode)  
> **總指揮官**：Jack Hu (霸丸哥)  
> **參賽身分**：Solo Developer + 特化 Agent 軍團  
> **官方平臺**：Devpost (https://amazonappdev2026.devpost.com/)  
> **專案公開展台**：https://devpost.com/software/phantom-grid-alexa-autonomous-sre-hub  
> **交卷狀態**：✅ **已正式成功交卷（Project submitted!）**（超前 25 天滿分鎖定評選資格）  
> **截止時間**：2026 年 10 月 24 日 上午 03:00 GMT+8（October 23, 2026 at 03:00pm EDT）  
> **總獎金池**：,000 美元現金 ＋ ,000 AWS 抵用金（總值 ,000 美元）  

---

## 賽道鎖定與戰略定位

本賽事由 Amazon Developer 官方主辦，涵蓋五大賽道：

| 賽道名稱 | 官方核心要求 | PHANTOM GRID 契合度 | 戰略推薦度 |
| :--- | :--- | :---: | :---: |
| **Alexa+ Track** | 自建 Model Context Protocol (MCP) 伺服器、自訂 Agent Skills、多模態智慧語音助理 | 5星 | **首選（極致契合）** |
| **AWS Builder Mini Challenge** | Amazon Bedrock、AgentCore、SageMaker 整合構建自治工作流 | 5星 | **加分兼報（雙重獲獎機會）** |
| **Bee (Wearable AI)** | 智慧穿戴設備傳感器、即時運動/健康狀態反饋 | 3星 | 備選 |
| **Ring** | 智慧家庭防護、自動化安防偵測事件流 | 3星 | 備選 |
| **Fire TV** | Vega OS / Fire OS 客廳大螢幕互動娛樂體驗 | 2星 | 備選 |

### 推薦殺手級專案概念：Phantom Alexa+ Autonomous Operations Hub
- **核心架構**：以 FastMCP / stdio / SSE 協議為骨幹，將 Alexa+ 與自體代碼修復、智慧家庭監控、IoT 設備反饋、以及無人暗廠自治工作流深度串接。
- **亮點技術**：
  1. **標準 MCP Tools 擴充**：提供 Alexa+ 專屬之 10+ 組工具集（代碼執行、容器巡檢、數據快照、語音反饋）。
  2. **毫秒級即時狀態機**：整合 WebSocket / SSE，在 Alexa 終端與網頁看板同步推送。
  3. **方案 B 1080P 技術實機影片**：全面沿用今日固化之 hackathon-demo-video-pipeline 打造發布會級動態實機展示。

---

## 作戰里程碑推進表

- **Phase 1（現階段）**：賽事後勤專區與架構藍圖確立（已完成）。
- **Phase 2（10/01 - 10/10）**：核心 MCP Server 與 Alexa+ Skill 接口原型鍛造。
- **Phase 3（10/11 - 10/18）**：整合測試、Chaos Verifier 壓測、雙向狀態大盤。
- **Phase 4（10/19 - 10/22）**：1080P 方案 B 影片渲染、A4 橫向 Pitch Deck PDF、官方 Dossier 封裝。
- **Phase 5（10/23）**：提前 24 小時 Devpost 官方滿分交卷！

---

## 交付與備份路徑（嚴格死守憲法第 11 條）

- **本地高速戰鬥鏡像**：amazon_appdev_delivery/
- **雲端硬碟真身金庫**：G:\我的雲端硬碟\AI產出成品總庫\AMAZON_APPDEV_2026_DELIVERY\


---

## 📋 小米整理之官方核心繳交規範與評審標準（100% 嚴格對齊）

### 一、 繳交資料標準（Submission Requirements）
1. **可運行的展示成品（Working Project / Demo）**：
   - 需提供公開可訪問的線上演示連結（URL）或可供評審測試的環境與測試帳號憑據。
   - 必須實際串接並運行競賽指定技術，僅在文件中提及技術名稱而不含實際功能會被視為不合格。
2. **公開程式碼庫（Public GitHub Repository）**：
   - 須包含專案完整的原始碼。
   - 需附上詳細的 README.md，清楚列出環境建置步驟、依賴套件、架構說明以及如何本機運行或測試的指示。
3. **展示影片（Demo Video）**：
   - 時長限制：3 分鐘以內（上傳至 YouTube/Vimeo 公開/不公開連結）。
   - **官方 Demo 影片直達連結**：`https://youtu.be/svW3_FiVXPs`（片長 1:55，1080P）
   - 影片內容：需說明專案欲解決的問題、系統/代理（Agent）技術架構，以及完整 End-to-End 的操作流程示範。
   - 嚴格遵守憲法第 13 條 hackathon-demo-video-pipeline（文字動態算距零重疊、底部逐字稿全景字幕列、講到那指到那動態指引）。
4. **Amazon 工具產品反饋（Product Feedback）**：
   - 在 Devpost 提交表單中撰寫對所使用 Amazon / AWS 工具、SDK 或模擬器的硬核使用心得與專業改進建議。
5. **技術堆疊要求（Tech Stack）**：
   - 主賽道（Tracks）：首選 **Alexa+**（Agent Skills、自建 FastMCP 伺服器整合）。
   - AWS / AI 服務：**Amazon Bedrock**、**AgentCore**、**AWS Lambda** 整合構建自治工作流。

### 二、 評審審查標準（Judging Criteria）
1. **技術實作與難度（Technological Implementation）**：深度運用 Alexa+ MCP 與 AWS Bedrock，架構高可用與容錯。
2. **創意與創新度（Quality of Idea & Innovation）**：將無人暗廠（Lights-Out Autopilot）與 Alexa+ 智慧語音中樞結合之獨創性。
3. **潛在影響力與實用價值（Potential Impact & Value）**：解決真實開發者/維運工程師的深夜告警與自動自治修復痛點。
4. **使用者體驗與設計（Design & Ease of Use）**：3D 視覺儀表板、SSE 毫秒級串流、語音對話自然流暢。
5. **展示完整度（Demonstration）**：發布會級 1080P 方案 B 影片、GitHub README 完備度、零人工作業震撼感。

### 三、 關鍵時程與安全防線
- **繳交截止時間**：2026 年 10 月 23 日 17:00 EDT（台灣時間 2026 年 10 月 24 日 上午 03:00 GMT+8）。
- **提早 24 小時交卷防線**：預計 2026 年 10 月 22 日前完成 Devpost 草稿、公開 GitHub、YouTube 影片測試。
