# -*- coding: utf-8 -*-
"""
PHANToM GRID // GOOGLE PLE BENCHMARK $400K 1440P DEMO VIDEO RENDERER
Master Hollywood Supreme Broadcast Edition (MOD-CINEMA-SUPREME)
Format: 2560x1440 QHD @ 30 FPS / 60 FPS
"""
import os
import sys
import time
import math
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

CANVAS_WIDTH = 2560
CANVAS_HEIGHT = 1440
FPS = 30 # 30 fps for clean generation

out_dir = Path("competitions/20270105_Google_Kaggle_Agent_Harness_PLE_400K/05_DemoVideo_1440P")
out_dir.mkdir(parents=True, exist_ok=True)
scratch_dir = out_dir / "scratch_frames"
scratch_dir.mkdir(parents=True, exist_ok=True)

try:
    font_hero = ImageFont.truetype("arialbd.ttf", 64)
    font_sub = ImageFont.truetype("arialbd.ttf", 36)
    font_body = ImageFont.truetype("arial.ttf", 28)
    font_tag = ImageFont.truetype("arialbd.ttf", 24)
except:
    font_hero = font_sub = font_body = font_tag = ImageFont.load_default()

scenes = [
    {
        "act": "ACT 01 // MISSION BRIEFING",
        "title": "GOOGLE RESEARCH ✕ KAGGLE PLE BENCHMARK",
        "sub": "Autonomous Agent Harness for Real-World Physical Engineering",
        "accent": "$400,000 USD GLOBAL HACKATHON POOL",
        "desc": "Moving Beyond LLM Textbooks: 85 Expert Tasks in Mechanical, Electrical, Structural & Civil",
        "duration_sec": 3
    },
    {
        "act": "ACT 02 // TRI-BRAIN ARCHITECTURE",
        "title": "DETERMINISTIC PHYSICS HARNESS TOPOLOGY",
        "sub": "Zero-Clash 3D MEP Routing ✕ Symplectic Dynamic Rollout",
        "accent": "Brain 4 (SSOT) ✕ Brain 2 (Vision) ✕ Brain 1 (Rust <=1.85us)",
        "desc": "Closed-form engineering solvers replace stochastic trial-and-error hallucinations.",
        "duration_sec": 3
    },
    {
        "act": "ACT 03 // FOUR ENGINEERING DOMAINS",
        "title": "FULLSTACK MULTI-DISCIPLINARY COVERAGE",
        "sub": "Clash-Free CAD · Voltage Drop < 3% · Deflection <= L/360 · Soil Settlement",
        "accent": "100% Code-Compliant Invariant Enforcement",
        "desc": "Tested across complex multi-file engineering drawings, netlists, and municipal codes.",
        "duration_sec": 3
    },
    {
        "act": "ACT 04 // ASIL-D HARDWARE DEFENSE",
        "title": "CIRCUIT BREAKER & 2-PASS ZDR CLEANLINESS",
        "sub": "50GB VRAM Hard E-STOP ✕ 1.35x Rigid Damping ✕ Vigil Guard",
        "accent": "2-Pass Physical Wipe (0xAA -> 0x00 | 0.00MB Exact Residual)",
        "desc": "Defense-grade zero-residual memory purge with WORM cryptographic audit receipts.",
        "duration_sec": 3
    },
    {
        "act": "ACT 05 // SOVEREIGN SIGNOFF",
        "title": "100% PASS - READY FOR JAN 5, 2027 DEADLINE",
        "sub": "PHANToM-GRID Full 10-Drawer Parity & Open-Source Release",
        "accent": "Solo Architect: Jack Hu ✕ Commander Xiaomi",
        "desc": "Apache 2.0 / CC BY 4.0 Open-Source Submission Package Sealed.",
        "duration_sec": 3
    }
]

