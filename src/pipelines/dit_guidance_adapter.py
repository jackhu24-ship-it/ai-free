"""
PHANToM Grid: DiT Geometric Guidance Adapter
將幾何防禦引擎無縫接入 Diffusion Transformer (DiT / Wan2.1) 去噪主迴圈
"""
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
import torch
import torch.nn as nn

from src.engine.defense_engine import PhantomDefenseEngine, DefenseOutput

@dataclass
class GuidanceOutput:
    guided_latents: torch.Tensor
    metrics: Dict[str, Any]
    sha256_fingerprint: str
    is_damped: bool

class DiTGeometricGuidanceAdapter(nn.Module):
    def __init__(
        self,
        base_guidance_scale: float = 0.15,
        max_grad_norm: float = 1.0,
        latent_channels: int = 16,
        hidden_points: int = 64,
    ):
        super().__init__()
        self.base_guidance_scale = float(base_guidance_scale)
        self.max_grad_norm = float(max_grad_norm)
        self.hidden_points = int(hidden_points)

        self.engine = PhantomDefenseEngine()

        self.spatial_pool = nn.AdaptiveAvgPool2d((4, 4))
        self.proj_fc = nn.Linear(latent_channels * 16, hidden_points * 3)

    def _project_latents_to_points(self, latents: torch.Tensor) -> torch.Tensor:
        B, C, T, H, W = latents.shape
        x = latents.permute(0, 2, 1, 3, 4).contiguous()
        x_flat = x.view(B * T, C, H, W)
        x_pooled = self.spatial_pool(x_flat)
        x_feat = x_pooled.view(B * T, -1)
        
        # 基準平滑時間流形
        t_base = torch.linspace(0, 1, T, device=latents.device).view(1, T, 1, 1).repeat(B, 1, self.hidden_points, 3)
        pts_delta = self.proj_fc(x_feat).view(B, T, self.hidden_points, 3)
        return t_base + pts_delta

    def guide_step(
        self,
        latents: torch.Tensor,
        camera_poses: Optional[torch.Tensor] = None,
        custom_scale: Optional[float] = None,
    ) -> GuidanceOutput:
        if torch.isnan(latents).any() or torch.isinf(latents).any():
            raise ValueError("[DiT Guidance Ingress] 潛變量包含 NaN 或 Inf 異常！")

        latents_in = latents.detach().requires_grad_(True)
        scale = self.base_guidance_scale if custom_scale is None else float(custom_scale)

        # 1. 投影至 3D 幾何流形
        manifold_pts = self._project_latents_to_points(latents_in)

        # 2. 呼叫防禦引擎 SDK
        defense_res: DefenseOutput = self.engine.protect_step(manifold_pts, camera_poses)

        # 3. 幾何損失反向傳播
        loss = defense_res.critic_loss.mean()
        loss.backward()

        grad = latents_in.grad
        if grad is None:
            grad = torch.zeros_like(latents)
        else:
            grad_norm = torch.norm(grad)
            if grad_norm > self.max_grad_norm:
                grad = grad * (self.max_grad_norm / (grad_norm + 1e-6))

        # 4. 幾何阻尼自適應融合
        effective_scale = scale * (1.35 if defense_res.is_damped else 1.0)
        guided_latents = latents - effective_scale * grad.detach()

        metrics = defense_res.metrics
        metrics.update({
            "effective_guidance_scale": effective_scale,
            "grad_norm": torch.norm(grad).item(),
            "loss_val": loss.item(),
        })

        grad.zero_()

        return GuidanceOutput(
            guided_latents=guided_latents,
            metrics=metrics,
            sha256_fingerprint=defense_res.sha256_fingerprint,
            is_damped=defense_res.is_damped,
        )

    def reset_state(self) -> None:
        self.engine.reset_state()
