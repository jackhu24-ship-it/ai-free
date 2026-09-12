import os
import sys
import subprocess
import math
import shutil
from PIL import Image, ImageDraw, ImageFont

VIDEO_IN = "auto_copilot/input_video.mp4"
BGM_IN = "auto_copilot/tech_ambient_bgm.wav"
TEMP_VIDEO = "auto_copilot/temp_pip_visual.mp4"
FINAL_LOCAL = "auto_copilot/final_pip_broadcast.mp4"
FINAL_CLOUD = r"G:\我的雲端硬碟\AI產出成品總庫\04_多媒體與教學素材\AutoCopilot_Hackathon_Demo_Broadcast_Remastered.mp4"

SRC_W, SRC_H = 1920, 1116
OUT_W, OUT_H = 1920, 1080
FPS = 29.93

# Font setup
try:
    font_pip_title = ImageFont.truetype("C:\\Windows\\Fonts\\segoeuib.ttf", 20)
    font_pip_body = ImageFont.truetype("C:\\Windows\\Fonts\\segoeui.ttf", 18)
    font_sub_speaker = ImageFont.truetype("C:\\Windows\\Fonts\\segoeuib.ttf", 26)
    font_sub_text = ImageFont.truetype("C:\\Windows\\Fonts\\segoeui.ttf", 24)
    font_live = ImageFont.truetype("C:\\Windows\\Fonts\\segoeuib.ttf", 18)
except:
    font_pip_title = ImageFont.load_default()
    font_pip_body = font_pip_title
    font_sub_speaker = font_pip_title
    font_sub_text = font_pip_title
    font_live = font_pip_title

def get_scene_state(t):
    if t < 6.5:
        return {
            "speaker": "👨‍🔧 Technician",
            "speaker_color": (56, 189, 248),
            "sub_text": '"AutoCopilot, check vehicle health status and active DTCs."',
            "pip_badge": "🎙️ LIVE AUDIO INGESTION",
            "pip_color": (59, 130, 246),
            "pip_title": "16kHz PCM WebRTC Streamer",
            "pip_detail": "AssemblyAI Universal-3 Pro • Word Boost: Active",
            # Crop region for PIP from main screen: audio spectrum area
            "crop_box": (680, 560, 1200, 780)
        }
    elif t < 17.5:
        return {
            "speaker": "🤖 AutoCopilot",
            "speaker_color": (250, 204, 21),
            "sub_text": '"Vehicle reports DTC P0117. Coolant temperature is elevated at 104.2°C, approaching limit."',
            "pip_badge": "⚠️ TELEMETRY MACRO CAM",
            "pip_color": (239, 68, 68),
            "pip_title": "Coolant: 104.2 °C (HIGH) | DTC: P0117",
            "pip_detail": "CAN-FD Telemetry Polled in 42.1ms • UDS 0x19 Active",
            # Crop region for PIP: Coolant gauge & DTC table
            "crop_box": (680, 220, 1200, 480)
        }
    elif t < 26.5:
        return {
            "speaker": "👨‍🔧 Technician (Barge-in)",
            "speaker_color": (248, 113, 113),
            "sub_text": '"Wait, stop! Is 104.2°C within the ISO 26262 safety limit?"',
            "pip_badge": "🛑 VAD BARGE-IN MONITOR",
            "pip_color": (220, 38, 38),
            "pip_title": "[INTERRUPTED] In 18.2 ms",
            "pip_detail": "Sub-20ms CancellationToken • Audio Buffer FLUSHED",
            # Crop region for PIP: INTERRUPTED badge area in inspector
            "crop_box": (1180, 530, 1750, 700)
        }
    elif t < 38.0:
        return {
            "speaker": "🤖 AutoCopilot",
            "speaker_color": (250, 204, 21),
            "sub_text": '"Negative. ISO 26262 ASIL-B mandates emergency shutdown if coolant exceeds 105.0°C."',
            "pip_badge": "📜 ISO 26262 COMPLIANCE",
            "pip_color": (16, 185, 129),
            "pip_title": "Emergency Shutdown Mandated",
            "pip_detail": "Vector SOP Match in 46.8ms • Safe State ASIL-B",
            # Crop region for PIP: SOP card in inspector
            "crop_box": (1180, 680, 1800, 860)
        }
    else:
        return {
            "speaker": "🎙️ AutoCopilot",
            "speaker_color": (165, 180, 252),
            "sub_text": '"AutoCopilot: Keeping hands on tools, eyes on machines, and diagnostics faster than ever."',
            "pip_badge": "✅ DIAGNOSTIC PASS",
            "pip_color": (99, 102, 241),
            "pip_title": "Hands-Free Voice AI Proven",
            "pip_detail": "Full 43-Second Closed-Loop Diagnostic Cycle",
            "crop_box": (680, 220, 1200, 480)
        }

print("Starting FFmpeg visual pipeline for Apple-style PIP (Picture-in-Picture)...")

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

# PIP In-set Window Geometry (Upper Right Corner)
PIP_X, PIP_Y = 1320, 30
PIP_W, PIP_H = 560, 330
PIP_CORNER_RADIUS = 12

