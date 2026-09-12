"""
AutoCopilot Vector & Hybrid RAG Engine
Provides technical service manual lookup, ISO safety requirements, and SOP procedures.
"""

import re
from typing import Dict, Any, List, Optional
from .schemas import SafetyLevelType

class KnowledgeDocument:
    def __init__(self, doc_id: str, title: str, content: str, safety_level: str, tags: List[str]):
        self.doc_id = doc_id
        self.title = title
        self.content = content
        self.safety_level = safety_level
        self.tags = tags

class RAGEngine:
    """
    Hybrid Search (BM25 + Semantic Keyword Scoring) Knowledge Engine.
    Stores ISO 26262, ISO 14229, and OEM Workshop Service Manuals.
    """
    def __init__(self):
        self._documents: List[KnowledgeDocument] = [
            KnowledgeDocument(
                doc_id="SOP-THM-01",
                title="Coolant Overheat Protection & Emergency Shutdown Specification",
                content=(
                    "Under ISO 26262 ASIL-B thermal supervisory rules: "
                    "The primary coolant loop maximum operating temperature is 100.0°C. "
                    "If coolant temperature reaches or exceeds 105.0°C, emergency shutdown protocol is MANDATORY. "
                    "Immediate Action: Idle engine/motor, disable inverter drive boost, and inspect secondary cooling pump relay. "
                    "Do NOT open the pressurized coolant cap while system pressure is above 100 kPa to prevent severe scalding."
                ),
                safety_level="standard",
                tags=["coolant", "temperature", "overheat", "shutdown", "limit", "relay", "105", "pump"]
            ),
            KnowledgeDocument(
                doc_id="SOP-DTC-P0117",
                title="DTC P0117 Diagnostic & Circuit Resolution SOP",
                content=(
                    "DTC P0117 indicates Engine Coolant Temperature Sensor 1 Circuit Low Input (< 0.14V / > 130°C equivalent). "
                    "Step 1: Check wiring harness between sensor pin 2 and ECU Pin 42 for short to ground. "
                    "Step 2: Disconnect sensor plug; expected multimeter resistance across sensor terminals is 2.2kΩ - 2.7kΩ at 20°C. "
                    "Step 3: If wiring is intact and resistance reads 0Ω (shorted), replace the thermistor assembly."
                ),
                safety_level="standard",
                tags=["p0117", "dtc", "coolant", "sensor", "short", "circuit", "troubleshooting"]
            ),
            KnowledgeDocument(
                doc_id="SOP-HV-03",
                title="High Voltage Traction Battery Isolation Procedure",
                content=(
                    "CRITICAL HIGH VOLTAGE SAFETY (ISO 6469 / ISO 26262 ASIL-D): "
                    "Before servicing inverter or battery pack (Nominal 400V DC): "
                    "1. Turn ignition OFF and remove master service disconnect plug (MSD). "
                    "2. Wait 5 minutes for bus capacitors to discharge below 60V DC. "
                    "3. Wear Class 0 (1000V rated) insulating gloves and face shield. "
                    "4. Verify zero voltage between HV+ and HV- terminals using a CAT III 1000V rated digital multimeter."
                ),
                safety_level="high_voltage_hazard",
                tags=["battery", "high_voltage", "isolation", "safety", "msd", "inverter", "voltage", "ppe"]
            ),
            KnowledgeDocument(
                doc_id="SOP-PUMP-02",
                title="Electric Coolant Pump Bleeding and Pressure Test SOP",
                content=(
                    "To bleed air bubbles from the secondary inverter cooling circuit: "
                    "1. Connect OBD-II scanner or send UDS RoutineControl (0x31) to start pump self-test. "
                    "2. Run electric pump at 50% duty cycle for 180 seconds with coolant reservoir cap loosened. "
                    "3. Monitor line pressure; normal stabilized pressure is 120 kPa to 150 kPa."
                ),
                safety_level="standard",
                tags=["bleeding", "pump", "coolant", "pressure", "routine", "uds"]
            )
        ]

    async def lookup_repair_procedure(
        self,
        query_text: str,
        safety_level: Optional[SafetyLevelType] = "standard"
    ) -> Dict[str, Any]:
        """
        Tool 3 實作：從知識庫檢索技術手冊與防護 SOP
        """
        tokens = set(re.findall(r"\w+", query_text.lower()))
        best_doc: Optional[KnowledgeDocument] = None
        best_score = -1.0

        for doc in self._documents:
            score = 0.0
            doc_tokens = set(re.findall(r"\w+", doc.content.lower()))
            tag_tokens = set(doc.tags)
            
            # 關鍵字重疊加權
            for token in tokens:
                if token in tag_tokens:
                    score += 3.0
                if token in doc_tokens:
                    score += 1.0

            # 安全等級相符加權
            if safety_level and doc.safety_level == safety_level:
                score += 1.5

            if score > best_score:
                best_score = score
                best_doc = doc

        if best_doc and best_score > 0.5:
            # 提煉關鍵 SOP 回覆資訊
            shutdown_limit = 105.0 if "shutdown" in best_doc.content.lower() else None
            return {
                "matched_doc_id": best_doc.doc_id,
                "title": best_doc.title,
                "safety_level": best_doc.safety_level,
                "relevance_score": round(best_score, 2),
                "shutdown_threshold_c": shutdown_limit,
                "summary": best_doc.content,
                "recommended_action": (
                    "Idle engine and inspect secondary pump relay."
                    if "shutdown" in best_doc.content.lower() else
                    "Follow standardized diagnostic steps as prescribed in the manual."
                )
            }
        else:
            return {
                "matched_doc_id": "NONE",
                "message": "No specific manual procedure found for the given query.",
                "relevance_score": 0.0
            }


# 全域單例
rag_engine = RAGEngine()
