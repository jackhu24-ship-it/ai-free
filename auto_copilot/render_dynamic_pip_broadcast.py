import os
import sys
import subprocess
import math
import shutil
from PIL import Image, ImageDraw, ImageFont

VIDEO_IN = "auto_copilot/input_video.mp4"
BGM_IN = "auto_copilot/tech_ambient_bgm.wav"
TEMP_VIDEO = "auto_copilot/temp_pip_v2_visual.mp4"
FINAL_LOCAL = "auto_copilot/final_pip_broadcast_v2.mp4"
FINAL_CLOUD = r"G:\我的雲端硬碟\AI產出成品總庫\04_多媒體與教學素材\AutoCopilot_Hackathon_Demo_Broadcast_Remastered.mp4"

SRC_W, SRC_H = 1920, 1116
OUT_W, OUT_H = 1920, 1080
FPS = 29.93

# Setup Fonts
try:
    font_sub_spk = ImageFont.truetype("C:\\Windows\\Fonts\\msyhbd.ttc", 28)
    font_sub_txt = ImageFont.truetype("C:\\Windows\\Fonts\\msyhbd.ttc", 26)
    font_pip_title = ImageFont.truetype("C:\\Windows\\Fonts\\segoeuib.ttf", 18)
    font_pip_meta = ImageFont.truetype("C:\\Windows\\Fonts\\segoeuib.ttf", 15)
    font_hud_lg = ImageFont.truetype("C:\\Windows\\Fonts\\segoeuib.ttf", 32)
    font_hud_md = ImageFont.truetype("C:\\Windows\\Fonts\\segoeuib.ttf", 20)
    font_hud_sm = ImageFont.truetype("C:\\Windows\\Fonts\\segoeui.ttf", 16)
    font_hud_mono = ImageFont.truetype("C:\\Windows\\Fonts\\consola.ttf", 16)
except:
    font_sub_spk = ImageFont.load_default()
    font_sub_txt = font_sub_spk
    font_pip_title = font_sub_spk
    font_pip_meta = font_sub_spk
    font_hud_lg = font_sub_spk
    font_hud_md = font_sub_spk
    font_hud_sm = font_sub_spk
    font_hud_mono = font_sub_spk

# Sub-window geometry
PIP_X, PIP_Y = 1250, 35
PIP_W, PIP_H = 630, 350
HEADER_H = 38
VIEW_W = PIP_W - 8
VIEW_H = PIP_H - HEADER_H - 4

