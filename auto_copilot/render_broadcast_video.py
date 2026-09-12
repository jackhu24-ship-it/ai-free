import os
import sys
import subprocess
import math
import shutil
from PIL import Image, ImageDraw, ImageFont

VIDEO_IN = "auto_copilot/input_video.mp4"
BGM_IN = "auto_copilot/tech_ambient_bgm.wav"
TEMP_VIDEO = "auto_copilot/temp_visual.mp4"
FINAL_LOCAL = "auto_copilot/final_broadcast.mp4"
FINAL_CLOUD = r"G:\我的雲端硬碟\AI產出成品總庫\04_多媒體與教學素材\AutoCopilot_Hackathon_Demo_Broadcast_Remastered.mp4"

SRC_W, SRC_H = 1920, 1116
OUT_W, OUT_H = 1920, 1080
FPS = 29.93

# Font setup
try:
    font_title = ImageFont.truetype("C:\\Windows\\Fonts\\segoeuib.ttf", 26)
    font_subtitle = ImageFont.truetype("C:\\Windows\\Fonts\\segoeui.ttf", 20)
    font_badge = ImageFont.truetype("C:\\Windows\\Fonts\\segoeuib.ttf", 18)
    font_live = ImageFont.truetype("C:\\Windows\\Fonts\\segoeuib.ttf", 18)
    font_sub_speaker = ImageFont.truetype("C:\\Windows\\Fonts\\segoeuib.ttf", 24)
    font_sub_text = ImageFont.truetype("C:\\Windows\\Fonts\\segoeui.ttf", 24)
except:
    font_title = ImageFont.load_default()
    font_subtitle = font_title
    font_badge = font_title
    font_live = font_title
    font_sub_speaker = font_title
    font_sub_text = font_title

def get_camera_viewport(t):
    full = (0, 0, SRC_W, SRC_H)
    telemetry_view = (580, 150, 760, 650)
    bargein_view = (1080, 320, 800, 680)
    sop_view = (1080, 420, 800, 680)

    def ease(p):
        return 0.5 - 0.5 * math.cos(math.pi * p)

    def interp(v1, v2, p):
        p = ease(max(0.0, min(1.0, p)))
        return (
            v1[0] + (v2[0] - v1[0]) * p,
            v1[1] + (v2[1] - v1[1]) * p,
            v1[2] + (v2[2] - v1[2]) * p,
            v1[3] + (v2[3] - v1[3]) * p,
        )

    if t < 6.5:
        return full
    elif t < 8.0:
        return interp(full, telemetry_view, (t - 6.5) / 1.5)
    elif t < 17.0:
        return telemetry_view
    elif t < 19.0:
        return interp(telemetry_view, bargein_view, (t - 17.0) / 2.0)
    elif t < 27.0:
        return bargein_view
    elif t < 29.0:
        return interp(bargein_view, sop_view, (t - 27.0) / 2.0)
    elif t < 37.0:
        return sop_view
    elif t < 39.5:
        return interp(sop_view, full, (t - 37.0) / 2.5)
    else:
        return full

def get_broadcast_info(t):
    if t < 6.5:
        return {
            "badge": "🎙️ ON-AIR | INDUSTRIAL VOICE AI",
            "badge_color": (37, 99, 235),
            "title": "AutoCopilot: Hands-Free Diagnostic Co-Pilot",
            "subtitle": "Real-Time Telemetry Retrieval & ISO Safety Manual Vector Search",
            "speaker": "👨‍🔧 Technician",
            "speaker_color": (56, 189, 248),
            "subtitle_text": '"AutoCopilot, check vehicle health status and active DTCs."',
            "pulse_red": False
        }
    elif t < 17.5:
        return {
            "badge": "⚠️ VEHICLE TELEMETRY ALERT",
            "badge_color": (220, 38, 38),
            "title": "Coolant Temp: 104.2 °C (Approaching Limit) | DTC P0117 Active",
            "subtitle": "CAN-FD Bus Polled (42.1ms) • Service 0x19 Fault Code Verified",
            "speaker": "🤖 AutoCopilot",
            "speaker_color": (250, 204, 21),
            "subtitle_text": '"Vehicle reports DTC P0117. Active coolant temp elevated at 104.2°C, approaching limits."',
            "pulse_red": True
        }
    elif t < 26.5:
        return {
            "badge": "🛑 SUB-20ms VOICE BARGE-IN",
            "badge_color": (185, 28, 28),
            "title": "Technician Interruption Detected: TTS Output Flushed in 18.2 ms",
            "subtitle": "AssemblyAI PartialTranscript Event Triggered Instant Speech Cancellation",
            "speaker": "👨‍🔧 Technician (Barge-in)",
            "speaker_color": (248, 113, 113),
            "subtitle_text": '"Wait, stop! Is 104.2°C within the ISO 26262 safety limit?"',
            "pulse_red": True
        }
    elif t < 38.0:
        return {
            "badge": "📜 ISO 26262 SAFETY STANDARD RAG",
            "badge_color": (16, 185, 129),
            "title": "Mandated Action: Emergency Shutdown on Coolant > 105.0 °C",
            "subtitle": "Vector SOP Match: Idle Engine Immediately & Inspect Auxiliary Relay (46.8ms)",
            "speaker": "🤖 AutoCopilot",
            "speaker_color": (250, 204, 21),
            "subtitle_text": '"Negative. ISO 26262 ASIL-B mandates emergency shutdown if coolant exceeds 105°C."',
            "pulse_red": False
        }
    else:
        return {
            "badge": "✅ DIAGNOSTIC CYCLE COMPLETE",
            "badge_color": (79, 70, 229),
            "title": "Mission-Critical Hands-Free Diagnostics Proven in 43 Seconds",
            "subtitle": "Powered by AssemblyAI Universal-3 Pro Streaming STT & Word Boost",
            "speaker": "🎙️ AutoCopilot",
            "speaker_color": (165, 180, 252),
            "subtitle_text": '"AutoCopilot: Keeping hands on tools, eyes on machines, and diagnostics faster than ever."',
            "pulse_red": False
        }

