import os
import math
from PIL import Image, ImageDraw, ImageFont

SRC_IMG = 'auto_copilot/frame_orig_5s.png'
img_orig = Image.open(SRC_IMG)
SRC_W, SRC_H = img_orig.size
OUT_W, OUT_H = 1920, 1080

# Load fonts
try:
    font_sub_spk = ImageFont.truetype('C:\\Windows\\Fonts\\msyhbd.ttc', 28)
    font_sub_txt = ImageFont.truetype('C:\\Windows\\Fonts\\msyhbd.ttc', 26)
    font_pip_title = ImageFont.truetype('C:\\Windows\\Fonts\\segoeuib.ttf', 18)
    font_pip_meta = ImageFont.truetype('C:\\Windows\\Fonts\\segoeuib.ttf', 15)
except:
    font_sub_spk = ImageFont.truetype('C:\\Windows\\Fonts\\segoeuib.ttf', 28)
    font_sub_txt = ImageFont.truetype('C:\\Windows\\Fonts\\segoeuib.ttf', 26)
    font_pip_title = ImageFont.load_default()
    font_pip_meta = font_pip_title

def render_test_frame(t, out_name):
    # Base frame
    frame = img_orig.resize((OUT_W, OUT_H), Image.Resampling.BILINEAR).convert('RGBA')

    # PIP Geometry
    PIP_X, PIP_Y = 1250, 35
    PIP_W, PIP_H = 630, 350
    HEADER_H = 38
    VIEW_W = PIP_W - 8
    VIEW_H = PIP_H - HEADER_H - 4

    # Scene state based on time
    if t < 6.5:
        speaker = "Technician: "
        spk_color = (0, 240, 255) # Electric Cyan
        txt_color = (255, 230, 0) # Vivid Cyber Gold
        sub_text = '"AutoCopilot, check vehicle health status and active DTCs."'
        pip_badge = "LIVE AUDIO SPECTRUM"
        pip_meta = "16kHz PCM • WebRTC Stream"
        theme_color = (0, 210, 255) # Cyan
        # Audio spectrum card rolling
        crop_x = 640
        crop_w = 480
        y_start, y_end = 220, 480
        p = min(1.0, max(0.0, (t - 0.0) / 6.5))
        crop_y = int(y_start + (y_end - y_start) * p)
    elif t < 17.5:
        speaker = "AutoCopilot: "
        spk_color = (255, 200, 0) # Bright Gold
        txt_color = (0, 240, 255) # Electric Cyan
        sub_text = '"Vehicle reports DTC P0117. Coolant temperature elevated at 104.2°C, approaching limit."'
        pip_badge = "TELEMETRY & DTC ROLL-CAM"
        pip_meta = "CAN-FD 500k • Polled in 42.1ms"
        theme_color = (255, 80, 80) # Vivid Red
        # Roll through Telemetry and Tool Calling
        crop_x = 1130
        crop_w = 640
        y_start, y_end = 150, 600
        p = min(1.0, max(0.0, (t - 6.5) / 11.0))
        # smooth roll
        smooth_p = 0.5 - 0.5 * math.cos(p * math.pi)
        crop_y = int(y_start + (y_end - y_start) * smooth_p)
    elif t < 26.5:
        speaker = "Technician (Barge-in): "
        spk_color = (255, 70, 70) # Alert Coral Red
        txt_color = (255, 230, 0) # Vivid Gold
        sub_text = '"Wait, stop! Is 104.2°C within the ISO 26262 safety limit?"'
        pip_badge = "VAD BARGE-IN MONITOR"
        pip_meta = "Sub-20ms Stop • TTS FLUSHED"
        theme_color = (255, 50, 50) # Bright Red
        # Roll through INTERRUPTED card
        crop_x = 1130
        crop_w = 640
        y_start, y_end = 450, 800
        p = min(1.0, max(0.0, (t - 17.5) / 9.0))
        smooth_p = 0.5 - 0.5 * math.cos(p * math.pi)
        crop_y = int(y_start + (y_end - y_start) * smooth_p)
    elif t < 38.0:
        speaker = "AutoCopilot: "
        spk_color = (255, 200, 0) # Gold
        txt_color = (0, 240, 255) # Cyan
        sub_text = '"Negative. ISO 26262 ASIL-B mandates emergency shutdown if coolant exceeds 105.0°C."'
        pip_badge = "ISO 26262 COMPLIANCE SOP"
        pip_meta = "ASIL-B RAG Match in 46.8ms"
        theme_color = (0, 230, 140) # Emerald Green
        # Roll through SOP card
        crop_x = 1130
        crop_w = 640
        y_start, y_end = 250, 750
        p = min(1.0, max(0.0, (t - 26.5) / 11.5))
        smooth_p = 0.5 - 0.5 * math.cos(p * math.pi)
        crop_y = int(y_start + (y_end - y_start) * smooth_p)
    else:
        speaker = "AutoCopilot: "
        spk_color = (255, 200, 0)
        txt_color = (0, 240, 255)
        sub_text = '"AutoCopilot: Keeping hands on tools, eyes on machines, and diagnostics faster than ever."'
        pip_badge = "FULL CYCLE DIAGNOSTIC PASS"
        pip_meta = "100% Autonomous Hands-Free"
        theme_color = (120, 140, 255) # Indigo
        crop_x = 1130
        crop_w = 640
        crop_y = 500

    # 1. CROP VIEWPORT FROM ORIGINAL IMAGE (Native 1:1 scale for maximum sharpness!)
    # Calculate crop height based on aspect ratio
    crop_h = int(crop_w * (VIEW_H / VIEW_W))
    # Ensure within bounds
    crop_y = max(0, min(SRC_H - crop_h, crop_y))
    crop_x = max(0, min(SRC_W - crop_w, crop_x))

    macro_crop = img_orig.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
    # Resize cleanly using LANCZOS
    macro_scaled = macro_crop.resize((VIEW_W, VIEW_H), Image.Resampling.LANCZOS).convert('RGBA')

    # 2. Add Cyber Scanline (動態掃描線效果)
    scan_y = int(((t * 1.5) % 1.0) * VIEW_H)
    scan_overlay = Image.new('RGBA', (VIEW_W, VIEW_H), (0, 0, 0, 0))
    scan_draw = ImageDraw.Draw(scan_overlay)
    # 2-line glowing scanline
    scan_draw.line([(0, scan_y), (VIEW_W, scan_y)], fill=(*theme_color, 80), width=2)
    scan_draw.line([(0, max(0, scan_y - 1)), (VIEW_W, max(0, scan_y - 1))], fill=(255, 255, 255, 120), width=1)
    macro_scaled = Image.alpha_composite(macro_scaled, scan_overlay)

    # 3. BUILD PIP CONTAINER WITH DYNAMIC NEON GLOW BORDER
    pip_container = Image.new('RGBA', (PIP_W, PIP_H), (10, 16, 28, 255))
    pip_draw = ImageDraw.Draw(pip_container)

    # Paste viewport
    pip_container.paste(macro_scaled, (4, HEADER_H))

    # Draw Header Bar
    pip_draw.rectangle([0, 0, PIP_W, HEADER_H], fill=(13, 21, 38, 255))
    # Accent top border
    pip_draw.rectangle([0, 0, PIP_W, 3], fill=theme_color)

    # Animated pulsing indicator dot
    pulse_val = int(170 + 85 * math.sin(t * 7.0))
    pip_draw.ellipse([14, 12, 24, 22], fill=(*theme_color, pulse_val))
    pip_draw.ellipse([16, 14, 22, 20], fill=(255, 255, 255, pulse_val))

    # Header Texts
    pip_draw.text((32, 8), pip_badge, font=font_pip_title, fill=theme_color)
    meta_w = pip_draw.textlength(pip_meta, font=font_pip_meta)
    pip_draw.text((PIP_W - meta_w - 14, 10), pip_meta, font=font_pip_meta, fill=(180, 200, 225, 255))

    # Outer border with pulsing glow
    border_alpha = int(200 + 55 * math.sin(t * 5.0))
    pip_draw.rounded_rectangle([0, 0, PIP_W - 1, PIP_H - 1], radius=10, outline=(*theme_color, border_alpha), width=2)

    # Rounded Corner Mask
    mask = Image.new('L', (PIP_W, PIP_H), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, PIP_W, PIP_H], radius=10, fill=255)

    # Drop shadow
    shadow = Image.new('RGBA', (PIP_W + 16, PIP_H + 16), (0, 0, 0, 140))
    frame.alpha_composite(shadow, (PIP_X - 8, PIP_Y - 4))
    frame.paste(pip_container, (PIP_X, PIP_Y), mask=mask)

    # 4. LIVE ON-AIR BADGE (Top-Left)
    draw = ImageDraw.Draw(frame)
    draw.rounded_rectangle([30, 25, 340, 68], radius=8, fill=(13, 21, 38, 230), outline=(*theme_color, 200), width=2)
    draw.ellipse([45, 41, 57, 53], fill=(255, 50, 50, pulse_val))
    draw.text((66, 36), "LIVE", font=font_pip_title, fill=(255, 255, 255, 255))
    draw.text((112, 36), "• AutoCopilot ✕ AssemblyAI", font=font_pip_title, fill=(170, 190, 220, 255))

    # 5. TRANSPARENT SUBTITLES (NO background box! Non-white vivid contrast text with outline!)
    sub_y = OUT_H - 85
    sub_x = 100
    # Speaker with 3px dark navy outline
    draw.text((sub_x, sub_y), speaker, font=font_sub_spk, fill=spk_color, stroke_width=3, stroke_fill=(5, 10, 20, 255))
    spk_len = int(draw.textlength(speaker, font=font_sub_spk))
    # Subtitle text with 3px dark outline (Vivid Yellow / Cyan, NOT white!)
    draw.text((sub_x + spk_len, sub_y), sub_text, font=font_sub_txt, fill=txt_color, stroke_width=3, stroke_fill=(5, 10, 20, 255))

    # 6. Bottom Glowing Progress Bar
    prog_w = int((t / 43.25) * OUT_W)
    draw.rectangle([0, OUT_H - 5, prog_w, OUT_H], fill=theme_color)

    frame.convert('RGB').save(out_name)
    print(f"Saved {out_name} at t={t}s")

render_test_frame(5.0, 'auto_copilot/test_t5s.png')
render_test_frame(12.0, 'auto_copilot/test_t12s.png')
render_test_frame(22.0, 'auto_copilot/test_t22s.png')
render_test_frame(32.0, 'auto_copilot/test_t32s.png')
