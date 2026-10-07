"""
PHANToM Grid: Flow-Match Sampler Scheduler Hook
封裝主流擴散採樣器 (Flow Matching / Euler) 並無縫掛載幾何防禦與顯存熔斷守門
"""
from dataclasses import dataclass
from typing import Any, Dict, Optional
import torch
import torch.nn as nn

from src.pipelines.dit_guidance_adapter import DiTGeometricGuidanceAdapter, GuidanceOutput
from src.governance.zdr_audit import ZDRAuditManager

@dataclass
class HookStepOutput:
    prev_sample: torch.Tensor
    metrics: Dict[str, Any]
    sha256_fingerprint: str
    is_damped: bool

class FlowMatchSamplerSchedulerHook(nn.Module):
    """
    通用流匹配 (Flow Matching / Euler) 採樣排程器幾何防禦 Hook
    """
    def __init__(
        self,
        base_guidance_scale: float = 0.15,
        max_grad_norm: float = 1.0,
        latent_channels: int = 16,
        hidden_points: int = 64,
    ):
        super().__init__()
        self.adapter = DiTGeometricGuidanceAdapter(
            base_guidance_scale=base_guidance_scale,
            max_grad_norm=max_grad_norm,
            latent_channels=latent_channels,
            hidden_points=hidden_points,
        )
        self.zdr = ZDRAuditManager()

    def step(
        self,
        model_output: torch.Tensor,
        timestep: float,
        sample: torch.Tensor,
        camera_poses: Optional[torch.Tensor] = None,
        dt: float = -0.05,
    ) -> HookStepOutput:
        """
        執行標準單步流匹配數值更新，並自動進行幾何引導防禦
        x_{t+dt} = x_t + dt * v(x_t, t)
        """
        if torch.isnan(model_output).any() or torch.isnan(sample).any():
            raise ValueError("[SchedulerHook Ingress] 輸入張量包含 NaN！")

        # 1. Flow-Matching Euler 積分步進
        candidate_prev = sample + dt * model_output

        # 2. 幾何轉接器進行流形防禦與潛變量修正
        guidance_res: GuidanceOutput = self.adapter.guide_step(
            latents=candidate_prev,
            camera_poses=camera_poses,
        )

        metrics = guidance_res.metrics
        metrics.update({
            "timestep": float(timestep),
            "dt": float(dt),
        })

        return HookStepOutput(
            prev_sample=guidance_res.guided_latents,
            metrics=metrics,
            sha256_fingerprint=guidance_res.sha256_fingerprint,
            is_damped=guidance_res.is_damped,
        )

    def reset_state(self) -> None:
        self.adapter.reset_state()
