# -*- coding: utf-8 -*-
"""
solver/fluid_force_integrator.py - 貼體翼面氣動力與力矩沿面積分器
================================================================
沿貼體 O-Grid 翼型內邊界表面進行法向壓力與切向黏性剪應力線積分，
精確求解翼型即時升力係數 (C_L)、阻力係數 (C_D) 與 1/4 弦長俯仰力矩 (C_M)。
"""
from typing import Dict, Tuple, Optional
import numpy as np


class FluidForceIntegrator:
    """貼體翼面氣動力積分運算元"""

    def __init__(self, chord: float = 1.0, rho_inf: float = 1.0, u_inf: float = 1.0):
        self.chord = chord
        self.rho_inf = rho_inf
        self.u_inf = u_inf
        self.q_inf = 0.5 * rho_inf * (u_inf ** 2)

    def integrate_forces(
        self,
        x_wall: np.ndarray,
        y_wall: np.ndarray,
        pressure_wall: np.ndarray,
        shear_wall: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """
        沿閉合翼面節點計算積分升力、阻力與力矩:
        x_wall, y_wall: 翼面座標序列 (順時針或逆時針閉合)
        pressure_wall: 翼面各節點之靜壓場 p(s)
        """
        n_pts = len(x_wall)
        if shear_wall is None:
            shear_wall = np.zeros(n_pts, dtype=np.float64)

        Fx_total = 0.0
        Fy_total = 0.0
        Mz_total = 0.0  # 繞 1/4 弦長 (0.25*c, 0.0) 俯仰力矩

        qc_x = 0.25 * self.chord
        qc_y = 0.0

        for i in range(n_pts - 1):
            dx = x_wall[i + 1] - x_wall[i]
            dy = y_wall[i + 1] - y_wall[i]
            ds = np.hypot(dx, dy)
            if ds < 1e-12:
                continue

            # 面元指向流體之外法向向量 (順時針閉合外法向 n_out = (-dy/ds, dx/ds))
            nx = -dy / ds
            ny = dx / ds

            # 面元中點壓強與剪應力
            p_mid = 0.5 * (pressure_wall[i] + pressure_wall[i + 1])
            tau_mid = 0.5 * (shear_wall[i] + shear_wall[i + 1])

            # 切向向量 t = (dx/ds, dy/ds)
            tx = dx / ds
            ty = dy / ds

            # 壓力貢獻 (朝內) + 黏性剪應力貢獻 (沿切向)
            dFx = (-p_mid * nx + tau_mid * tx) * ds
            dFy = (-p_mid * ny + tau_mid * ty) * ds

            Fx_total += dFx
            Fy_total += dFy

            # 臂長中點 (x_mid - 0.25c, y_mid)
            x_mid = 0.5 * (x_wall[i] + x_wall[i + 1])
            y_mid = 0.5 * (y_wall[i] + y_wall[i + 1])
            rx = x_mid - qc_x
            ry = y_mid - qc_y

            dMz = rx * dFy - ry * dFx
            Mz_total += dMz

        # 無因次係數
        cl = Fy_total / (self.q_inf * self.chord)
        cd = Fx_total / (self.q_inf * self.chord)
        cm = Mz_total / (self.q_inf * (self.chord ** 2))

        return {
            "Fx": float(Fx_total),
            "Fy": float(Fy_total),
            "Mz": float(Mz_total),
            "CL": float(cl),
            "CD": float(cd),
            "CM": float(cm)
        }
