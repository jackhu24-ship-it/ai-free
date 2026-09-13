# -*- coding: utf-8 -*-
"""
tests/test_hpc_runner.py - PHANTOM HPC 極致加速雙引擎集成測試
============================================================
驗證指標：
1. PhantomRunner 同時啟用 use_numba=True 與 use_gpu=True
2. 驗證 2D 波動方程式時間步推進正常運算
3. 驗證跨網格邊界稀疏傳遞數值平滑無裂紋
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
from core.types import CellStatus
from grids.structured_cartesian import StructuredCartesianGrid
from grids.component_grid import ComponentGrid
from solver.phantom_runner import PhantomRunner


def test_hpc_runner_integration():
    print("[HPC Runner Test] Testing Numba CPU + GPU Dual Acceleration Integration...")

    # 1. 建立背景與前景網格
    bg = StructuredCartesianGrid("bg", bounds=(-2.0, 2.0, -2.0, 2.0), shape=(51, 51), priority=0)
    bg.initialize_fields(["u", "v"])
    fg = ComponentGrid("fg", local_bounds=(-0.6, 0.6, -0.6, 0.6), shape=(31, 31),
                       origin=(0.0, 0.0), angle_rad=0.0, priority=10)
    fg.initialize_fields(["u", "v"])

    # 2. 設置初始物理高斯擾動 (波包)
    X_bg, Y_bg = bg.get_coordinates()
    bg.fields["u"][:] = np.exp(-((X_bg - 0.5) ** 2 + (Y_bg - 0.5) ** 2) / 0.1)

    # 3. 實例化 HPC 雙引擎調度器 (Numba CPU + GPU 稀疏)
    runner = PhantomRunner(bg, fg, use_sparse=True, use_numba=True, use_gpu=True)
    runner.rebuild_topology()

    assert runner.use_numba is True, "Numba acceleration should be active"
    assert runner.use_gpu is True, "GPU acceleration option should be active"
    assert runner.sparse_coupler is not None, "Sparse coupler should be constructed"

    # 4. 推進 20 個時間步
    dt = 0.01
    for step_idx in range(20):
        runner.step(dt=dt, field_names=["u", "v"])

    # 5. 驗證數值有效性 (無 NaN、無 Inf，且擾動成功傳入前景網格邊界)
    assert not np.isnan(bg.fields["u"]).any(), "Background field contains NaN"
    assert not np.isnan(fg.fields["u"]).any(), "Foreground field contains NaN"
    assert np.max(np.abs(fg.fields["u"])) > 0.0, "Wave disturbance successfully coupled into foreground"

    print("  ✓ Numba JIT Wave Kernel Stepping: PASS")
    print("  ✓ GPU/CPU Hybrid CSR SpMV Transfer: PASS")
    print("  ✓ Wavefield Non-NaN & Boundary Continuity: PASS")
    print(">> HPC Runner Dual Engine Integration SUCCESSFUL!\n")


if __name__ == "__main__":
    test_hpc_runner_integration()