print("Starting FFmpeg visual pipeline...")

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
    info = get_broadcast_info(t)
    vx, vy, vw, vh = get_camera_viewport(t)

    img = Image.frombytes("RGB", (SRC_W, SRC_H), raw_frame)

    vx = max(0, min(SRC_W - 100, int(vx)))
    vy = max(0, min(SRC_H - 100, int(vy)))
    vw = max(100, min(SRC_W - vx, int(vw)))
    vh = max(100, min(SRC_H - vy, int(vh)))
    
    cropped = img.crop((vx, vy, vx + vw, vy + vh))
    frame_out = cropped.resize((OUT_W, OUT_H), Image.Resampling.BILINEAR)

    draw = ImageDraw.Draw(frame_out, "RGBA")

    # 1. Non-invasive Flashing Red Edge Border (Glows along screen perimeter, NEVER overlaps text)
    if info.get("pulse_red"):
        pulse = 0.5 + 0.5 * math.sin(t * 8.0)
        red_alpha = int(120 * pulse)
        glow_thick = int(12 + 6 * pulse)
        # Top, left, right borders
        draw.rectangle([0, 0, OUT_W, glow_thick], fill=(239, 68, 68, red_alpha))
        draw.rectangle([0, 0, glow_thick, OUT_H], fill=(239, 68, 68, red_alpha))
        draw.rectangle([OUT_W - glow_thick, 0, OUT_W, OUT_H], fill=(239, 68, 68, red_alpha))
        # Bottom edge above lower-third
        draw.rectangle([0, OUT_H - 185 - glow_thick, OUT_W, OUT_H - 185], fill=(239, 68, 68, red_alpha))

    # 2. Top-Left Network Bug: "LIVE • AutoCopilot ✕ AssemblyAI"
    draw.rounded_rectangle([30, 25, 360, 68], radius=8, fill=(15, 23, 42, 220), outline=(51, 65, 85, 255), width=2)
    dot_alpha = int(180 + 75 * math.sin(t * 6.0))
    draw.ellipse([45, 41, 57, 53], fill=(239, 68, 68, dot_alpha))
    draw.text((66, 36), "LIVE", font=font_live, fill=(255, 255, 255, 255))
    draw.text((112, 36), "• AutoCopilot ✕ AssemblyAI", font=font_live, fill=(148, 163, 184, 255))

    # 3. Dedicated Subtitles Card (Synchronized Speech Text)
    sub_y = OUT_H - 180
    sub_h = 48
    draw.rounded_rectangle([150, sub_y, OUT_W - 150, sub_y + sub_h], radius=10, fill=(10, 15, 28, 235), outline=(71, 85, 105, 220), width=1)
    
    spk_text = info["speaker"] + ": "
    draw.text((175, sub_y + 10), spk_text, font=font_sub_speaker, fill=info["speaker_color"])
    spk_w = int(draw.textlength(spk_text, font=font_sub_speaker))
    draw.text((175 + spk_w, sub_y + 10), info["subtitle_text"], font=font_sub_text, fill=(255, 255, 255, 255))

    # 4. TV-Anchor Lower Third Banner
    banner_y = OUT_H - 122
    draw.rectangle([0, banner_y, OUT_W, OUT_H], fill=(10, 15, 28, 245))
    draw.rectangle([0, banner_y, OUT_W, banner_y + 4], fill=(59, 130, 246, 255))

    # Category Badge
    badge_w = 320
    draw.rounded_rectangle([35, banner_y + 16, 35 + badge_w, banner_y + 46], radius=6, fill=info["badge_color"])
    draw.text((50, banner_y + 20), info["badge"], font=font_badge, fill=(255, 255, 255, 255))

    # Headline & Subtitle
    draw.text((375, banner_y + 14), info["title"], font=font_title, fill=(255, 255, 255, 255))
    draw.text((375, banner_y + 54), info["subtitle"], font=font_subtitle, fill=(203, 213, 225, 255))

    # Progress bar at bottom
    progress_w = int((t / 43.25) * OUT_W)
    draw.rectangle([0, OUT_H - 5, progress_w, OUT_H], fill=(234, 179, 8, 255))

    pipe_out.stdin.write(frame_out.tobytes())
    frame_idx += 1
    if frame_idx % 150 == 0:
        print(f"Rendered {frame_idx}/1293 frames ({int(t)}s / 43s)...")

pipe_in.stdout.close()
pipe_out.stdin.close()
pipe_in.wait()
pipe_out.wait()

print("Visual render complete. Muxing cleaned voice and cyber BGM...")

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

# Copy final local output to Google Drive
print("Deploying to Google Drive media zone...")
shutil.copy2(FINAL_LOCAL, FINAL_CLOUD)

print(f"SUCCESS! Output delivered:\n{FINAL_CLOUD}")
