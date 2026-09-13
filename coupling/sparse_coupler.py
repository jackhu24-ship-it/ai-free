# -*- coding: utf-8 -*-
"""
coupling/sparse_coupler.py - 稀疏矩陣插值運算元 (CSR Matrix Coupler)
========================================================================
將跨網格插值關係預編譯為稀疏矩陣 (scipy.sparse.csr_matrix)，
實現 O(1) 時間步的高速矩陣向量乘法 (SpMV)。
"""
from typing import List, Optional
import numpy as np
from scipy.sparse import csr_matrix
from core.types import CellStatus
from core.base_grid import AbstractGrid
from grids.component_grid import ComponentGrid
from grids.structured_cartesian import StructuredCartesianGrid


from coupling.gpu_coupler import GPUSparseOversetCoupler


class SparseOversetCoupler:
    """將跨網格插值關係預編譯為稀疏矩陣，實現 O(1) 時間步的高速矩陣向量乘法"""

    def __init__(self, donor_grid: AbstractGrid, receiver_grid: AbstractGrid, use_gpu: bool = False):
        self.donor = donor_grid
        self.receiver = receiver_grid
        self.use_gpu = use_gpu
        self.gpu_coupler: Optional[GPUSparseOversetCoupler] = None
        self.weight_matrix: Optional[csr_matrix] = None
        self.receiver_indices_flat: Optional[np.ndarray] = None
        self.build_sparse_operator()

    def build_sparse_operator(self) -> None:
        """組裝 Donor -> Receiver 的雙線性插值稀疏權重矩陣"""
        recv_mask = (self.receiver.status_mask == CellStatus.RECEIVER)
        self.receiver_indices_flat = np.flatnonzero(recv_mask)
        n_recv = len(self.receiver_indices_flat)

        nx, ny = self.donor.nx, self.donor.ny
        n_donor_total = nx * ny

        if n_recv == 0:
            self.weight_matrix = csr_matrix((0, n_donor_total), dtype=np.float64)
            return

        # 1. 取得接收點的世界座標
        X_w, Y_w = self.receiver.get_coordinates()
        x_target = X_w.ravel()[self.receiver_indices_flat]
        y_target = Y_w.ravel()[self.receiver_indices_flat]

        # 2. 供體網格座標正規化
        if isinstance(self.donor, ComponentGrid):
            x_loc, y_loc = self.donor.transform.world_to_local(x_target, y_target)
            xmin, ymin = self.donor.xmin, self.donor.ymin
            dx, dy = self.donor.dx, self.donor.dy
            nx, ny = self.donor.nx, self.donor.ny
        else:
            x_loc, y_loc = x_target, y_target
            xmin, ymin = self.donor.xmin, self.donor.ymin
            dx, dy = self.donor.dx, self.donor.dy
            nx, ny = self.donor.nx, self.donor.ny

        # 3. 計算供體網格的 2D 基礎索引
        i = np.clip(np.floor((x_loc - xmin) / dx).astype(np.int32), 0, nx - 2)
        j = np.clip(np.floor((y_loc - ymin) / dy).astype(np.int32), 0, ny - 2)

        xi = np.clip((x_loc - (xmin + i * dx)) / dx, 0.0, 1.0)
        eta = np.clip((y_loc - (ymin + j * dy)) / dy, 0.0, 1.0)

        # 4. 計算 4 個節點的雙線性權重
        w00 = (1.0 - xi) * (1.0 - eta)
        w10 = xi * (1.0 - eta)
        w01 = (1.0 - xi) * eta
        w11 = xi * eta

        # 5. 將供體 2D 索引 (i, j) 映射為 1D 扁平索引 (保持 'ij' indexing: idx = i * ny + j)
        idx_00 = i * ny + j
        idx_10 = (i + 1) * ny + j
        idx_01 = i * ny + (j + 1)
        idx_11 = (i + 1) * ny + (j + 1)

        # 6. 組裝 COO 格式數據並轉換為 CSR 稀疏矩陣
        rows = np.repeat(np.arange(n_recv, dtype=np.int32), 4)
        cols = np.column_stack([idx_00, idx_10, idx_01, idx_11]).ravel()
        data = np.column_stack([w00, w10, w01, w11]).ravel()

        self.weight_matrix = csr_matrix((data, (rows, cols)), shape=(n_recv, n_donor_total), dtype=np.float64)
        if self.use_gpu:
            self.gpu_coupler = GPUSparseOversetCoupler(self.weight_matrix, prefer_gpu=True)

    def transfer(self, field_name: str) -> None:
        """利用矩陣乘法極速更新接收邊界 (支援 GPU CuPy 與 CPU SciPy)"""
        if self.weight_matrix is None or self.receiver_indices_flat is None or len(self.receiver_indices_flat) == 0:
            return

        donor_flat = self.donor.fields[field_name].ravel()
        if self.use_gpu and self.gpu_coupler is not None:
            # GPU / CuPy SpMV 或優雅降級
            interpolated = self.gpu_coupler.transfer(donor_flat)
        else:
            # CPU CSR SpMV: (n_recv, n_donor) @ (n_donor,) -> (n_recv,)
            interpolated = self.weight_matrix.dot(donor_flat)

        # 向量化寫回 Receiver 邊界
        self.receiver.fields[field_name].ravel()[self.receiver_indices_flat] = interpolated


