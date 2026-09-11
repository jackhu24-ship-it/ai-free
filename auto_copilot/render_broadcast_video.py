import sys
import subprocess
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

VIDEO_IN = r"G:\我的雲端硬碟\AI產出成品總庫\04_多媒體與教學素材\AutoCopilot_Hackathon_Demo_Video.mp4"
BGM_IN = r"auto_copilot\tech_ambient_bgm.wav"
FINAL_OUT = r"G:\我的雲端硬碟\AI產出成品總庫\04_多媒體與教學素材\AutoCopilot_Hackathon_Demo_Broadcast_Remastered.mp4"

SRC_W, SRC_H = 1920, 1116
OUT_W, OUT_H = 1920, 1080
FPS = 29.93

# Font setup
try:
    font_title = ImageFont.truetype("C:\\Windows\\Fonts\\segoeuib.ttf", 32)
    font_subtitle = ImageFont.truetype("C:\\Windows\\Fonts\\segoeui.ttf", 22)
    font_badge = ImageFont.truetype("C:\\Windows\\Fonts\\segoeuib.ttf", 20)
    font_live = ImageFont.truetype("C:\\Windows\\Fonts\\segoeuib.ttf", 18)
except:
    font_title = ImageFont.load_default()
    font_subtitle = font_title
    font_badge = font_title
    font_live = font_title

# Camera Waypoints (t_start, t_end, x, y, w, h)
# t = 0 to 43.25
def get_camera_viewport(t):
    # Default Full Screen
    full = (0, 0, SRC_W, SRC_H)
    
    # Target 1: Left Telemetry (Coolant 104.2C & DTC table)
    # x around 550..1300, y around 160..800
    telemetry_view = (580, 150, 760, 650)
    
    # Target 2: Right Agent Inspector (Barge-in / INTERRUPTED)
    # x around 1050..1880, y around 320..880
    bargein_view = (1080, 320, 800, 680)
    
    # Target 3: ISO 26262 SOP execution
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
        # Subtle gentle float zoom in telemetry
        sway = math.sin((t - 8.0) * 0.5) * 10
        return (telemetry_view[0] + sway, telemetry_view[1], telemetry_view[2], telemetry_view[3])
    elif t < 19.0:
        return interp(telemetry_view, bargein_view, (t - 17.0) / 2.0)
    elif t < 27.0:
        sway = math.sin((t - 19.0) * 0.6) * 8
        return (bargein_view[0], bargein_view[1] + sway, bargein_view[2], bargein_view[3])
    elif t < 29.0:
        return interp(bargein_view, sop_view, (t - 27.0) / 2.0)
    elif t < 37.0:
        return sop_view
    elif t < 39.5:
        return interp(sop_view, full, (t - 37.0) / 2.5)
    else:
        return full

def get_broadcast_info(t):
    if t < 7.0:
        return {
            "badge": "🎙️ ON-AIR | INDUSTRIAL VOICE AI",
            "badge_color": (37, 99, 235), # Blue
            "title": "AutoCopilot: Hands-Free Diagnostic Co-Pilot",
            "subtitle": "Real-Time Telemetry Retrieval & ISO Safety Manual Vector Search",
            "highlight_box": None
        }
    elif t < 17.5:
        return {
            "badge": "⚠️ VEHICLE TELEMETRY ALERT",
            "badge_color": (220, 38, 38), # Red
            "title": "Coolant Temp: 104.2 °C (Approaching Limit) | DTC P0117 Active",
            "subtitle": "CAN-FD Bus Polled (42.1ms) • Service 0x19 Fault Code Verified",
            "highlight_box": (640, 240, 520, 180) # Gauges area
        }
    elif t < 27.5:
        return {
            "badge": "🛑 SUB-20ms VOICE BARGE-IN",
            "badge_color": (185, 28, 28), # Dark Red
            "title": "Technician Interruption Detected: TTS Output Flushed in 18.2 ms",
            "subtitle": "AssemblyAI PartialTranscript Event Triggered Instant Speech Cancellation",
            "highlight_box": (1180, 520, 480, 130) # Interrupted badge area
        }
    elif t < 38.0:
        return {
            "badge": "📜 ISO 26262 SAFETY STANDARD RAG",
            "badge_color": (16, 185, 129), # Emerald Green
            "title": "Mandated Action: Emergency Shutdown on Coolant > 105.0 °C",
            "subtitle": "Vector SOP Match: Idle Engine Immediately & Inspect Auxiliary Relay (46.8ms)",
            "highlight_box": (1180, 640, 680, 140) # SOP card area
        }
    else:
        return {
            "badge": "✅ DIAGNOSTIC CYCLE COMPLETE",
            "badge_color": (79, 70, 229), # Indigo
            "title": "Mission-Critical Hands-Free Diagnostics Proven in 43 Seconds",
            "subtitle": "Powered by AssemblyAI Universal-3 Pro Streaming STT & Word Boost",
            "highlight_box": None
        }

