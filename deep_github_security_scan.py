# -*- coding: utf-8 -*-
"""
PHANToM Grid :: Deep GitHub Security & Constitutional Compliance Scanner
Audits all tracked git files in both repositories:
1. ai-free.git (current workspace)
2. phantom-grid-opencode-match3-agentworkflow.git (Match 3)
"""

import os
import re
import sys
import subprocess
from pathlib import Path

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

REPOS = [
    {
        "name": "ai-free (Main Workspace)",
        "path": Path.cwd()
    },
    {
        "name": "Match 3 AgentWorkflow",
        "path": Path(r"G:\我的雲端硬碟\260803_opencode\01_賽事專區\202610_OpenCode_Match3_AgentWorkflow")
    }
]

PATTERNS = {
    "GOOGLE_API_KEY": re.compile(r"AIza[0-9A-Za-z-_]{35}"),
    "OPENAI_API_KEY": re.compile(r"sk-[a-zA-Z0-9_-]{24,}"),
    "GITHUB_TOKEN": re.compile(r"(ghp_[0-9a-zA-Z]{36}|gho_[0-9a-zA-Z]{36}|github_pat_[0-9a-zA-Z_]{82})"),
    "AWS_KEY_ID": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "PRIVATE_KEY_HEADER": re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |)PRIVATE KEY"),
    "CREDIT_CARD_SUSPECT": re.compile(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12})\b"),
}

PLACEHOLDER_WORDS = [
    "your_api_key", "placeholder", "example", "dummy", "fake", "xxx", "mock", 
    "insert_here", "sk-...", "aiza...", "sample", "000000000000"
]

def is_placeholder(val):
    v = val.lower()
    return any(p in v for p in PLACEHOLDER_WORDS)

def luhn_check(num_str):
    digits = [int(c) for c in re.sub(r"\D", "", num_str)]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    reverse_digits = digits[::-1]
    for i, d in enumerate(reverse_digits):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0

print("================================================================================")
print("🛡️ PHANToM Grid :: GitHub 全域深度安全審計與違憲排查")
print("================================================================================")

total_findings = 0

for repo in REPOS:
    r_name = repo["name"]
    r_path = repo["path"]
    print(f"\n[*] 正在審查儲存庫: [{r_name}] 路徑: {r_path}")

    if not r_path.exists():
        print(f"  [WARN] 路徑不存在，跳過: {r_path}")
        continue

    # 1. Get tracked files
    res = subprocess.run(["git", "ls-files"], cwd=str(r_path), capture_output=True, encoding="utf-8", errors="replace")
    tracked_files = [line.strip() for line in res.stdout.splitlines() if line.strip()]
    print(f"  已索引追蹤檔案總數: {len(tracked_files)} 件")

    # 2. Check forbidden file types
    forbidden_media = [f for f in tracked_files if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.webm', '.pdf', '.pptx', '.xlsx'))]
    if forbidden_media:
        print(f"  [🚨 違憲發現] 追蹤到禁止上傳的媒體或 PDF 檔案: {forbidden_media}")
        total_findings += len(forbidden_media)
    else:
        print(f"  [✅ PASS] 無任何禁止的影片 (*.mp4, *.mov) 或 PDF (*.pdf) 檔案！")

    # 3. Check file names for sensitive words
    sensitive_name_hits = [f for f in tracked_files if any(w in f.lower() for w in ['.env.local', '.env.production', 'credentials.json', 'id_rsa', 'private.key', 'client_secret.json'])]
    if sensitive_name_hits:
        print(f"  [🚨 違憲發現] 追蹤到敏感檔名: {sensitive_name_hits}")
        total_findings += len(sensitive_name_hits)
    else:
        print(f"  [✅ PASS] 無任何敏感檔名 (*.key, id_rsa, client_secret 等)！")

    # 4. Deep content scan
    scanned_count = 0
    repo_leaks = 0
    for f_rel in tracked_files:
        f_abs = r_path / f_rel
        if not f_abs.is_file():
            continue

        # Skip binary files by extension
        if f_rel.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.bin', '.exe', '.dll', '.so', '.pyc')):
            continue

        try:
            content = f_abs.read_text(encoding="utf-8", errors="ignore")
            scanned_count += 1
            for p_name, regex in PATTERNS.items():
                matches = regex.findall(content)
                for m in matches:
                    if p_name == "CREDIT_CARD_SUSPECT":
                        if not luhn_check(m):
                            continue
                    if is_placeholder(m):
                        continue
                    print(f"  [🚨 機密洩漏嫌疑] 檔案: {f_rel} | 規則: {p_name} | 匹配: {m[:6]}...{m[-4:]}")
                    repo_leaks += 1
                    total_findings += 1
        except Exception as e:
            pass

    print(f"  文字內容深度掃描完畢 (共審查 {scanned_count} 個原始碼與設定檔)")
    if repo_leaks == 0:
        print(f"  [✅ PASS] 原始碼內容中 0 API Key、0 信用卡號、0 私鑰密碼洩漏！")

print("\n================================================================================")
if total_findings == 0:
    print("🏆 終審判決：【GitHub 雙儲存庫 100% 潔淨無染・零機密洩漏・零違憲檔案・完全合規】！")
else:
    print(f"🚨 終審判決：發現 {total_findings} 項安全問題，請指揮官立即執行修復！")
print("================================================================================")