def render_telemetry_hud(w, h, roll_p):
    """Renders a razor-sharp, rolling CAN-FD Telemetry & DTC HUD for Scene 2."""
    CANVAS_H = 500
    canvas = Image.new('RGBA', (w, CANVAS_H), (15, 23, 42, 255))
    draw = ImageDraw.Draw(canvas)

    # 1. Top Section: Telemetry Metrics
    draw.rounded_rectangle([15, 12, w - 15, 135], radius=8, fill=(30, 41, 59, 255), outline=(239, 68, 68, 220), width=2)
    draw.text((30, 20), "ENGINE COOLANT TEMP (ECT)", font=font_hud_md, fill=(248, 113, 113))
    draw.text((30, 48), "104.2 °C", font=font_hud_lg, fill=(255, 255, 255))
    draw.text((195, 58), "+4.2 °C (LIMIT: 105.0°C)", font=font_hud_sm, fill=(239, 68, 68))
    
    # Critical Alert Badge
    draw.rounded_rectangle([w - 180, 46, w - 30, 86], radius=6, fill=(220, 38, 38, 230))
    draw.text((w - 165, 54), "CRITICAL ALERT", font=font_hud_sm, fill=(255, 255, 255))
    
    # Telemetry parameters
    draw.text((30, 102), "Bus Voltage: 384.0 V   |   Line Pressure: 140.0 kPa   |   Pump: 100%", font=font_hud_mono, fill=(148, 163, 184))

    # 2. Middle Section: Active DTCs (UDS 0x19)
    draw.text((20, 150), "ACTIVE TROUBLE CODES (ISO 14229 / UDS 0x19)", font=font_hud_md, fill=(250, 204, 21))
    
    # DTC Row 1: P0117
    draw.rounded_rectangle([15, 182, w - 15, 248], radius=6, fill=(24, 33, 53, 255), outline=(239, 68, 68, 180), width=1)
    draw.rounded_rectangle([25, 192, 105, 238], radius=4, fill=(220, 38, 38, 240))
    draw.text((35, 202), "P0117", font=font_hud_md, fill=(255, 255, 255))
    draw.text((120, 195), "ECM • Coolant Temp Sensor 1 Low Input", font=font_hud_md, fill=(241, 245, 249))
    draw.text((120, 222), "Status: Confirmed | MIL: Active | Severity: High", font=font_hud_sm, fill=(148, 163, 184))

    # DTC Row 2: U0100
    draw.rounded_rectangle([15, 260, w - 15, 326], radius=6, fill=(24, 33, 53, 255), outline=(234, 179, 8, 180), width=1)
    draw.rounded_rectangle([25, 270, 105, 316], radius=4, fill=(202, 138, 4, 240))
    draw.text((35, 280), "U0100", font=font_hud_md, fill=(255, 255, 255))
    draw.text((120, 273), "BMS • Lost Communication with ECM/PCM", font=font_hud_md, fill=(241, 245, 249))
    draw.text((120, 300), "Status: Pending | Bus: CAN-FD CH1 | Latency: 38.6ms", font=font_hud_sm, fill=(148, 163, 184))

    # 3. Bottom Section: CAN-FD Telemetry Packet Stream
    draw.text((20, 345), "CAN-FD RAW BUS TELEMETRY (100Hz STREAM)", font=font_hud_md, fill=(56, 189, 248))
    draw.rounded_rectangle([15, 372, w - 15, 480], radius=6, fill=(15, 23, 42, 255), outline=(51, 65, 85, 255), width=1)
    draw.text((25, 384), "RX 0x7E8  DLC:8  DATA: 02 01 05 68 00 00 00 00 (ECT: 104°C)", font=font_hud_mono, fill=(52, 211, 153))
    draw.text((25, 408), "RX 0x7E0  DLC:8  DATA: 03 19 02 08 00 00 00 00 (DTC Poll OK)", font=font_hud_mono, fill=(148, 163, 184))
    draw.text((25, 432), "RX 0x140  DLC:8  DATA: 0F 28 80 00 00 00 00 00 (Bus: 384V)", font=font_hud_mono, fill=(148, 163, 184))
    draw.text((25, 456), "TX 0x7DF  DLC:8  DATA: 01 00 00 00 00 00 00 00 (Broadcast Req)", font=font_hud_mono, fill=(96, 165, 250))

    # Rolling calculation
    max_scroll = CANVAS_H - h
    scroll_y = int(max_scroll * roll_p)
    return canvas.crop((0, scroll_y, w, scroll_y + h))

# Step 0: Delete old output files first!
print("Applying rule: Delete old target video before generating new...")
if os.path.exists(TEMP_VIDEO):
    os.remove(TEMP_VIDEO)
if os.path.exists(FINAL_LOCAL):
    os.remove(FINAL_LOCAL)
if os.path.exists(FINAL_CLOUD):
    os.remove(FINAL_CLOUD)

print("Starting FFmpeg visual pipeline for High-Res Rolling PIP & Transparent Subtitles...")

pipe_in = subprocess.Popen([
    "ffmpeg", "-i", VIDEO_IN,
    "-f", "image2pipe", "-pix_fmt", "rgb24", "-vcodec", "rawvideo", "-"
], stdout=subprocess.PIPE, bufsize=10**8)

pipe_out = subprocess.Popen([
    "ffmpeg", "-y",
    "-f", "rawvideo", "-vcodec", "rawvideo",
    "-s", f"{OUT_W}x{OUT_H}", "-pix_fmt", "rgb24", "-r", str(FPS),
    "-i", "-",
    "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
    TEMP_VIDEO
], stdin=subprocess.PIPE)

frame_idx = 0
frame_bytes = SRC_W * SRC_H * 3

