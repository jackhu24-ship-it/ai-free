# -*- coding: utf-8 -*-
"""
output_distributor.py
Five-Agent AI OS - 全自動產出成品分發與總庫索引引擎
支援 9+1 旗艦專區自動歸檔、標準時間戳命名、桌面捷徑與動態 HTML 視覺索引
"""

import os
import sys
import shutil
import glob
import json
import datetime
from pathlib import Path

# 強制 Windows 繁中 UTF-8
if sys.platform.startswith("win"):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

OUTPUT_ROOT = r"G:\我的雲端硬碟\AI產出成品總庫"

CATEGORY_MAPPING = {
    "launchers": {
        "dir": "00_🚀_一鍵工具站",
        "name": "一鍵工具站",
        "subdirs": {
            "gui": "桌面GUI與示波器",
            "sla": "SLA監控與守護進程"
        }
    },
    "education": {
        "dir": "01_🎓_教學備課專區",
        "name": "教學備課專區",
        "subdirs": {
            "lesson": "課堂教案與講義",
            "feedback": "課堂互動與回饋"
        }
    },
    "question_bank": {
        "dir": "02_📚_題庫專區",
        "name": "題庫專區",
        "subdirs": {
            "exams": "測驗考卷與解答",
            "boss_questions": "魔王題與素養題庫",
            "diagnosis": "AI批改與學力診斷"
        }
    },
    "presentations": {
        "dir": "03_📊_簡報專案專區",
        "name": "簡報專案專區",
        "subdirs": {
            "templates": "00_標準母片與設計規格",
            "pptx": "PPTX簡報作品",
            "html": "HTML互動簡報",
            "speech": "講稿與大綱摘要"
        }
    },
    "finance": {
        "dir": "04_📈_財經季報專區",
        "name": "財經季報專區",
        "subdirs": {
            "etf": "基金與ETF分析",
            "quarterly": "投資季報彙編",
            "charts": "財務統計圖表"
        }
    },
    "forms": {
        "dir": "05_📝_各式表單專區",
        "name": "各式表單專區",
        "subdirs": {
            "templates": "00_標準表單空白模板與規範",
            "sign_forms": "簽呈與公文表單",
            "tgb": "TGB專案表單與文件",
            "admin": "行政與申請表單",
            "surveys": "調查問卷與統計",
            "checklists": "檢核清單與Checklist"
        }
    },
    "automotive": {
        "dir": "06_🚗_車電韌體專區",
        "name": "車電韌體專區",
        "subdirs": {
            "can": "CAN報文與示波器數據",
            "mcu": "MCU孿生與韌體HEX"
        }
    },
    "cad": {
        "dir": "07_📐_CAD工程圖紙",
        "name": "CAD工程圖紙",
        "subdirs": {
            "templates": "00_標準圖框與繪圖規範",
            "harness": "01_車輛主電線束圖",
            "schematics": "02_電氣電路原理圖",
            "parts": "03_機構零件與鈑件圖"
        }
    },
    "manuals": {
        "dir": "08_📄_手冊文檔專區",
        "name": "手冊文檔專區",
        "subdirs": {
            "system_manuals": "系統操作手冊",
            "specs_sop": "技術規格與SOP"
        }
    },
    "archive": {
        "dir": "99_🗄️_歷史封存區",
        "name": "歷史封存區",
        "subdirs": {
            "current_quarter": datetime.datetime.now().strftime("%Y_Q") + str((datetime.datetime.now().month - 1) // 3 + 1)
        }
    }
}

def init_output_structure(base_dir=OUTPUT_ROOT):
    """初始化並建立所有 9+1 專區實體資料夾"""
    os.makedirs(base_dir, exist_ok=True)
    created_count = 0
    for cat_key, cat_val in CATEGORY_MAPPING.items():
        cat_path = os.path.join(base_dir, cat_val["dir"])
        os.makedirs(cat_path, exist_ok=True)
        for sub_key, sub_val in cat_val["subdirs"].items():
            sub_path = os.path.join(cat_path, sub_val)
            os.makedirs(sub_path, exist_ok=True)
            created_count += 1
    return created_count

def publish_output(source_path, category_key, subcategory_key=None, custom_name=None, date_prefix=True):
    """
    全自動將產出檔案分發至對應專區
    :param source_path: 原檔案絕對路徑
    :param category_key: 專區鍵值 (如 forms, cad, question_bank, finance...)
    :param subcategory_key: 子分類鍵值 (如 tgb, sign_forms, parts, etf...)
    :param custom_name: 自訂目標檔名 (若無則取原始檔名)
    :param date_prefix: 是否自動加上 YYYYMMDD 前綴
    :return: 目標檔案絕對路徑
    """
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"來源檔案不存在: {source_path}")
    
    init_output_structure(OUTPUT_ROOT)
    
    if category_key not in CATEGORY_MAPPING:
        raise ValueError(f"無效的專區分類: {category_key}，可用值: {list(CATEGORY_MAPPING.keys())}")
    
    cat_info = CATEGORY_MAPPING[category_key]
    target_dir = os.path.join(OUTPUT_ROOT, cat_info["dir"])
    
    if subcategory_key and subcategory_key in cat_info["subdirs"]:
        target_dir = os.path.join(target_dir, cat_info["subdirs"][subcategory_key])
    elif subcategory_key is None and cat_info["subdirs"]:
        # 預設取第一個子目錄
        first_sub = list(cat_info["subdirs"].values())[0]
        target_dir = os.path.join(target_dir, first_sub)
    
    os.makedirs(target_dir, exist_ok=True)
    
    src_p = Path(source_path)
    base_name = custom_name if custom_name else src_p.stem
    ext = src_p.suffix
    
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    if date_prefix and not base_name.startswith(today_str):
        final_filename = f"{today_str}_{base_name}{ext}"
    else:
        final_filename = f"{base_name}{ext}"
        
    dest_path = os.path.join(target_dir, final_filename)
    shutil.copy2(source_path, dest_path)
    
    # 產出後自動重新生成目錄總索引
    generate_html_index()
    return dest_path

