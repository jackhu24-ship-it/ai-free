#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
PHANTOM GRID - Headless AI Video Generator (方案 B 實裝)
語音合成 (Edge-TTS) + 規格化字卡 (FFmpeg) + 1080P/60FPS 無損封裝

【影音排版與提詞器標準 (Video Typography Standards)】
1. 畫布規格：1080P (1920x1080), 30/60 FPS, YUV420P 高相容性色彩空間
2. 底色定錨：科技深黑 `#0B0F19` 畫布
3. 提詞卡規範：底部半透明卡片 `rgba(15, 23, 42, 0.88)`，保留安全邊距 (x:160, y:760, w:1600, h:180)
4. 階層字級：大標題 48pt 純白 (#FFFFFF) + 副標題 32pt 科技藍 (#38BDF8)
5. 雙軌金庫：產出直通 G 槽真身金庫，並單向投影至 C 槽鏡像，嚴守 Zero-Desktop Pollution
"""

import os
import sys
import asyncio
import tempfile
import argparse
import subprocess
import shutil
from pathlib import Path
import edge_tts

# Windows UTF-8 強制防護
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 引入路徑解析器以動態錨定真身金庫與戰鬥鏡像
tools_dir = Path(__file__).resolve().parent
if str(tools_dir) not in sys.path:
    sys.path.insert(0, str(tools_dir))

try:
    from path_resolver import TRUTH_ROOT, COMBAT_ROOT, find_g_drive_truth
except ImportError:
    COMBAT_ROOT = Path(r"C:\260728-code")
    TRUTH_ROOT = Path(r"G:\我的雲端硬碟\260803_opencode")

# 真身輸出金庫 (優先寫入 G 槽，死守零桌面污染)
OUTPUT_DIR = TRUTH_ROOT / "AI產出成品總庫" / "Videos_1080P"
COMBAT_OUTPUT_DIR = COMBAT_ROOT / "AI產出成品總庫" / "Videos_1080P"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
try:
    COMBAT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass


def escape_ffmpeg_text(text: str) -> str:
    r"""
    嚴格過濾與轉義 FFmpeg drawtext 濾鏡之特殊字元
    防止冒號、單引號、反斜線、百分比造成 filtergraph 解析崩潰
    """
    if not text:
        return ""
    # 反斜線轉義
    t = text.replace("\\", "\\\\")
    # 單引號轉義
    t = t.replace("'", "'\\''")
    # 冒號轉義 (FFmpeg 選項分隔符需要 1 個反斜線: \:)
    t = t.replace(":", "\\:")
    # 百分比符號轉義 (FFmpeg 擴展語法需要 2 個反斜線: \\%)
    t = t.replace("%", "\\\\%")
    return t


async def generate_speech(
    text: str,
    voice: str = "zh-TW-YunJheNeural",
    audio_path: str = "temp_audio.mp3",
    rate: str = "+0%",
    pitch: str = "+0Hz"
) -> str:
    """生成廣播級自然神經網路語音"""
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(audio_path)
    return audio_path


def compose_video(
    title: str,
    subtitle: str,
    audio_file: str,
    output_name: str,
    fps: int = 30
) -> Path:
    """調用 FFmpeg 壓制符合廣播級排版標準之 1080P 影片"""
    out_path = OUTPUT_DIR / output_name
    combat_path = COMBAT_OUTPUT_DIR / output_name

    # 轉義文字內容
    safe_title = escape_ffmpeg_text(title)
    safe_subtitle = escape_ffmpeg_text(subtitle)

    # 符合 PHANTOM 規範：底部安全邊距、深色半透明卡片、雙行字級差
    filter_graph = (
        f"[0:v]"
        f"drawbox=x=160:y=760:w=1600:h=180:color=0x0F172A@0.88:t=fill,"
        f"drawtext=text='{safe_title}':fontcolor=white:fontsize=48:x=200:y=790,"
        f"drawtext=text='{safe_subtitle}':fontcolor=0x38BDF8:fontsize=32:x=200:y=860[v]"
    )

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", f"color=c=0x0B0F19:s=1920x1080:r={fps}:d=60",  # 深黑底色畫布
        "-i", str(audio_file),
        "-filter_complex", filter_graph,
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(out_path)
    ]

    result = subprocess.run(
        ffmpeg_cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg 壓制失敗: {result.stderr[-800:]}")

    # 單向鏡像投影至 C 槽戰鬥目錄
    try:
        combat_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(out_path, combat_path)
    except Exception as e:
        print(f"⚠️ [鏡像提示] C 槽戰鬥鏡像投影跳過: {e}")

    file_size_kb = out_path.stat().st_size / 1024
    print(f"🎬 [影片全自動出爐] 成品已直通真身金庫: {out_path} ({file_size_kb:.1f} KB)")
    if combat_path.exists():
        print(f"⚡ [戰鬥鏡像已就緒] 高速讀取路徑: {combat_path}")

    return out_path


def produce_video(
    title: str = "【PHANTOM GRID】全域雙層認證架構落地",
    subtitle: str = "雙軌架構實時監控，25項極限驗收全數通過",
    text_script: str = "PHANTOM GRID 雙層認證全域架構已完成部署，所有指標全數綠燈。",
    voice: str = "zh-TW-YunJheNeural",
    output_name: str = "phantom_demo_01.mp4",
    rate: str = "+0%"
) -> dict:
    """無人值守純代碼流水線端到端生產函數"""
    temp_dir = Path(tempfile.gettempdir()) / "phantom_video_tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    audio_tmp = temp_dir / f"voice_{os.getpid()}_{hash(text_script) % 100000}.mp3"

    try:
        # 1. 生成自然語音
        print(f"🎙️ [語音合成] 正在調用 Edge-TTS ({voice})...")
        asyncio.run(generate_speech(text_script, voice=voice, audio_path=str(audio_tmp), rate=rate))

        # 2. 自動合成 1080P 影片
        print("🎞️ [影像壓制] 正在啟動 FFmpeg 1080P 規格化合成...")
        out_path = compose_video(
            title=title,
            subtitle=subtitle,
            audio_file=str(audio_tmp),
            output_name=output_name
        )

        combat_path = COMBAT_OUTPUT_DIR / output_name
        return {
            "status": "SUCCESS",
            "g_path": str(out_path),
            "c_path": str(combat_path) if combat_path.exists() else str(out_path),
            "size_bytes": out_path.stat().st_size
        }
    finally:
        # 潔癖清理暫存語音檔
        if audio_tmp.exists():
            try:
                audio_tmp.unlink()
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(description="PHANTOM GRID 方案 B: 全自動無人化 1080P 影片生成器")
    parser.add_argument("--title", default="【PHANTOM GRID】全域雙層認證架構落地", help="影片主標題 (48pt)")
    parser.add_argument("--subtitle", default="雙軌架構實時監控，25項極限驗收全數通過", help="影片副標題 (32pt)")
    parser.add_argument("--script", default="PHANTOM GRID 雙層認證全域架構已完成部署，所有指標全數綠燈。", help="配音逐字文案")
    parser.add_argument("--voice", default="zh-TW-YunJheNeural", help="Edge-TTS 語音角色 (如 zh-TW-YunJheNeural, en-US-ChristopherNeural)")
    parser.add_argument("--output", default="phantom_demo_01.mp4", help="輸出檔案名稱")
    parser.add_argument("--rate", default="+0%", help="語速微調 (如 +10%, -5%)")

    args = parser.parse_args()

    result = produce_video(
        title=args.title,
        subtitle=args.subtitle,
        text_script=args.script,
        voice=args.voice,
        output_name=args.output,
        rate=args.rate
    )
    print(f"✅ [流水線完工] {result}")


if __name__ == "__main__":
    main()