while True:
    raw_frame = pipe_in.stdout.read(frame_bytes)
    if len(raw_frame) < frame_bytes:
        break

    t = frame_idx / FPS

    # Determine Scene Parameters
    if t < 6.5:
        speaker = "Technician: "
        spk_color = (0, 240, 255) # Electric Cyan
        txt_color = (255, 230, 0) # Vivid Gold
        sub_text = '"AutoCopilot, check vehicle health status and active DTCs."'
        pip_badge = "LIVE AUDIO SPECTRUM"
        pip_meta = "16kHz PCM • WebRTC"
        theme_color = (0, 210, 255)
        # Roll through Audio spectrum
        crop_x = 640
        crop_w = 500
        p = min(1.0, max(0.0, t / 6.5))
        smooth_p = 0.5 - 0.5 * math.cos(p * math.pi)
        crop_y = int(220 + 200 * smooth_p)
        is_hud = False
    elif t < 17.5:
        speaker = "AutoCopilot: "
        spk_color = (255, 200, 0) # Bright Gold
        txt_color = (0, 240, 255) # Electric Cyan
        sub_text = '"Vehicle reports DTC P0117. Coolant temperature elevated at 104.2°C, approaching limit."'
        pip_badge = "TELEMETRY & DTC ROLL-CAM"
        pip_meta = "CAN-FD • Polled in 42.1ms"
        theme_color = (239, 68, 68) # Red Alert
        p = min(1.0, max(0.0, (t - 6.5) / 11.0))
        # smooth roll down across metrics, DTCs, and CAN bus
        smooth_p = 0.5 - 0.5 * math.cos(p * math.pi)
        is_hud = True
    elif t < 26.5:
        speaker = "Technician (Barge-in): "
        spk_color = (255, 75, 75) # Coral Red
        txt_color = (255, 230, 0) # Vivid Gold
        sub_text = '"Wait, stop! Is 104.2°C within the ISO 26262 safety limit?"'
        pip_badge = "VAD BARGE-IN MONITOR"
        pip_meta = "18.2ms Stop • Buffer FLUSHED"
        theme_color = (220, 38, 38)
        # Roll smoothly down so INTERRUPTED and its parameter payload are centered
        crop_x = 1130
        crop_w = 640
        p = min(1.0, max(0.0, (t - 17.5) / 9.0))
        smooth_p = 0.5 - 0.5 * math.cos(p * math.pi)
        crop_y = int(580 + 170 * smooth_p)
        is_hud = False
    elif t < 38.0:
        speaker = "AutoCopilot: "
        spk_color = (255, 200, 0) # Gold
        txt_color = (0, 240, 255) # Cyan
        sub_text = '"Negative. ISO 26262 ASIL-B mandates emergency shutdown if coolant exceeds 105.0°C."'
        pip_badge = "ISO 26262 COMPLIANCE SOP"
        pip_meta = "Safe State ASIL-B • 46.8ms"
        theme_color = (16, 185, 129) # Emerald Green
        # Roll through SOP card and repair procedure in full
        crop_x = 1130
        crop_w = 640
        p = min(1.0, max(0.0, (t - 26.5) / 11.5))
        smooth_p = 0.5 - 0.5 * math.cos(p * math.pi)
        crop_y = int(240 + 320 * smooth_p)
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
        crop_y = 520
        is_hud = False

    # 1. Main Background Frame: 100% Untouched Native Dashboard
    src_img = Image.frombytes("RGB", (SRC_W, SRC_H), raw_frame)
    main_frame = src_img.resize((OUT_W, OUT_H), Image.Resampling.BILINEAR).convert('RGBA')

    # 2. Viewport Content Generation (Native 1:1 Scale Sharpness)
    if is_hud:
        viewport_img = render_telemetry_hud(VIEW_W, VIEW_H, smooth_p)
    else:
        crop_h = int(crop_w * (VIEW_H / VIEW_W))
        crop_y = max(0, min(SRC_H - crop_h, crop_y))
        crop_x = max(0, min(SRC_W - crop_w, crop_x))
        macro_crop = src_img.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
        viewport_img = macro_crop.resize((VIEW_W, VIEW_H), Image.Resampling.LANCZOS).convert('RGBA')

    # Dynamic Cyber Scanline
    scan_y = int(((t * 1.5) % 1.0) * VIEW_H)
    scan_overlay = Image.new('RGBA', (VIEW_W, VIEW_H), (0, 0, 0, 0))
    scan_draw = ImageDraw.Draw(scan_overlay)
    scan_draw.line([(0, scan_y), (VIEW_W, scan_y)], fill=(*theme_color, 90), width=2)
    scan_draw.line([(0, max(0, scan_y - 1)), (VIEW_W, max(0, scan_y - 1))], fill=(255, 255, 255, 140), width=1)
    viewport_img = Image.alpha_composite(viewport_img, scan_overlay)

    # 3. Assemble Sub-Window Container
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

    # Pulsing neon glow border
    border_alpha = int(200 + 55 * math.sin(t * 5.0))
    pip_draw.rounded_rectangle([0, 0, PIP_W - 1, PIP_H - 1], radius=10, outline=(*theme_color, border_alpha), width=2)

    # Mask for smooth rounded corners
    mask = Image.new('L', (PIP_W, PIP_H), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, PIP_W, PIP_H], radius=10, fill=255)

    # Composite Sub-Window with Drop Shadow
    shadow = Image.new('RGBA', (PIP_W + 16, PIP_H + 16), (0, 0, 0, 140))
    main_frame.alpha_composite(shadow, (PIP_X - 8, PIP_Y - 4))
    main_frame.paste(pip_container, (PIP_X, PIP_Y), mask=mask)

    # 4. LIVE On-Air Badge (Top-Left)
    draw = ImageDraw.Draw(main_frame)
    draw.rounded_rectangle([30, 25, 340, 68], radius=8, fill=(13, 21, 38, 230), outline=(*theme_color, 200), width=2)
    draw.ellipse([45, 41, 57, 53], fill=(239, 68, 68, pulse_val))
    draw.text((66, 36), "LIVE", font=font_pip_title, fill=(255, 255, 255, 255))
    draw.text((112, 36), "• AutoCopilot x AssemblyAI", font=font_pip_title, fill=(170, 190, 220, 255))

    # 5. Transparent Subtitles (NO background box, high-contrast non-white colors with 3px dark stroke)
    sub_y = OUT_H - 85
    sub_x = 100
    draw.text((sub_x, sub_y), speaker, font=font_sub_spk, fill=spk_color, stroke_width=3, stroke_fill=(5, 10, 20, 255))
    spk_len = int(draw.textlength(speaker, font=font_sub_spk))
    draw.text((sub_x + spk_len, sub_y), sub_text, font=font_sub_txt, fill=txt_color, stroke_width=3, stroke_fill=(5, 10, 20, 255))

    # 6. Bottom Glowing Progress Line
    prog_w = int((t / 43.25) * OUT_W)
    draw.rectangle([0, OUT_H - 5, prog_w, OUT_H], fill=theme_color)

    # Output to ffmpeg pipe
    pipe_out.stdin.write(main_frame.convert("RGB").tobytes())
    frame_idx += 1
    if frame_idx % 150 == 0:
        print(f"Rendered {frame_idx}/1293 frames ({int(t)}s / 43s)...")

pipe_in.stdout.close()
pipe_out.stdin.close()
pipe_in.wait()
pipe_out.wait()

print("Visual composition complete. Mixing cleaned voice audio and cyber telemetry BGM...")

subprocess.run([
    "ffmpeg", "-y",
    "-i", TEMP_VIDEO,
    "-i", VIDEO_IN,
    "-i", BGM_IN,
    "-filter_complex",
    "[1:a]afftdn=nf=-25,volume=1.35[clean_voice];[2:a]volume=0.85[bgm];[clean_voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]",
    "-map", "0:v",
    "-map", "[aout]",
    "-c:v", "copy",
    "-c:a", "aac", "-b:a", "192k",
    FINAL_LOCAL
], check=True)

if os.path.exists(TEMP_VIDEO):
    os.remove(TEMP_VIDEO)

print("Deploying final broadcast remastered video to Google Drive AI Output Vault...")
shutil.copy2(FINAL_LOCAL, FINAL_CLOUD)

if os.path.exists(FINAL_LOCAL):
    os.remove(FINAL_LOCAL)

print(f"\n==========================================")
print(f"SUCCESS! Broadcast Remastered Video Delivered:")
print(f"{FINAL_CLOUD}")
print(f"==========================================")