def generate_html_index(base_dir=OUTPUT_ROOT):
    """掃描總庫內所有檔案並產出漂亮的 HTML 視覺導航總表"""
    all_files = []
    
    for root, dirs, files in os.walk(base_dir):
        # 排除根目錄下的 index 本身與暫存檔
        for f in files:
            if f.startswith("📁_成品目錄總索引") or f.startswith(".") or f.endswith(".tmp"):
                continue
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, base_dir)
            rel_parts = rel_path.split(os.sep)
            
            main_cat = rel_parts[0] if len(rel_parts) > 1 else "根目錄"
            sub_cat = rel_parts[1] if len(rel_parts) > 2 else "-"
            
            try:
                stat = os.stat(full_path)
                mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                size_kb = round(stat.st_size / 1024, 1)
            except Exception:
                mtime = "-"
                size_kb = 0
            
            all_files.append({
                "filename": f,
                "main_cat": main_cat,
                "sub_cat": sub_cat,
                "rel_path": rel_path.replace("\\", "/"),
                "full_path": full_path.replace("\\", "/"),
                "mtime": mtime,
                "size_kb": size_kb
            })
            
    # 按修改時間倒序
    all_files.sort(key=lambda x: x["mtime"], reverse=True)
    
    html_content = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📦 AI 產出成品總庫 - 目錄總索引</title>
    <style>
        :root {{
            --bg-color: #0F172A;
            --card-bg: #1E293B;
            --text-main: #F8FAFC;
            --text-muted: #94A3B8;
            --accent: #38BDF8;
            --accent-green: #4ADE80;
            --accent-purple: #C084FC;
            --border: #334155;
            --hover: #2D3748;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; }}
        body {{ background-color: var(--bg-color); color: var(--text-main); padding: 24px; }}
        header {{ margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; }}
        h1 {{ font-size: 24px; color: var(--accent); display: flex; align-items: center; gap: 10px; }}
        .badge {{ background: #0369A1; color: #E0F2FE; padding: 4px 10px; border-radius: 9999px; font-size: 13px; font-weight: bold; }}
        .stats {{ color: var(--text-muted); font-size: 14px; }}
        .search-bar {{ margin-bottom: 20px; display: flex; gap: 12px; }}
        .search-input {{ flex: 1; padding: 12px 16px; background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; color: #FFF; font-size: 15px; outline: none; }}
        .search-input:focus {{ border-color: var(--accent); box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2); }}
        .table-container {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3); }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 14px; }}
        th {{ background: #182234; padding: 14px 16px; color: var(--accent); font-weight: 600; border-bottom: 1px solid var(--border); }}
        td {{ padding: 12px 16px; border-bottom: 1px solid var(--border); }}
        tr:hover td {{ background: var(--hover); }}
        a.file-link {{ color: var(--text-main); text-decoration: none; font-weight: 500; display: inline-flex; align-items: center; gap: 6px; }}
        a.file-link:hover {{ color: var(--accent); text-decoration: underline; }}
        .tag {{ display: inline-block; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 500; }}
        .tag-cat {{ background: #1E3A8A; color: #93C5FD; }}
        .tag-sub {{ background: #374151; color: #D1D5DB; }}
        .time {{ color: var(--text-muted); font-size: 13px; font-family: monospace; }}
        .size {{ color: var(--text-muted); font-size: 13px; text-align: right; }}
    </style>
</head>
<body>
    <header>
        <div>
            <h1>📦 AI 產出成品總庫 <span class="badge">9+1 旗艦分區</span></h1>
            <p style="margin-top: 6px; color: var(--text-muted); font-size: 13px;">Five-Agent AI OS 自動分發歸檔系統 ✕ 跨電腦 Google Drive 雲端同步</p>
        </div>
        <div class="stats">
            最後更新：<strong>{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</strong> ｜ 總收錄檔案：<strong>{len(all_files)}</strong> 個
        </div>
    </header>

    <div class="search-bar">
        <input type="text" id="searchInput" class="search-input" placeholder="🔍 輸入關鍵字搜尋檔案名稱、專案、格式 (如: dxf, docx, pdf, 螺帽, 簽呈, TGB, 考卷)..." onkeyup="filterTable()">
    </div>

    <div class="table-container">
        <table id="filesTable">
            <thead>
                <tr>
                    <th style="width: 40%;">檔案名稱 (點擊開啟)</th>
                    <th style="width: 22%;">所屬專區</th>
                    <th style="width: 18%;">子分類</th>
                    <th style="width: 12%;">更新時間</th>
                    <th style="width: 8%; text-align: right;">大小</th>
                </tr>
            </thead>
            <tbody>
"""
    if not all_files:
        html_content += """
                <tr>
                    <td colspan="5" style="text-align: center; padding: 40px; color: var(--text-muted);">
                        目前總庫尚無檔案，產出後將全自動在此列出！
                    </td>
                </tr>
"""
    else:
        for item in all_files:
            html_content += f"""
                <tr>
                    <td>
                        <a href="{item['rel_path']}" class="file-link" target="_blank">
                            📄 {item['filename']}
                        </a>
                    </td>
                    <td><span class="tag tag-cat">{item['main_cat']}</span></td>
                    <td><span class="tag tag-sub">{item['sub_cat']}</span></td>
                    <td class="time">{item['mtime']}</td>
                    <td class="size">{item['size_kb']} KB</td>
                </tr>
"""
            
    html_content += """
            </tbody>
        </table>
    </div>

    <script>
        function filterTable() {
            var input = document.getElementById("searchInput");
            var filter = input.value.toLowerCase();
            var table = document.getElementById("filesTable");
            var tr = table.getElementsByTagName("tr");

            for (var i = 1; i < tr.length; i++) {
                var rowText = tr[i].textContent || tr[i].innerText;
                if (rowText.toLowerCase().indexOf(filter) > -1) {
                    tr[i].style.display = "";
                } else {
                    tr[i].style.display = "none";
                }
            }
        }
    </script>
<div style="background:#1E293B;color:#F8FAFC;padding:12px;margin-top:24px;border-radius:8px;text-align:center">
    <p>為持續優化後續版本，歡迎您填寫以下簡短滿意度問卷：<br>
    <a href="https://docs.google.com/forms/d/e/1FAIpQLScZ___pseudo?usp=sharing" target="_blank" style="color:#38BDF8;">點此進入問卷</a></p>
</div>
</body>
</html>
"""
    index_path = os.path.join(base_dir, "📁_成品目錄總索引.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    return index_path

def create_desktop_shortcut():
    """在 Windows 桌面建立直達總庫的捷徑"""
    results = []
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        
        desktop_targets = [
            os.path.join(os.environ.get("USERPROFILE", ""), "OneDrive", "桌面"),
            os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
        ]
        
        for d in desktop_targets:
            if os.path.exists(d):
                shortcut_path = os.path.join(d, "AI產出成品快速通道.lnk")
                shortcut = shell.CreateShortcut(shortcut_path)
                shortcut.TargetPath = OUTPUT_ROOT
                shortcut.WorkingDirectory = OUTPUT_ROOT
                shortcut.Description = "直達 AI 產出成品總庫 (9+1 旗艦分區)"
                shortcut.IconLocation = "shell32.dll,4"
                shortcut.Save()
                results.append(shortcut_path)
        return results
    except Exception as e:
        return [f"Desktop shortcut error: {e}"]

def sync_existing_deliverables():
    """將現有各模組的代表性成品同步歸檔至總庫"""
    workspaces = [
        r"G:\我的雲端硬碟\AI_master_workspace\three_memory",
        r"G:\我的雲端硬碟\260803_opencode"
    ]
    
    # 1. 手冊與文檔
    manual_files = [
        r"G:\我的雲端硬碟\AI_master_workspace\three_memory\DOCS\數位模擬與儀表系統全功能操作備查手冊_全8頁.pdf",
        r"G:\我的雲端硬碟\260803_opencode\ollama-operation-manual.md",
        r"G:\我的雲端硬碟\260803_opencode\ai-models-guide.md"
    ]
    for mf in manual_files:
        if os.path.exists(mf):
            publish_output(mf, "manuals", "system_manuals", date_prefix=True)
            
    # 2. CAD 圖紙
    cad_files = [
        r"G:\我的雲端硬碟\AI_master_workspace\three_memory\DATA\sample_wiring_harness.dxf",
        r"G:\我的雲端硬碟\AI_master_workspace\three_memory\DATA\fault_diagnostic_harness.dxf",
        r"G:\我的雲端硬碟\AI_master_workspace\three_memory\DATA\live_bench_annotated_harness.dxf"
    ]
    for cf in cad_files:
        if os.path.exists(cf):
            publish_output(cf, "cad", "harness", date_prefix=True)
            
    # 3. 簡報作品
    ppt_files = glob.glob(r"G:\我的雲端硬碟\260803_opencode\簡報作品\*.pptx") + glob.glob(r"G:\我的雲端硬碟\260803_opencode\簡報作品\*.pdf")
    for pf in ppt_files:
        publish_output(pf, "presentations", "pptx", date_prefix=True)
        
    # 4. 一鍵工具批次檔
    launcher_files = [
        (r"G:\我的雲端硬碟\AI_master_workspace\three_memory\launch_mcu_dashboard.bat", "launchers", "gui"),
        (r"G:\我的雲端硬碟\AI_master_workspace\three_memory\launch_dynamic_dashboard.bat", "launchers", "gui"),
        (r"G:\我的雲端硬碟\AI_master_workspace\three_memory\start_endpoint_monitor.bat", "launchers", "sla")
    ]
    for lf, cat, subcat in launcher_files:
        if os.path.exists(lf):
            publish_output(lf, cat, subcat, date_prefix=False)

if __name__ == "__main__":
    count = init_output_structure()
    print(f"✅ 成功初始化 AI 產出成品總庫結構（建立 {count} 個子分類資料夾）")
    sync_existing_deliverables()
    print("✅ 現有成果已全量分發同步至 9+1 專區！")
    idx = generate_html_index()
    print(f"✅ 成功生成目錄總索引: {idx}")
    lnk = create_desktop_shortcut()
    print(f"✅ 桌面捷徑狀態: {lnk}")
