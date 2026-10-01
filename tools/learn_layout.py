# -*- coding: utf-8 -*-
"""
PHANTOM GRID 視覺逆向與自學排版中樞 (learn_layout.py)
第二辦公室純文字環境三大排版自學方案：
方案 A (主流 - 路徑指引): 本地丟圖，終端傳路徑 `python tools/learn_layout.py --image samples/layout.png --name auto_style_01`
方案 B (極速 - 文字風格令): 自然語言映射 `python tools/learn_layout.py --style "簡約大廠風, 雙欄, 懸掛縮排" --name tech_corp`
方案 C (沉澱 - 風格代號): 調用預置代號 `python tools/learn_layout.py --token executive-airy`
全自動解析並沉澱至 02_Knowledge/Layout_Rules.json，雙軌同步回寫 G 槽與 C 槽。
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

LAYOUT_RULES_LOCAL = Path("02_Knowledge") / "Layout_Rules.json"
LAYOUT_RULES_G = Path(r"G:\我的雲端硬碟\260803_opencode\02_Knowledge\Layout_Rules.json")
LAYOUT_RULES_C = Path(r"C:\260728-code\02_Knowledge\Layout_Rules.json")

def load_all_rules() -> dict:
    for p in [LAYOUT_RULES_LOCAL, LAYOUT_RULES_G, LAYOUT_RULES_C]:
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                pass
    return {
        "version": "1.0",
        "description": "PHANTOM GRID 語意區塊排版決策規則庫",
        "rules": {}
    }

def save_all_rules(data: dict):
    content = json.dumps(data, indent=2, ensure_ascii=False)
    for p in [LAYOUT_RULES_LOCAL, LAYOUT_RULES_G, LAYOUT_RULES_C]:
        if p.parent.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            print(f"   • 規則已沉澱固化 -> {p}")

def analyze_image_layout(image_path: Path, name: str) -> dict:
    """方案 A：由實體圖片逆向分析幾何與色彩特徵"""
    print(f"\n👁️  [方案 A · 視覺逆向分析] 讀取圖片: {image_path}...")
    if not image_path.exists():
        raise FileNotFoundError(f"找不到採樣圖片: {image_path}")

    # 預設頂級工程排版特徵
    extracted_rule = {
        "style_name": name,
        "source": str(image_path),
        "learned_at": datetime.now().isoformat(),
        "font_family": "Noto Sans TC, Inter, sans-serif",
        "font_family_code": "JetBrains Mono, monospace",
        "heading_color": "#1A202C",
        "body_color": "#2D3748",
        "bg_color": "#FFFFFF",
        "accent_border": "#CBD5E1",
        "hanging_indent": "1.8em",
        "block_style": "border-left-card",
        "border_left_width": "2px",
        "card_bg": "#F8FAFC",
        "layout_mode": "two-column",
        "spacing_ratio": 1.55,
        "depth_cutoff": 3,
        "depth_fallback": "micro-card"
    }

    try:
        from PIL import Image
        with Image.open(image_path) as img:
            w, h = img.size
            extracted_rule["image_dimensions"] = f"{w}x{h}"
            # 若寬高比 > 1.4，偏向雙欄或 16:9 展台
            if w / h > 1.4:
                extracted_rule["layout_mode"] = "two-column"
            else:
                extracted_rule["layout_mode"] = "single-column-a4"
                
            # 取樣圖片主色調
            img_small = img.resize((30, 30)).convert("RGB")
            colors = img_small.getcolors(900)
            if colors:
                # 排序出現最多次的顏色
                dominant = sorted(colors, key=lambda x: x[0], reverse=True)[0][1]
                avg_luma = 0.299 * dominant[0] + 0.587 * dominant[1] + 0.114 * dominant[2]
                if avg_luma < 100:
                    # 暗黑背景版型
                    extracted_rule["bg_color"] = "#0D1117"
                    extracted_rule["heading_color"] = "#58A6FF"
                    extracted_rule["body_color"] = "#C9D1D9"
                    extracted_rule["card_bg"] = "#161B22"
                    extracted_rule["accent_border"] = "#30363D"
                else:
                    # 亮色呼吸版型
                    extracted_rule["bg_color"] = "#FFFFFF"
                    extracted_rule["heading_color"] = "#1A202C"
                    extracted_rule["body_color"] = "#2D3748"
                    extracted_rule["card_bg"] = "#F8FAFC"
                    extracted_rule["accent_border"] = "#CBD5E1"
            print(f"   • PIL 影像取樣成功: 尺寸 {w}x{h}，版型幾何: {extracted_rule['layout_mode']}")
    except Exception as e:
        print(f"   • PIL 取樣提示 ({e})，使用標準黃金比例排版規則")

    return extracted_rule

def parse_style_command(style_text: str, name: str) -> dict:
    """方案 B：將三行純文字或語意白話命令映射為幾何參數"""
    print(f"\n⚡ [方案 B · 文字風格令映射] 解析語意: 『{style_text}』...")
    text_lower = style_text.lower()
    
    is_two_col = "雙欄" in style_text or "two-column" in text_lower or "考卷" in style_text
    is_dark = "深色" in style_text or "暗黑" in style_text or "科技黑" in style_text
    is_hanging = "懸掛" in style_text or "hanging" in text_lower
    
    rule = {
        "style_name": name,
        "source": "text_style_command",
        "raw_command": style_text,
        "learned_at": datetime.now().isoformat(),
        "font_family": "Noto Sans TC, Inter, sans-serif",
        "font_family_code": "JetBrains Mono, monospace",
        "heading_color": "#58A6FF" if is_dark else "#1A202C",
        "body_color": "#C9D1D9" if is_dark else "#2D3748",
        "bg_color": "#0D1117" if is_dark else "#FFFFFF",
        "card_bg": "#161B22" if is_dark else "#F8FAFC",
        "accent_border": "#30363D" if is_dark else "#CBD5E1",
        "hanging_indent": "1.8em" if is_hanging else "0",
        "block_style": "border-left-card",
        "border_left_width": "2px",
        "layout_mode": "two-column" if is_two_col else "single-column-a4",
        "spacing_ratio": 1.55,
        "depth_cutoff": 3,
        "depth_fallback": "micro-card"
    }
    return rule

def resolve_preset_token(token_name: str) -> dict:
    """方案 C：從知識庫中解析預置風格 Token"""
    print(f"\n🏛️  [方案 C · 沉澱風格代號] 調用預置 Token: 『{token_name}』...")
    typo_dir = Path("02_Knowledge") / "Typography"
    clean_id = token_name.replace("-", "_").lower()
    
    matched_file = None
    if typo_dir.exists():
        for f in typo_dir.glob("*.json"):
            if clean_id in f.stem.lower():
                matched_file = f
                break
                
    if matched_file:
        raw_data = json.loads(matched_file.read_text(encoding="utf-8"))
        print(f"   • 載入成功: {matched_file.name}")
        return {
            "style_name": matched_file.stem,
            "source": str(matched_file),
            "font_family": raw_data.get("font_family_tc", "Noto Sans TC"),
            "font_family_code": raw_data.get("font_family_code", "JetBrains Mono"),
            "heading_color": raw_data.get("color_heading", "#1A202C"),
            "body_color": raw_data.get("color_body", "#2D3748"),
            "hanging_indent": "1.8em",
            "block_style": "border-left-card",
            "layout_mode": "adaptive",
            "spacing_ratio": raw_data.get("line_height", 1.55)
        }
    else:
        # Fallback to executive airy
        return {
            "style_name": "Theme_Executive_Airy",
            "font_family": "Noto Sans TC, Inter",
            "heading_color": "#1A202C",
            "body_color": "#2D3748",
            "hanging_indent": "1.8em",
            "block_style": "border-left-card"
        }

def main():
    parser = argparse.ArgumentParser(description="PHANTOM GRID 視覺逆向與自學排版中樞 (learn_layout)")
    parser.add_argument("--image", type=str, help="方案 A: 採樣圖片實體路徑 (例如 samples/layout.png)")
    parser.add_argument("--style", type=str, help="方案 B: 自然文字風格描述 (例如 '簡約大廠風, 雙欄, 懸掛縮排')")
    parser.add_argument("--token", type=str, help="方案 C: 預置風格 Token 代號 (例如 executive-airy)")
    parser.add_argument("--name", type=str, default="auto_style_learned", help="固化時的樣式代號")
    args = parser.parse_args()

    if args.image:
        rule = analyze_image_layout(Path(args.image), args.name)
    elif args.style:
        rule = parse_style_command(args.style, args.name)
    elif args.token:
        rule = resolve_preset_token(args.token)
    else:
        parser.print_help()
        return

    # 存檔至 Layout_Rules.json
    all_data = load_all_rules()
    style_key = rule.get("style_name", args.name)
    all_data["rules"][style_key] = rule
    all_data["last_updated"] = datetime.now().isoformat()
    save_all_rules(all_data)

    print("\n" + "="*80)
    print(f"🎉 [自學成功] 第二辦公室排版規則已更新！風格標籤: 『{style_key}』")
    print(f"   • 骨架拓撲: {rule.get('layout_mode', 'N/A')}")
    print(f"   • 標題色彩: {rule.get('heading_color', 'N/A')} | 內文: {rule.get('body_color', 'N/A')}")
    print(f"   • 縮排機制: 負首行懸掛 {rule.get('hanging_indent', 'N/A')}，深層自動微卡片化")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
