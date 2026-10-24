# -*- coding: utf-8 -*-
import os
import sys

bin_dir = r"C:\Users\user\.local\bin"
skills_dir = r"C:\Users\user\.gemini\config\skills"
base_modules_dir = r"G:\我的雲端硬碟\260803_opencode\04_功能模組庫_Level2_Modules"

os.makedirs(bin_dir, exist_ok=True)
os.makedirs(skills_dir, exist_ok=True)

# 1. Batch Wrappers
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
    bat_content = f"@echo off\r\npython \"{cli_target}\" %*\r\n"
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(bat_content)
    print(f"Created batch wrapper: {bat_path}")

# 2. Global Skills
skills_info = {
    "pg-vjepa-world": {
        "name": "pg-vjepa-world",
        "description": "PHANToM Grid 第 14 神兵 PG-MOD-14-JEPA V-JEPA 物理世界潛在因果預測模型。當任務或將士需要潛在空間因果預測、世界動態模擬、非生成式能量最小化因果推演或 vjepa 命令時調用。配備 50GB 熔斷與 ZDR 0.00MB 置零。",
        "cli": "vjepa / pg-vjepa",
        "mod_dir": "physical_world_vjepa",
        "custodian": "二辦參謀小深 ✕ 指揮官小米",
        "triggers": ["vjepa", "v-jepa", "物理世界模型", "因果預測", "潛在世界模型", "JEPA", "physical_world_vjepa"]
    },
    "pg-force-tactile": {
        "name": "pg-force-tactile",
        "description": "PHANToM Grid 第 15 神兵 PG-MOD-15-TACT 力控觸覺物理沙盒 (FM-VLA)。當任務涉及機器人力控反饋、觸覺滑移預測、6-DOF 扭矩向量即時閉環、接觸動力學或 forcetactile 命令時調用。配備 50GB 熔斷與 ZDR 0.00MB 置零。",
        "cli": "forcetactile / pg-tactile",
        "mod_dir": "force_tactile_sandbox",
        "custodian": "一辦先鋒小克 ✕ 三辦指揮官小馬",
        "triggers": ["力控", "觸覺沙盒", "觸覺反饋", "FM-VLA", "force-tactile", "forcetactile", "滑移檢測", "6軸扭矩"]
    },
    "pg-turbo-vla": {
        "name": "pg-turbo-vla",
        "description": "PHANToM Grid 第 16 神兵 PG-MOD-16-VLA Turbo VLA 邊緣視覺語言動作模型 (32Hz)。當任務需要高頻視覺語言動作推論 (32Hz 硬即時)、投機解碼推演、邊緣端低顯存具身控制或 turbovla 命令時調用。配備 50GB 熔斷與 ZDR 0.00MB 置零。",
        "cli": "turbovla / pg-vla",
        "mod_dir": "turbo_vla_edge",
        "custodian": "一辦先鋒小克 ✕ 三辦先鋒小開",
        "triggers": ["turbovla", "turbo vla", "視覺語言動作", "32Hz", "具身動作推論", "邊緣端VLA", "turbo_vla_edge"]
    },
    "pg-cosmos-sandbox": {
        "name": "pg-cosmos-sandbox",
        "description": "PHANToM Grid 第 17 神兵 PG-MOD-17-COSMOS Cosmos 物理世界沙盒。當任務涉及大規模多體物理微分模擬、空間分層 VDB 網格樹、辛幾何保能量推演或 cosmos 命令時調用。配備 50GB 熔斷與 ZDR 0.00MB 置零。",
        "cli": "cosmos / pg-cosmos",
        "mod_dir": "cosmos_physical_sandbox",
        "custodian": "二辦參謀小深 ✕ 天文台小小米",
        "triggers": ["cosmos", "物理沙盒", "cosmos世界模型", "多體物理", "辛幾何", "宇宙物理沙盒", "cosmos_physical_sandbox"]
    },
    "pg-spatial-eye": {
        "name": "pg-spatial-eye",
        "description": "PHANToM Grid 第 18 神兵 PG-MOD-18-EYE 空間視覺眼 3D 流形感知器 (3DGS)。當任務涉及 3D 高斯潑濺 (3DGS) 幾何重建、點雲流形神經輻射場、八叉樹剪枝或 spatialeye 命令時調用。配備 50GB 熔斷與 ZDR 0.00MB 置零。",
        "cli": "spatialeye / pg-eye",
        "mod_dir": "spatial_vision_eye",
        "custodian": "一辦先鋒小克 ✕ 視效工兵 Bob 2",
        "triggers": ["spatialeye", "空間視覺眼", "3DGS", "高斯潑濺", "點雲流形", "輻射場重建", "spatial_vision_eye"]
    }
}

for s_name, s_data in skills_info.items():
    s_folder = os.path.join(skills_dir, s_name)
    os.makedirs(s_folder, exist_ok=True)
    s_file = os.path.join(s_folder, "SKILL.md")
    cli_path = os.path.join(base_modules_dir, s_data["mod_dir"], "cli.py")
    
    triggers_str = ", ".join([f"`{t}`" for t in s_data["triggers"]])
    
    skill_content = f"""---
name: {s_data['name']}
description: {s_data['description']}
---

# PHANToM Grid :: {s_data['name']}
> **全軍神兵編號**：`{s_data['mod_dir'].upper()}`  
> **專任主管兵種**：`{s_data['custodian']}`（全軍現役 26 員將士全員標配，除名服刑人員 PENAL-01 小幫手嚴禁調用）  
> **作業系統命令**：`{s_data['cli']}`  
> **實體代碼指針**：`{cli_path}`

---

## ⚡ 一、模組功能與觸發情境
- **核心觸發詞**：{triggers_str}
- **核心功能**：{s_data['description']}

---

## 🛠️ 二、CLI 呼叫規範 (Level 4 Sovereign CLI)
本神兵支援五大標準終端旗標與互動式選單：

```bash
# 1. 互動式 1-N 華爾街深色選單
{s_data['cli'].split(' / ')[0]}

# 2. 顯示系統狀態與安全指標卡片
{s_data['cli'].split(' / ')[0]} --status

# 3. 輸出純 JSON 機器合約（供 CI/CD 或 Agent 直接剖析）
{s_data['cli'].split(' / ')[0]} --json

# 4. 執行實機運算閉環 (50GB 熔斷防禦 + ZDR 0.00MB 置零)
{s_data['cli'].split(' / ')[0]} --real

# 5. 執行全要素自動化門禁自測 (100% 通過斷言)
{s_data['cli'].split(' / ')[0]} --test

# 6. 強制執行 ZDR 物理銷毀 (0xAA -> 0x00)
{s_data['cli'].split(' / ')[0]} --purge
```

---

## 🛡️ 三、硬性作業天條 (Golden Invariants)
1. **50GB 顯存硬熔斷**：運算中若瞬時 VRAM 超標 50.0 GB，底層自動物理熔斷中止。
2. **ZDR 物理雙重置零**：每次推演結束後，強制執行 `0xAA -> 0x00` 雙重覆寫，確保殘留記憶體絕對為 `0.00 MB`。
3. **服刑人員絕對隔離**：除名服刑人員（PENAL-01 小幫手）若調用本模組，安全哨兵立即回傳 `403 FORBIDDEN` 並啟動高壓熔斷！
"""
    with open(s_file, "w", encoding="utf-8") as f:
        f.write(skill_content)
    print(f"Created Global Skill: {s_file}")

print("All batch wrappers and global skills created successfully!")
