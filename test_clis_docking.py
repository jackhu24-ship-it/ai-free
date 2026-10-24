# -*- coding: utf-8 -*-
import subprocess
import sys
import json

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

base_dir = r"G:\我的雲端硬碟\260803_opencode\04_功能模組庫_Level2_Modules"
mods = [
    'physical_world_vjepa',
    'force_tactile_sandbox',
    'turbo_vla_edge',
    'cosmos_physical_sandbox',
    'spatial_vision_eye'
]

print("=== VERIFYING ALL 5 MODULE CLIS ===")
for m in mods:
    cli = f"{base_dir}\\{m}\\cli.py"
    
    # 1. Test --json status
    res = subprocess.run([sys.executable, cli, "--json"], capture_output=True, encoding="utf-8")
    if res.returncode != 0:
        print(f"FAILED --json on {m}: {res.stderr}")
        sys.exit(1)
    d = json.loads(res.stdout)
    code = d["module_code"]
    st = d["status"]
    print(f"[STATUS] {code:16} | Status: {st} | Level: {d['architecture_level']}")

    # 2. Test --real --json execution
    res_real = subprocess.run([sys.executable, cli, "--real", "--json"], capture_output=True, encoding="utf-8")
    if res_real.returncode != 0:
        print(f"FAILED --real on {m}: {res_real.stderr}")
        sys.exit(1)
    d_real = json.loads(res_real.stdout)
    assert d_real["status"] == "SUCCESS"
    assert d_real["zdr_residue_mb"] == 0.00
    lat = d_real["latency_us"]
    zdr = d_real["zdr_residue_mb"]
    print(f"[REAL]   {code:16} | Latency: {lat:7.2f} us | ZDR: {zdr:.2f} MB | Gate: PASS")

    # 3. Test --test closure suite
    res_test = subprocess.run([sys.executable, cli, "--test"], capture_output=True, encoding="utf-8")
    if res_test.returncode != 0:
        print(f"FAILED --test on {m}: {res_test.stderr}")
        sys.exit(1)
    print(f"[TEST]   {code:16} | 100% Closure Self-Test: PASSED")

print("\n>>> ALL 5 MODULE LEVEL 4 CLIS PASSED 100% VERIFICATION CLOSURE! <<<")
