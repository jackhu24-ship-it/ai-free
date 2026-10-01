#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
PHANTOM GRID - 生活樂趣短片全自動生成器 (單一快速指令版)
《一人成軍的極致偷懶指南》
"""

import os
import sys
import asyncio
from pathlib import Path
import subprocess
import shutil
import edge_tts

# Windows UTF-8 強制防護
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

tools_dir = Path(__file__).resolve().parent
if str(tools_dir) not in sys.path:
    sys.path.insert(0, str(tools_dir))

try:
    from path_resolver import TRUTH_ROOT, COMBAT_ROOT
except ImportError:
    COMBAT_ROOT = Path(r"C:\260728-code")
    TRUTH_ROOT = Path(r"G:\我的雲端硬碟\260803_opencode")

OUTPUT_DIR = TRUTH_ROOT / "AI產出成品總庫" / "Videos_1080P"
COMBAT_OUTPUT_DIR = COMBAT_ROOT / "AI產出成品總庫" / "Videos_1080P"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
try:
    COMBAT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

# 幽默短片完整逐字稿
SCRIPT_TEXT = (
    "在 PHANTOM GRID 基地，統帥日常上班的第一個動作：隨手丟一張圖，然後去泡咖啡。"
    "外部傭兵 Bob 已經開始加班，把圖形代碼扒得乾乾淨淨。"
    "小米海關光速除錯，二辦沙盒無頭渲染。25 項考驗大滿貫，全數綠燈通關！"
    "咖啡剛喝第一口，Jack 哥落款完成。一人成軍的樂趣，就是這麼樸實無華。"
)


async def make_audio(audio_path: str = "temp_fun_voice.mp3"):
    comm = edge_tts.Communicate(SCRIPT_TEXT, voice="zh-TW-YunJheNeural", rate="+10%")
    await comm.save(audio_path)


def render_short():
    out_file = OUTPUT_DIR / "phantom_fun_daily.mp4"
    combat_file = COMBAT_OUTPUT_DIR / "phantom_fun_daily.mp4"
    audio_tmp = "temp_fun_voice.mp3"

    print("🎙️ 正在生成《一人成軍的極致偷懶指南》旁白...")
    asyncio.run(make_audio(audio_tmp))

    print("🎞️ 正在調用 FFmpeg 壓制 1080P 科技短片...")
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", "color=c=0x0B0F19:s=1920x1080:r=30:d=30",
        "-i", audio_tmp,
        "-filter_complex",
        "[0:v]drawbox=x=160:y=740:w=1600:h=200:color=0x0F172A@0.9:t=fill,"
        "drawtext=text='【PHANTOM GRID 基地日常】一人成軍的極致偷懶':fontcolor=white:fontsize=44:x=200:y=770,"
        "drawtext=text='截圖丟進去 ➔ 自動逆向 ➔ 雙層認證 ➔ 喝咖啡收工':fontcolor=0x38BDF8:fontsize=32:x=200:y=840,"
        "drawtext=text='[STATUS\\: COFFEE BREWING ➔ ALL GREEN 100\\\\%]':fontcolor=0x34D399:fontsize=24:x=200:y=895[v]",
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(out_file)
    ]
    subprocess.run(cmd, check=True)

    # 鏡像至 C 槽
    try:
        shutil.copy2(out_file, combat_file)
    except Exception:
        pass

    if os.path.exists(audio_tmp):
        try:
            os.remove(audio_tmp)
        except Exception:
            pass

    print(f"🎬 樂趣短片生成完成，已存入真身金庫: {out_file}")
    if combat_file.exists():
        print(f"⚡ 高速戰鬥鏡像: {combat_file}")


if __name__ == "__main__":
    render_short()
