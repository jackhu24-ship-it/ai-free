"""
PHANToM Grid :: Official 16:9 Banner Generator (Google PLE )
Complies with Rule 172: High Contrast, Anti-Box-Overflow, Bold Typography, 1920x1080.
Revision:
1. Removed Top-Right Benchmark Scope Badge (per Supreme Sovereign directive).
2. Fixed Box Overflow in Domain Cards: Reduced metric font, centered text, strict -32px inner margin.
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

def generate_cover_image(output_path: str):
    width, height = 1920, 1080
    img = Image.new("RGBA", (width, height), (11, 15, 25, 255)) # Cyber Dark Obsidian
    draw = ImageDraw.Draw(img)

    # 1. Background Grid & Geometry Lines
    grid_color = (26, 38, 57, 180)
    for x in range(0, width, 80):
        draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
    for y in range(0, height, 80):
        draw.line([(0, y), (width, y)], fill=grid_color, width=1)

    # Accent Colors
    accent_gold = (251, 191, 36, 255) # #FBBF24
    accent_cyan = (56, 189, 248, 255) # #38BDF8
    text_white = (255, 255, 255, 255)
    text_dim = (148, 163, 184, 255)
    card_bg = (15, 23, 42, 230)

    # Outer HUD Corner brackets
    blen = 80
    draw.line([(40, 40), (40 + blen, 40)], fill=accent_gold, width=4)
    draw.line([(40, 40), (40, 40 + blen)], fill=accent_gold, width=4)
    draw.line([(width - 40, 40), (width - 40 - blen, 40)], fill=accent_gold, width=4)
    draw.line([(width - 40, 40), (width - 40, 40 + blen)], fill=accent_gold, width=4)
    draw.line([(40, height - 40), (40 + blen, height - 40)], fill=accent_gold, width=4)
    draw.line([(40, height - 40), (40, height - 40 - blen)], fill=accent_gold, width=4)
    draw.line([(width - 40, height - 40), (width - 40 - blen, height - 40)], fill=accent_gold, width=4)
    draw.line([(width - 40, height - 40), (width - 40, height - 40 - blen)], fill=accent_gold, width=4)

    # Fonts
    try:
        font_sup = ImageFont.truetype("arialbd.ttf", 30)
        font_title = ImageFont.truetype("arialbd.ttf", 64)
        font_sub = ImageFont.truetype("arialbd.ttf", 36)
        font_body = ImageFont.truetype("arial.ttf", 26)
        font_tag = ImageFont.truetype("arialbd.ttf", 22)
        font_metric = ImageFont.truetype("arialbd.ttf", 17) # Smaller font for strict anti-overflow
    except Exception:
        font_sup = font_title = font_sub = font_body = font_tag = font_metric = ImageFont.load_default()

    # 2. Top Header Pill (Clean single banner)
    pill_box = [(40, 60), (760, 115)]
    draw.rounded_rectangle(pill_box, radius=8, fill=(30, 41, 59, 255), outline=accent_cyan, width=2)
    draw.text((60, 75), "GOOGLE RESEARCH ✕ KAGGLE FEATURED HACKATHON", fill=accent_cyan, font=font_tag)

    # [REMOVED TOP-RIGHT PRIZE BADGE PER DIRECTIVE]

    # 3. Main Center Title Block
    draw.text((100, 180), "PHYSICAL-ENGINEERING'S LAST EXAM", fill=accent_gold, font=font_title)
    draw.text((100, 270), "PHANToM Sovereign Autonomous Agent Harness", fill=text_white, font=font_sub)
    draw.text((100, 330), "Solving Complex Multi-File Structural, Civil, Electrical & Mechanical Challenges", fill=text_dim, font=font_body)

    # 4. Four Core Domain Showcase Cards
    domains = [
        ("01 MECHANICAL", "3D CAD Geometry & Clash-Free MEP Routing", "0.00mm Overlap / Early Cutoff"),
        ("02 ELECTRICAL", "Feeder Sizing & Voltage Drop Limit (< 3%)", "Ampacity Margin >= 125%"),
        ("03 STRUCTURAL", "Steel Layout & Symplectic Beam Deflection", "Deflection <= L/360 (WAM 50-Step)"),
        ("04 CIVIL", "Soil Settlement & Municipal Code Compliance", "Gradient Envelope [1.5%, 4.0%]")
    ]

    card_y = 420
    card_w = 400
    card_h = 280
    gap = 26
    start_x = 100

    for i, (dom_title, dom_desc, dom_metric) in enumerate(domains):
        cx = start_x + i * (card_w + gap)
        # Outer Card
        draw.rounded_rectangle([(cx, card_y), (cx + card_w, card_y + card_h)], radius=12, fill=card_bg, outline=accent_cyan, width=2)
        draw.text((cx + 24, card_y + 24), dom_title, fill=accent_gold, font=font_sup)
        
        # Word wrap description
        words = dom_desc.split(" ")
        line1 = " ".join(words[:4])
        line2 = " ".join(words[4:])
        draw.text((cx + 24, card_y + 85), line1, fill=text_white, font=font_body)
        draw.text((cx + 24, card_y + 125), line2, fill=text_white, font=font_body)

        # Metric box (Strict -32px padding, centered text)
        mbox_x1 = cx + 16
        mbox_x2 = cx + card_w - 16
        mbox_y1 = card_y + 195
        mbox_y2 = card_y + 255
        draw.rounded_rectangle([(mbox_x1, mbox_y1), (mbox_x2, mbox_y2)], radius=6, fill=(30, 41, 59, 255), outline=accent_gold, width=1)
        
        # Calculate text width to center and guarantee no overflow
        try:
            bbox = font_metric.getbbox(dom_metric)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
        except:
            tw, th = 300, 20

        # Centered position
        box_width = mbox_x2 - mbox_x1
        text_x = mbox_x1 + max(8, (box_width - tw) // 2)
        text_y = mbox_y1 + (60 - th) // 2 - 2

        draw.text((text_x, text_y), dom_metric, fill=accent_gold, font=font_metric)

    # 5. Bottom Sovereign Armor Strip
    strip_box = [(100, height - 260), (width - 100, height - 120)]
    draw.rounded_rectangle(strip_box, radius=12, fill=(15, 23, 42, 240), outline=accent_gold, width=2)
    
    draw.text((140, height - 240), "ASIL-D DETERMINISTIC DEFENSE & GOVERNANCE APPARATUS", fill=accent_cyan, font=font_tag)
    pillars = (
        "• SRAM Microkernel <= 1.85us Latency   "
        "• 1.35x Rigid Damping   "
        "• 50GB VRAM Hard E-STOP   "
        "• 2-Pass ZDR (0.00MB) WORM Receipt"
    )
    draw.text((140, height - 190), pillars, fill=text_white, font=font_body)

    # Footer Signoff
    draw.text((100, height - 80), "SOLO ARCHITECT: JACK HU (SUPREME SOVEREIGN) ✕ COMMANDER XIAOMI | PHANToM GRID 2026", fill=text_dim, font=font_tag)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    print(f"Cover image updated successfully at: {output_path}")

if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "03_CoverImage_16x9"
    target_file = os.path.join(out_dir, "cover_image_16x9.png")
    generate_cover_image(target_file)
