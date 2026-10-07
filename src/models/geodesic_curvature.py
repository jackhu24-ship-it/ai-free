from typing import Dict, Tuple
import torch
import torch.nn as nn

class GeodesicCurvatureEstimator(nn.Module):
    def __init__(
        self,
        damping_factor: float = 1.35,
        max_curvature_threshold: float = 0.08,
        ema_alpha: float = 0.3,
        max_fallback_frames: int = 5,
    ):
        super().__init__()
        self.damping_factor = float(damping_factor)
        self.max_curvature_threshold = float(max_curvature_threshold)
        self.ema_alpha = float(ema_alpha)
        self.max_fallback_frames = int(max_fallback_frames)

        self.register_buffer("ema_curvature", torch.tensor(0.0))
        self.register_buffer("fallback_counter", torch.tensor(0, dtype=torch.long))

    def _phase1_ingress(self, points: torch.Tensor) -> None:
        if torch.isnan(points).any() or torch.isinf(points).any():
            raise ValueError("[Phase 1 Ingress] 輸入特徵包含 NaN 或 Inf 異常值！")
        if points.dim() != 4 or points.shape[-1] != 3:
            raise ValueError(f"[Phase 1 Ingress] 形狀契約錯誤，預期 (B, T, N, 3)，實際為 {list(points.shape)}")

    def _phase3_compute(self, points: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        B, T, N, _ = points.shape
        if T < 3:
            curvatures = torch.zeros((B, T, N), device=points.device, dtype=points.dtype)
            return points, curvatures

        v = points[:, 1:] - points[:, :-1]
        a = v[:, 1:] - v[:, :-1]

        v_norm_sq = torch.sum(v[:, :-1] ** 2, dim=-1).clamp(min=1e-6)
        a_norm = torch.norm(a, dim=-1)
        curv = a_norm / v_norm_sq

        curvatures = torch.zeros((B, T, N), device=points.device, dtype=points.dtype)
        curvatures[:, 1:-1] = curv
        return points, curvatures

    def _phase4_governance(
        self, points: torch.Tensor, curvatures: torch.Tensor
    ) -> Tuple[torch.Tensor, Dict[str, any]]:
        mean_curv = curvatures.mean()
        
        if self.ema_curvature.item() == 0.0:
            self.ema_curvature.copy_(mean_curv.detach())
        else:
            self.ema_curvature.copy_(
                self.ema_alpha * mean_curv.detach() + (1.0 - self.ema_alpha) * self.ema_curvature
            )

        is_damped = False
        reset_triggered = False

        if mean_curv.item() > self.max_curvature_threshold:
            is_damped = True
            self.fallback_counter += 1
            smoothed_points = points / self.damping_factor
        else:
            self.fallback_counter.zero_()
            smoothed_points = points

        if self.fallback_counter.item() >= self.max_fallback_frames:
            reset_triggered = True
            self.reset_state()

        metrics = {
            "mean_curvature": mean_curv.item(),
            "ema_curvature": self.ema_curvature.item(),
            "is_damped": is_damped,
            "damping_applied": self.damping_factor if is_damped else 1.0,
            "fallback_count": self.fallback_counter.item(),
            "reset_triggered": reset_triggered,
        }
        return smoothed_points, metrics

    def forward(self, points: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, any]]:
        self._phase1_ingress(points)
        pts, curvatures = self._phase3_compute(points)
        out_points, metrics = self._phase4_governance(pts, curvatures)
        return out_points, metrics

    def reset_state(self) -> None:
        self.ema_curvature.zero_()
        self.fallback_counter.zero_()