while True:
    raw_frame = pipe_in.stdout.read(frame_bytes)
    if len(raw_frame) < frame_bytes:
        break

    t = frame_idx / FPS
    st = get_scene_state(t)

    # 1. Main Background: 100% Pure, Untouched, High-Res Dashboard!
    src_img = Image.frombytes("RGB", (SRC_W, SRC_H), raw_frame)
    # Fit SRC_H (1116) to OUT_H (1080) cleanly
    main_frame = src_img.resize((OUT_W, OUT_H), Image.Resampling.BILINEAR)

    # 2. Render Picture-in-Picture (子畫面) Macro In-set
    cb = st["crop_box"]
    # Safely crop macro region from original high-res frame
    crop_w = max(50, cb[2] - cb[0])
    crop_h = max(50, cb[3] - cb[1])
    macro_crop = src_img.crop((cb[0], cb[1], cb[0] + crop_w, cb[1] + crop_h))
    
    # Target inner video area inside PIP: leaving top bar for header
    inner_h = PIP_H - 65
    macro_fitted = macro_crop.resize((PIP_W, inner_h), Image.Resampling.BILINEAR)

    # Assemble PIP Window with Glassmorphism Card
    pip_card = Image.new("RGBA", (PIP_W, PIP_H), (15, 23, 42, 245))
    # Paste macro video inside
    pip_card.paste(macro_fitted.convert("RGBA"), (0, 65))

    pip_draw = ImageDraw.Draw(pip_card)
    # Header Accent bar
    pip_draw.rectangle([0, 0, PIP_W, 65], fill=(10, 15, 28, 255))
    pip_draw.rectangle([0, 0, PIP_W, 4], fill=st["pip_color"])

    # Blinking Mini Dot
    pulse_alpha = int(180 + 75 * math.sin(t * 8.0))
    pip_draw.ellipse([18, 20, 30, 32], fill=(239, 68, 68, pulse_alpha))
    # Badge Text
    pip_draw.text((38, 14), st["pip_badge"], font=font_pip_title, fill=st["pip_color"])
    pip_draw.text((38, 38), st["pip_detail"], font=font_pip_body, fill=(203, 213, 225, 255))

    # Border around PIP Card
    pip_draw.rounded_rectangle([0, 0, PIP_W - 1, PIP_H - 1], radius=PIP_CORNER_RADIUS, outline=(71, 85, 105, 255), width=2)

    # Create mask for smooth rounded corners on PIP
    mask = Image.new("L", (PIP_W, PIP_H), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, PIP_W, PIP_H], radius=PIP_CORNER_RADIUS, fill=255)

    # Composite PIP onto Main Frame with Subtle Outer Drop Shadow
    main_frame = main_frame.convert("RGBA")
    # Soft shadow behind PIP
    shadow = Image.new("RGBA", (PIP_W + 16, PIP_H + 16), (0, 0, 0, 130))
    main_frame.alpha_composite(shadow, (PIP_X - 8, PIP_Y - 4))
    main_frame.paste(pip_card, (PIP_X, PIP_Y), mask=mask)

    # 3. Top-Left Live On-Air Bug: "LIVE • AutoCopilot ✕ AssemblyAI"
    draw = ImageDraw.Draw(main_frame)
    draw.rounded_rectangle([30, 25, 360, 68], radius=8, fill=(15, 23, 42, 220), outline=(51, 65, 85, 255), width=2)
    draw.ellipse([45, 41, 57, 53], fill=(239, 68, 68, pulse_alpha))
    draw.text((66, 36), "LIVE", font=font_live, fill=(255, 255, 255, 255))
    draw.text((112, 36), "• AutoCopilot ✕ AssemblyAI", font=font_live, fill=(148, 163, 184, 255))

    # 4. Clean TV-Style Subtitles Bar (Centered at Bottom)
    sub_y = OUT_H - 95
    sub_h = 60
    draw.rounded_rectangle([120, sub_y, OUT_W - 120, sub_y + sub_h], radius=10, fill=(10, 15, 28, 235), outline=(51, 65, 85, 230), width=1)
    
    spk_str = st["speaker"] + ": "
    draw.text((150, sub_y + 14), spk_str, font=font_sub_speaker, fill=st["speaker_color"])
    spk_len = int(draw.textlength(spk_str, font=font_sub_speaker))
    draw.text((150 + spk_len, sub_y + 15), st["sub_text"], font=font_sub_text, fill=(255, 255, 255, 255))

    # 5. Amber Progress Bar at Bottom
    progress_w = int((t / 43.25) * OUT_W)
    draw.rectangle([0, OUT_H - 6, progress_w, OUT_H], fill=(234, 179, 8, 255))

    # Convert back to RGB and output
    pipe_out.stdin.write(main_frame.convert("RGB").tobytes())
    frame_idx += 1
    if frame_idx % 150 == 0:
        print(f"Rendered {frame_idx}/1293 frames ({int(t)}s / 43s)...")

pipe_in.stdout.close()
pipe_out.stdin.close()
pipe_in.wait()
pipe_out.wait()

print("PIP Video composition complete. Muxing cleaned voice and cyber BGM...")

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

print("Deploying final PIP broadcast video to Google Drive...")
shutil.copy2(FINAL_LOCAL, FINAL_CLOUD)

if os.path.exists(FINAL_LOCAL):
    os.remove(FINAL_LOCAL)

print(f"SUCCESS! Apple-Style Picture-in-Picture Video Delivered:\n{FINAL_CLOUD}")