class SparseCoupler:
    """雙向 CSR 稀疏矩陣重疊網格耦合器 (協同調度封裝)"""

    def __init__(self, bg_grid: AbstractGrid, comp_grid: ComponentGrid, use_gpu: bool = False):
        self.bg_grid = bg_grid
        self.comp_grid = comp_grid
        self.use_gpu = use_gpu
        self.coupler_bg_to_fg: Optional[SparseOversetCoupler] = None
        self.coupler_fg_to_bg: Optional[SparseOversetCoupler] = None
        self.build()

    def build(self) -> None:
        """構建雙向稀疏運算元 (支援 GPU 加速傳輸)"""
        self.coupler_bg_to_fg = SparseOversetCoupler(donor_grid=self.bg_grid, receiver_grid=self.comp_grid, use_gpu=self.use_gpu)
        self.coupler_fg_to_bg = SparseOversetCoupler(donor_grid=self.comp_grid, receiver_grid=self.bg_grid, use_gpu=self.use_gpu)

    @property
    def W_bg_to_comp(self) -> csr_matrix:
        return self.coupler_bg_to_fg.weight_matrix

    @property
    def W_comp_to_bg(self) -> csr_matrix:
        return self.coupler_fg_to_bg.weight_matrix

    @property
    def comp_recv_mask(self) -> np.ndarray:
        return self.comp_grid.status_mask == CellStatus.RECEIVER

    @property
    def bg_recv_mask(self) -> np.ndarray:
        return self.bg_grid.status_mask == CellStatus.RECEIVER

    def exchange_fields(self, field_names: List[str]) -> None:
        """利用 CSR 稀疏矩陣 SpMV 同步所有指定物理場"""
        for field in field_names:
            if self.coupler_bg_to_fg is not None:
                self.coupler_bg_to_fg.transfer(field)
            if self.coupler_fg_to_bg is not None:
                self.coupler_fg_to_bg.transfer(field)

    def get_sparsity_info(self) -> dict:
        """回傳雙向矩陣之規模與稀疏度統計"""
        bg_total = self.bg_grid.nx * self.bg_grid.ny
        comp_total = self.comp_grid.nx * self.comp_grid.ny

        W1 = self.W_bg_to_comp
        W2 = self.W_comp_to_bg

        nnz1 = W1.nnz if W1 is not None else 0
        nnz2 = W2.nnz if W2 is not None else 0

        tot1 = W1.shape[0] * bg_total if W1 is not None and W1.shape[0] > 0 else 1
        tot2 = W2.shape[0] * comp_total if W2 is not None and W2.shape[0] > 0 else 1

        return {
            "bg_to_comp": {
                "shape": W1.shape if W1 is not None else (0, bg_total),
                "nnz": nnz1,
                "sparsity": 1.0 - (nnz1 / tot1)
            },
            "comp_to_bg": {
                "shape": W2.shape if W2 is not None else (0, comp_total),
                "nnz": nnz2,
                "sparsity": 1.0 - (nnz2 / tot2)
            }
        }
