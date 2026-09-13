# -*- coding: utf-8 -*-
"""
exporters/vtk_exporter.py - ParaView 國際賽事級 Multi-Block VTK (.vtm / .vts) 資料集導出模組
========================================================================================
將 PHANTOM Grid 的多網格架構（含背景笛卡爾網格與貼體/組件曲面網格）導出為標準 VTK XML 格式：
1. 各網格獨立存為 XML 結構化網格 (.vts, StructuredGrid)
2. 頂層組裝為多塊資料集容器 (.vtm, vtkMultiBlockDataSet)
3. 同時支援 CellStatus、status_mask 與 vtkGhostType 遮罩，
   使 ParaView 既可自動隱藏/剔除 HOLE 孔洞區域，亦可手動進行 Threshold 門檻篩選。
"""
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from typing import List, Optional, Union
import numpy as np

from core.types import CellStatus
from core.base_grid import AbstractGrid


class VTKMultiBlockExporter:
    """ParaView XML Multi-Block 資料集導出器"""

    @staticmethod
    def _write_vts(
        filepath: Union[str, Path],
        grid: AbstractGrid,
        field_names: List[str]
    ) -> None:
        """導出單一結構化網格為標準 XML .vts 檔案"""
        filepath = Path(filepath)
        X, Y = grid.get_coordinates()
        nx, ny = X.shape
        nz = 1  # 2D 平面設為 1

        # 準備點座標 (X, Y, Z=0)
        Z = np.zeros_like(X)
        pts_3d = np.column_stack([X.ravel(order='F'), Y.ravel(order='F'), Z.ravel(order='F')])

        # 準備幽靈節點遮罩 vtkGhostType:
        # 0 = 正常活動點 (FIELD / RECEIVER)
        # 8 = VTK_POINT_HIDDEN (隱藏/遮蔽盲點 HOLE)
        ghost_mask = np.zeros(nx * ny, dtype=np.uint8)
        if grid.status_mask is not None:
            ghost_mask[grid.status_mask.ravel(order='F') == CellStatus.HOLE] = 8

        root = ET.Element("VTKFile", type="StructuredGrid", version="0.1", byte_order="LittleEndian")
        sgrid = ET.SubElement(root, "StructuredGrid", WholeExtent=f"0 {nx-1} 0 {ny-1} 0 {nz-1}")
        piece = ET.SubElement(sgrid, "Piece", Extent=f"0 {nx-1} 0 {ny-1} 0 {nz-1}")

        # 1. 寫入座標點 (Points)
        points_elem = ET.SubElement(piece, "Points")
        p_data = ET.SubElement(points_elem, "DataArray", type="Float64", NumberOfComponents="3", format="ascii")
        p_data.text = "\n" + "\n".join(f"{p[0]:.6e} {p[1]:.6e} {p[2]:.6e}" for p in pts_3d) + "\n"

        # 2. 寫入點資料 (PointData)
        point_data_elem = ET.SubElement(piece, "PointData")

        # 寫入狀態遮罩 (CellStatus 與 status_mask 同步支援)
        if grid.status_mask is not None:
            status_flat = grid.status_mask.ravel(order='F')
            s_data1 = ET.SubElement(point_data_elem, "DataArray", type="Int32", Name="CellStatus", format="ascii")
            s_data1.text = "\n" + " ".join(str(int(val)) for val in status_flat) + "\n"

            s_data2 = ET.SubElement(point_data_elem, "DataArray", type="Int32", Name="status_mask", format="ascii")
            s_data2.text = "\n" + " ".join(str(int(val)) for val in status_flat) + "\n"

            s_ghost = ET.SubElement(point_data_elem, "DataArray", type="UInt8", Name="vtkGhostType", format="ascii")
            s_ghost.text = "\n" + " ".join(str(int(val)) for val in ghost_mask) + "\n"

        # 寫入物理場量 (如 u, v)
        for name in field_names:
            if name in grid.fields:
                field_flat = grid.fields[name].ravel(order='F')
                f_data = ET.SubElement(point_data_elem, "DataArray", type="Float64", Name=name, format="ascii")
                f_data.text = "\n" + " ".join(f"{val:.6e}" for val in field_flat) + "\n"

        # 美化並寫出 XML
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        filepath.write_text(xml_str, encoding="utf-8")

    # 別名方法以滿足不同呼叫慣例
    _write_vts_file = _write_vts

    @classmethod
    def export_multiblock(
        cls,
        output_dir: Union[str, Path] = "./export_paraview",
        case_name: Optional[str] = None,
        grids: Optional[List[AbstractGrid]] = None,
        field_names: Optional[List[str]] = None,
        file_prefix: Optional[str] = None,
        **kwargs
    ) -> Path:
        """
        將所有重疊網格導出為 ParaView Multi-Block 資料集 (.vtm 容器 + 多個 .vts 子塊)。
        相容兩套呼叫協定：
        協定 A: (output_dir, case_name, grids, field_names)
        協定 B: (grids, output_dir, file_prefix, field_names)
        """
        # 參數調解
        if grids is None and isinstance(output_dir, list):
            # Positional call: export_multiblock(grids, output_dir, file_prefix, field_names)
            grids = output_dir
            output_dir = case_name if case_name is not None else kwargs.get("output_dir", "./vtk_output")

        if grids is None:
            raise ValueError("grids 網格清單不能為空！")

        if field_names is None:
            field_names = ["u", "v"]

        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        if file_prefix is not None:
            prefix = file_prefix
            naming_style = "prefix"  # f"{prefix}_block{idx}_{safe_id}.vts"
        else:
            prefix = case_name if case_name is not None else "phantom_case"
            naming_style = "case"    # f"{prefix}_block_{idx}_{grid.grid_id}.vts"

        vtm_root = ET.Element("VTKFile", type="vtkMultiBlockDataSet", version="1.0", byte_order="LittleEndian")
        multiblock = ET.SubElement(vtm_root, "vtkMultiBlockDataSet")

        for idx, grid in enumerate(grids):
            safe_id = "".join(c if c.isalnum() or c in "_-" else "_" for c in grid.grid_id)
            if naming_style == "prefix":
                vts_filename = f"{prefix}_block{idx}_{safe_id}.vts"
            else:
                vts_filename = f"{prefix}_block_{idx}_{grid.grid_id}.vts"

            vts_path = out_path / vts_filename
            cls._write_vts(vts_path, grid, field_names)

            block_elem = ET.SubElement(
                multiblock,
                "Block",
                index=str(idx),
                name=f"[{grid.priority}] {grid.grid_id}"
            )
            ET.SubElement(block_elem, "DataSet", index="0", file=vts_filename)

        vtm_filepath = out_path / f"{prefix}.vtm"
        xml_str = minidom.parseString(ET.tostring(vtm_root)).toprettyxml(indent="  ")
        vtm_filepath.write_text(xml_str, encoding="utf-8")

        return vtm_filepath
