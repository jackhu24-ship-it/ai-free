# -*- coding: utf-8 -*-
"""
geometry/airfoil.py - NACA 4 位數翼型輪廓幾何生成器
===================================================
提供解析 NACA 4-Digit 幾何曲線生成功能，以 Cosine 分佈精確解析前緣與後緣。
"""
import numpy as np
from typing import Tuple


class NACA4Airfoil:
    """生成 NACA 4-digit 翼型幾何曲線"""

    @staticmethod
    def generate_contour(
        n_points: int = 100,
        thickness: float = 0.12,
        chord: float = 1.0
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        生成順時針閉合翼型座標 (從後緣出發經下翼面、前緣再回後緣)。

        參數:
            n_points: 翼面上/下表面的離散點數
            thickness: 最大相對厚度 (例如 0.12 代表 NACA 0012)
            chord: 翼弦長
        """
        # 採用餘弦分佈 (Cosine Clustering) 確保前緣曲率大處具有足夠解析度
        beta = np.linspace(0.0, np.pi, n_points)
        x = (chord / 2.0) * (1.0 - np.cos(beta))

        # NACA 4-digit 對稱厚度分佈公式
        yt = 5.0 * thickness * chord * (
            0.2969 * np.sqrt(x / chord)
            - 0.1260 * (x / chord)
            - 0.3516 * (x / chord)**2
            + 0.2843 * (x / chord)**3
            - 0.1015 * (x / chord)**4  # 0.1036 可強制後緣完全閉合，此處取經典係數
        )

        # 組合上下表面 (後緣 -> 下翼面 -> 前緣 -> 上翼面 -> 後緣)
        x_lower = x[::-1]
        y_lower = -yt[::-1]
        x_upper = x[1:]
        y_upper = yt[1:]

        x_coords = np.concatenate([x_lower, x_upper])
        y_coords = np.concatenate([y_lower, y_upper])

        # 強制最後一點封閉回起點
        x_coords = np.append(x_coords, x_coords[0])
        y_coords = np.append(y_coords, y_coords[0])

        return x_coords, y_coords
