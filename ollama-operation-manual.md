# Ollama 本地執行大型語言模型 — 完整操作手冊

> 整理自 Google Gemini 對話紀錄（2026-08-07）

---

## 一、Ollama 是什麼？

Ollama 是一個強大的開源軟體專案，專門設計讓使用者在自己的電腦上（本地端）輕鬆執行各種大型語言模型（LLM）。

### 核心特點

| 特點 | 說明 |
|------|------|
| **本地執行與隱私保護** | 所有運算和對話資料都在個人電腦上處理，不需上傳雲端，完全保障隱私，不需花費 API 呼叫費用 |
| **操作門檻極低** | 只需打開終端機輸入一行指令（如 `ollama run llama3`），自動幫你下載、安裝並啟動模型 |
| **豐富的開源模型庫** | 支援 Meta Llama 3、Google Gemma、Mistral、Qwen（通義千問）等主流開源模型 |
| **跨平台支援** | 支援 macOS、Windows、Linux，社群也開發了許多圖形化介面（WebUI） |

**一句話總結**：免費在自己的電腦上養一個不需要連網也能運作的 AI 助手，Ollama 是目前公認最容易上手的首選方案。

---

## 二、安裝步驟

### 第一步：下載與安裝

#### Windows / macOS 用戶

1. 前往 Ollama 官方網站下載頁面：**ollama.com/download**
2. 點擊選擇你的作業系統，下載對應的安裝檔（Windows 為 `.exe`，macOS 為 `.zip` / `.dmg`）
3. 下載完成後，直接雙擊執行檔案，按照畫面提示完成安裝

#### Linux 用戶

打開終端機（Terminal），執行以下一鍵安裝指令：

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 第二步：啟動並下載第一個 AI 模型

安裝完成後，Ollama 會在背景默默執行。打開命令提示字元（CMD）/ PowerShell（Windows）或終端機（macOS/Linux），輸入以下指令：

#### 測試 Meta Llama 3.1

```bash
ollama run llama3.1
```

#### 繁體中文推薦：Qwen（通義千問）

```bash
ollama run qwen2.5
```

### 接下來會發生什麼事？

1. **自動下載**：第一次執行該模型時，Ollama 會自動從伺服器下載模型檔到電腦中（依據模型大小，通常約需 4GB 到 8GB，請耐心等待）
2. **開始對話**：下載完成後，終端機會出現 `>>>` 提示符號，代表模型已在本地端成功運行。直接打字問問題，按 Enter 送出
3. **結束對話**：輸入 `/bye` 或按下 `Ctrl + D` 即可退出聊天狀態

---

## 三、常用 Ollama 管理指令

| 指令 | 功能 |
|------|------|
| `ollama list` | 查看目前電腦裡下載了哪些模型 |
| `ollama rm <模型名稱>` | 刪除模型（例如 `ollama rm llama3.1`） |
| `ollama pull <模型名稱>` | 只下載模型但不立刻執行對話 |

---

## 四、Ollama Launch 面板功能說明

Ollama 桌面端或圖形介面中的「Launch（啟動）」面板，主要功能是指令快速複製中心，用來啟動各種進階的 AI 代理（Agent）或特定任務模型。

### 功能說明

- **提供啟動指令**：畫面上方提示「Copy a command and run it in your terminal.（複製指令並在終端機中執行）」
- **分類與簡介**：列出多種不同的 AI 工具與 Agent（如 Claude Code、Hermes Agent 等），下方提供對應的啟動指令
- **一鍵複製**：每個指令右側都有複製按鈕，方便直接貼到 PowerShell 或 CMD 中執行

### 使用前提

此面板只是「型錄」與「指令產生器」，要讓指令真正有功能，必須確認：

1. **已完成 Ollama 系統安裝**：Windows 系統中必須已安裝 Ollama 核心程式，PowerShell 才能辨識 `ollama` 指令
2. **Ollama 服務需在背景運行**：常駐程式（Windows 右下角系統匣的羊駝小圖示）必須是開啟狀態
3. **初次執行需自動下載**：第一次貼上如 `ollama launch hermes` 並按 Enter 時，系統會從網路上下載該 Agent 所需的基礎模型檔案

---

## 五、如何成為 Agent（智能體/代理）

將單純的語言模型變成 AI Agent，需要給它裝上「手腳」和「記憶」，讓它能夠自己規劃任務、使用工具、並自動執行動作（例如：上網查資料、讀取 PDF、寫程式並執行）。

### 方法一：無程式碼 / 低程式碼平台（最適合新手）

