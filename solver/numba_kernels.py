# -*- coding: utf-8 -*-
"""
solver/numba_kernels.py - Numba 多執行緒平行 JIT 編譯核心運算元
=============================================================
利用 numba.njit(parallel=True, fastmath=True) 消除 Python 直譯循環開銷，
壓榨 CPU 多核心 SIMD 向量化極限，加速重疊網格拉普拉斯差分與偏微分方程推進。
"""
import numpy as np
from numba import njit, prange


@njit(parallel=True, fastmath=True)
def laplacian_2d_cartesian_numba(
    u: np.ndarray,
    dx: float,
    dy: float,
    active_mask: np.ndarray
) -> np.ndarray:
    """
    JIT 加速 2D 笛卡爾五點中心差分拉普拉斯運算元:
    lap(u) = (u_{i+1, j} - 2 u_{i, j} + u_{i-1, j}) / dx^2 + (u_{i, j+1} - 2 u_{i, j} + u_{i, j-1}) / dy^2
    僅對 active_mask == True (即 FIELD) 節點計算，HOLE/RECEIVER 自動隔離。
    """
    nx, ny = u.shape
    lap = np.zeros((nx, ny), dtype=np.float64)
    inv_dx2 = 1.0 / (dx * dx)
    inv_dy2 = 1.0 / (dy * dy)

    for i in prange(1, nx - 1):
        for j in range(1, ny - 1):
            if active_mask[i, j]:
                d2u_dx2 = (u[i + 1, j] - 2.0 * u[i, j] + u[i - 1, j]) * inv_dx2
                d2u_dy2 = (u[i, j + 1] - 2.0 * u[i, j] + u[i, j - 1]) * inv_dy2
                lap[i, j] = d2u_dx2 + d2u_dy2

    return lap


@njit(parallel=True, fastmath=True)
def step_wave_2d_numba(
    u: np.ndarray,
    v: np.ndarray,
    dt: float,
    c: float,
    dx: float,
    dy: float,
    active_mask: np.ndarray
) -> None:
    """
    JIT 加速 2D 二階波動方程式 Symplectic Euler 時間步推進:
    1. 同步計算所有活躍節點之拉普拉斯差分 lap(u^n)
    2. 更新速度場 v^{n+1} = v^n + dt * c^2 * lap(u^n)
    3. 更新位移場 u^{n+1} = u^n + dt * v^{n+1}
    """
    nx, ny = u.shape
    lap = np.zeros((nx, ny), dtype=np.float64)
    inv_dx2 = 1.0 / (dx * dx)
    inv_dy2 = 1.0 / (dy * dy)
    c2_dt = (c * c) * dt

    # 階段 1: 計算全域拉普拉斯差分 (嚴格依據 u^n)
    for i in prange(1, nx - 1):
        for j in range(1, ny - 1):
            if active_mask[i, j]:
                d2u_dx2 = (u[i + 1, j] - 2.0 * u[i, j] + u[i - 1, j]) * inv_dx2
                d2u_dy2 = (u[i, j + 1] - 2.0 * u[i, j] + u[i, j - 1]) * inv_dy2
                lap[i, j] = d2u_dx2 + d2u_dy2

    # 階段 2: 同步更新速度場 v 與位移場 u
    for i in prange(1, nx - 1):
        for j in range(1, ny - 1):
            if active_mask[i, j]:
                new_v = v[i, j] + c2_dt * lap[i, j]
                v[i, j] = new_v
                u[i, j] += dt * new_v


@njit(parallel=True, fastmath=True)
def curvilinear_step_wave_numba(
    u: np.ndarray,
    v: np.ndarray,
    dt: float,
    c: float,
    J_safe: np.ndarray,
    g11: np.ndarray,
    g12: np.ndarray,
    g22: np.ndarray,
    active_mask: np.ndarray
) -> None:
    """
    JIT 加速貼體曲面座標強守恆型 2D 二階波動方程式推進:
    div(grad u) = 1/J [ d/d_xi (J (g11 u_xi + g12 u_eta)) + d/d_eta (J (g12 u_xi + g22 u_eta)) ]
    """
    n_xi, n_eta = u.shape
    c2_dt = (c * c) * dt

    u_xi = np.zeros((n_xi, n_eta), dtype=np.float64)
    u_eta = np.zeros((n_xi, n_eta), dtype=np.float64)

    for i in prange(1, n_xi - 1):
        for j in range(n_eta):
            u_xi[i, j] = 0.5 * (u[i + 1, j] - u[i - 1, j])

    for i in prange(n_xi):
        for j in range(1, n_eta - 1):
            u_eta[i, j] = 0.5 * (u[i, j + 1] - u[i, j - 1])

    flux_xi = np.zeros((n_xi, n_eta), dtype=np.float64)
    flux_eta = np.zeros((n_xi, n_eta), dtype=np.float64)

    for i in prange(n_xi):
        for j in range(n_eta):
            J_val = J_safe[i, j]
            flux_xi[i, j] = J_val * (g11[i, j] * u_xi[i, j] + g12[i, j] * u_eta[i, j])
            flux_eta[i, j] = J_val * (g12[i, j] * u_xi[i, j] + g22[i, j] * u_eta[i, j])

    for i in prange(1, n_xi - 1):
        for j in range(1, n_eta - 1):
            if active_mask[i, j]:
                d_flux_xi = 0.5 * (flux_xi[i + 1, j] - flux_xi[i - 1, j])
                d_flux_eta = 0.5 * (flux_eta[i, j + 1] - flux_eta[i, j - 1])
                lap = (d_flux_xi + d_flux_eta) / J_safe[i, j]

                new_v = v[i, j] + c2_dt * lap
                v[i, j] = new_v
                u[i, j] += dt * new_v


@njit(parallel=True, fastmath=True)
def fast_bilinear_sample_numba(
    src_data: np.ndarray,
    x_min: float,
    dx: float,
    y_min: float,
    dy: float,
    query_x: np.ndarray,
    query_y: np.ndarray
) -> np.ndarray:
    """
    JIT 加速多點批次雙線性插值採樣 (Batch Bilinear Interpolator):
    直接將世界座標點陣列 (query_x, query_y) 映射至規則供體網格並向量化插值。
    """
    n_pts = query_x.shape[0]
    nx, ny = src_data.shape
    out = np.zeros(n_pts, dtype=np.float64)

    for p in prange(n_pts):
        qx = query_x[p]
        qy = query_y[p]

        # 計算標準化局部坐標 (xi, eta)
        xi = (qx - x_min) / dx
        eta = (qy - y_min) / dy

        i = int(np.floor(xi))
        j = int(np.floor(eta))

        # 邊界保護防越界
        if 0 <= i < nx - 1 and 0 <= j < ny - 1:
            u_frac = xi - i
            v_frac = eta - j

            f00 = src_data[i, j]
            f10 = src_data[i + 1, j]
            f01 = src_data[i, j + 1]
            f11 = src_data[i + 1, j + 1]

            val = (
                (1.0 - u_frac) * (1.0 - v_frac) * f00
                + u_frac * (1.0 - v_frac) * f10
                + (1.0 - u_frac) * v_frac * f01
                + u_frac * v_frac * f11
            )
            out[p] = val

    return out
