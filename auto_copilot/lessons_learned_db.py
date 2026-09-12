"""
AutoCopilot Lessons Learned Failure Database & Knowledge Graph Manager
======================================================================
依據 霸丸總指揮官 組織級安全文化與數位資產庫大令：
歸檔實車 Shadow Mode、HIL 極限邊界注入與測試過程中的所有異常日誌，
形成專屬的「車規失效案例知識圖譜 (Knowledge Graph)」，反哺新車型研發。
"""

import json
import logging
import os
import sys
import time
from typing import Any, Dict, List

# Windows UTF-8 控制台保護
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(CURRENT_DIR, "docs")
os.makedirs(DOCS_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("AutoCopilot.LessonsLearned")


FAILURE_ONTOLOGY = [
    {
        "failure_code": "FAIL-CRC-001",
        "category": "ROOT_ELECTRICAL_NOISE",
        "title": "高壓逆變器 IGBT 開關引發之 CAN-FD 總線位元翻轉 (Bit-Flip)",
        "symptom": "連續 2~3 幀 CRC-8 校驗失敗，Alive Counter 丟失",
        "root_cause": "雙絞線遮蔽層接地阻抗不良，高頻 PWM 電磁脈衝耦合至通訊線束",
        "countermeasure": "AUTOSAR E2E Profile 1 演算法三級抑制 + 產線 60Ω 終端阻抗校驗",
        "verification_evidence": "TC-SEC-01 (4.78ms 抑制) & EOL Step 3"
    },
    {
        "failure_code": "FAIL-TIM-002",
        "category": "ROOT_TIMING_JITTER",
        "title": "Linux/RTOS 多任務調度引發之看門狗逾時抖動 (Timing Jitter)",
        "symptom": "週期性遙測心跳間隔由 50ms 突增至 210ms，觸發安全降級",
        "root_cause": "日誌記錄未採用非同步 I/O，阻塞主調度任務時間片",
        "countermeasure": "遷移至硬體計時器 (Windowed Watchdog) + 微秒級中斷服務常式 (MCAL ISR)",
        "verification_evidence": "TC-HIL-03 (200ms 剛性關斷)"
    },
    {
        "failure_code": "FAIL-THM-003",
        "category": "ROOT_THERMAL_DRIFT",
        "title": "長爬坡重載工況冷卻水溫突破 105°C 熱失控邊界",
        "symptom": "電機溫度達到 108°C，駕駛員持續深踩油門",
        "root_cause": "散熱風扇繼電器作動延遲，單純依賴儀表警示不足以防範熱衰竭",
        "countermeasure": "雙軌影子模式檢出 Discrepancy ➔ 100ms 內強制作動限扭 (DEGRADED_WARN)",
        "verification_evidence": "TC-HIL-05 (動態實證沉澱)"
    },
    {
        "failure_code": "FAIL-AI-004",
        "category": "ROOT_AI_HALLUCINATION",
        "title": "端到端神經網絡輸出超越物理極限之急暴衝指令",
        "symptom": "AI 模組在障礙物逼近時突然輸出 +5.8 m/s^2 加速度請求",
        "root_cause": "視覺盲區與神經網絡分佈外數據 (OOD) 引發權重激活值異常",
        "countermeasure": "部署 ASIL-D Safe AI Cage 護欄，3.2 微秒內強制限幅於安全動態包絡線",
        "verification_evidence": "SafeAICageSupervisor.arbitrate_ai_command"
    }
]


def build_knowledge_graph() -> Dict[str, Any]:
    """生成結構化車規失效案例知識圖譜"""
    logger.info("啟動車規失效案例數據庫 (Lessons Learned) 知識圖譜編譯...")

    kg = {
        "graph_title": "AutoCopilot ASIL-D Lessons Learned Knowledge Graph",
        "compiled_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_failures_indexed": len(FAILURE_ONTOLOGY),
        "categories_covered": ["ROOT_ELECTRICAL_NOISE", "ROOT_TIMING_JITTER", "ROOT_THERMAL_DRIFT", "ROOT_AI_HALLUCINATION"],
        "records": FAILURE_ONTOLOGY
    }

    # 寫入 JSON
    json_path = os.path.join(DOCS_DIR, "LESSONS_LEARNED_KNOWLEDGE_GRAPH.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(kg, f, indent=2, ensure_ascii=False)

    # 寫入 Markdown
    md_path = os.path.join(DOCS_DIR, "LESSONS_LEARNED_KNOWLEDGE_GRAPH.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# 車規級失效案例知識圖譜與經驗庫 (Lessons Learned Knowledge Graph)\n\n")
        f.write(f"> **編譯時間**：{kg['compiled_at']}  \n")
        f.write(f"> **收錄案例**：{kg['total_failures_indexed']} 類核心車規失效模式  \n")
        f.write("> **價值**：組織級安全資產沉澱，反哺下一代全地形無人車與具身智駕研發。  \n\n")
        f.write("---\n\n")
        for r in FAILURE_ONTOLOGY:
            f.write(f"### [{r['failure_code']}] {r['title']}\n")
            f.write(f"- **根本原因類別**：`{r['category']}`\n")
            f.write(f"- **失效現象**：{r['symptom']}\n")
            f.write(f"- **深層根因 (Root Cause)**：{r['root_cause']}\n")
            f.write(f"- **固化防禦對策 (Countermeasure)**：{r['countermeasure']}\n")
            f.write(f"- **實證支撐**：{r['verification_evidence']}\n\n")

    logger.info(f"知識圖譜生成完畢！JSON: {json_path}, MD: {md_path}")
    return kg


if __name__ == "__main__":
    res = build_knowledge_graph()
    print("\n=== 車規失效案例知識圖譜編譯摘要 ===")
    print(f"索引案例數: {res['total_failures_indexed']} 個")
    print(f"涵蓋失效維度: {', '.join(res['categories_covered'])}")
    print("===================================\n")
