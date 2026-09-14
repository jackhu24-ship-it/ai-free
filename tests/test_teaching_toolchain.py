# -*- coding: utf-8 -*-
"""
tests/test_teaching_toolchain.py - AI 智慧教學備課與閱卷診斷工具鏈單元測試
=============================================================================
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import unittest
import os
from teaching_toolchain.exam_diagnostic_ai import ExamDiagnosticAI
from teaching_toolchain.lesson_plan_generator import LessonPlanGenerator


class TestTeachingToolchain(unittest.TestCase):

    def setUp(self):
        self.diagnostic = ExamDiagnosticAI(cohort_name="AutoSafe_CFD_Cohort_01")

    def test_single_student_grading_and_privacy(self):
        """測試單一學生批改與個資脫敏 (僅以座號識別)"""
        answers = {"Q1": "B", "Q2": "C", "Q3": "A", "Q4": "D", "Q5": "B"}
        rec = self.diagnostic.grade_student(seat_no=7, student_answers=answers)

        self.assertEqual(rec["seat_id"], "Seat_07")
        self.assertEqual(rec["total_score"], 100.0)
        self.assertEqual(rec["correct_count"], 5)
        # 確保沒有姓名等私密屬性
        self.assertNotIn("name", rec)
        self.assertNotIn("id_number", rec)

    def test_cohort_batch_grading_and_radar_chart(self):
        """測試 30 人班級批量閱卷與雷達圖輸出 (遵從零桌面污染原則)"""
        submissions = []
        for seat in range(1, 31):
            # 模擬不同學生的答題情況
            ans = {
                "Q1": "B" if seat % 2 == 0 else "A",
                "Q2": "C",
                "Q3": "A" if seat % 3 != 0 else "B",
                "Q4": "D",
                "Q5": "B" if seat % 5 != 0 else "C"
            }
            submissions.append((seat, ans))

        batch_res = self.diagnostic.batch_grade_cohort(submissions)
        self.assertEqual(batch_res["total_students"], 30)
        self.assertGreater(batch_res["class_average"], 50.0)

        # 輸出雷達圖至 generated/
        radar_path = "generated/exam_radar_diagnosis.png"
        saved_path = self.diagnostic.generate_radar_chart(radar_path)
        self.assertTrue(os.path.exists(saved_path))
        self.assertGreater(os.path.getsize(saved_path), 5000)

    def test_lesson_plan_and_question_bank_generation(self):
        """測試車載與 CFD 跨領域教案與題庫產出至成品總庫"""
        plan_path = r"G:\我的雲端硬碟\AI產出成品總庫\01_🎓_教學備課專區\LESSON_PLAN_ASIL_D_AND_PHANTOM_GRID.md"
        bank_path = r"G:\我的雲端硬碟\AI產出成品總庫\02_📚_題庫專區\EXAM_QUESTION_BANK_ASIL_D_AND_CFD.md"

        LessonPlanGenerator.generate_lesson_plan(plan_path)
        LessonPlanGenerator.generate_question_bank(bank_path)

        self.assertTrue(os.path.exists(plan_path))
        self.assertTrue(os.path.exists(bank_path))

        with open(plan_path, "r", encoding="utf-8") as f:
            plan_text = f.read()
            self.assertIn("ISO 26262 ASIL-D", plan_text)
            self.assertIn("PHANTOM", plan_text)

        with open(bank_path, "r", encoding="utf-8") as f:
            bank_text = f.read()
            self.assertIn("0x27 安全訪問", bank_text)
            self.assertIn("Berger 跨邊界通量匹配", bank_text)


if __name__ == "__main__":
    unittest.main()
