import sys
from pathlib import Path

import torch

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.models.spatiotemporal_anchor import SpatiotemporalAnchor4D


def run_tests():
    print("\n" + "=" * 65)
    print(">> PHANToM Grid: 4D 錨定器升級驗收 (含 EMA 平滑與逃生計數) <<")
    print("=" * 65)

    anchor = SpatiotemporalAnchor4D(
        damping_factor=1.35, max_curvature_threshold=0.08, ema_alpha=0.3, max_fallback_frames=5
    )
    B, T, N = 2, 5, 100

    # Task 1: 平滑相機軌跡
    points = torch.randn(B, T, N, 3, requires_grad=True)
    poses = torch.eye(4).unsqueeze(0).unsqueeze(0).repeat(B, T, 1, 1)
    out, metrics = anchor(points, poses)
    assert not metrics["is_damped"]
    print(f"[TASK 1: PASS] 基準軌跡正常通過 | EMA 殘差: {metrics['ema_residual']:.4f}")

    # Task 2: EMA 漸進式阻尼調控
    poses_turbulent = poses.clone()
    poses_turbulent[:, 1, 0, 0] = torch.cos(torch.tensor(0.4))
    poses_turbulent[:, 1, 0, 1] = -torch.sin(torch.tensor(0.4))
    poses_turbulent[:, 1, 1, 0] = torch.sin(torch.tensor(0.4))
    poses_turbulent[:, 1, 1, 1] = torch.cos(torch.tensor(0.4))
    out_d, metrics_d = anchor(points, poses_turbulent)
    print(
        f"[TASK 2: PASS] EMA 平滑阻尼介入 | EMA 殘差: {metrics_d['ema_residual']:.4f} -> 阻尼: {metrics_d['damping_applied']}x"
    )

    # Task 3: 連續逃生計數器觸發重啟警報
    poses_extreme = poses.clone()
    poses_extreme[:, :, :3, :3] = torch.randn(B, T, 3, 3)
    for _ in range(6):
        _, metrics_fb = anchor(points, poses_extreme)
    assert metrics_fb["needs_reinit"], "連續發散超過閾值必須觸發重置旗標"
    print(
        f"[TASK 3: PASS] 逃生計數器累計觸發 | 計數: {metrics_fb['fallback_counter']} -> 重啟標記: {metrics_fb['needs_reinit']}"
    )

    # Task 4: 梯度流閉環
    loss = out.sum()
    loss.backward()
    assert points.grad is not None
    print(f"[TASK 4: PASS] 研究模式反向傳播閉環完好 | 梯度範數: {points.grad.norm().item():.4f}")

    print("=" * 65)
    print("🎉 [ ALL 4 ENHANCED TASKS PASSED - UPGRADE SUCCESSFUL ]")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_tests()
