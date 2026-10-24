# -*- coding: utf-8 -*-
import os
import shutil

# 1. Update GLOBAL_ELEMENTS_REGISTRY.md
registry_path = "03_研發專區/PHANTOM_GRID_Aria_Titan/00_System/Standards/GLOBAL_ELEMENTS_REGISTRY.md"
with open(registry_path, "r", encoding="utf-8") as f:
    reg_content = f.read()

new_mod_rows = """| **PG-MOD-14-JEPA** | V-JEPA 物理世界潛在因果預測模型 | `04_功能模組庫_Level2_Modules/physical_world_vjepa/docs/SPEC_14_VJepa_Physical_World.md` | `04_功能模組庫_Level2_Modules/physical_world_vjepa/` | V-JEPA 潛在空間因果預測、非生成式能量最小化、50GB 熔斷、ZDR 0.00MB、Level 4 CLI (`vjepa` / `pg-vjepa`) |
| **PG-MOD-15-TACT** | 力控觸覺物理沙盒 (FM-VLA) | `04_功能模組庫_Level2_Modules/force_tactile_sandbox/docs/SPEC_15_Force_Tactile_Sandbox.md` | `04_功能模組庫_Level2_Modules/force_tactile_sandbox/` | 6-DOF 扭矩向量即時閉環、滑移接觸動力學、50GB 熔斷、ZDR 0.00MB、Level 4 CLI (`forcetactile` / `pg-tactile`) |
| **PG-MOD-16-VLA** | Turbo VLA 邊緣視覺語言動作模型 (32Hz) | `04_功能模組庫_Level2_Modules/turbo_vla_edge/docs/SPEC_16_Turbo_VLA_Edge.md` | `04_功能模組庫_Level2_Modules/turbo_vla_edge/` | 32Hz 硬即時視覺語言動作推論、投機解碼預測、50GB 熔斷、ZDR 0.00MB、Level 4 CLI (`turbovla` / `pg-vla`) |
| **PG-MOD-17-COSMOS** | Cosmos 物理世界沙盒 | `04_功能模組庫_Level2_Modules/cosmos_physical_sandbox/docs/SPEC_17_Cosmos_Physical_Sandbox.md` | `04_功能模組庫_Level2_Modules/cosmos_physical_sandbox/` | 大規模多體物理微分模擬、辛幾何保能量推演、50GB 熔斷、ZDR 0.00MB、Level 4 CLI (`cosmos` / `pg-cosmos`) |
| **PG-MOD-18-EYE** | 空間視覺眼 3D 流形感知器 (3DGS) | `04_功能模組庫_Level2_Modules/spatial_vision_eye/docs/SPEC_18_Spatial_Vision_Eye.md` | `04_功能模組庫_Level2_Modules/spatial_vision_eye/` | 3D 高斯潑濺幾何重建、點雲流形神經輻射場感知、50GB 熔斷、ZDR 0.00MB、Level 4 CLI (`spatialeye` / `pg-eye`) |
"""

target_marker = "| **MOD-SUPREMACY-01** | 全球第一旗艦戰略系統 (Supremacy)"
if target_marker in reg_content and "PG-MOD-14-JEPA" not in reg_content:
    reg_content = reg_content.replace(target_marker, new_mod_rows + target_marker)
    with open(registry_path, "w", encoding="utf-8") as f:
        f.write(reg_content)
    print("Updated GLOBAL_ELEMENTS_REGISTRY.md successfully!")
else:
    print("GLOBAL_ELEMENTS_REGISTRY.md already has new modules or target marker not found.")

# 2. Update AGENTS.md
agents_path = "AGENTS.md"
with open(agents_path, "r", encoding="utf-8") as f:
    agents_content = f.read()

scenario_11_line = "| **11. 3D 提詞與 1440P 串流可視化** | `[三、功能模組 PG-MOD-09-VIS]` ＆ `[teleprompter-streamer]` | 三辦 (小馬 ✕ 視效工兵 Bob 2) | 調用 2560x1440 提詞引擎、雙軌狀態機、42pt 大字級貪婪排版、50GB 熔斷與 ZDR 0.00MB 物理銷毀 |"

new_scenarios = scenario_11_line + """
| **12. V-JEPA 物理世界潛在因果預測** | `[三、功能模組 PG-MOD-14-JEPA]` ＆ `[pg-vjepa-world]` | 二辦 (小深 ✕ 小米) | 調用潛在因果世界模型、能量最小化非生成式預測、50GB 熔斷與 ZDR 0.00MB 物理銷毀 |
| **13. 力控觸覺物理沙盒 (FM-VLA)** | `[三、功能模組 PG-MOD-15-TACT]` ＆ `[pg-force-tactile]` | 一辦 (小克) ✕ 三辦 (小馬) | 調用 6-DOF 扭矩向量即時回饋、滑移動態檢測、50GB 熔斷與 ZDR 0.00MB 物理銷毀 |
| **14. Turbo VLA 邊緣視覺語言動作 (32Hz)** | `[三、功能模組 PG-MOD-16-VLA]` ＆ `[pg-turbo-vla]` | 一辦 (小克) ✕ 三辦 (小開) | 調用 32Hz 硬即時視覺語言動作推論、投機解碼預測、50GB 熔斷與 ZDR 0.00MB 物理銷毀 |
| **15. Cosmos 物理世界沙盒** | `[三、功能模組 PG-MOD-17-COSMOS]` ＆ `[pg-cosmos-sandbox]` | 二辦 (小深) ✕ 天文台 (小小米) | 調用大規模多體物理微分模擬、辛幾何保能量推演、50GB 熔斷與 ZDR 0.00MB 物理銷毀 |
| **16. 空間視覺眼 3D 流形感知 (3DGS)** | `[三、功能模組 PG-MOD-18-EYE]` ＆ `[pg-spatial-eye]` | 一辦 (小克) ✕ 視效工兵 Bob 2 | 調用 3D 高斯潑濺幾何重建、點雲流形輻射場感知、50GB 熔斷與 ZDR 0.00MB 物理銷毀 |"""

if scenario_11_line in agents_content and "12. V-JEPA" not in agents_content:
    agents_content = agents_content.replace(scenario_11_line, new_scenarios)
    with open(agents_path, "w", encoding="utf-8") as f:
        f.write(agents_content)
    print("Updated AGENTS.md with Scenarios 12 to 16 successfully!")
else:
    print("AGENTS.md already has new scenarios or Scenario 11 line not matched.")

# 3. Mirror files to Google Drive
gdrive_base = r"G:\我的雲端硬碟\260803_opencode"
if os.path.exists(gdrive_base):
    # Mirror AGENTS.md
    gdrive_agents = os.path.join(gdrive_base, "AGENTS.md")
    shutil.copy2(agents_path, gdrive_agents)
    print(f"Mirrored AGENTS.md to Google Drive: {gdrive_agents}")

    # Mirror GLOBAL_ELEMENTS_REGISTRY.md
    gdrive_reg = os.path.join(gdrive_base, "03_研發專區", "PHANTOM_GRID_Aria_Titan", "00_System", "Standards", "GLOBAL_ELEMENTS_REGISTRY.md")
    if os.path.exists(os.path.dirname(gdrive_reg)):
        shutil.copy2(registry_path, gdrive_reg)
        print(f"Mirrored GLOBAL_ELEMENTS_REGISTRY.md to Google Drive: {gdrive_reg}")

print("All updates and mirrors finished successfully!")
