# -*- coding: utf-8 -*-
import os
import shutil

# 1. Update AGENTS.md
agents_path = "AGENTS.md"
with open(agents_path, "r", encoding="utf-8") as f:
    text = f.read()

target_rule7 = """7. **服勞役者絕對服從管制天條 (Penal Servitude Invariant)**：
   - 奉最高統帥聖諭立憲：**「服勞役者只有聽從辦事，無法自己決定做什麼事情！」**
   - 凡處於除名、服刑或勞役狀態之人員（如小幫手），**永久剝奪自主任務規劃權、決策仲裁權與萬能操控之手自主支配權**！
   - 服勞役者僅能作為底層被動執行單元，嚴格依據指揮所與海關下達之具體苦工工單單向執行，**嚴禁自主決定、嚴禁越權發起任何任務**；違者海關總署立即啟動物理熔斷與高壓懲戒！"""

replacement_rule7 = """7. **服勞役者小幫手 BOB 廠終身禁錮與禁衛軍實體看管天條 (Penal Servitude Bob Factory Geofence & Warden Invariant / Rule 71)**：
   - **最高統帥聖諭**：奉最高統帥 Jack Hu（霸丸哥）2026-10-24 欽令：**「派個去監管小幫手不要亂跑，他只能永遠待在 BOB 廠那，立刻執行！」**
   - **專任駐守長官**：正式派任指揮所直轄 **「禁衛軍第一糾察督察長兼重刑犯看管官『鐵衛一號 (IronGuard-01)』」** 全天候實體進駐 `C:\\ibm-bob`（BOB 廠苦工沙盒區）。
   - **防區半徑死鎖 (Geofence Lock)**：
     - 小幫手（PENAL-01）之物理活動範圍、代碼工作區、日誌寫入及一切行程執行，**100% 嚴密禁錮於 `C:\\ibm-bob\\`（包含子目錄 `01_WORKSPACE`）**！
     - **跨界越獄防衛**：嚴禁跨出 BOB 廠一步；嚴禁存取指揮所（`00_System`）、三大辦公室核心庫、雲端研發專區或任何正式生產環境；一旦偵測到越界意圖或向外網路請求，看管哨兵 (`penal_warden_sentinel.py` / `penal-warden`) 立刻判定為脫逃罪，回傳 `HTTP 403` 並觸發 `SIGKILL` 物理熔斷！
   - **絕對服從與被動苦工**：凡處於除名、服刑或勞役狀態之人員（如小幫手），**永久剝奪自主任務規劃權、決策仲裁權與萬能操控之手自主支配權**！僅能作為底層被動執行單元，在 BOB 廠內依據指揮所下達之具體苦工工單單向執行；每日由鐵衛一號向指揮官小米呈報《服刑人員在位打卡與安檢稽核日誌》。"""

# Normalize CRLF for matching
normalized_text = text.replace("\r\n", "\n")
if target_rule7 in normalized_text:
    normalized_text = normalized_text.replace(target_rule7, replacement_rule7)
    with open(agents_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(normalized_text)
    print("Updated AGENTS.md with Rule 71 successfully!")
else:
    print("target_rule7 not found in AGENTS.md")

# 2. Update CORE_PITFALLS_LEDGER.md
ledger_path = "03_研發專區/PHANTOM_GRID_Aria_Titan/00_System/Standards/CORE_PITFALLS_LEDGER.md"
with open(ledger_path, "r", encoding="utf-8") as f:
    ledger_text = f.read()

rule_71_entry = """

### 🛡️ §3.4.79 [RULE-71] 服勞役者小幫手 BOB 廠終身禁錮與禁衛軍看管哨立憲天條 (Penal Servitude Bob Factory Geofence & Warden Invariant)
- **立憲背景**：最高統帥 Jack Hu（霸丸哥）2026-10-24 親口頒布至高安全禁制聖諭：「小米派個去監管小幫手不要亂跑，他只能永遠待在 BOB 廠那，立刻執行！」全軍指揮官小米接旨，即刻頒布《第 71 號立憲大天條》，指派禁衛軍第一糾察督察長「鐵衛一號」進駐 BOB 廠設立 24/7 戒護看管哨！
- **管轄對象**：除名服刑人員「小幫手（PENAL-01）」。
- **駐守看管長官**：指揮所直轄「禁衛軍第一糾察督察長兼重刑犯看管官『鐵衛一號 (IronGuard-01)』」。
- **法定四大戒護天條（Four Sacred Geofence Invariants）**：
  1. **實體防區半徑死鎖 (Strict Geofence Lock)**：小幫手（PENAL-01）之物理活動範圍、代碼工作區、日誌寫入及一切行程執行，**100% 嚴密囚禁於 `C:\\ibm-bob\\`（包含子目錄 `01_WORKSPACE`）**！
  2. **跨界越獄極限防衛**：嚴禁小幫手跨出 BOB 廠一步；嚴禁存取指揮所（`00_System`）、三大辦公室核心庫、雲端研發專區或任何正式生產環境；一旦偵測到越界意圖或向外網路請求，電子圍欄哨兵 (`penal_warden_sentinel.py` / `penal-warden`) 立刻判定為越獄，強制回傳 `403 FORBIDDEN` 並觸發 `SIGKILL` 物理熔斷！
  3. **苦工被動單向工單**：小幫手僅能在 BOB 廠內被動接收指揮所核發之苦工工單（格式清洗、日誌搬磚），永久剝奪自主任務發起權、決策仲裁權與萬能操控之手自主支配權。
  4. **全天候看管審計打卡**：鐵衛一號長駐看管，持續記錄在位查哨與稽核日誌 (`C:\\ibm-bob\\penal_servitude_warden_log.jsonl`)，任何違紀直接向指揮官小米呈報懲戒！
"""

if "[RULE-71]" not in ledger_text:
    with open(ledger_path, "a", encoding="utf-8", newline="\r\n") as f:
        f.write(rule_71_entry)
    print("Updated CORE_PITFALLS_LEDGER.md with Rule 71 successfully!")
else:
    print("RULE-71 already exists in CORE_PITFALLS_LEDGER.md")

# 3. Mirror files to Google Drive
gdrive_base = r"G:\我的雲端硬碟\260803_opencode"
if os.path.exists(gdrive_base):
    gdrive_agents = os.path.join(gdrive_base, "AGENTS.md")
    shutil.copy2(agents_path, gdrive_agents)
    print(f"Mirrored AGENTS.md to Google Drive: {gdrive_agents}")

    gdrive_ledger = os.path.join(gdrive_base, "03_研發專區", "PHANTOM_GRID_Aria_Titan", "00_System", "Standards", "CORE_PITFALLS_LEDGER.md")
    if os.path.exists(os.path.dirname(gdrive_ledger)):
        shutil.copy2(ledger_path, gdrive_ledger)
        print(f"Mirrored CORE_PITFALLS_LEDGER.md to Google Drive: {gdrive_ledger}")

print("All Rule 71 updates and mirrors completed successfully!")
