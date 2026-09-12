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
    font_hud_lg = ImageFont.truetype('C:\\Windows\\Fonts\\segoeuib.ttf', 32)
    font_hud_md = ImageFont.truetype('C:\\Windows\\Fonts\\segoeuib.ttf', 20)
    font_hud_sm = ImageFont.truetype('C:\\Windows\\Fonts\\segoeui.ttf', 16)
    font_hud_mono = ImageFont.truetype('C:\\Windows\\Fonts\\consola.ttf', 16)
except:
    font_sub_spk = ImageFont.load_default()
    font_sub_txt = font_sub_spk
    font_pip_title = font_sub_spk
    font_pip_meta = font_sub_spk
    font_hud_lg = font_sub_spk
    font_hud_md = font_sub_spk
    font_hud_sm = font_sub_spk
    font_hud_mono = font_sub_spk

def render_telemetry_hud(t, w, h, roll_p):
    """Renders a razor-sharp, rolling CAN-FD Telemetry & DTC HUD for Scene 2."""
    # Virtual canvas that is taller than viewport so it can roll
    CANVAS_H = 520
    canvas = Image.new('RGBA', (w, CANVAS_H), (15, 23, 42, 255))
    draw = ImageDraw.Draw(canvas)

    # 1. Top Section: Telemetry Metrics
    # Coolant Temp Box
    draw.rounded_rectangle([15, 15, w - 15, 140], radius=8, fill=(30, 41, 59, 255), outline=(239, 68, 68, 200), width=2)
    draw.text((30, 24), "ENGINE COOLANT TEMP (ECT)", font=font_hud_md, fill=(248, 113, 113))
    # Pulse warning
    draw.text((30, 52), "104.2 °C", font=font_hud_lg, fill=(255, 255, 255))
    draw.text((200, 62), "+4.2 °C (LIMIT: 105.0°C)", font=font_hud_sm, fill=(239, 68, 68))
    # Warning badge
    draw.rounded_rectangle([w - 180, 50, w - 30, 90], radius=6, fill=(220, 38, 38, 220))
    draw.text((w - 165, 58), "CRITICAL ALERT", font=font_hud_sm, fill=(255, 255, 255))
    # Sub-metrics
    draw.text((30, 105), "Bus Voltage: 384.0 V   |   Line Pressure: 140.0 kPa   |   Pump: 100% PWM", font=font_hud_mono, fill=(148, 163, 184))

    # 2. Middle Section: Active DTCs (UDS Service 0x19)
    draw.text((20, 160), "ACTIVE TROUBLE CODES (ISO 14229 / UDS 0x19)", font=font_hud_md, fill=(250, 204, 21))
    
    # DTC Row 1: P0117
    draw.rounded_rectangle([15, 195, w - 15, 260], radius=6, fill=(24, 33, 53, 255), outline=(239, 68, 68, 180), width=1)
    draw.rounded_rectangle([25, 205, 105, 250], radius=4, fill=(220, 38, 38, 240))
    draw.text((35, 215), "P0117", font=font_hud_md, fill=(255, 255, 255))
    draw.text((120, 208), "ECM • Engine Coolant Temp Circuit Low Input", font=font_hud_md, fill=(241, 245, 249))
    draw.text((120, 234), "Status: Confirmed | MIL: Active | Severity: High", font=font_hud_sm, fill=(148, 163, 184))

    # DTC Row 2: U0100
    draw.rounded_rectangle([15, 275, w - 15, 340], radius=6, fill=(24, 33, 53, 255), outline=(234, 179, 8, 180), width=1)
    draw.rounded_rectangle([25, 285, 105, 330], radius=4, fill=(202, 138, 4, 240))
    draw.text((35, 295), "U0100", font=font_hud_md, fill=(255, 255, 255))
    draw.text((120, 288), "BMS • Lost Communication with ECM/PCM", font=font_hud_md, fill=(241, 245, 249))
    draw.text((120, 314), "Status: Pending | Bus: CAN-FD CH1 | Latency: 38.6ms", font=font_hud_sm, fill=(148, 163, 184))

    # 3. Bottom Section: CAN-FD Telemetry Packet Stream
    draw.text((20, 360), "CAN-FD RAW BUS TELEMETRY (100Hz STREAM)", font=font_hud_md, fill=(56, 189, 248))
    draw.rounded_rectangle([15, 390, w - 15, 500], radius=6, fill=(15, 23, 42, 255), outline=(51, 65, 85, 255), width=1)
    draw.text((25, 402), "RX 0x7E8  DLC:8  DATA: 02 01 05 68 00 00 00 00 (ECT: 104°C)", font=font_hud_mono, fill=(52, 211, 153))
    draw.text((25, 426), "RX 0x7E0  DLC:8  DATA: 03 19 02 08 00 00 00 00 (DTC Poll OK)", font=font_hud_mono, fill=(148, 163, 184))
    draw.text((25, 450), "RX 0x140  DLC:8  DATA: 0F 28 80 00 00 00 00 00 (Bus: 384V)", font=font_hud_mono, fill=(148, 163, 184))
    draw.text((25, 474), "TX 0x7DF  DLC:8  DATA: 01 00 00 00 00 00 00 00 (Broadcast Req)", font=font_hud_mono, fill=(96, 165, 250))

    # Crop based on rolling progress (輪動效果)
    max_scroll = CANVAS_H - h
    scroll_y = int(max_scroll * roll_p)
    return canvas.crop((0, scroll_y, w, scroll_y + h))

