#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
PHANTOM GRID - 電影級多角色立繪對白短片生成器 (含頭像切換與 HUD 介面)
【一人成軍的極致偷懶指南 // PHANTOM GRID 基地日常樂趣】

【聲線配置】
- 👑 統帥 Jack 哥    : zh-TW-YunJheNeural (-5%)  [沉穩威嚴/從容幽默]
- 👩💼 執行秘書 小米  : zh-TW-HsiaoChenNeural (+15%) [幹練俐落/元氣滿滿]
- 🛠️ 外部傭兵 Bob    : en-US-ChristopherNeural (+10%) [粗獷硬核/美式特戰]
- 📊 二辦 戰情官     : zh-TW-HsiaoYuNeural (+5%)   [冷靜嚴肅/精密分析]

【畫面規格】
- 1080P (1920x1080), 30 FPS, YUV420P
- 左側：HUD 角色通訊卡 (專屬發光霓虹框 + 實體頭像立繪 + 職級代號)
- 右側：戰情實況動態展台 (依發言切換指揮所、DMZ 代碼、海關安檢、二辦大盤)
- 底部：深色半透明廣播級雙行字幕框，毫秒級同步
- 雙軌金庫存儲：直通 Studio_Cinema 與 Videos_1080P，恪守 Zero-Desktop Pollution
"""

import os
import sys
import json
import asyncio
import tempfile
import subprocess
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import edge_tts

# Windows UTF-8 強制防護
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 路徑動態解析
tools_dir = Path(__file__).resolve().parent
if str(tools_dir) not in sys.path:
    sys.path.insert(0, str(tools_dir))

try:
    from path_resolver import TRUTH_ROOT, COMBAT_ROOT
except ImportError:
    COMBAT_ROOT = Path(r"C:\260728-code")
    TRUTH_ROOT = Path(r"G:\我的雲端硬碟\260803_opencode")

# 專屬影視金庫路徑 (真身與戰鬥鏡像)
G_STUDIO = TRUTH_ROOT / "02_Knowledge" / "Studio_Cinema"
C_STUDIO = COMBAT_ROOT / "02_Knowledge" / "Studio_Cinema"

G_SCRIPTS = G_STUDIO / "01_Scripts_Teleprompter"
G_AVATARS = G_STUDIO / "02_Avatars_Characters"
G_VOICES = G_STUDIO / "03_Voice_Masters"
G_RENDERS = G_STUDIO / "04_Master_Renders"

C_SCRIPTS = C_STUDIO / "01_Scripts_Teleprompter"
C_AVATARS = C_STUDIO / "02_Avatars_Characters"
C_VOICES = C_STUDIO / "03_Voice_Masters"
C_RENDERS = C_STUDIO / "04_Master_Renders"

LOCAL_AVATAR_DIR = COMBAT_ROOT / "assets" / "avatars"

# 成品常規總庫
G_VIDEOS_1080P = TRUTH_ROOT / "AI產出成品總庫" / "Videos_1080P"
C_VIDEOS_1080P = COMBAT_ROOT / "AI產出成品總庫" / "Videos_1080P"

# 保證所有目錄存在
for p in [G_SCRIPTS, G_AVATARS, G_VOICES, G_RENDERS,
          C_SCRIPTS, C_AVATARS, C_VOICES, C_RENDERS,
          LOCAL_AVATAR_DIR, G_VIDEOS_1080P, C_VIDEOS_1080P]:
    p.mkdir(parents=True, exist_ok=True)

# 劇本分鏡與聲線配置清單
TIMELINE_SCENES = [
    {
        "scene_id": 1,
        "speaker": "Jack 哥",
        "title": "👑 總指揮官 Jack 哥 // SUPREME COMMANDER",
        "role_badge": "👑 COMMAND HQ // SUPREME COMMANDER",
        "color": (245, 158, 11),  # 金黃色
        "text": "截圖丟 samples 夾了。小的們，動起來吧。",
        "avatar": "avatar_jack.png",
        "voice": "zh-TW-YunJheNeural",
        "rate": "-5%",
        "tac_title": "COMMAND HQ // COFFEE PROTOCOL",
        "tac_lines": [
            "[ACTION: SCREENSHOT DROP] -> samples/drop_target.png",
            "[SYSTEM: WATCHDOG ARMED & LISTENING]",
            "[COMMANDER STATUS: BREWING COFFEE ☕]"
        ]
    },
    {
        "scene_id": 2,
        "speaker": "Bob",
        "title": "🛠️ 外部特戰傭兵 Bob // VISION REVERSE",
        "role_badge": "🛠️ EXT-MERCENARY // BOB // VISION REVERSE",
        "color": (251, 146, 60),  # 警戒橘
        "text": "Got it boss! Layout extracted, CSS variables ready! This is insane!",
        "avatar": "avatar_bob.png",
        "voice": "en-US-ChristopherNeural",
        "rate": "+10%",
        "tac_title": "DMZ SANDBOX // BOB WORKING OVERTIME",
        "tac_lines": [
            "[AST PARSING: GEOMETRY & TYPOGRAPHY EXTRACTION]",
            "[CSS GENERATED: font-weights, line-heights, hanging-indent]",
            "[CORE INTEGRITY: 0 TOKEN LEAKAGE | ISOLATED]"
        ]
    },
    {
        "scene_id": 3,
        "speaker": "小米",
        "title": "👩💼 執行秘書 小米 // CUSTOMS CLEARANCE",
        "role_badge": "👩💼 SECRETARIAT // XIAOMI // CUSTOMS",
        "color": (56, 189, 248),  # 科技青
        "text": "報告統帥！草案通過海關安檢，純黑已校準為石墨灰，放行！",
        "avatar": "avatar_xiaomi.png",
        "voice": "zh-TW-HsiaoChenNeural",
        "rate": "+15%",
        "tac_title": "CUSTOMS GATEWAY // SECURITY CLEARANCE",
        "tac_lines": [
            "[SCAN: CWE-1236 FORMULA INJECTION DEFENSE -> PASS]",
            "[STYLE CHECK: Pure black replaced with graphite #2D3748]",
            "[GATEWAY STATUS: PASS_L1_SECURITY CERTIFIED]"
        ]
    },
    {
        "scene_id": 4,
        "speaker": "戰情官",
        "title": "📊 第二辦公室 戰情官 // CHAOS VERIFIER",
        "role_badge": "📊 OFFICE 2 // WAR ROOM // VERIFIER",
        "color": (52, 211, 153),  # 翡翠綠
        "text": "二辦沙盒渲染完成！二十五項極限驗收大滿貫，全數綠燈！",
        "avatar": "avatar_office2.png",
        "voice": "zh-TW-HsiaoYuNeural",
        "rate": "+5%",
        "tac_title": "WAR ROOM 8765 // SECOND OFFICE VERIFIER",
        "tac_lines": [
            "[HEADLESS RENDER: A4 Sheet Dry-Run -> 100% OK]",
            "[CHAOS STRESS: 25/25 Extreme Acceptance Tests Passed]",
            "[WAR ROOM MATRIX: 100% GREEN GRAND SLAM]"
        ]
    },
    {
        "scene_id": 5,
        "speaker": "Jack 哥",
        "title": "👑 總指揮官 Jack 哥 // SUPREME COMMANDER",
        "role_badge": "👑 COMMAND HQ // SOVEREIGN SEAL",
        "color": (245, 158, 11),  # 金黃色
        "text": "落款完成。收工，備份回 G 槽。",
        "avatar": "avatar_jack.png",
        "voice": "zh-TW-YunJheNeural",
        "rate": "-5%",
        "tac_title": "SOVEREIGN SEAL // COMMANDER JACK SIGN-OFF",
        "tac_lines": [
            "[DIGITAL FINGERPRINT: PHANTOM-GRID-JACK-SOVEREIGN-SEAL-2026]",
            "[FINAL ACTION: Theme_Grid_Certified Approved]",
            "[VAULT ROUTE: Direct sync to G-Drive Truth]"
        ]
    },
    {
        "scene_id": 6,
        "speaker": "小米",
        "title": "👩💼 執行秘書 小米 // CUSTOMS CLEARANCE",
        "role_badge": "👩💼 SECRETARIAT // MISSION ACCOMPLISHED",
        "color": (56, 189, 248),  # 科技青
        "text": "收到！一鍵安裝包百分之百同步，指揮所全體休眠！",
        "avatar": "avatar_xiaomi.png",
        "voice": "zh-TW-HsiaoChenNeural",
        "rate": "+15%",
        "tac_title": "FULL SYSTEM // 100% IN-SYNC & SLEEP",
        "tac_lines": [
            "[INSTALLER TEMPLATE: SHA256 Match Verified]",
            "[DISASTER RECOVERY: 5-Minute Instant Resurrection Armed]",
            "[COMMAND HQ: All Agents Sleep Mode | Ready for Next War]"
        ]
    },
]


def find_avatar_image(avatar_filename: str) -> Image.Image:
    """從戰鬥目錄或真身目錄尋找頭像，找不到則動態合成科幻頭像"""
    candidates = [
        LOCAL_AVATAR_DIR / avatar_filename,
        C_AVATARS / avatar_filename,
        G_AVATARS / avatar_filename,
    ]
    for c in candidates:
        if c.exists():
            try:
                return Image.open(c).convert("RGBA")
            except Exception:
                pass

    # 若不存在，合成科技頭像
    fallback = Image.new("RGBA", (360, 360), color=(15, 23, 42, 255))
    draw = ImageDraw.Draw(fallback)
    draw.rectangle([10, 10, 350, 350], outline=(56, 189, 248), width=4)
    draw.text((30, 160), "PHANTOM", fill=(255, 255, 255))
    return fallback


def get_audio_duration(audio_path: Path) -> float:
    """利用 ffprobe 獲取音訊精確秒數"""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        return max(1.5, float(res.stdout.strip()) + 0.3)  # 保留 0.3 秒停頓餘裕
    except Exception:
        return 3.5


def render_scene_frame(scene: dict, output_png: Path):
    """使用 Pillow 繪製 1080P 電影級 HUD 科幻通訊畫面"""
    width, height = 1920, 1080
    img = Image.new("RGB", (width, height), color=(11, 15, 25))
    draw = ImageDraw.Draw(img)

    # 字型加載
    font_bold = ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc", 36)
    font_main = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 32)
    font_hud = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 22)
    font_hud_title = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 28)

    # 1. 頂部科技 HUD 條
    draw.rectangle([60, 30, 1860, 85], fill=(15, 23, 42), outline=(30, 41, 59), width=2)
    draw.text((90, 44), "PHANTOM GRID 2026 // BASE COMM-LINK HUD [TAC-NET 01]", fill=(56, 189, 248), font=font_hud)
    draw.text((1540, 44), "STATUS: 100% OPERATIONAL", fill=(52, 211, 153), font=font_hud)

    # 2. 左側：發言者 HUD 角色立繪卡
    card_color = scene["color"]
    draw.rectangle([80, 115, 520, 715], fill=(15, 23, 42), outline=card_color, width=4)
    draw.rectangle([90, 125, 510, 705], fill=(20, 29, 48), outline=(card_color[0]//2, card_color[1]//2, card_color[2]//2), width=1)

    # 角色立繪貼入
    avatar_img = find_avatar_image(scene["avatar"]).resize((380, 380))
    img.paste(avatar_img, (110, 150))

    # 角色代號與職級
    draw.rectangle([110, 560, 490, 680], fill=(15, 23, 42), outline=(30, 41, 59), width=2)
    draw.text((125, 575), scene["speaker"], fill=(255, 255, 255), font=font_bold)
    draw.text((125, 625), scene["role_badge"], fill=card_color, font=font_hud)

    # 3. 右側：戰情實況展台 (Tactical Situation Monitor)
    draw.rectangle([550, 115, 1840, 715], fill=(15, 23, 42), outline=(30, 41, 59), width=2)
    draw.rectangle([550, 115, 1840, 175], fill=(24, 34, 53))
    draw.text((580, 130), f"⚡ TACTICAL DISPLAY // {scene['tac_title']}", fill=(56, 189, 248), font=font_hud_title)

    # 戰情終端線條
    y_offset = 220
    for line in scene["tac_lines"]:
        draw.text((590, y_offset), f"▶  {line}", fill=(203, 213, 225), font=font_main)
        y_offset += 70

    # 科技邊界點綴裝飾
    draw.line([590, 520, 1800, 520], fill=(30, 41, 59), width=2)
    draw.text((590, 545), "DATA PROTOCOL: ISO 26262 ASIL-D STATE PERSISTENCE", fill=(100, 116, 139), font=font_hud)
    draw.text((590, 585), "AUDIT TRAIL: SHA256 IMMUTABLE LEDGER REGISTERED", fill=(100, 116, 139), font=font_hud)
    draw.text((590, 625), "ZERO-DESKTOP POLLUTION: 100% VAULT ENFORCED", fill=(52, 211, 153), font=font_hud)

    # 4. 底部：廣播級雙行字幕通訊框
    draw.rectangle([80, 750, 1840, 1020], fill=(15, 23, 42), outline=card_color, width=3)
    # 發言者標籤
    draw.rectangle([110, 775, 480, 825], fill=(24, 34, 53), outline=card_color, width=2)
    draw.text((125, 782), f"【通訊】{scene['speaker']}", fill=card_color, font=font_hud)

    # 字幕主文案 (白色 36pt 粗體)
    draw.text((115, 850), scene["text"], fill=(255, 255, 255), font=font_bold)
    # 底部微型科技戳記
    draw.text((115, 945), f"TAC-NET COMM // {scene['title']} // TIME: 2026-10-01", fill=(148, 163, 184), font=font_hud)

    img.save(output_png)


async def synthesize_all_voices(temp_dir: Path):
    """批次生成全體角色語音，並備份至 03_Voice_Masters"""
    print("🎙️ [語音母帶錄製] 正在為每位角色生成獨立神經網路語音...")
    for scene in TIMELINE_SCENES:
        v_name = f"voice_{scene['scene_id']}_{scene['speaker'].replace(' ', '_')}.mp3"
        v_path = temp_dir / v_name
        comm = edge_tts.Communicate(scene["text"], scene["voice"], rate=scene["rate"])
        await comm.save(str(v_path))
        print(f"  • Scene {scene['scene_id']} [{scene['speaker']}] 已錄製: {v_path.name}")

        # 備份母帶至 G 槽與 C 槽 Voice_Masters
        shutil.copy2(v_path, G_VOICES / v_name)
        shutil.copy2(v_path, C_VOICES / v_name)


def assemble_movie():
    """組裝 6 大分鏡影片並無損拼接為完整 1080P 電影"""
    temp_dir = Path(tempfile.gettempdir()) / "phantom_movie_build"
    temp_dir.mkdir(parents=True, exist_ok=True)

    # 1. 導出分鏡文字稿至 01_Scripts_Teleprompter
    script_data = {
        "title": "PHANTOM GRID 基地日常樂趣短片：一人成軍的極致偷懶指南",
        "created_at": "2026-10-01",
        "format": "1080P 30FPS Multi-Agent Movie",
        "scenes": TIMELINE_SCENES
    }
    with open(G_SCRIPTS / "phantom_daily_fun_script.json", "w", encoding="utf-8") as f:
        json.dump(script_data, f, ensure_ascii=False, indent=2)
    shutil.copy2(G_SCRIPTS / "phantom_daily_fun_script.json", C_SCRIPTS / "phantom_daily_fun_script.json")
    print(f"📝 [提詞稿入庫] 分鏡劇本已固化至 01_Scripts_Teleprompter")

    # 2. 錄製各角色音訊
    asyncio.run(synthesize_all_voices(temp_dir))

    # 3. 逐段繪製畫面並合成 Scene MP4
    scene_clips = []
    print("\n🎞️ [分鏡影像壓制] 正在逐段壓制電影級 HUD 視訊...")

    for scene in TIMELINE_SCENES:
        s_id = scene["scene_id"]
        v_name = f"voice_{s_id}_{scene['speaker'].replace(' ', '_')}.mp3"
        v_path = temp_dir / v_name
        slide_path = temp_dir / f"slide_{s_id}.png"
        clip_path = temp_dir / f"clip_{s_id}.mp4"

        # 繪製該場景專屬 1080P HUD 畫面
        render_scene_frame(scene, slide_path)

        # 獲取音訊時間長度
        duration = get_audio_duration(v_path)

        # 壓制單一分鏡
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-t", str(duration),
            "-i", str(slide_path),
            "-i", str(v_path),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            str(clip_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if res.returncode != 0:
            raise RuntimeError(f"Scene {s_id} 壓制失敗: {res.stderr[-400:]}")

        scene_clips.append(clip_path)
        print(f"  • Scene {s_id} 合成完成 ({duration:.1f}s): {clip_path.name}")

    # 4. 無損拼接為完整電影 (Concat Demuxer)
    concat_txt = temp_dir / "concat_list.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for clip in scene_clips:
            clean_path = str(clip).replace("\\", "/")
            f.write(f"file '{clean_path}'\n")

    master_g_video = G_RENDERS / "phantom_grid_full_movie.mp4"
    public_g_video = G_VIDEOS_1080P / "phantom_grid_full_movie.mp4"

    master_c_video = C_RENDERS / "phantom_grid_full_movie.mp4"
    public_c_video = C_VIDEOS_1080P / "phantom_grid_full_movie.mp4"

    print("\n🎬 [電影大合體] 正在拼接多角色對白全片...")
    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_txt),
        "-c", "copy",
        str(master_g_video)
    ]
    res_concat = subprocess.run(concat_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res_concat.returncode != 0:
        raise RuntimeError(f"影片拼接失敗: {res_concat.stderr[-400:]}")

    # 5. 雙軌四向金庫固化 (真身優先 ➔ 戰鬥鏡像 ➔ 1080P 成品庫)
    shutil.copy2(master_g_video, public_g_video)
    shutil.copy2(master_g_video, master_c_video)
    shutil.copy2(master_g_video, public_c_video)

    # 獲取最終大小與長度
    total_mb = master_g_video.stat().st_size / (1024 * 1024)
    print("=" * 80)
    print(f"🎉 【PHANTOM GRID 基地日常樂趣短片】電影級多角色大片 100% 完工！")
    print(f"📁 影視真身母帶: {master_g_video} ({total_mb:.2f} MB)")
    print(f"📁 交付展示成品: {public_g_video}")
    print(f"⚡ 高速戰鬥鏡像: {master_c_video}")
    print(f"🛡️ 嚴格恪守: Zero-Desktop Pollution (Windows 桌面 100% 零殘留)")
    print("=" * 80)

    # 清理暫存
    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass

    return master_g_video


if __name__ == "__main__":
    assemble_movie()
