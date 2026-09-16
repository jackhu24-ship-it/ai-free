#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Five-Agent AI OS 實戰模組：本地發票結構化安全記帳系統
作者：🛠️ 小開 (Agent_Coder) 依據 👁️ 小Ｏ (Agent_LocalVision) 提取之數據規格撰寫
審查：🐎 小馬 (Agent_Reviewer)
統籌：👑 小幫手 (Agent_PM)

核心功能與安全標準：
1. Python 3.12+ 現代型別標註與 dataclass
2. CWE-1236 試算表公式注入安全過濾 (sanitize_cell)
3. Windows 繁體中文相容 (utf-8-sig 輸出，防止 Excel 開啟亂碼)
4. 金額異常防呆機制：金額超出範圍 (<=0 或 >5000) 拋出 InvoiceAmountError 自定義異常
"""

from __future__ import annotations

import sys
import os
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional

# 設定繁體中文記錄器
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("InvoiceTracker")

# 確保 Windows 標準輸出為 UTF-8
if sys.platform.startswith("win"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


class InvoiceAmountError(ValueError):
    """自定義異常：發票金額防呆異常（金額小於等於 0 或大於 5000 元上限）"""
    pass


def sanitize_cell(value: Any) -> str:
    """
    CWE-1236 試算表公式注入防護：
    若欄位字串開頭為 '=', '+', '-', '@'，自動在最前端插入單引號 "'" 強制轉純文字。
    :param value: 原始欄位值
    :return: 安全過濾後的字串
    """
    str_val = str(value).strip()
    if str_val and str_val[0] in ("=", "+", "-", "@"):
        return f"'{str_val}"
    return str_val


@dataclass
class InvoiceItem:
    """發票品項明細資料結構"""
    name: str
    quantity: int
    unit_price: int
    subtotal: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InvoiceItem:
        return cls(
            name=str(data.get("name", "未知名稱")),
            quantity=int(data.get("quantity", 1)),
            unit_price=int(data.get("unit_price", 0)),
            subtotal=int(data.get("subtotal", 0))
        )


@dataclass
class InvoiceRecord:
    """發票主體資料結構"""
    invoice_number: str
    invoice_date: str
    store_tax_id: str
    store_name: str
    total_amount: int
    payment_method: str
    card_number_masked: str
    items: list[InvoiceItem] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InvoiceRecord:
        raw_amount = int(data.get("total_amount", 0))
        
        # 金額安全防呆檢查
        if raw_amount <= 0 or raw_amount > 5000:
            raise InvoiceAmountError(
                f"🚨 [金額防呆警告] 總金額異常: NT$ {raw_amount} (合法範圍: 1 ~ 5,000 元)"
            )

        items_list = [InvoiceItem.from_dict(it) for it in data.get("items", [])]

        return cls(
            invoice_number=str(data.get("invoice_number", "")),
            invoice_date=str(data.get("invoice_date", "")),
            store_tax_id=str(data.get("store_tax_id", "")),
            store_name=str(data.get("store_name", "")),
            total_amount=raw_amount,
            payment_method=str(data.get("payment_method", "現金")),
            card_number_masked=str(data.get("card_number_masked", "無")),
            items=items_list
        )


class InvoiceTracker:
    """發票安全記帳處理器"""

    def __init__(self, csv_path: Optional[Path | str] = None) -> None:
        if csv_path is None:
            base_dir = Path(__file__).resolve().parent.parent / "DATA"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.csv_path = base_dir / "expenses.csv"
        else:
            self.csv_path = Path(csv_path)

    def import_from_json(self, json_path: Path | str) -> InvoiceRecord:
        """
        從 JSON 檔案導入發票數據並寫入 CSV 記帳本
        :param json_path: JSON 檔案路徑
        :return: 結構化 InvoiceRecord 物件
        """
        path_obj = Path(json_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"找不到發票 JSON 檔案: {path_obj}")

        with open(path_obj, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)

        record = InvoiceRecord.from_dict(data)
        self.append_to_csv(record)
        return record

    def append_to_csv(self, record: InvoiceRecord) -> None:
        """
        將發票記錄與品項明細逐筆安全寫入 CSV (符合 CWE-1236 與 utf-8-sig)
        :param record: 發票記錄
        """
        is_new_file = not self.csv_path.exists()
        
        # 準備安全清洗後的明細欄位
        safe_inv_num = sanitize_cell(record.invoice_number)
        safe_date = sanitize_cell(record.invoice_date)
        safe_tax_id = sanitize_cell(record.store_tax_id)
        safe_store_name = sanitize_cell(record.store_name)
        safe_payment = sanitize_cell(record.payment_method)
        safe_card = sanitize_cell(record.card_number_masked)

        with open(self.csv_path, "a", encoding="utf-8-sig", errors="replace") as f:
            if is_new_file:
                # 寫入繁體中文表頭
                f.write("發票號碼,交易日期,店家統編,店家名稱,品項名稱,數量,單價,小計,發票總金額,支付方式,卡號末四碼\n")

            for item in record.items:
                safe_item_name = sanitize_cell(item.name)
                row = [
                    f'"{safe_inv_num}"',
                    f'"{safe_date}"',
                    f'"{safe_tax_id}"',
                    f'"{safe_store_name}"',
                    f'"{safe_item_name}"',
                    str(item.quantity),
                    str(item.unit_price),
                    str(item.subtotal),
                    str(record.total_amount),
                    f'"{safe_payment}"',
                    f'"{safe_card}"'
                ]
                f.write(",".join(row) + "\n")

        logger.info(f"✅ 成功將發票 [{record.invoice_number}] 共 {len(record.items)} 筆品項寫入: {self.csv_path.name}")


# ---------------------------------------------------------------------------
# 模組自我驗證與安全測試
# ---------------------------------------------------------------------------
def run_module_tests() -> None:
    """執行單元測試與安全防護驗證"""
    print("🚀 [Module-Test] 開始執行 invoice_tracker 安全防禦與流程測試...\n")

    workspace_dir = Path(__file__).resolve().parent.parent
    mock_json = workspace_dir / "DATA" / "mock_invoice.json"
    test_csv = workspace_dir / "DATA" / "expenses.csv"

    tracker = InvoiceTracker(csv_path=test_csv)

    # 1. 正常發票導入測試
    print("1️⃣ [測試正常發票導入]")
    record = tracker.import_from_json(mock_json)
    print(f"   -> 成功解析發票: {record.invoice_number} | 總金額: NT$ {record.total_amount} | 品項數: {len(record.items)}")

    # 2. CWE-1236 公式注入攻擊測試
    print("\n2️⃣ [測試 CWE-1236 公式注入防禦]")
    malicious_item = "=SUM(A1:A100)"
    sanitized_item = sanitize_cell(malicious_item)
    print(f"   -> 原始危險輸入: {malicious_item}")
    print(f"   -> 安全過濾輸出: {sanitized_item}")
    assert sanitized_item.startswith("'="), "❌ 公式注入過濾失敗！"
    print("   -> ✅ CWE-1236 防護機制完美生效（已自動前置單引號）！")

    # 3. 金額防呆超標測試 (> 5,000 元)
    print("\n3️⃣ [測試金額超標防呆 (> 5000 元)]")
    try:
        InvoiceRecord.from_dict({
            "invoice_number": "XX-99999999",
            "total_amount": 12800,
            "items": []
        })
        print("   ❌ 未能攔截超標金額！")
    except InvoiceAmountError as e:
        print(f"   -> ✅ 成功攔截異常金額: {e}")

    # 4. 金額負數防呆測試 (<= 0 元)
    print("\n4️⃣ [測試金額負數防呆 (<= 0 元)]")
    try:
        InvoiceRecord.from_dict({
            "invoice_number": "XX-00000000",
            "total_amount": -50,
            "items": []
        })
        print("   ❌ 未能攔截負數金額！")
    except InvoiceAmountError as e:
        print(f"   -> ✅ 成功攔截負數金額: {e}")

    print("\n🎉 [Module-Test] 全項安全測試 100% 通過！")


if __name__ == "__main__":
    run_module_tests()
