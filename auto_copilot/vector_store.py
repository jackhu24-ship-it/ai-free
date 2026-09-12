"""
AutoCopilot Lightweight Vector Store & Hybrid Retrieval Engine
Pure-Python TF-IDF + Cosine Similarity Vector Store for ISO / Workshop Manuals.
"""

import math
import re
from typing import Dict, Any, List, Optional, Tuple

class DocumentChunk:
    def __init__(self, doc_id: str, section: str, content: str, safety_level: str, metadata: Dict[str, Any]):
        self.doc_id = doc_id
        self.section = section
        self.content = content
        self.safety_level = safety_level
        self.metadata = metadata
        self.tokens = self._tokenize(content)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"[a-zA-Z0-9_\u4e00-\u9fff]+", text.lower())

class LightweightVectorStore:
    """
    In-memory Vector Store with TF-IDF Vector Space Model & Hybrid BM25 Scoring.
    """
    def __init__(self):
        self.chunks: List[DocumentChunk] = []
        self._df: Dict[str, int] = {}
        self._doc_vectors: List[Dict[str, float]] = []
        self._initialize_kb()

    def _initialize_kb(self):
        """載入標準車規與維修手冊章節"""
        raw_documents = [
            DocumentChunk(
                doc_id="SEC-TH-402",
                section="Emergency Thermal Overheat & Shutdown SOP",
                content=(
                    "Under ISO 26262 ASIL-B thermal supervisory rules: "
                    "The primary coolant loop maximum operating temperature is 100.0°C. "
                    "If coolant temperature reaches or exceeds 105.0°C, emergency shutdown protocol is MANDATORY. "
                    "Step 1: Shift to neutral / idle. "
                    "Step 2: Verify auxiliary cooling pump relay engagement. "
                    "Step 3: If temperature exceeds 105°C for more than 30s, trigger ASIL-B emergency safe state. "
                    "Do NOT open the pressurized coolant cap while system pressure is above 100 kPa to prevent severe scalding."
                ),
                safety_level="standard",
                metadata={"shutdown_limit_c": 105.0, "asil_level": "ASIL-B", "subsystem": "thermal"}
            ),
            DocumentChunk(
                doc_id="SEC-DTC-P0117",
                section="DTC P0117 Diagnostic & Circuit Resolution SOP",
                content=(
                    "DTC P0117 indicates Engine Coolant Temperature Sensor 1 Circuit Low Input (< 0.14V / > 130°C equivalent). "
                    "Step 1: Inspect wiring harness between ECT sensor pin 2 and ECM pin 42 for short to chassis ground. "
                    "Step 2: Measure thermistor resistance: expected value is 2.2kΩ - 2.7kΩ at 20°C ambient. "
                    "Step 3: If wiring is intact and resistance reads 0Ω, replace the sensor assembly and clear diagnostic trouble code."
                ),
                safety_level="standard",
                metadata={"dtc": "P0117", "ecu": "engine_control", "service": "UDS 0x19"}
            ),
            DocumentChunk(
                doc_id="SEC-HV-801",
                section="High Voltage Traction Battery De-energization Procedure",
                content=(
                    "CRITICAL HIGH VOLTAGE SAFETY (ISO 6469 / ISO 26262 ASIL-D): "
                    "Before servicing inverter or 400V traction battery: "
                    "1. Turn ignition OFF and remove Master Service Disconnect (MSD) manual service plug. "
                    "2. Wait 5 minutes for bus discharge resistors to bring DC voltage below 60V. "
                    "3. Put on Class 0 (1000V rated) insulating gloves and full face shield. "
                    "4. Verify zero voltage between DC+ and DC- terminals with CAT III 1000V rated multimeter."
                ),
                safety_level="high_voltage_hazard",
                metadata={"voltage": "400V", "asil_level": "ASIL-D", "safety": "MSD"}
            ),
            DocumentChunk(
                doc_id="SEC-BLEED-204",
                section="Secondary Inverter Coolant Bleeding Routine",
                content=(
                    "Bleeding air bubbles from secondary inverter circuit: "
                    "Connect diagnostic tool and invoke UDS RoutineControl (0x31) to start auxiliary pump test. "
                    "Run pump at 50% duty cycle for 180 seconds. Monitor line pressure; normal stabilized pressure is 120 kPa to 150 kPa."
                ),
                safety_level="standard",
                metadata={"pressure_kpa": "120-150", "uds_service": "0x31"}
            )
        ]

        self.chunks = raw_documents
        self._build_index()

    def _build_index(self):
        """計算詞頻 (TF) 與逆向文件頻率 (IDF) 並建立文件向量"""
        num_docs = len(self.chunks)
        self._df = {}
        for chunk in self.chunks:
            unique_terms = set(chunk.tokens)
            for term in unique_terms:
                self._df[term] = self._df.get(term, 0) + 1

        self._doc_vectors = []
        for chunk in self.chunks:
            vec = {}
            total_tokens = len(chunk.tokens) or 1
            term_counts = {}
            for t in chunk.tokens:
                term_counts[t] = term_counts.get(t, 0) + 1

            for term, count in term_counts.items():
                tf = count / total_tokens
                idf = math.log(1.0 + (num_docs / (1.0 + self._df.get(term, 0))))
                vec[term] = tf * idf
            
            # L2 歸一化
            norm = math.sqrt(sum(v ** 2 for v in vec.values())) or 1.0
            norm_vec = {k: v / norm for k, v in vec.items()}
            self._doc_vectors.append(norm_vec)

    def search(self, query: str, top_k: int = 1, safety_filter: Optional[str] = None) -> List[Tuple[DocumentChunk, float]]:
        """執行餘弦相似度 (Cosine Similarity) 向量檢索"""
        query_tokens = DocumentChunk._tokenize(query)
        if not query_tokens:
            return []

        # 計算 Query 向量
        q_counts = {}
        for t in query_tokens:
            q_counts[t] = q_counts.get(t, 0) + 1
        total_q = len(query_tokens)
        num_docs = len(self.chunks)

        q_vec = {}
        for t, count in q_counts.items():
            tf = count / total_q
            idf = math.log(1.0 + (num_docs / (1.0 + self._df.get(t, 0))))
            q_vec[t] = tf * idf
        
        q_norm = math.sqrt(sum(v ** 2 for v in q_vec.values())) or 1.0
        q_norm_vec = {k: v / q_norm for k, v in q_vec.items()}

        # 相似度打分
        scored: List[Tuple[DocumentChunk, float]] = []
        for i, doc_vec in enumerate(self._doc_vectors):
            chunk = self.chunks[i]
            if safety_filter and chunk.safety_level != safety_filter:
                continue

            dot_product = sum(doc_vec.get(term, 0.0) * weight for term, weight in q_norm_vec.items())
            
            # 關鍵字提權
            overlap_boost = sum(1.5 for t in query_tokens if t in chunk.tokens)
            final_score = dot_product + (overlap_boost * 0.1)
            scored.append((chunk, round(final_score, 4)))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


# 全域單例
vector_store = LightweightVectorStore()
