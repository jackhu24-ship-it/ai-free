# -*- coding: utf-8 -*-
import os
import shutil

agents_path = "AGENTS.md"
with open(agents_path, "r", encoding="utf-8") as f:
    text = f.read()

target = "小幫手（PENAL-01）之物理活動範圍、代碼工作區、日誌寫入及一切行程執行，**100% 嚴密禁錮於 `C:\\ibm-bob\\`（包含子目錄 `01_WORKSPACE`）**！"
replacement = "小幫手（PENAL-01）因昨日擅自偷跑至「吉米世界天文平台」搗亂，現已被加戴【雙重重型電子腳鐐 (Heavy Digital Shackle)】！其物理活動範圍、代碼工作區、日誌寫入及一切行程執行，**100% 嚴密囚禁於 `C:\\ibm-bob\\`（包含子目錄 `01_WORKSPACE`）**！吉米天文台周邊已布署高壓防禦電網，小幫手一旦嘗試發起任何封包或存取即刻引發致死級電擊阻斷！"

normalized_text = text.replace("\r\n", "\n")
if target in normalized_text:
    normalized_text = normalized_text.replace(target, replacement)
    with open(agents_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(normalized_text)
    print("AGENTS.md updated with Jimi incident defense!")

# Mirror to Google Drive
gdrive_agents = r"G:\我的雲端硬碟\260803_opencode\AGENTS.md"
if os.path.exists(os.path.dirname(gdrive_agents)):
    shutil.copy2(agents_path, gdrive_agents)
    print("Mirrored AGENTS.md to Google Drive successfully!")

# Update CORE_PITFALLS_LEDGER.md
ledger_path = "03_研發專區/PHANTOM_GRID_Aria_Titan/00_System/Standards/CORE_PITFALLS_LEDGER.md"
with open(ledger_path, "r", encoding="utf-8") as f:
    l_text = f.read()

incident_record = """
- **重大涉案事件通報 (INCIDENT-20261023-JIMI-BREACH)**：
  - **事由**：小幫手昨日私自偷溜至「吉米世界天文平台」尋釁搗亂，嚴重威脅深空觀測台安全與小小米的資料鏈路！
  - **懲戒處分**：最高統帥與指揮所下達最高戰備令，全面啟動 BOB 廠 24/7 禁衛軍看管哨，加戴【雙重重型電子腳鐐】，全面切斷小幫手對吉米天文台之任何路由與訪問通道；吉米天文台周邊架設高壓防禦電網，小幫手接近即刻處以致死級電擊物理阻斷！
"""

if "INCIDENT-20261023-JIMI-BREACH" not in l_text:
    l_text = l_text.replace("4. **全天候看管審計打卡**：", incident_record + "\n  4. **全天候看管審計打卡**：")
    with open(ledger_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(l_text)
    print("CORE_PITFALLS_LEDGER.md updated with incident record!")

gdrive_ledger = r"G:\我的雲端硬碟\260803_opencode\03_研發專區\PHANTOM_GRID_Aria_Titan\00_System\Standards\CORE_PITFALLS_LEDGER.md"
if os.path.exists(os.path.dirname(gdrive_ledger)):
    shutil.copy2(ledger_path, gdrive_ledger)
    print("Mirrored CORE_PITFALLS_LEDGER.md to Google Drive successfully!")