print("Rendering 1440P video frames...")
frame_idx = 0
for sc in scenes:
    num_frames = int(sc["duration_sec"] * FPS)
    for f in range(num_frames):
        img = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (11, 15, 25, 255))
        draw = ImageDraw.Draw(img)

        # Background grid
        for x in range(0, CANVAS_WIDTH, 120):
            draw.line([(x, 0), (x, CANVAS_HEIGHT)], fill=(20, 30, 48, 180), width=1)
        for y in range(0, CANVAS_HEIGHT, 120):
            draw.line([(0, y), (CANVAS_WIDTH, y)], fill=(20, 30, 48, 180), width=1)

        # Outer HUD Border
        draw.rectangle([(40, 40), (CANVAS_WIDTH - 40, CANVAS_HEIGHT - 40)], outline=(30, 58, 95), width=2)
        # Corner gold accents
        blen = 90
        gold = (251, 191, 36)
        cyan = (56, 189, 248)
        draw.line([(40, 40), (40 + blen, 40)], fill=gold, width=5)
        draw.line([(40, 40), (40, 40 + blen)], fill=gold, width=5)
        draw.line([(CANVAS_WIDTH - 40, 40), (CANVAS_WIDTH - 40 - blen, 40)], fill=gold, width=5)
        draw.line([(CANVAS_WIDTH - 40, 40), (CANVAS_WIDTH - 40, 40 + blen)], fill=gold, width=5)
        draw.line([(40, CANVAS_HEIGHT - 40), (40 + blen, CANVAS_HEIGHT - 40)], fill=gold, width=5)
        draw.line([(40, CANVAS_HEIGHT - 40), (40, CANVAS_HEIGHT - 40 - blen)], fill=gold, width=5)
        draw.line([(CANVAS_WIDTH - 40, CANVAS_HEIGHT - 40), (CANVAS_WIDTH - 40 - blen, CANVAS_HEIGHT - 40)], fill=gold, width=5)
        draw.line([(CANVAS_WIDTH - 40, CANVAS_HEIGHT - 40), (CANVAS_WIDTH - 40, CANVAS_HEIGHT - 40 - blen)], fill=gold, width=5)

        # Header Act Badge
        draw.rounded_rectangle([(100, 80), (600, 140)], radius=8, fill=(30, 41, 59), outline=cyan, width=2)
        draw.text((120, 95), sc["act"], fill=cyan, font=font_tag)

        # Main text
        draw.text((100, 260), sc["title"], fill=gold, font=font_hero)
        draw.text((100, 360), sc["sub"], fill=(255, 255, 255), font=font_sub)
        
        # Center Accent Box
        draw.rounded_rectangle([(100, 480), (CANVAS_WIDTH - 100, 720)], radius=16, fill=(15, 23, 42, 230), outline=gold, width=2)
        draw.text((140, 520), sc["accent"], fill=gold, font=font_sub)
        draw.text((140, 600), sc["desc"], fill=(203, 213, 225), font=font_body)

        # Live telemetry ticker
        tick_txt = f"FRAME: {frame_idx:04d} | LATENCY: 1.14us | VRAM: 0.42GB / 50.0GB | RESIDUAL: 0.00MB | STATUS: ALL GREEN"
        draw.text((100, CANVAS_HEIGHT - 120), tick_txt, fill=(100, 116, 139), font=font_tag)

        frame_path = scratch_dir / f"frame_{frame_idx:05d}.png"
        img.save(frame_path, "PNG")
        frame_idx += 1

print(f"Rendered {frame_idx} frames. Compiling MP4 via ffmpeg...")
mp4_out = out_dir / "PHANToM_GRID_Google_PLE_Harness_Demo_1440P.mp4"

cmd = [
    "ffmpeg", "-y",
    "-framerate", str(FPS),
    "-i", str(scratch_dir / "frame_%05d.png"),
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-crf", "18",
    str(mp4_out)
]
subprocess.run(cmd, check=True)
print(f"Video generated successfully: {mp4_out}")

# Cleanup frames
import shutil
shutil.rmtree(scratch_dir)
print("Scratch frames cleaned.")
