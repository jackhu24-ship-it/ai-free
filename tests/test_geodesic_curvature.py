import sys
from pathlib import Path

ROOT_DIR = Path.cwd()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import torch

from src.models.geodesic_curvature import GeodesicCurvatureEstimator


def run_tests():
    print("\n" + "=" * 65)
    print(">> PHANToM Grid: 測地曲率估算器 (Geodesic Curvature) 升級驗收 <<")
    print("=" * 65)

    estimator = GeodesicCurvatureEstimator(
        damping_factor=1.35, max_curvature_threshold=0.08, ema_alpha=0.3, max_fallback_frames=5
    )
    B, T, N = 2, 6, 64

    # Task 1: 基準平滑軌跡
    t_steps = torch.linspace(0, 1, T).view(1, T, 1, 1).repeat(B, 1, N, 3)
    points_linear = t_steps + torch.randn(B, 1, N, 3) * 0.0001
    points_linear.requires_grad_(True)
    out1, m1 = estimator(points_linear)
    assert not m1["is_damped"]
    print(
        f"[TASK 1: PASS] 線性軌跡平穩通過 | 平均曲率: {m1['mean_curvature']:.4f} | EMA: {m1['ema_curvature']:.4f}"
    )

    # Task 2: 注入曲率擾動
    points_turbulent = points_linear.detach().clone()
    points_turbulent[:, 2:4] += torch.randn_like(points_turbulent[:, 2:4]) * 0.5
    out2, m2 = estimator(points_turbulent)
    assert m2["is_damped"]
    print(
        f"[TASK 2: PASS] 曲率突變阻尼介入 | 平均曲率: {m2['mean_curvature']:.4f} -> 阻尼: {m2['damping_applied']}x"
    )

    # Task 3: 逃生計數器熔斷重置 (驗證累計達標時成功觸發重啟)
    reset_happened = False
    for _ in range(5):
        _, m = estimator(points_turbulent)
        if m["reset_triggered"]:
            reset_happened = True
            break

    assert reset_happened, "連續擾動未成功觸發重啟熔斷！"
    print("[TASK 3: PASS] 逃生計數器累計觸發 | 重啟標記: True (計數已觸發歸零)")

    # Task 4: 反向傳播閉環
    loss = out1.sum()
    loss.backward()
    assert points_linear.grad is not None
    grad_norm = points_linear.grad.norm().item()
    print(f"[TASK 4: PASS] 研究模式反向傳播閉環完好 | 梯度範數: {grad_norm:.4f}")

    print("=" * 65)
    print("🎉 [ ALL 4 ENHANCED TASKS PASSED - UPGRADE SUCCESSFUL ]")
    print("=" * 65)


if __name__ == "__main__":
    run_tests()
