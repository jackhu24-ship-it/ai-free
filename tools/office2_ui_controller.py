# C:\ibm-bob\office2_ui_controller.py
# -*- coding: utf-8 -*-
"""
==============================================================================
 第二辦公室 (Office 2) UI 控制器 - 批次原子提取與閘門檢驗 (Batch Audit Gate)
 職責規範：
 1. 批次全覽確認：一次性掃描 N 個檔案，右側輸出 AUDIT DETAILS，左側播報摘要。
 2. 嚴格落實「要麼全過、要麼全退 (All-or-Nothing)」原則。
 3. 只做質檢與移交，絕不越權落款！
==============================================================================
"""

try:
    from office2_engine import Office2AuditEngine
except ImportError:
    from tools.office2_engine import Office2AuditEngine


def handle_btn_outbox_review():
    """
    第一階段：點擊『🚀 審查並移交指揮所』觸發批次原子提取與閘門檢驗
    """
    review_res = Office2AuditEngine.execute_stage_review()
    
    if not review_res["success"]:
        return {
            "copilot_chat": f"⚠️ 第二辦公室審查終止：{review_res['msg']}",
            "panel_data": [],
            "items": [],
            "count": 0,
            "status": "REVIEW_ABORTED",
            "can_sync_core": False
        }

    total_count = review_res["total_count"]
    passed_count = review_res["passed_count"]
    blocked_cache = review_res["blocked_cache_count"]
    latency = review_res["latency_s"]
    pass_rate_str = review_res["pass_rate_str"]
    compliance_status = review_res["compliance_status"]

    # 組織右側終端看板 AUDIT DETAILS
    panel_rows = [
        f"待審總數: {total_count}       耗時: {latency}       通過率: {pass_rate_str}       合規狀態: {compliance_status}",
        "",
        "【審查合格明細清單 (AUDIT DETAILS)】:"
    ]
    for it in review_res["items"]:
        panel_rows.append(
            f" {it['no']:>2}. {it['name']:<24} | {it['size_formatted']:>8} | SHA: {it['sha256'][:10]}... | [{it['status']}] {it['details']}"
        )

    # 左側手機 Copilot 播報
    if review_res["all_passed"]:
        chat_msg = (
            f"報告 Jack 哥！02_OUTBOX 內 {total_count} 個檔案已完成批次質檢！\n\n"
            "📋 **【批量審查摘要】**：\n"
            f"• 待審檔案總數：{total_count} 支\n"
            f"• 快取過濾：已阻斷 {blocked_cache} 個快取雜訊\n"
            f"• 靜態合規檢驗：{pass_rate_str} 全數通過 (無敏感函式)\n"
            f"• 簽證狀態：已生成 {total_count} 檔合規認證單！\n\n"
            "👉 右側已列出完整檔案指紋清單。請確認無誤後，點選「移交核心庫待簽區」，交由指揮所第三辦公室落款！"
        )
        status_code = "BATCH_AUDIT_PASSED"
    else:
        chat_msg = (
            f"❌ 報告 Jack 哥！批次審查檢測到不合規檔案！\n\n"
            f"• 待審檔案總數：{total_count} 支\n"
            f"• 靜態合規檢驗：{pass_rate_str} (未全數合格)\n"
            f"• 門禁策略：All-or-Nothing 整批阻斷，未放行任何檔案！"
        )
        status_code = "BATCH_AUDIT_BLOCKED"

    return {
        "copilot_chat": chat_msg,
        "panel_data": panel_rows,
        "items": review_res["items"],
        "data": review_res.get("data", []),
        "count": total_count,
        "total_count": total_count,
        "passed_count": passed_count,
        "pass_rate_str": pass_rate_str,
        "compliance_status": compliance_status,
        "blocked_cache_count": blocked_cache,
        "latency_s": latency,
        "status": status_code,
        "can_sync_core": review_res["all_passed"]
    }


def handle_btn_sync_core():
    """
    第二階段：操作者確認右側清單無誤後，點擊『移交核心庫待簽區』
    """
    sync_res = Office2AuditEngine.execute_sync_core()
    if sync_res["success"]:
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
        chat_msg = f"❌ 移交失敗：{sync_res['msg']}"
        status_code = "TRANSFER_FAILED"

    return {
        "copilot_chat": chat_msg,
        "status": status_code,
        "result": sync_res
    }
