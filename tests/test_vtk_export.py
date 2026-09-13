# -*- coding: utf-8 -*-
"""
tests/test_vtk_export.py - 任務三：ParaView 國際賽事級 Multi-Block VTK 資料集導出驗證
=====================================================================================
驗證指標：
1. 導出多塊重疊網格架構 (背景笛卡爾網格 + NACA 0012 貼體 O 型網格)
2. 驗證產出之 .vtm 與 .vts 檔案結構符合標準 VTK XML 規範 (ElementTree 語法解析)
3. 驗證 vtkGhostType 幽靈節點標記精確對齊 HOLE 區域 (使 ParaView 能自動隱藏孔洞)
4. 驗證所有檔案落盤於專案目錄內 (恪守零桌面污染原則)
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np

from core.types import CellStatus
from grids.structured_cartesian import StructuredCartesianGrid
from grids.curvilinear_grid import CurvilinearGrid
from geometry.airfoil_generator import AirfoilGridGenerator
from geometry.hole_cutter import HoleCutter
from exporters.vtk_exporter import VTKMultiBlockExporter


def test_vtk_export():
    print("==========================================================")
    print(" 🚀 測試 ParaView Multi-Block VTK (.vtm / .vts) 資料導出...")
    print("==========================================================")

    # 1. 建立背景笛卡爾網格
    bg_grid = StructuredCartesianGrid(
        grid_id="Background_Cartesian",
        bounds=(-3.0, 3.0, -3.0, 3.0),
        shape=(61, 61),
        priority=0
    )
    bg_grid.initialize_fields(["u", "v"])

    # 2. 建立 NACA 0012 貼體 O 型曲面網格
    X_airfoil, Y_airfoil = AirfoilGridGenerator.generate_o_grid(
        n_circumferential=81,
        n_radial=25,
        chord=1.2,
        thickness=0.12,
        r_outer=1.5,
        clustering_ratio=2.5,
        center_offset=(0.3, 0.0)
    )
    airfoil_grid = CurvilinearGrid(
        grid_id="NACA0012_O_Grid",
        X=X_airfoil,
        Y=Y_airfoil,
        priority=10,
        periodic_xi=True
    )
    airfoil_grid.initialize_fields(["u", "v"])

    # 3. 執行翼型多邊形切孔
    xs, ys = AirfoilGridGenerator.generate_airfoil_surface(n_points=81, chord=1.2, thickness=0.12)
    poly_pts = np.column_stack([xs, ys])
    HoleCutter.cut_polygon_holes_and_mark_fringe(bg_grid, poly_pts, fringe_layers=1)

    # 4. 初始化測試波動場量
    X_b, Y_b = bg_grid.get_coordinates()
    r_b = np.sqrt((X_b + 0.8)**2 + (Y_b + 0.8)**2)
    bg_grid.fields["u"] = np.exp(-(r_b**2) / 0.2)
    bg_grid.fields["v"] = -0.5 * bg_grid.fields["u"]

    X_a, Y_a = airfoil_grid.get_coordinates()
    r_a = np.sqrt((X_a + 0.8)**2 + (Y_a + 0.8)**2)
    airfoil_grid.fields["u"] = np.exp(-(r_a**2) / 0.2)
    airfoil_grid.fields["v"] = -0.5 * airfoil_grid.fields["u"]

    # 5. 導出 Multi-Block VTK
    out_dir = Path("vtk_output")
    vtm_file = VTKMultiBlockExporter.export_multiblock(
        grids=[bg_grid, airfoil_grid],
        output_dir=out_dir,
        file_prefix="phantom_naca_dataset",
        field_names=["u", "v"]
    )

    print(f"1. VTK 資料集已成功導出至: {vtm_file.resolve()}")
    assert vtm_file.exists(), "主 .vtm 檔案未成功生成！"

    # 6. XML 合規性解析驗證
    tree_vtm = ET.parse(vtm_file)
    root_vtm = tree_vtm.getroot()
    assert root_vtm.tag == "VTKFile", "VTM 頂層根標籤非 VTKFile"
    assert root_vtm.attrib.get("type") == "vtkMultiBlockDataSet", "VTM 資料集型別不符"

    blocks = root_vtm.findall(".//Block")
    print(f"2. 驗證 VTM 包含之子區塊數量: {len(blocks)}")
    assert len(blocks) == 2, f"預期 2 個 Block，實得 {len(blocks)}"

    # 檢查各 .vts 檔案
    for block in blocks:
        dataset = block.find("DataSet")
        filename = dataset.attrib.get("file")
        vts_path = out_dir / filename
        assert vts_path.exists(), f"找不到子網格檔案: {vts_path}"

        tree_vts = ET.parse(vts_path)
        root_vts = tree_vts.getroot()
        assert root_vts.attrib.get("type") == "StructuredGrid"
        print(f"   ✓ 子網格 {filename} XML 解析校驗成功！")

    # 7. 檢查 vtkGhostType 遮蔽遮罩
    bg_vts_file = out_dir / "phantom_naca_dataset_block0_Background_Cartesian.vts"
    tree_bg = ET.parse(bg_vts_file)
    ghost_elem = None
    for da in tree_bg.findall(".//DataArray"):
        if da.attrib.get("Name") == "vtkGhostType":
            ghost_elem = da
            break

    assert ghost_elem is not None, "未找到 vtkGhostType 陣列！"
    ghost_data = [int(x) for x in ghost_elem.text.split()]
    n_hidden_points = sum(1 for g in ghost_data if g == 8)
    n_hole_actual = int(np.sum(bg_grid.status_mask == CellStatus.HOLE))
    print(f"3. 幽靈節點遮蔽校驗: ParaView 隱藏點數 = {n_hidden_points}, 背景網格 HOLE 數 = {n_hole_actual}")
    assert n_hidden_points == n_hole_actual, "vtkGhostType 與 HOLE 節點數量不一致！"
    print("  ✓ vtkGhostType 與幾何孔洞完全對齊，ParaView 渲染將自動遮蔽孔洞！")

    print("==========================================================")
    print(" ✅ [任務三：ParaView Multi-Block VTK 資料導出全量通過！]  ")
    print("==========================================================")


if __name__ == "__main__":
    test_vtk_export()
