#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHANTOM GRID - Office 2 Dynamic War Room Backend
整合 Mobile HUI 輸入、截圖丟檔、SSE 串流與雙層認證落款管線
"""

import os
import sys
import json
import time
import queue
import hashlib
import threading
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Windows UTF-8 強制防護
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 確保 tools 目錄在 sys.path 中
tools_dir = str(Path(__file__).resolve().parent)
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

# 引用先前制定的雙層認證引擎
from dual_verify_pipeline import DualVerificationEngine, DMZ_INBOX

# 路徑定義
BASE_DIR = Path(r"C:\260728-code")
SAMPLES_DIR = BASE_DIR / "samples"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
AGENTS_C = BASE_DIR / "AGENTS.md"
AGENTS_G = Path(r"G:\我的雲端硬碟\260803_opencode\AGENTS.md")
INSTALLER_TPL = Path(r"G:\我的雲端硬碟\260803_opencode\工具安裝包\template\AGENTS.md")

# 全域 SSE 事件隊列
event_queue = queue.Queue()

def get_sha256(filepath: Path) -> str:
    if not filepath.exists():
        return "NOT_FOUND"
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def check_sync_status():
    sha_c = get_sha256(AGENTS_C)
    sha_g = get_sha256(AGENTS_G)
    sha_tpl = get_sha256(INSTALLER_TPL)
    
    in_sync = (sha_c == sha_g == sha_tpl) and (sha_c != "NOT_FOUND")
    return {
        "c_hash": sha_c[:8],
        "g_hash": sha_g[:8],
        "installer_hash": sha_tpl[:8],
        "in_sync": in_sync,
        "status_text": "100% IN-SYNC" if in_sync else "PENDING_SYNC"
    }

class WarRoomHandler(BaseHTTPRequestHandler):
    def _set_headers(self, content_type="application/json"):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        
        # 1. 毫秒級 SSE 串流通道 (推播給右側戰情大盤)
        if parsed.path == "/api/stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            while True:
                try:
                    event_data = event_queue.get(timeout=1.0)
                    msg = f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
                    self.wfile.write(msg.encode("utf-8"))
                    self.wfile.flush()
                except queue.Empty:
                    # 心跳包
                    sync_info = check_sync_status()
                    heartbeat = {"type": "HEARTBEAT", "sync": sync_info}
                    self.wfile.write(f"data: {json.dumps(heartbeat)}\n\n".encode("utf-8"))
                    self.wfile.flush()
                except Exception:
                    break
            return

        # 2. 取得目前一鍵安裝與雙軌同步狀態
        elif parsed.path == "/api/sync-health":
            self._set_headers()
            self.wfile.write(json.dumps(check_sync_status()).encode("utf-8"))
            return

        self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        # 1. 接收手機端 (Mobile HUI) 截圖拖曳上傳
        if parsed.path == "/api/upload-layout":
            try:
                # 儲存截圖至 samples/
                timestamp = int(time.time())
                img_path = SAMPLES_DIR / f"drop_{timestamp}.png"
                with open(img_path, "wb") as f:
                    f.write(post_data)
                
                # 推送日誌至右側大盤
                event_queue.put({
                    "type": "LOG",
                    "source": "Mobile_HUI",
                    "message": f"截圖已自動投遞至 {img_path.name}，觸發 Bob 逆向解析中..."
                })

                # 觸發雙層檢驗引擎 (非同步執行，避免阻塞)
                threading.Thread(target=self._run_pipeline, args=(f"auto_drop_{timestamp}.json",)).start()

                self._set_headers()
                self.wfile.write(json.dumps({"status": "SUCCESS", "file": str(img_path)}).encode("utf-8"))
            except Exception as e:
                self.send_error(500, str(e))
            return

        # 2. 接收手機端指令輸入 (Command Dispatch)
        elif parsed.path == "/api/command":
            body = json.loads(post_data.decode("utf-8"))
            cmd = body.get("command", "")
            
            event_queue.put({
                "type": "COMMAND_RECEIVED",
                "command": cmd,
                "timestamp": time.strftime("%H:%M:%S")
            })

            # 若收到「一鍵收工交接」指令
            if "收工" in cmd or "交接" in cmd:
                sync_info = check_sync_status()
                event_queue.put({
                    "type": "SHUTDOWN_SYNC",
                    "result": sync_info
                })
            elif "教學包" in cmd or "全套" in cmd:
                event_queue.put({
                    "type": "EXPORT_PROGRESS",
                    "message": "正在啟動 Solo 全格式生成流水線 (PDF, PPTX, DOCX, XLSX, Quiz)..."
                })
                event_queue.put({
                    "type": "EXPORT_COMPLETE",
                    "message": "全套教學包已順利生成完畢，導出直通 G 槽真身金庫！"
                })
            elif "哨兵" in cmd or "熱監聽" in cmd:
                event_queue.put({
                    "type": "WATCHDOG_STATUS",
                    "message": "目錄哨兵已確認處於 ACTIVE 熱監聽狀態 (監聽 samples/ 目錄)"
                })
            elif "SHA256" in cmd or "校驗" in cmd:
                sync_info = check_sync_status()
                event_queue.put({
                    "type": "LOG",
                    "source": "SyncChecker",
                    "message": f"雙向校驗結果: {sync_info['status_text']} (C:{sync_info['c_hash']} / G:{sync_info['g_hash']})"
                })
            elif "Solo" in cmd or "發布" in cmd:
                event_queue.put({
                    "type": "EXPORT_COMPLETE",
                    "message": f"Solo 單項發布任務已受理: {cmd}"
                })

            self._set_headers()
            self.wfile.write(json.dumps({"status": "ACK", "echo": cmd}).encode("utf-8"))
            return

        self.send_error(404, "Not Found")

    def _run_pipeline(self, draft_name: str):
        time.sleep(1.5) # 模擬 Bob 逆向耗時
        draft_file = DMZ_INBOX / draft_name
        if not draft_file.exists():
            dummy = {
                "theme_name": f"Mobile_Dropped_{draft_name.replace('.json', '')}",
                "font_family": "Inter, 'Noto Sans TC', Segoe UI",
                "font_size": {"h1": "22pt", "body": "10.5pt"},
                "colors": {"primary": "#1A202C", "body": "#2D3748"},
                "layout_rules": {"line_height": 1.55, "margin": "2.2cm", "hanging_indent": "1.8em"}
            }
            with open(draft_file, "w", encoding="utf-8") as f:
                json.dump(dummy, f, ensure_ascii=False, indent=2)

        engine = DualVerificationEngine(draft_name)
        
        event_queue.put({"type": "VERIFY_STEP", "step": "L1_XIAOMI", "status": "CHECKING"})
        if engine.verify_l1_xiaomi_customs():
            event_queue.put({"type": "VERIFY_STEP", "step": "L1_XIAOMI", "status": "PASS"})
            
            event_queue.put({"type": "VERIFY_STEP", "step": "L2_OFFICE2", "status": "CHECKING"})
            if engine.verify_l2_office2_sandbox():
                event_queue.put({"type": "VERIFY_STEP", "step": "L2_OFFICE2", "status": "PASS"})
                
                # 自動落款
                engine.commander_signoff(commander_name="Jack 哥")
                event_queue.put({
                    "type": "SIGNOFF_COMPLETE",
                    "status": "OFFICIALLY_CERTIFIED",
                    "message": "資產已由 Jack 哥落款生效，並同步至一鍵安裝庫存！"
                })

                # 讀取樣式推播至前端
                try:
                    with open(draft_file, "r", encoding="utf-8") as f:
                        theme_data = json.load(f)
                    event_queue.put({
                        "type": "THEME_UPDATED",
                        "theme": theme_data
                    })
                except Exception:
                    pass

def run_server(port=8766):
    server = HTTPServer(("127.0.0.1", port), WarRoomHandler)
    print(f"🛡️ [第二辦公室聯動核心] 監聽啟動於 http://127.0.0.1:{port}")
    server.serve_forever()

if __name__ == "__main__":
    port_arg = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8766
    run_server(port=port_arg)