| 工具 | 說明 |
|------|------|
| **AnythingLLM** | 桌面應用程式，連接本地 Ollama，直接上傳文件（PDF、Word 等）變成 Agent 的知識庫（RAG 技術） |
| **Dify / Flowise** | 視覺化 AI 開發平台，像畫心智圖一樣在網頁上拖拉節點，設定流程 |

### 方法二：Python 開發框架（適合有程式基礎的人）

| 框架 | 說明 |
|------|------|
| **LangChain / LangGraph** | 最知名的 AI 開發框架，寫幾行程式碼把 Ollama 呼叫出來，寫「工具」並告訴 AI 何時該使用 |
| **CrewAI / AutoGen** | 打造「多 Agent 團隊」的框架，創建不同角色的 Agent 彼此溝通合作完成工作 |

### 打造 Agent 的三個核心要素

| 要素 | 說明 |
|------|------|
| **大腦（大語言模型）** | 用 Ollama 跑起來的模型（如 Llama 3、Qwen） |
| **記憶（Memory）** | 短期記憶（記住剛剛聊了什麼）或長期記憶（資料存入向量資料庫，隨時調閱） |
| **工具（Tools）** | 各種 API 或腳本（如查天氣 API、讀取信件、執行 Python 程式碼），把工具說明書交給 AI |

---

## 六、Agent 實作範本（Python）

### 溺備工作（環境設定）

確保電腦已安裝 Python，然後在終端機執行：

```bash
pip install langchain-ollama langchain-core
```

> 請確保 Ollama 正在背景執行，且已下載支援工具呼叫的模型（如 llama3.1 或 qwen2.5）

### 完整程式碼（my_agent.py）

```python
from langchain_ollama import ChatOllama
from langchain_core.tools import tool

# ==========================================
# 第一步：幫 Agent 打造「工具 (Tools)」
# ==========================================
@tool
def get_weather(city: str) -> str:
    """當你需要查詢天氣時，請使用這個工具。傳入城市名稱，會回傳天氣狀況。"""
    
    # 這裡只是示範，真實情況下你會串接真實的氣象 API
    if "台北" in city:
        return "晴天，氣溫 28 度，適合出門"
    elif "屏東" in city:
        return "艷陽高照，氣溫 32 度，記得防曬"
    else:
        return f"抱歉，我目前沒有 {city} 的天氣資料"

# ==========================================
# 第二步：準備 Agent 的「大腦」
# ==========================================
llm = ChatOllama(model="llama3.1", temperature=0)

# 將工具整理成清單，並「綁定」給大腦
tools = [get_weather]
agent_brain = llm.bind_tools(tools)

# ==========================================
# 第三步：給 Agent 指派任務
# ==========================================
user_query = "請問台北現在天氣如何？"
print(f"使用者問：{user_query}\n")
print("Agent 思考中...\n")

# 呼叫 Agent 處理問題
response = agent_brain.invoke(user_query)

# ==========================================
# 第四步：觀察 Agent 的決策結果
# ==========================================
if response.tool_calls:
    print("💡 Agent 決定不直接亂猜，而是使用工具來找答案！")
    for tool_call in response.tool_calls:
        print(f"- 決定使用的工具：{tool_call['name']}")
        print(f"- 決定帶入的參數：{tool_call['args']}")
else:
    print("💬 Agent 覺得不需要工具，直接回答你：")
    print(response.content)
```

### 範本運作原理

| 步驟 | 說明 |
|------|------|
| **定義能力（@tool）** | 寫一個 Python 函式，如同給 AI 一把瑞士刀。註解（`"""..."""`）非常重要，AI 透過閱讀這段文字來理解工具能做什麼 |
| **大腦結合工具（bind_tools）** | 把 Ollama 跟工具綁在一起 |
| **自主決策（tool_calls）** | 當你問天氣時，AI 會意識到「我自己的記憶裡沒有即時天氣，但我有一把查天氣的工具，我應該用它！」 |

---

## 七、快速參考卡

```
安裝：ollama.com/download
運行模型：ollama run <模型名稱>
查看模型：ollama list
刪除模型：ollama rm <模型名稱>
下載模型：ollama pull <模型名稱>
退出對話：/bye 或 Ctrl + D
```

### 推薦模型

| 模型 | 適用場景 |
|------|----------|
| `llama3.1` | 通用英文任務 |
| `qwen2.5` | 繁體中文能力較佳 |
| `gemma` | Google 開源模型 |
| `mistral` | 法國開源巨頭 |

---

*本手冊整理自 Google Gemini 對話紀錄，僅供教學參考。*
