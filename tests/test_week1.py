# -*- coding: utf-8 -*-
"""
tests/test_week1.py - 第 1 週驗證：網格抽象契約、狀態遮罩與物理場管理
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
from core.types import CellStatus
from grids.structured_cartesian import StructuredCartesianGrid


def test_week1():
    print("[PHANTOM Week 1 Test] Testing Core Grid Abstraction & Interfaces...")
    
    # 1. 建立結構化直角網格 (Background Grid)
    grid = StructuredCartesianGrid(
        grid_id="bg_grid",
        bounds=(0.0, 1.0, 0.0, 2.0),
        shape=(11, 21),
        priority=0
    )
    
    # 2. 幾何形狀與邊界檢查
    assert grid.get_shape() == (11, 21), f"Shape mismatch: {grid.get_shape()}"
    bbox = grid.get_bounding_box()
    assert np.allclose(bbox, (0.0, 1.0, 0.0, 2.0)), f"Bounding box mismatch: {bbox}"
    assert np.isclose(grid.dx, 0.1), f"dx mismatch: {grid.dx}"
    assert np.isclose(grid.dy, 0.1), f"dy mismatch: {grid.dy}"
    
    # 3. 座標網格驗證
    X, Y = grid.get_coordinates()
    assert X.shape == (11, 21), f"X shape mismatch: {X.shape}"
    assert Y.shape == (11, 21), f"Y shape mismatch: {Y.shape}"
    assert np.isclose(X[0, 0], 0.0) and np.isclose(X[-1, -1], 1.0)
    assert np.isclose(Y[0, 0], 0.0) and np.isclose(Y[-1, -1], 2.0)
    
    # 4. 狀態遮罩 (CellStatus) 初始狀態與切換驗證
    assert grid.status_mask.shape == (11, 21)
    assert np.all(grid.status_mask == CellStatus.FIELD)
    
    # 模擬孔洞與接收點標定
    grid.status_mask[4:7, 8:13] = CellStatus.HOLE
    grid.status_mask[3, 8:13] = CellStatus.RECEIVER
    assert np.sum(grid.status_mask == CellStatus.HOLE) == 3 * 5
    assert np.sum(grid.status_mask == CellStatus.RECEIVER) == 5
    
    # 5. 物理場管理
    pressure = np.sin(np.pi * X) * np.cos(np.pi * Y)
    grid.set_field("pressure", pressure)
    retrieved = grid.get_field("pressure")
    assert np.allclose(pressure, retrieved)
    
    print("  ✓ Shape & Bounding Box: PASS")
    print("  ✓ Coordinate Meshgrid: PASS")
    print("  ✓ CellStatus Masks (HOLE/RECEIVER/FIELD): PASS")
    print("  ✓ Field Allocation & Retrieval: PASS")
    print(">> Week 1 Core Grid Verification SUCCESSFUL!\n")


if __name__ == "__main__":
    test_week1()
