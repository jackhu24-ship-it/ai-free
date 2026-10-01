# -*- coding: utf-8 -*-
"""
PHANTOM GRID 字體工程學與動態字型美學演進引擎 (Type Engineering & Evolution Engine)
核心功能：
1. 可變字型無段調諧 (Variable Fonts OpenType-VF: wght, wdth, opsz)
2. 中西混排黃金比例 (Composite Font Pairing & X-Height 對齊)
3. 數值與工程對齊特性 (OpenType Features: tnum, zero, ss01)
4. 視覺樣式採樣、逆向工程與風格資產沉澱 (Asset Freezing into 02_Knowledge/Typography/)
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Windows UTF-8 強制防護
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

LOCAL_TYPO_DIR = Path("02_Knowledge") / "Typography"
G_TYPO_DIR = Path(r"G:\我的雲端硬碟\260803_opencode\02_Knowledge\Typography")
C_TYPO_DIR = Path(r"C:\260728-code\02_Knowledge\Typography")

# 基礎設計風格 Token 預置
FOUNDATIONAL_TOKENS = {
    "Theme_Executive_Airy": {
        "name": "Executive Airy (矽谷高階透氣商務風)",
        "font_family_tc": '"Noto Sans TC", "Microsoft JhengHei", "PingFang TC", sans-serif',
        "font_family_en": '"Inter", "Segoe UI", sans-serif',
        "font_family_code": '"JetBrains Mono", Consolas, monospace',
        "font_variation_settings": "'wght' 450, 'wdth' 100, 'opsz' 14",
        "font_feature_settings": "'tnum' 1, 'ss01' 1, 'zero' 1",
        "line_height": 1.55,
        "paragraph_spacing_pt": 7.0,
        "color_body": "#2D3748",
        "color_heading": "#1A202C",
        "color_secondary": "#718096",
        "x_height_ratio": 0.72,
        "description": "中文字盤以思源黑體為底，西文完美對齊 Inter 字腹高度，數值等寬切齊。"
    },
    "Theme_Engineering_Rigorous": {
        "name": "Engineering Rigorous (航太與軍工嚴謹工程風)",
        "font_family_tc": '"Noto Sans TC", "Microsoft JhengHei", sans-serif',
        "font_family_en": '"Inter", "Consolas", sans-serif',
        "font_family_code": '"JetBrains Mono", Consolas, monospace',
        "font_variation_settings": "'wght' 500, 'wdth' 100, 'opsz' 12",
        "font_feature_settings": "'tnum' 1, 'zero' 1, 'liga' 1",
        "line_height": 1.50,
        "paragraph_spacing_pt": 6.0,
        "color_body": "#1A202C",
        "color_heading": "#0F172A",
        "color_secondary": "#64748B",
        "x_height_ratio": 0.75,
        "description": "數字 0 帶斜線區隔字母 O，開啟程式碼連字特性 (Ligatures)，報表小數點絕對對齊。"
    },
    "Theme_Academic_Classic": {
        "name": "Academic Classic (旗艦出版社級學術典藏風)",
        "font_family_tc": '"Noto Sans TC", "Microsoft JhengHei", sans-serif',
        "font_family_en": '"Segoe UI", "Georgia", serif',
        "font_family_code": '"Consolas", monospace',
        "font_variation_settings": "'wght' 400, 'wdth' 100, 'opsz' 10",
        "font_feature_settings": "'tnum' 1, 'pnum' 0",
        "line_height": 1.60,
        "paragraph_spacing_pt": 8.0,
        "color_body": "#2D3748",
        "color_heading": "#1E293B",
        "color_secondary": "#6B7280",
        "x_height_ratio": 0.70,
        "description": "段落呼吸留白充足，嚴格雙欄 A4 排版，單行字數嚴鎖 32~40 字。"
    }
}

class TypographyEngine:
    def __init__(self):
        for d in [LOCAL_TYPO_DIR, G_TYPO_DIR, C_TYPO_DIR]:
            if d.parent.exists():
                d.mkdir(parents=True, exist_ok=True)

    def initialize_foundational_tokens(self):
        """將基礎三大字樣 Token 固化至知識庫"""
        print("🏛️ [Typography Engine] 初始化基礎字樣風格 Token 庫...")
        for token_id, data in FOUNDATIONAL_TOKENS.items():
            self.freeze_style_token(token_id, data)
        print("✅ 基礎字樣庫已全量雙向固化入 02_Knowledge/Typography/！")

    def freeze_style_token(self, token_id: str, data: dict):
        """將樣式逆向分析結果固化為 JSON 資產"""
        data["frozen_at"] = datetime.now().isoformat()
        content = json.dumps(data, indent=2, ensure_ascii=False)
        targets = [LOCAL_TYPO_DIR / f"{token_id}.json"]
        if G_TYPO_DIR.exists():
            targets.append(G_TYPO_DIR / f"{token_id}.json")
        if C_TYPO_DIR.exists():
            targets.append(C_TYPO_DIR / f"{token_id}.json")
            
        for t in targets:
            t.write_text(content, encoding="utf-8")
        print(f"   • [Asset Frozen] {token_id} -> {targets[0]}")

    def generate_css_variables(self, token_id: str) -> str:
        """載入 Token 並生成標準 CSS 變數與字體特性注入代碼"""
        token_file = LOCAL_TYPO_DIR / f"{token_id}.json"
        if not token_file.exists():
            if token_id in FOUNDATIONAL_TOKENS:
                data = FOUNDATIONAL_TOKENS[token_id]
            else:
                raise FileNotFoundError(f"找不到字樣風格: {token_id}")
        else:
            data = json.loads(token_file.read_text(encoding="utf-8"))

        css = (
            f"/* PHANTOM GRID Typography Token: {data['name']} */\n"
            f":root {{\n"
            f"  --pg-font-tc: {data['font_family_tc']};\n"
            f"  --pg-font-en: {data['font_family_en']};\n"
            f"  --pg-font-code: {data['font_family_code']};\n"
            f"  --pg-font-variation: {data['font_variation_settings']};\n"
            f"  --pg-font-features: {data['font_feature_settings']};\n"
            f"  --pg-line-height: {data['line_height']};\n"
            f"  --pg-para-spacing: {data['paragraph_spacing_pt']}pt;\n"
            f"  --pg-color-body: {data['color_body']};\n"
            f"  --pg-color-heading: {data['color_heading']};\n"
            f"  --pg-color-secondary: {data['color_secondary']};\n"
            f"}}\n\n"
            f"body {{\n"
            f"  font-family: var(--pg-font-tc);\n"
            f"  font-variation-settings: var(--pg-font-variation);\n"
            f"  font-feature-settings: var(--pg-font-features);\n"
            f"  line-height: var(--pg-line-height);\n"
            f"  color: var(--pg-color-body);\n"
            f"}}\n\n"
            f"table, .tabular-nums, .gradebook-num {{\n"
            f"  font-variant-numeric: tabular-nums;\n"
            f"  font-feature-settings: 'tnum' 1, 'zero' 1;\n"
            f"}}\n"
        )
        return css

    def ingest_and_learn_style(self, style_name: str, sample_meta: dict):
        """四步自動演進工作流：採樣 ➔ 逆向工程 ➔ 沉澱 ➔ 待調用"""
        print(f"\n🔬 [Type Reverse Engineering] 啟動全新字樣自學提取: 『{style_name}』...")
        new_token = {
            "name": style_name,
            "font_family_tc": sample_meta.get("font_tc", '"Noto Sans TC", sans-serif'),
            "font_family_en": sample_meta.get("font_en", '"Inter", sans-serif'),
            "font_family_code": sample_meta.get("font_code", '"JetBrains Mono", monospace'),
            "font_variation_settings": sample_meta.get("variation", "'wght' 450, 'opsz' 14"),
            "font_feature_settings": sample_meta.get("features", "'tnum' 1, 'ss01' 1, 'zero' 1"),
            "line_height": sample_meta.get("line_height", 1.55),
            "paragraph_spacing_pt": sample_meta.get("para_spacing", 7.0),
            "color_body": sample_meta.get("color_body", "#2D3748"),
            "color_heading": sample_meta.get("color_heading", "#1A202C"),
            "color_secondary": sample_meta.get("color_sec", "#718096"),
            "x_height_ratio": sample_meta.get("x_height_ratio", 0.72),
            "description": f"由指揮所秘書處逆向提取之神級字樣資產，支援一三辦即時動態調用。"
        }
        token_id = f"Theme_{style_name.replace(' ', '_')}"
        self.freeze_style_token(token_id, new_token)
        print(f"🎉 學習成功！風格已沉澱為知識資產，指令即時可用: 『{token_id}』\n")
        return token_id

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PHANTOM GRID 字體工程學引擎")
    parser.add_argument("--init", action="store_true", help="初始化預置三大神級字樣 Token")
    parser.add_argument("--generate-css", type=str, default="Theme_Executive_Airy", help="生成指定風格的 CSS 代碼")
    args = parser.parse_args()

    engine = TypographyEngine()
    if args.init:
        engine.initialize_foundational_tokens()
    else:
        css = engine.generate_css_variables(args.generate_css)
        print(css)