print("Starting FFmpeg pipeline for Dynamic TV Anchor Broadcast...")

# 1. Read frames from source video
pipe_in = subprocess.Popen([
    "ffmpeg", "-i", VIDEO_IN,
    "-f", "image2pipe", "-pix_fmt", "rgb24", "-vcodec", "rawvideo", "-"
], stdout=subprocess.PIPE, bufsize=10**8)

# 2. Temporary raw video output for multiplexing
TEMP_VIDEO = "auto_copilot\\temp_broadcast_visual.mp4"
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

    # Convert to PIL Image
    img = Image.frombytes("RGB", (SRC_W, SRC_H), raw_frame)

    # Optional: Draw animated highlight overlay on source image before crop
    if info["highlight_box"]:
        bx, by, bw, bh = info["highlight_box"]
        # Animated pulse factor
        pulse = 0.5 + 0.5 * math.sin(t * 8.0)
        glow_width = int(3 + 3 * pulse)
        draw_src = ImageDraw.Draw(img)
        # Corner brackets
        col = (255, int(60 + 195 * (1 - pulse)), int(60 * pulse))
        draw_src.rectangle([bx, by, bx + bw, by + bh], outline=col, width=glow_width)

    # Crop and Resize to Output Dimensions
    vx = max(0, min(SRC_W - 100, int(vx)))
    vy = max(0, min(SRC_H - 100, int(vy)))
    vw = max(100, min(SRC_W - vx, int(vw)))
    vh = max(100, min(SRC_H - vy, int(vh)))
    
    cropped = img.crop((vx, vy, vx + vw, vy + vh))
    frame_out = cropped.resize((OUT_W, OUT_H), Image.Resampling.BILINEAR)

    # Draw TV Broadcaster Overlays
    draw = ImageDraw.Draw(frame_out, "RGBA")

    # A. Top Left TV Network Bug: "LIVE | 🎙️ AutoCopilot ✕ AssemblyAI"
    draw.rounded_rectangle([30, 25, 380, 70], radius=8, fill=(15, 23, 42, 230), outline=(51, 65, 85, 255), width=2)
    # Pulsing Live Dot
    dot_alpha = int(180 + 75 * math.sin(t * 6.0))
    draw.ellipse([45, 42, 57, 54], fill=(239, 68, 68, dot_alpha))
    draw.text((68, 38), "LIVE", font=font_live, fill=(255, 255, 255, 255))
    draw.text((118, 38), "• AutoCopilot ✕ AssemblyAI", font=font_live, fill=(148, 163, 184, 255))

    # B. TV-Anchor Lower Third Banner (Dynamic Topic Tracker)
    banner_y = OUT_H - 135
    # Dark Glassmorphism background with blue accent top line
    draw.rectangle([0, banner_y, OUT_W, OUT_H], fill=(10, 15, 28, 240))
    draw.rectangle([0, banner_y, OUT_W, banner_y + 4], fill=(59, 130, 246, 255)) # Cyan-blue accent bar

    # Category Pill / Badge
    badge_w = 340
    draw.rounded_rectangle([40, banner_y + 16, 40 + badge_w, banner_y + 46], radius=6, fill=info["badge_color"])
    draw.text((55, banner_y + 20), info["badge"], font=font_badge, fill=(255, 255, 255, 255))

    # Dynamic Headline
    draw.text((400, banner_y + 14), info["title"], font=font_title, fill=(255, 255, 255, 255))
    # Dynamic Subtitle
    draw.text((400, banner_y + 56), info["subtitle"], font=font_subtitle, fill=(203, 213, 225, 255))

    # C. Real-time Progress Bar at bottom
    progress_w = int((t / 43.25) * OUT_W)
    draw.rectangle([0, OUT_H - 5, progress_w, OUT_H], fill=(234, 179, 8, 255)) # Amber yellow progress

    # Push to FFmpeg pipe
    pipe_out.stdin.write(frame_out.tobytes())
    frame_idx += 1
    if frame_idx % 150 == 0:
        print(f"Rendered {frame_idx}/1293 frames ({int(t)}s / 43s)...")

pipe_in.stdout.close()
pipe_out.stdin.close()
pipe_in.wait()
pipe_out.wait()

print("Video stream rendering complete. Now muxing audio & BGM...")

# 3. Final Mux: Video + Denoised Speech + Cyber BGM
subprocess.run([
    "ffmpeg", "-y",
    "-i", TEMP_VIDEO,
    "-i", VIDEO_IN,
    "-i", BGM_IN,
    "-filter_complex",
    "[1:a]afftdn=nf=-25,volume=1.35[clean_voice];[2:a]volume=0.85[bgm];[clean_voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]",
    "-map", "0:v",
    "-map", "[aout]",
    "-c:v", "libx264", "-crf", "18", "-preset", "fast",
    "-c:a", "aac", "-b:a", "192k",
    FINAL_OUT
], check=True)

print(f"SUCCESS! Dynamic Broadcast Edition Video Generated:\n{FINAL_OUT}")
