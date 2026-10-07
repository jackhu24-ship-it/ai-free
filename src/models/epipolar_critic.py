"""
PHANToM Grid: Epipolar Consistency Critic (對極幾何一致性判別器)
規格先行架構：四階段流向、本質矩陣評估、1.35x 剛性懲罰、逃生計數器與 ZDR 接口
"""
from typing import Dict, Tuple
import torch
import torch.nn as nn

class EpipolarConsistencyCritic(nn.Module):
    def __init__(
        self,
        damping_factor: float = 1.35,
        max_residual_threshold: float = 0.08,
        ema_alpha: float = 0.3,
        max_fallback_frames: int = 5,
    ):
        super().__init__()
        self.damping_factor = float(damping_factor)
        self.max_residual_threshold = float(max_residual_threshold)
        self.ema_alpha = float(ema_alpha)
        self.max_fallback_frames = int(max_fallback_frames)

        self.register_buffer("ema_residual", torch.tensor(0.0))
        self.register_buffer("fallback_counter", torch.tensor(0, dtype=torch.long))

    def _phase1_ingress(self, points: torch.Tensor, camera_poses: torch.Tensor) -> None:
        if torch.isnan(points).any() or torch.isinf(points).any():
            raise ValueError("[Phase 1 Ingress] 點雲特徵包含 NaN 或 Inf 異常值！")
        if torch.isnan(camera_poses).any() or torch.isinf(camera_poses).any():
            raise ValueError("[Phase 1 Ingress] 相機外參包含 NaN 或 Inf 異常值！")
        if points.dim() != 4 or points.shape[-1] != 3:
            raise ValueError(f"[Phase 1 Ingress] 點雲維度錯誤，預期 (B, T, N, 3)，實際為 {list(points.shape)}")
        if camera_poses.dim() != 4 or camera_poses.shape[-2:] != (4, 4):
            raise ValueError(f"[Phase 1 Ingress] 外參維度錯誤，預期 (B, T, 4, 4)，實際為 {list(camera_poses.shape)}")

        # 檢驗相機旋轉矩陣 det(R) = 1.0 正交契約
        R = camera_poses[:, :, :3, :3]
        dets = torch.linalg.det(R)
        if not torch.allclose(dets, torch.ones_like(dets), atol=1e-3):
            raise ValueError("[Phase 1 Ingress] 外參旋轉矩陣違反 det(R) = 1.0 正交契約！")

    def _phase3_compute(
        self, points: torch.Tensor, camera_poses: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        # points: (B, T, N, 3), camera_poses: (B, T, 4, 4)
        B, T, N, _ = points.shape
        if T < 2:
            residuals = torch.zeros((B, T, N), device=points.device, dtype=points.dtype)
            return residuals, residuals

        # 取前後相鄰幀
        pts1 = points[:, :-1]  # (B, T-1, N, 3)
        pts2 = points[:, 1:]   # (B, T-1, N, 3)

        R1 = camera_poses[:, :-1, :3, :3]
        t1 = camera_poses[:, :-1, :3, 3:]
        R2 = camera_poses[:, 1:, :3, :3]
        t2 = camera_poses[:, 1:, :3, 3:]

        # 相對變換: R_rel = R2 * R1^T, t_rel = t2 - R_rel * t1
        R_rel = torch.matmul(R2, R1.transpose(-1, -2))
        t_rel = (t2 - torch.matmul(R_rel, t1)).squeeze(-1)  # (B, T-1, 3)

        # 反對稱矩陣 [t_rel]x
        tx = torch.zeros((B, T - 1, 3, 3), device=points.device, dtype=points.dtype)
        tx[..., 0, 1] = -t_rel[..., 2]
        tx[..., 0, 2] = t_rel[..., 1]
        tx[..., 1, 0] = t_rel[..., 2]
        tx[..., 1, 2] = -t_rel[..., 0]
        tx[..., 2, 0] = -t_rel[..., 1]
        tx[..., 2, 1] = t_rel[..., 0]

        # 本質矩陣 E = [t]x * R
        E = torch.matmul(tx, R_rel)  # (B, T-1, 3, 3)

        # 評估對極殘差 |x2^T * E * x1|
        E_expanded = E.unsqueeze(2)  # (B, T-1, 1, 3, 3)
        pts1_un = pts1.unsqueeze(-1) # (B, T-1, N, 3, 1)
        pts2_un = pts2.unsqueeze(-2) # (B, T-1, N, 1, 3)

        epipolar_line = torch.matmul(E_expanded, pts1_un).squeeze(-1) # (B, T-1, N, 3)
        err = torch.abs(torch.matmul(pts2_un, torch.matmul(E_expanded, pts1_un)).squeeze(-1).squeeze(-1))
        norm_line = torch.norm(epipolar_line[..., :2], dim=-1).clamp(min=1e-5)
        residual_pairs = err / norm_line  # (B, T-1, N)

        # 對齊為 (B, T, N)
        residuals = torch.zeros((B, T, N), device=points.device, dtype=points.dtype)
        residuals[:, 1:] = residual_pairs

        return residuals, E

    def _phase4_governance(
        self, residuals: torch.Tensor
    ) -> Tuple[torch.Tensor, Dict[str, any]]:
        mean_res = residuals.mean()

        if self.ema_residual.item() == 0.0:
            self.ema_residual.copy_(mean_res.detach())
        else:
            self.ema_residual.copy_(
                self.ema_alpha * mean_res.detach() + (1.0 - self.ema_alpha) * self.ema_residual
            )

        is_damped = False
        reset_triggered = False

        if mean_res.item() > self.max_residual_threshold:
            is_damped = True
            self.fallback_counter += 1
            # 施加 1.35x 幾何一致性懲罰權重
            critic_loss = residuals * self.damping_factor
        else:
            self.fallback_counter.zero_()
            critic_loss = residuals

        if self.fallback_counter.item() >= self.max_fallback_frames:
            reset_triggered = True
            self.reset_state()

        metrics = {
            "mean_residual": mean_res.item(),
            "ema_residual": self.ema_residual.item(),
            "is_damped": is_damped,
            "damping_applied": self.damping_factor if is_damped else 1.0,
            "fallback_count": self.fallback_counter.item(),
            "reset_triggered": reset_triggered,
        }
        return critic_loss, metrics

    def forward(
        self, points: torch.Tensor, camera_poses: torch.Tensor
    ) -> Tuple[torch.Tensor, Dict[str, any]]:
        self._phase1_ingress(points, camera_poses)
        residuals, _ = self._phase3_compute(points, camera_poses)
        critic_loss, metrics = self._phase4_governance(residuals)
        return critic_loss, metrics

    def reset_state(self) -> None:
        self.ema_residual.zero_()
        self.fallback_counter.zero_()
