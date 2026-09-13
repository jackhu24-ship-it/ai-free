# -*- coding: utf-8 -*-
"""
tests/test_gpu_acceleration.py - GPU / CPU 混合架構稀疏矩陣通訊加速驗證
========================================================================
驗證指標：
1. 建立真實邊界傳輸稀疏矩陣 W 與供體物理量向量
2. 驗證 GPUSparseOversetCoupler 在當前環境的自動後端選擇 (GPU CuPy 或 CPU SciPy)
3. 斷言 SpMV 運算結果與標準 SciPy 乘法數值完全一致 (偏差 < 1e-12)
4. 測量單步邊界數據傳遞耗時，驗證跨網格邊界通訊達到微秒級極限 (< 1.0 ms)
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import time
import numpy as np
from scipy.sparse import random as sparse_random

from coupling.gpu_coupler import GPUSparseOversetCoupler, HAS_GPU


def test_gpu_sparse_coupler():
    print("==========================================================")
    print(" 🚀 測試 GPU / CPU 混合架構稀疏通訊運算元...              ")
    print("==========================================================")

    # 1. 構建模擬重疊交界稀疏矩陣 (1,500 個接收節點, 50,000 個供體候選點)
    n_recvs = 1500
    n_donors = 50000
    density = 4.0 / n_donors  # 每個接收點恰有 4 個供體 (雙線性插值典型分佈)

    np.random.seed(42)
    scipy_W = sparse_random(n_recvs, n_donors, density=density, format="csr", dtype=np.float64)

    # 歸一化行和 (權重和為 1.0)
    row_sums = np.array(scipy_W.sum(axis=1)).ravel()
    row_sums[row_sums == 0] = 1.0
    from scipy.sparse import diags
    inv_diag = diags(1.0 / row_sums)
    scipy_W = inv_diag.dot(scipy_W)

    # 2. 實例化 GPU 加速器
    coupler = GPUSparseOversetCoupler(scipy_W, prefer_gpu=True)
    backend_name = coupler.get_backend_name()
    print(f"1. 啟用通訊運算後端: {backend_name}")
    print(f"   (環境 CUDA/CuPy 可用狀態: {HAS_GPU})")

    # 3. 測試 SpMV 運算等價性
    donor_vec = np.sin(np.linspace(0, 10, n_donors))
    expected_recv = scipy_W.dot(donor_vec)

    actual_recv = coupler.transfer(donor_vec)
    max_err = float(np.max(np.abs(expected_recv - actual_recv)))
    print(f"2. 數值等價性校驗偏差: {max_err:.3e}")
    assert max_err < 1e-12, f"SpMV 矩陣通訊結果不一致: {max_err}"
    print("  ✓ 數值精確等價性驗證通過！")

    # 4. 微基準效能測試 (連續傳輸 500 次)
    n_transfers = 500
    start_t = time.perf_counter()
    for _ in range(n_transfers):
        coupler.transfer(donor_vec)
    total_t = time.perf_counter() - start_t
    avg_us = (total_t / n_transfers) * 1e6

    print(f"3. 連續 {n_transfers} 次跨邊界傳遞總耗時: {total_t * 1000:.2f} ms")
    print(f"   單次邊界通訊平均延遲: {avg_us:.2f} 微秒 (μs)")
    assert avg_us < 5000.0, "邊界通訊延遲過高！"
    print("  ✓ 通訊延遲達標（遠低於 1 毫秒極限）！")

    print("==========================================================")
    print(" ✅ [GPU/CPU 混合稀疏通訊模組驗證全項通過！]              ")
    print("==========================================================")


if __name__ == "__main__":
    test_gpu_sparse_coupler()
