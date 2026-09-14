# -*- coding: utf-8 -*-
"""
teaching_toolchain/exam_diagnostic_ai.py - AI 智慧考卷診斷與弱點雷達圖分析引擎
=============================================================================
支援車載 ASIL-D 功能安全與 PHANTOM CFD 數值計算雙跨領域考卷自動批改、
學生個資完全脫敏（僅以座號識別）、五維知識點掌握度評估與雷達圖視覺化導出。
"""
from typing import Dict, List, Any, Optional, Tuple
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False


class ExamDiagnosticAI:
    """車載安全與 CFD 數值模擬智慧閱卷與診斷大腦"""

    # 5 大核心評量知識點與權重
    KNOWLEDGE_POINTS = [
        "ISO 26262 ASIL-D 冗餘架構",
        "UDS 診斷與 DoIP 刷寫協定",
        "CAN-FD 匯流排與 E2E 安全",
        "PHANTOM 重疊網格度量張量",
        "Berger 守恆通量與 HPC 加速"
    ]

    # 標準答案鍵 (Standard Answer Keys)
    ANSWER_KEY = {
        "Q1": "B",  # ASIL-D 要求雙核熱接管時間 (< 5ms)
        "Q2": "C",  # UDS 0x27 安全訪問 Seed & Key
        "Q3": "A",  # CAN-FD 最大數據載荷 64 Bytes
        "Q4": "D",  # 貼體度量張量保證 GCL 幾何守恆
        "Q5": "B"   # Berger 補償通量殘差抑制質量漂移
    }

    def __init__(self, cohort_name: str = "Class_2026_Advanced_HPC"):
        self.cohort_name = cohort_name
        self.student_records: List[Dict[str, Any]] = []

    def grade_student(self, seat_no: int, student_answers: Dict[str, str]) -> Dict[str, Any]:
        """
        批改單一學生考卷 (嚴格僅以座號登記，嚴禁姓名/個資洩漏)
        """
        scores_by_point = []
        correct_count = 0

        for idx, (q_id, correct_ans) in enumerate(self.ANSWER_KEY.items()):
            ans = student_answers.get(q_id, "").upper().strip()
            is_correct = (ans == correct_ans)
            if is_correct:
                correct_count += 1
                scores_by_point.append(100.0)
            else:
                scores_by_point.append(40.0)  # 錯誤或未答基本觀念分

        total_score = (correct_count / len(self.ANSWER_KEY)) * 100.0

        record = {
            "seat_id": f"Seat_{seat_no:02d}",
            "total_score": total_score,
            "dimension_scores": scores_by_point,
            "correct_count": correct_count
        }
        self.student_records.append(record)
        return record

    def batch_grade_cohort(self, submissions: List[Tuple[int, Dict[str, str]]]) -> Dict[str, Any]:
        """批量閱卷並統計班級五維度平均掌握率"""
        self.student_records.clear()
        for seat_no, answers in submissions:
            self.grade_student(seat_no, answers)

        # 班級平均
        all_dim_scores = np.array([r["dimension_scores"] for r in self.student_records])
        avg_dimensions = np.mean(all_dim_scores, axis=0)
        class_avg_score = float(np.mean([r["total_score"] for r in self.student_records]))

        return {
            "cohort": self.cohort_name,
            "total_students": len(self.student_records),
            "class_average": class_avg_score,
            "dimension_averages": avg_dimensions.tolist()
        }

    def generate_radar_chart(self, output_png_path: str) -> str:
        """生成班級五維知識點弱點診斷雷達圖 (儲存於工作區或 generated/)"""
        if not self.student_records:
            raise ValueError("No student records to generate radar chart")

        os.makedirs(os.path.dirname(os.path.abspath(output_png_path)), exist_ok=True)

        all_dim_scores = np.array([r["dimension_scores"] for r in self.student_records])
        avg_scores = np.mean(all_dim_scores, axis=0).tolist()

        # 雷達圖閉合
        categories = list(self.KNOWLEDGE_POINTS)
        N = len(categories)
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]
        avg_scores += avg_scores[:1]

        fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True), dpi=150)
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)

        plt.xticks(angles[:-1], categories, size=10, color="#1e293b", weight="bold")
        ax.set_rlabel_position(0)
        plt.yticks([20, 40, 60, 80, 100], ["20%", "40%", "60%", "80%", "100%"], color="#64748b", size=8)
        plt.ylim(0, 100)

        # 繪製雷達面
        ax.plot(angles, avg_scores, linewidth=2, linestyle="solid", color="#2563eb", label="Cohort Mastery")
        ax.fill(angles, avg_scores, color="#3b82f6", alpha=0.3)

        plt.title(f"Class Diagnostic Radar Chart: {self.cohort_name}", size=14, y=1.08, weight="bold")
        plt.tight_layout()
        plt.savefig(output_png_path)
        plt.close(fig)

        return output_png_path
