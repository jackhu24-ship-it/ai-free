"""
PHANToM Grid: 4D Spatiotemporal Anchor Pipeline Adapter
支援 Non-Default CUDA Stream 雙流並行計算與事件握手機制。
"""
from typing import Dict, Optional, Tuple
import torch
import torch.nn as nn
from src.models.spatiotemporal_anchor import SpatiotemporalAnchor4D


class AnchorPipelineAdapter(nn.Module):
    def __init__(
        self,
        damping_factor: float = 1.35,
        max_curvature_threshold: float = 0.08,
        ema_alpha: float = 0.3,
        max_fallback_frames: int = 5,
        enable_cuda_stream: bool = True,
    ):
        super().__init__()
        self.anchor = SpatiotemporalAnchor4D(
            damping_factor=damping_factor,
            max_curvature_threshold=max_curvature_threshold,
            ema_alpha=ema_alpha,
            max_fallback_frames=max_fallback_frames,
        )
        self.enable_cuda_stream = enable_cuda_stream and torch.cuda.is_available()
        
        if self.enable_cuda_stream:
            self.anchor_stream = torch.cuda.Stream()
            self.anchor_event = torch.cuda.Event()
        else:
            self.anchor_stream = None
            self.anchor_event = None

    def forward_step(
        self,
        latent_points: torch.Tensor,
        camera_poses: torch.Tensor,
        current_stream: Optional[torch.cuda.Stream] = None,
    ) -> Tuple[torch.Tensor, Dict[str, any]]:
        if not self.enable_cuda_stream or not latent_points.is_cuda:
            return self.anchor(latent_points, camera_poses)

        if current_stream is None:
            current_stream = torch.cuda.current_stream()

        current_stream.record_event(self.anchor_event)

        with torch.cuda.stream(self.anchor_stream):
            self.anchor_stream.wait_event(self.anchor_event)
            out_points, metrics = self.anchor(latent_points, camera_poses)
            self.anchor_stream.record_event(self.anchor_event)

        current_stream.wait_event(self.anchor_event)

        return out_points, metrics

    def reset_state(self):
        if hasattr(self.anchor, "reset_state"):
            self.anchor.reset_state()