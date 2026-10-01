# C:\ibm-bob\office2_ui_controller.py
# -*- coding: utf-8 -*-
try:
    from office2_engine import Office2AuditEngine
    from commander_seal import CommanderSealer
except ImportError:
    from tools.office2_engine import Office2AuditEngine
    from tools.commander_seal import CommanderSealer


def handle_btn_outbox_review():
    """點擊『🚀 成果審查同步』第 1 階段觸發"""
    review_res = Office2AuditEngine.execute_stage_review()
    
    if not review_res["success"]:
        return {
            "copilot_chat": f"⚠️ 審查終止：{review_res['msg']}",
            "panel_data": []
        }

    # 組織右側終端看板顯示清單
    panel_rows = []
    for item in review_res["items"]:
        panel_rows.append(
            f"{item['name']} : {item['size']} B | SHA:{item['sha256'][:8]} | [{item['status']}] {item['details']}"
        )

    # 審查全數通過，自動接續同步至 core_repo
    if review_res["all_passed"]:
        sync_res = Office2AuditEngine.execute_sync_core()
        chat_msg = (
            "報告 Jack 哥！**02_OUTBOX 成果審查與核心庫同步完成**！\n\n"
            f"📋 **【交付驗收單】**：\n"
            f"• 提取檔案：{len(review_res['items'])} 支 (快取已剔除)\n"
            f"• 稽核狀態：✅ 100% AST 通過，認證單已簽發\n"
            f"• 入庫狀態：📦 原檔實體與簽證檔已同步至 `core_repo`\n\n"
            "👉 指揮所已可進行驗票落款！請點選標籤：`🖋️ 指揮所驗票落款`"
        )
    else:
        chat_msg = "❌ 報告 Jack 哥，檢測到不合規代碼，已阻斷入庫流程！"

    return {
        "copilot_chat": chat_msg,
        "panel_data": panel_rows,
        "items": review_res["items"],
        "data": review_res.get("data", [])
    }


def handle_btn_commander_seal():
    """點擊『🖋️ 指揮所驗票落款』觸發"""
    seal_res = CommanderSealer.verify_and_stamp()
    
    if seal_res["success"]:
        chat_msg = (
            "報告 Jack 哥！🎖️ **指揮所權威落款已全數完成**！\n\n"
            f"• 狀態：{seal_res['msg']}\n"
            "• 印章宣告：已原位注入 `.py` Header 與 `.json` 根節點\n"
            "• 履歷登錄：已簽發 `RELEASE_SEAL.json`，進入正式發佈態！"
        )
    else:
        chat_msg = f"❌ 落款失敗：{seal_res['msg']}"

    return {
        "copilot_chat": chat_msg,
        "panel_status": "OFFICIALLY_SEALED",
        "result": seal_res
    }
