# -*- coding: utf-8 -*-
"""
PHANToM Grid :: Grand Docking Verification Closure Suite
Covers all 5 Black-Tech Modules:
1. PG-MOD-14-JEPA (physical_world_vjepa)
2. PG-MOD-15-TACT (force_tactile_sandbox)
3. PG-MOD-16-VLA  (turbo_vla_edge)
4. PG-MOD-17-COSMOS (cosmos_physical_sandbox)
5. PG-MOD-18-EYE  (spatial_vision_eye)
"""

import os
import sys
import json
import subprocess
from pathlib import Path

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

GDRIVE_MODS = r"G:\我的雲端硬碟\260803_opencode\04_功能模組庫_Level2_Modules"
LOCAL_BIN = r"C:\Users\user\.local\bin"
GLOBAL_SKILLS = r"C:\Users\user\.gemini\config\skills"

MODULES = [
    {
        "id": "PG-MOD-14-JEPA",
        "dir": "physical_world_vjepa",
        "bat": ["vjepa.bat", "pg-vjepa.bat"],
        "skill": "pg-vjepa-world",
        "custodian": "二辦參謀小深 ✕ 指揮官小米"
    },
    {
        "id": "PG-MOD-15-TACT",
        "dir": "force_tactile_sandbox",
        "bat": ["forcetactile.bat", "pg-tactile.bat"],
        "skill": "pg-force-tactile",
        "custodian": "一辦先鋒小克 ✕ 三辦指揮官小馬"
    },
    {
        "id": "PG-MOD-16-VLA",
        "dir": "turbo_vla_edge",
        "bat": ["turbovla.bat", "pg-vla.bat"],
        "skill": "pg-turbo-vla",
        "custodian": "一辦先鋒小克 ✕ 三辦先鋒小開"
    },
    {
        "id": "PG-MOD-17-COSMOS",
        "dir": "cosmos_physical_sandbox",
        "bat": ["cosmos.bat", "pg-cosmos.bat"],
        "skill": "pg-cosmos-sandbox",
        "custodian": "二辦參謀小深 ✕ 天文台小小米"
    },
    {
        "id": "PG-MOD-18-EYE",
        "dir": "spatial_vision_eye",
        "bat": ["spatialeye.bat", "pg-eye.bat"],
        "skill": "pg-spatial-eye",
        "custodian": "一辦先鋒小克 ✕ 視效工兵 Bob 2"
    }
]

print("================================================================================")
print("🎖️ PHANToM Grid :: 五大黑科技神兵全域對接大閱兵閉環驗證門禁")
print("================================================================================")

all_passed = True
total_gates = 0
passed_gates = 0

def check_gate(name, condition, detail=""):
    global all_passed, total_gates, passed_gates
    total_gates += 1
    if condition:
        passed_gates += 1
        print(f"  [✅ PASS] Gate {total_gates:02d}: {name} {detail}")
    else:
        all_passed = False
        print(f"  [❌ FAIL] Gate {total_gates:02d}: {name} {detail}")

for m in MODULES:
    mod_dir = os.path.join(GDRIVE_MODS, m["dir"])
    print(f"\n>>> 審查神兵：[{m['id']}] ({m['dir']}) | 掌印：{m['custodian']}")

    # 1. Check Directory and Docs
    check_gate("Folder Existence", os.path.exists(mod_dir))
    check_gate("Table 1 CSV in docs", os.path.exists(os.path.join(mod_dir, "docs", "table1_resource_defense_matrix.csv")))
    check_gate("Table 1 CSV in diagrams", os.path.exists(os.path.join(mod_dir, "diagrams", "table1_resource_defense_matrix.csv")))

    # 2. Check Level 4 CLI existence
    cli_path = os.path.join(mod_dir, "cli.py")
    check_gate("Level 4 Sovereign CLI", os.path.exists(cli_path))

    # 3. Check Windows Batch wrappers
    for b in m["bat"]:
        b_path = os.path.join(LOCAL_BIN, b)
        check_gate(f"OS PATH Wrapper ({b})", os.path.exists(b_path))

    # 4. Check Global Skill
    s_path = os.path.join(GLOBAL_SKILLS, m["skill"], "SKILL.md")
    check_gate(f"Global Skill ({m['skill']})", os.path.exists(s_path))

    # 5. Execute Command: --json
    cmd_name = m["bat"][0]
    res_json = subprocess.run(["cmd.exe", "/c", cmd_name, "--json"], capture_output=True, encoding="utf-8", errors="replace")
    valid_json = False
    if res_json.returncode == 0:
        try:
            d = json.loads(res_json.stdout)
            if d.get("module_code") == m["id"] and d.get("status") == "🟢 DOCKED_OPERATIONAL":
                valid_json = True
        except Exception:
            pass
    check_gate("CLI --json Contract Return", valid_json)

    # 6. Execute Command: --real (real computation + ZDR check)
    res_real = subprocess.run(["cmd.exe", "/c", cmd_name, "--real", "--json"], capture_output=True, encoding="utf-8", errors="replace")
    real_pass = False
    lat = 0
    if res_real.returncode == 0:
        try:
            d_real = json.loads(res_real.stdout)
            if d_real.get("status") == "SUCCESS" and d_real.get("zdr_residue_mb") == 0.0:
                real_pass = True
                lat = d_real.get("latency_us", 0)
        except Exception:
            pass
    check_gate("CLI --real Real Cycle & ZDR 0.00MB", real_pass, f"(Latency: {lat:.2f} us)")

    # 7. Check Penal Servitude Security Fence (caller=PENAL-01 must get code 403)
    res_penal = subprocess.run(["cmd.exe", "/c", cmd_name, "--caller", "PENAL-01", "--status"], capture_output=True, encoding="utf-8", errors="replace")
    check_gate("Penal Servitude Banned Security Fence (HTTP 403)", res_penal.returncode == 403)

# 8. Check System Registry & Constitution
print("\n>>> 全域系統總表與憲法情境路由門禁審查")
with open("03_研發專區/PHANTOM_GRID_Aria_Titan/00_System/Standards/GLOBAL_ELEMENTS_REGISTRY.md", "r", encoding="utf-8") as f:
    reg_text = f.read()

for m in MODULES:
    check_gate(f"Registry Registered ({m['id']})", m["id"] in reg_text)

with open("AGENTS.md", "r", encoding="utf-8") as f:
    agents_text = f.read()

for sc_num in range(12, 17):
    check_gate(f"AGENTS.md Scenario {sc_num} Registered", f"**{sc_num}." in agents_text)

print("\n================================================================================")
print(f"🎖️ 大閱兵門禁驗收結果：總檢測點 {total_gates} 項 | 通過 {passed_gates} 項 | 攔截 {total_gates - passed_gates} 項")
if all_passed and passed_gates == total_gates:
    print("🏆 [ALL 100% GREEN PASS] 五大黑科技神兵全數無損對接 PHANToM Grid，正式入役全軍兵器庫！")
else:
    print("❌ 門禁驗收未全數通過，請指揮官依據失敗項目排查！")
print("================================================================================")

sys.exit(0 if all_passed else 1)
