#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
PHANTOM GRID - 多角色擬真對白生成引擎
批次錄製角色獨立音軌母帶並支援 FFmpeg 依時間軸無縫拼裝
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

G_STUDIO_VOICES = TRUTH_ROOT / "02_Knowledge" / "Studio_Cinema" / "03_Voice_Masters"
C_STUDIO_VOICES = COMBAT_ROOT / "02_Knowledge" / "Studio_Cinema" / "03_Voice_Masters"
OUTPUT_DIR = TRUTH_ROOT / "AI產出成品總庫" / "Videos_1080P"
COMBAT_OUTPUT_DIR = COMBAT_ROOT / "AI產出成品總庫" / "Videos_1080P"

for p in [G_STUDIO_VOICES, C_STUDIO_VOICES, OUTPUT_DIR, COMBAT_OUTPUT_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# 劇本角色音軌清單 (文字、配音角色、語速調整、暫存檔名)
SCENE_SCRIPTS = [
    (
        "截圖丟 samples 夾了。小的們，動起來吧。",
        "zh-TW-YunJheNeural",
        "-5%",
        "voice_1_jack.mp3",
    ),
    (
        "Got it boss! Layout extracted, CSS variables ready! This is insane!",
        "en-US-ChristopherNeural",
        "+10%",
        "voice_2_bob.mp3",
    ),
    (
        "報告統帥！草案通過海關安檢，純黑已校準為石墨灰，放行！",
        "zh-TW-HsiaoChenNeural",
        "+15%",
        "voice_3_xiaomi.mp3",
    ),
    (
        "二辦沙盒渲染完成！二十五項極限驗收大滿貫，全數綠燈！",
        "zh-TW-HsiaoYuNeural",
        "+5%",
        "voice_4_office2.mp3",
    ),
    (
        "落款完成。收工，備份回 G 槽。",
        "zh-TW-YunJheNeural",
        "-5%",
        "voice_5_jack.mp3",
    ),
    (
        "收到！一鍵安裝包百分之百同步，指揮所全體休眠！",
        "zh-TW-HsiaoChenNeural",
        "+15%",
        "voice_6_xiaomi.mp3",
    ),
]


async def generate_all_voices():
    print("🎙️ 正在錄製全體 Agent 角色語音母帶...")
    for text, voice, rate, filename in SCENE_SCRIPTS:
        comm = edge_tts.Communicate(text, voice, rate=rate)
        out_g = G_STUDIO_VOICES / filename
        out_c = C_STUDIO_VOICES / filename
        await comm.save(str(out_g))
        shutil.copy2(out_g, out_c)
        print(f"  • [{voice}] 錄音完成: {filename} (已入庫 Voice_Masters)")


def concat_and_render():
    voice_list = G_STUDIO_VOICES / "voice_list.txt"
    with open(voice_list, "w", encoding="utf-8") as f:
        for _, _, _, filename in SCENE_SCRIPTS:
            clean_p = str((G_STUDIO_VOICES / filename).resolve()).replace("\\", "/")
            f.write(f"file '{clean_p}'\n")

    out_video = OUTPUT_DIR / "phantom_grid_movie_trailer.mp4"
    combat_video = COMBAT_OUTPUT_DIR / "phantom_grid_movie_trailer.mp4"

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(voice_list),
        "-f", "lavfi",
        "-i", "color=c=0x0B0F19:s=1920x1080:r=30",
        "-filter_complex",
        "[1:v]drawbox=x=160:y=760:w=1600:h=180:color=0x0F172A@0.88:t=fill,"
        "drawtext=text='【PHANTOM GRID】一人成軍基地日常':fontcolor=white:fontsize=48:x=220:y=790,"
        "drawtext=text='多角色實兵演練對白 (Jack 哥 / 小米 / Bob / 戰情官)':fontcolor=0x38BDF8:fontsize=32:x=220:y=860[v]",
        "-map", "[v]",
        "-map", "0:a",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(out_video),
    ]
    subprocess.run(cmd, check=True)
    try:
        shutil.copy2(out_video, combat_video)
    except Exception:
        pass
    print(f"\n🎬 [電影級有聲短片出爐] 存放於金庫: {out_video}")


if __name__ == "__main__":
    asyncio.run(generate_all_voices())
    concat_and_render()
