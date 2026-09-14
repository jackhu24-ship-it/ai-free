# -*- coding: utf-8 -*-
"""
solver/aeroelastic_flutter.py - 二自由度典型翼段氣動彈性顫振 (Aeroelastic Flutter) 求解器
========================================================================================
基於典型翼段模型 (Typical Section Model)，建立沉浮 (Plunge h) 與俯仰 (Pitch alpha)
二自由度結構運動微分方程，並與 PHANTOM 重疊網格剛體變換引擎 SE(2) 實現雙向流固耦合 (FSI)。
"""
from typing import Dict, Tuple, Optional
import numpy as np
from grids.component_grid import ComponentGrid


class AeroelasticFlutterSolver:
    """二自由度翼型氣動彈性顫振動力學求解器"""

    def __init__(
        self,
        chord: float = 1.0,
        mass: float = 10.0,            # 結構質量 m (kg)
        I_alpha: float = 1.0,          # 繞彈性軸轉動慣量 (kg*m^2)
        x_alpha: float = 0.2,          # 重心與彈性軸無因次距離 (x_alpha * b)
        omega_h: float = 10.0,         # 沉浮固有角頻率 (rad/s)
        omega_alpha: float = 25.0,     # 俯仰固有角頻率 (rad/s)
        zeta_h: float = 0.01,          # 沉浮阻尼比
        zeta_alpha: float = 0.01       # 俯仰阻尼比
    ):
        self.chord = chord
        self.b = 0.5 * chord           # 半弦長 b
        self.mass = mass
        self.I_alpha = I_alpha
        self.x_alpha = x_alpha

        # 剛度係數
        self.k_h = mass * (omega_h ** 2)
        self.k_alpha = I_alpha * (omega_alpha ** 2)

        # 結構阻尼係數
        self.c_h = 2.0 * mass * omega_h * zeta_h
        self.c_alpha = 2.0 * I_alpha * omega_alpha * zeta_alpha

        # 質量矩陣 M = [[m, m*x_alpha*b], [m*x_alpha*b, I_alpha]]
        m_cross = mass * x_alpha * self.b
        self.M = np.array([
            [mass, m_cross],
            [m_cross, I_alpha]
        ], dtype=np.float64)
        self.inv_M = np.linalg.inv(self.M)

        # 狀態向量 [h, h_dot, alpha, alpha_dot]
        # h: 沉浮位移 (向下為正), alpha: 俯仰角 (低頭/抬頭 rad)
        self.state = np.zeros(4, dtype=np.float64)

    @property
    def h(self) -> float:
        return float(self.state[0])

    @property
    def h_dot(self) -> float:
        return float(self.state[1])

    @property
    def alpha(self) -> float:
        return float(self.state[2])

    @property
    def alpha_dot(self) -> float:
        return float(self.state[3])

    def set_initial_conditions(self, h0: float = 0.0, alpha0_rad: float = 0.0) -> None:
        """設置初始擾動位移與攻角"""
        self.state[0] = h0
        self.state[1] = 0.0
        self.state[2] = alpha0_rad
        self.state[3] = 0.0

    def _derivatives(self, state: np.ndarray, Lift: float, Moment_ea: float) -> np.ndarray:
        """計算狀態導數 d/dt [h, h_dot, alpha, alpha_dot]"""
        h = state[0]
        h_dot = state[1]
        alpha = state[2]
        alpha_dot = state[3]

        # 廣義力向量 Q = [-Lift, Moment_ea]
        Q = np.array([-Lift, Moment_ea], dtype=np.float64)

        # 阻尼力與彈性恢復力
        F_damping = np.array([self.c_h * h_dot, self.c_alpha * alpha_dot])
        F_restoring = np.array([self.k_h * h, self.k_alpha * alpha])

        # 加速度 = inv(M) * (Q - F_damping - F_restoring)
        accelerations = self.inv_M.dot(Q - F_damping - F_restoring)

        return np.array([h_dot, accelerations[0], alpha_dot, accelerations[1]], dtype=np.float64)

    def step_rk4(self, dt: float, Lift: float, Moment_ea: float) -> Tuple[float, float, float, float]:
        """採用四階 Runge-Kutta (RK4) 推進氣動彈性結構時間步"""
        k1 = self._derivatives(self.state, Lift, Moment_ea)
        k2 = self._derivatives(self.state + 0.5 * dt * k1, Lift, Moment_ea)
        k3 = self._derivatives(self.state + 0.5 * dt * k2, Lift, Moment_ea)
        k4 = self._derivatives(self.state + dt * k3, Lift, Moment_ea)

        self.state += (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        return (self.h, self.h_dot, self.alpha, self.alpha_dot)

    def update_grid_pose(self, comp_grid: ComponentGrid) -> None:
        """
        將結構計算之 (h, alpha) 姿態同步寫回 PHANTOM 前景網格變換器 (SE2 Transform)
        沉浮 h 對應 y0 偏移，俯仰 alpha 對應 theta 旋轉
        """
        comp_grid.transform.y0 = -self.h  # 沉浮向上定義
        comp_grid.transform.theta = self.alpha
        comp_grid.transform.cos_t = np.cos(self.alpha)
        comp_grid.transform.sin_t = np.sin(self.alpha)