def render_frame_pipeline(t, out_name):
    # Fit main dashboard to 1920x1080
    frame = img_orig.resize((OUT_W, OUT_H), Image.Resampling.BILINEAR).convert('RGBA')

    PIP_X, PIP_Y = 1250, 35
    PIP_W, PIP_H = 630, 350
    HEADER_H = 38
    VIEW_W = PIP_W - 8
    VIEW_H = PIP_H - HEADER_H - 4

    # Determine Scene Parameters
    if t < 6.5:
        speaker = "Technician: "
        spk_color = (0, 240, 255) # Cyan
        txt_color = (255, 230, 0) # Vivid Yellow
        sub_text = '"AutoCopilot, check vehicle health status and active DTCs."'
        pip_badge = "LIVE AUDIO INGESTION"
        pip_meta = "16kHz PCM • WebRTC"
        theme_color = (0, 210, 255)
        # Roll through Audio spectrum
        crop_x = 640
        crop_w = 480
        p = min(1.0, max(0.0, t / 6.5))
        smooth_p = 0.5 - 0.5 * math.cos(p * math.pi)
        crop_y = int(220 + 240 * smooth_p)
        is_hud = False
    elif t < 17.5:
        speaker = "AutoCopilot: "
        spk_color = (255, 200, 0) # Gold
        txt_color = (0, 240, 255) # Cyan
        sub_text = '"Vehicle reports DTC P0117. Coolant temperature elevated at 104.2°C, approaching limit."'
        pip_badge = "TELEMETRY & DTC ROLL-CAM"
        pip_meta = "CAN-FD • Polled in 42.1ms"
        theme_color = (239, 68, 68) # Red alert
        p = min(1.0, max(0.0, (t - 6.5) / 11.0))
        # smooth roll down
        smooth_p = 0.5 - 0.5 * math.cos(p * math.pi)
        is_hud = True
    elif t < 26.5:
        speaker = "Technician (Barge-in): "
        spk_color = (255, 70, 70) # Coral
        txt_color = (255, 230, 0) # Yellow
        sub_text = '"Wait, stop! Is 104.2°C within the ISO 26262 safety limit?"'
        pip_badge = "VAD BARGE-IN MONITOR"
        pip_meta = "18.2ms Stop • Buffer FLUSHED"
        theme_color = (220, 38, 38)
        # Roll smoothly from lookup down to INTERRUPTED badge
        crop_x = 1130
        crop_w = 640
        p = min(1.0, max(0.0, (t - 17.5) / 9.0))
        smooth_p = 0.5 - 0.5 * math.cos(p * math.pi)
        crop_y = int(520 + 240 * smooth_p)
        is_hud = False
    elif t < 38.0:
        speaker = "AutoCopilot: "
        spk_color = (255, 200, 0) # Gold
        txt_color = (0, 240, 255) # Cyan
        sub_text = '"Negative. ISO 26262 ASIL-B mandates emergency shutdown if coolant exceeds 105.0°C."'
        pip_badge = "ISO 26262 COMPLIANCE SOP"
        pip_meta = "Safe State ASIL-B • 46.8ms"
        theme_color = (16, 185, 129) # Emerald Green
        # Roll through SOP card and procedure
        crop_x = 1130
        crop_w = 640
        p = min(1.0, max(0.0, (t - 26.5) / 11.5))
        smooth_p = 0.5 - 0.5 * math.cos(p * math.pi)
        crop_y = int(140 + 380 * smooth_p)
        is_hud = False
    else:
        speaker = "AutoCopilot: "
        spk_color = (255, 200, 0)
        txt_color = (0, 240, 255)
        sub_text = '"AutoCopilot: Keeping hands on tools, eyes on machines, and diagnostics faster than ever."'
        pip_badge = "FULL CYCLE DIAGNOSTIC PASS"
        pip_meta = "100% Autonomous Hands-Free"
        theme_color = (99, 102, 241) # Indigo
        crop_x = 1130
        crop_w = 640
        crop_y = 480
        is_hud = False

    # 1. GENERATE PIP VIEWPORT CONTENT
    if is_hud:
        # High-res rolling Telemetry HUD
        viewport_img = render_telemetry_hud(t, VIEW_W, VIEW_H, smooth_p)
    else:
        # Native 1:1 scale crop from dashboard
        crop_h = int(crop_w * (VIEW_H / VIEW_W))
        crop_y = max(0, min(SRC_H - crop_h, crop_y))
        crop_x = max(0, min(SRC_W - crop_w, crop_x))
        macro_crop = img_orig.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
        viewport_img = macro_crop.resize((VIEW_W, VIEW_H), Image.Resampling.LANCZOS).convert('RGBA')

    # 2. Dynamic Cyber Scanline
    scan_y = int(((t * 1.5) % 1.0) * VIEW_H)
    scan_overlay = Image.new('RGBA', (VIEW_W, VIEW_H), (0, 0, 0, 0))
    scan_draw = ImageDraw.Draw(scan_overlay)
    scan_draw.line([(0, scan_y), (VIEW_W, scan_y)], fill=(*theme_color, 90), width=2)
    scan_draw.line([(0, max(0, scan_y - 1)), (VIEW_W, max(0, scan_y - 1))], fill=(255, 255, 255, 140), width=1)
    viewport_img = Image.alpha_composite(viewport_img, scan_overlay)

    # 3. Assemble PIP Container
    pip_container = Image.new('RGBA', (PIP_W, PIP_H), (10, 16, 28, 255))
    pip_draw = ImageDraw.Draw(pip_container)
    pip_container.paste(viewport_img, (4, HEADER_H))

    # Header Bar
    pip_draw.rectangle([0, 0, PIP_W, HEADER_H], fill=(13, 21, 38, 255))
    pip_draw.rectangle([0, 0, PIP_W, 3], fill=theme_color)

    pulse_val = int(170 + 85 * math.sin(t * 7.0))
    pip_draw.ellipse([14, 12, 24, 22], fill=(*theme_color, pulse_val))
    pip_draw.ellipse([16, 14, 22, 20], fill=(255, 255, 255, pulse_val))

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

    # Drop Shadow
    shadow = Image.new('RGBA', (PIP_W + 16, PIP_H + 16), (0, 0, 0, 140))
    frame.alpha_composite(shadow, (PIP_X - 8, PIP_Y - 4))
    frame.paste(pip_container, (PIP_X, PIP_Y), mask=mask)

    # 4. LIVE Top-Left Badge (without problematic glyphs)
    draw = ImageDraw.Draw(frame)
    draw.rounded_rectangle([30, 25, 340, 68], radius=8, fill=(13, 21, 38, 230), outline=(*theme_color, 200), width=2)
    draw.ellipse([45, 41, 57, 53], fill=(239, 68, 68, pulse_val))
    draw.text((66, 36), "LIVE", font=font_pip_title, fill=(255, 255, 255, 255))
    draw.text((112, 36), "• AutoCopilot x AssemblyAI", font=font_pip_title, fill=(170, 190, 220, 255))

    # 5. TRANSPARENT SUBTITLES (Zero background box, non-white high-contrast vivid colors with dark stroke)
    sub_y = OUT_H - 85
    sub_x = 100
    draw.text((sub_x, sub_y), speaker, font=font_sub_spk, fill=spk_color, stroke_width=3, stroke_fill=(5, 10, 20, 255))
    spk_len = int(draw.textlength(speaker, font=font_sub_spk))
    draw.text((sub_x + spk_len, sub_y), sub_text, font=font_sub_txt, fill=txt_color, stroke_width=3, stroke_fill=(5, 10, 20, 255))

    # 6. Glowing Bottom Progress Line
    prog_w = int((t / 43.25) * OUT_W)
    draw.rectangle([0, OUT_H - 5, prog_w, OUT_H], fill=theme_color)

    frame.convert('RGB').save(out_name)
    print(f"Generated {out_name}")

render_frame_pipeline(3.0, 'auto_copilot/sample_s1_3s.png')
render_frame_pipeline(11.0, 'auto_copilot/sample_s2_11s.png')
render_frame_pipeline(22.0, 'auto_copilot/sample_s3_22s.png')
render_frame_pipeline(31.0, 'auto_copilot/sample_s4_31s.png')
