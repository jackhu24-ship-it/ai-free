# C:\ibm-bob\office2_ui_controller.py
# -*- coding: utf-8 -*-
"""
==============================================================================
 第二辦公室 (Office 2) UI 控制器 - 前端作業審查與合規移交台
 職責規範：
 1. 專注前端作業與合規審查（雜訊剔除、AST 安全稽核、簽證生成）。
 2. 嚴禁越權落款！本台無落款權限，審查通過後即刻將控制權移交「指揮所第三辦公室」。
 3. 實體原檔與 .audit_certificate.json 成對移交至核心庫待簽區 (core_repo)。
==============================================================================
"""

try:
    from office2_engine import Office2AuditEngine
except ImportError:
    from tools.office2_engine import Office2AuditEngine


def handle_btn_outbox_review():
    """
    點擊『🚀 審查並移交指揮所』觸發：
    執行兩階段質檢（提取過濾 ➔ AST 檢查 ➔ 生成簽證 ➔ 移交 core_repo）
    完成後交出控制權，嚴禁越權落款！
    """
    review_res = Office2AuditEngine.execute_stage_review()
    
    if not review_res["success"]:
        return {
            "copilot_chat": f"⚠️ 第二辦公室審查終止：{review_res['msg']}",
            "panel_data": [],
            "items": [],
            "status": "REVIEW_ABORTED"
        }

    # 組織右側終端看板顯示清單
    panel_rows = []
    for item in review_res["items"]:
        panel_rows.append(
            f"{item['name']} : {item['size']} B | SHA:{item['sha256'][:8]} | [{item['status']}] {item['details']}"
        )

    # 審查全數通過，自動移交推送至核心庫待簽區 (core_repo)
    if review_res["all_passed"]:
        sync_res = Office2AuditEngine.execute_sync_core()
        chat_msg = (
            "報告 Jack 哥！第二辦公室質檢完成！\n\n"
            "📋 **【移交報告】**：\n"
            "• 實體原檔：.py / .json 檢驗合規 (Clean)\n"
            "• 簽證狀態：已簽發 `.audit_certificate.json`\n"
            "• 移交目的地：核心庫待簽區 (`core_repo`)\n\n"
            "⚠️ **本台無落款權限，已將權限移交給「指揮所第三辦公室」進行大腦深度驗收與最終落款！**"
        )
        status_code = "TRANSFERRED_TO_OFFICE3"
    else:
        chat_msg = "❌ 報告 Jack 哥，檢測到不合規代碼，第二辦公室已阻斷移交流程！"
        status_code = "AUDIT_REJECTED"

    return {
        "copilot_chat": chat_msg,
        "panel_data": panel_rows,
        "items": review_res["items"],
        "data": review_res.get("data", []),
        "status": status_code,
        "transferred": review_res["all_passed"]
    }
