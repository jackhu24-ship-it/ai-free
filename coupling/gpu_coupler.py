# -*- coding: utf-8 -*-
"""
coupling/gpu_coupler.py - 跨網格稀疏通訊 GPU 加速遷移與優雅降級模組
==================================================================
支援利用 GPU (CuPy / cupyx.scipy.sparse.csr_matrix) 加速重疊邊界插值矩陣運算 u_recv = W * u_donor。
若當前主機無 NVIDIA GPU 或未安裝 cupy，則自動且透明地降級為 CPU SciPy CSR 矩陣，
兼顧競賽伺服器極致算力加速與各平台 100% 無縫相容性。
"""
from typing import Optional, Tuple
import numpy as np
from scipy.sparse import csr_matrix

try:
    import cupy as cp
    import cupyx.scipy.sparse as csp
    HAS_GPU = True
except ImportError:
    HAS_GPU = False


class GPUSparseOversetCoupler:
    """
    支援 GPU (CuPy) 與 CPU (SciPy) 混合架構的跨網格邊界插值加速器。
    """

    def __init__(self, cpu_csr_matrix: csr_matrix, prefer_gpu: bool = True):
        self.cpu_W = cpu_csr_matrix
        self.is_gpu = HAS_GPU and prefer_gpu
        self.gpu_W = None

        if self.is_gpu:
            try:
                # 將 CPU CSR 稀疏矩陣上傳至 GPU VRAM
                self.gpu_W = csp.csr_matrix(cpu_csr_matrix)
            except Exception as e:
                print(f"[GPUSparseOversetCoupler] GPU 初始化失敗，降級至 CPU: {e}")
                self.is_gpu = False

    def get_backend_name(self) -> str:
        return "GPU (cupyx.scipy.sparse)" if self.is_gpu else "CPU (scipy.sparse)"

    def transfer(self, donor_flat: np.ndarray) -> np.ndarray:
        """
        執行 SpMV 稀疏矩陣乘法運算: u_recv = W * u_donor
        """
        if self.is_gpu and self.gpu_W is not None:
            # 1. 將供體向量傳輸至 GPU
            donor_gpu = cp.asarray(donor_flat, dtype=cp.float64)
            # 2. GPU 極速矩陣乘法 (SpMV)
            recv_gpu = self.gpu_W.dot(donor_gpu)
            # 3. 異步傳回 Host 主記憶體
            return cp.asnumpy(recv_gpu)
        else:
            # CPU 高效 SciPy CSR SpMV
            return self.cpu_W.dot(donor_flat)
