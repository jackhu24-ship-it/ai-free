import sys
from pathlib import Path

ROOT_DIR = Path.cwd()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import torch

from src.models.epipolar_critic import EpipolarConsistencyCritic


def run_tests():
    print("\n" + "=" * 65)
    print(">> PHANToM Grid: 對極幾何 Critic (Epipolar Critic) 升級驗收 <<")
    print("=" * 65)

    critic = EpipolarConsistencyCritic(
        damping_factor=1.35, max_residual_threshold=0.08, ema_alpha=0.3, max_fallback_frames=5
    )
    B, T, N = 2, 5, 64

    # 基準恆等外參與點雲
    points = torch.randn(B, T, N, 3, requires_grad=True)
    poses = torch.eye(4).unsqueeze(0).repeat(B, T, 1, 1)

    # Task 1: 基準靜態/恆等相機軌跡
    out1, m1 = critic(points, poses)
    assert not m1["is_damped"]
    print(
        f"[TASK 1: PASS] 靜態基準通過 | 對極殘差: {m1['mean_residual']:.4f} | EMA: {m1['ema_residual']:.4f}"
    )

    # Task 2: 注入旋轉擾動使對極約束失諧，觸發 1.35x 剛性阻尼
    poses_turbulent = poses.clone()
    poses_turbulent[:, 1:, :3, 3] += 1.5  # 加入位移
    poses_turbulent[:, 1:, 0, 0] = torch.cos(torch.tensor(0.5))
    poses_turbulent[:, 1:, 0, 1] = -torch.sin(torch.tensor(0.5))
    poses_turbulent[:, 1:, 1, 0] = torch.sin(torch.tensor(0.5))
    poses_turbulent[:, 1:, 1, 1] = torch.cos(torch.tensor(0.5))

    out2, m2 = critic(points, poses_turbulent)
    assert m2["is_damped"]
    print(
        f"[TASK 2: PASS] 幾何失諧阻尼介入 | 對極殘差: {m2['mean_residual']:.4f} -> 阻尼: {m2['damping_applied']}x"
    )

    # Task 3: 逃生計數器熔斷重置
    reset_happened = False
    for _ in range(5):
        _, m = critic(points, poses_turbulent)
        if m["reset_triggered"]:
            reset_happened = True
            break
    assert reset_happened, "連續擾動未成功觸發重啟熔斷！"
    print("[TASK 3: PASS] 逃生計數器累計觸發 | 重啟標記: True (計數已觸發歸零)")

    # Task 4: 反向傳播閉環梯度驗證
    loss = out2.sum()
    loss.backward()
    assert points.grad is not None
    grad_norm = points.grad.norm().item()
    print(f"[TASK 4: PASS] 研究模式反向傳播閉環完好 | 梯度範數: {grad_norm:.4f}")

    print("=" * 65)
    print("🎉 [ ALL 4 ENHANCED TASKS PASSED - UPGRADE SUCCESSFUL ]")
    print("=" * 65)


if __name__ == "__main__":
    run_tests()
