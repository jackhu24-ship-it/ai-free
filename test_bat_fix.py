# -*- coding: utf-8 -*-
import os
import subprocess
import sys

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

bin_dir = r"C:\Users\user\.local\bin"
base_modules_dir = r"G:\我的雲端硬碟\260803_opencode\04_功能模組庫_Level2_Modules"

wrappers = [
    ("vjepa.bat", "physical_world_vjepa"),
    ("pg-vjepa.bat", "physical_world_vjepa"),
    ("forcetactile.bat", "force_tactile_sandbox"),
    ("pg-tactile.bat", "force_tactile_sandbox"),
    ("turbovla.bat", "turbo_vla_edge"),
    ("pg-vla.bat", "turbo_vla_edge"),
    ("cosmos.bat", "cosmos_physical_sandbox"),
    ("pg-cosmos.bat", "cosmos_physical_sandbox"),
    ("spatialeye.bat", "spatial_vision_eye"),
    ("pg-eye.bat", "spatial_vision_eye"),
]

for bat_name, mod_dir in wrappers:
    bat_path = os.path.join(bin_dir, bat_name)
    cli_target = os.path.join(base_modules_dir, mod_dir, "cli.py")
    # Using @chcp 65001 > nul ensures cmd.exe parses UTF-8 paths cleanly
    bat_content = f"@chcp 65001 > nul\r\n@python \"{cli_target}\" %*\r\n"
    with open(bat_path, "wb") as f:
        f.write(bat_content.encode("utf-8"))
    print(f"Updated batch wrapper with chcp 65001: {bat_name}")

# Now test executing them via cmd.exe
print("\n--- Testing execution via cmd.exe ---")
for cmd in ["vjepa", "forcetactile", "turbovla", "cosmos", "spatialeye"]:
    res = subprocess.run(["cmd.exe", "/c", f"{cmd}.bat", "--json"], capture_output=True, encoding="utf-8", errors="replace")
    print(f"[{cmd}.bat] Return Code: {res.returncode}")
    if res.returncode == 0:
        print(f"  Output: {res.stdout.strip()[:100]}...")
    else:
        print(f"  Error: {res.stderr.strip()}")
