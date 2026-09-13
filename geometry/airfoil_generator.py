# -*- coding: utf-8 -*-
"""
geometry/airfoil_generator.py - NACA 4-Digit 貼體 O 型/C 型網格生成器
===================================================================
提供解析 NACA 翼型外形方程式，並利用幾何代數拉伸法構建近壁面指數加密的高品質貼體 O-Grid。
"""
from typing import Tuple, Optional
import numpy as np


class AirfoilGridGenerator:
    """NACA 翼型貼體曲面網格生成器"""

    @staticmethod
    def naca4_half_thickness(x: np.ndarray, t: float = 0.12) -> np.ndarray:
        """
        NACA 4 位數對稱翼型解析半厚度方程式 (如 NACA 0012, t=0.12)
        最後一項係數設為 -0.1036 以保證後緣 (x=1.0) 嚴格閉合 (y=0)。
        """
        x_clean = np.clip(x, 0.0, 1.0)
        yt = 5.0 * t * (
            0.2969 * np.sqrt(x_clean)
            - 0.1260 * x_clean
            - 0.3516 * (x_clean**2)
            + 0.2843 * (x_clean**3)
            - 0.1036 * (x_clean**4)
        )
        return yt

    @classmethod
    def generate_airfoil_surface(
        cls,
        n_points: int = 121,
        chord: float = 1.0,
        thickness: float = 0.12
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        生成閉合翼型表面點列 (從後緣沿下表面 -> 前緣 -> 上表面 -> 後緣，順時針定向，
        保證與向外拉伸的徑向基底構成右手系正向 Jacobian)。
        """
        if n_points % 2 == 0:
            n_points += 1  # 奇數點使前緣 (x=0) 恰好在中央

        # Cosine 分佈在前緣與後緣加密
        beta = np.linspace(0.0, np.pi, (n_points // 2) + 1)
        x_half = 0.5 * chord * (1.0 - np.cos(beta))
        yt_half = cls.naca4_half_thickness(x_half / chord, t=thickness) * chord

        # 下表面 (從後緣 x=1 到前緣 x=0)
        x_lower = x_half[::-1]
        y_lower = -yt_half[::-1]

        # 上表面 (從前緣 x=0 到後緣 x=1)
        x_upper = x_half[1:]
        y_upper = yt_half[1:]

        x_surface = np.concatenate([x_lower, x_upper])
        y_surface = np.concatenate([y_lower, y_upper])

        return x_surface, y_surface

    @classmethod
    def generate_o_grid(
        cls,
        n_circumferential: int = 121,
        n_radial: int = 41,
        chord: float = 1.0,
        thickness: float = 0.12,
        r_outer: float = 2.0,
        clustering_ratio: float = 2.5,
        center_offset: Tuple[float, float] = (0.25, 0.0)
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        構建貼體 O 型網格 (O-Grid):
        - 周向 (xi): 沿翼型表面閉合
        - 徑向 (eta): 從翼面 (eta=0) 向外拉伸至遠場外邊界 (eta=1)
        """
        x0, y0 = center_offset

        # 1. 內邊界翼面點
        x_surf, y_surf = cls.generate_airfoil_surface(
            n_points=n_circumferential,
            chord=chord,
            thickness=thickness
        )
        xc = x_surf - x0
        yc = y_surf - y0

        # 2. 外邊界：利用表面點的極角投影外邊界，防止射線交叉
        theta = np.unwrap(np.arctan2(yc, xc))
        x_outer = r_outer * np.cos(theta)
        y_outer = r_outer * np.sin(theta)

        # 3. 徑向非均勻指數拉伸
        s = np.linspace(0.0, 1.0, n_radial)
        r_factor = (np.exp(clustering_ratio * s) - 1.0) / (np.exp(clustering_ratio) - 1.0)

        # 4. 超限插值 TFI 組裝內部場點
        X = np.zeros((n_circumferential, n_radial), dtype=np.float64)
        Y = np.zeros((n_circumferential, n_radial), dtype=np.float64)

        for j in range(n_radial):
            w = r_factor[j]
            X[:, j] = (1.0 - w) * xc + w * x_outer + x0
            Y[:, j] = (1.0 - w) * yc + w * y_outer + y0

        return X, Y
