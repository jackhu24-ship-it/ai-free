import torch
import torch.nn as nn

class SpatiotemporalAnchor4D(nn.Module):
    """
    PHANToM Grid: 4D 時空流形錨定器 (融合 se(3) 測地度量、EMA 阻尼平滑與連續逃生計數器)
    """
    def __init__(self, damping_factor: float = 1.35, max_curvature_threshold: float = 0.08, ema_alpha: float = 0.2, max_fallback_frames: int = 10):
        super().__init__()
        self.damping_factor = damping_factor
        self.max_curvature_threshold = max_curvature_threshold
        self.ema_alpha = ema_alpha
        self.max_fallback_frames = max_fallback_frames
        
        self.spatiotemporal_proj = nn.Linear(3, 32)
        self.temporal_fusion = nn.GRU(32, 64, batch_first=True)
        
        self.register_buffer("ema_residual", torch.tensor(0.0))
        self.fallback_counter = 0

    def verify_and_project_so3(self, R: torch.Tensor) -> torch.Tensor:
        det = torch.linalg.det(R)
        drift = torch.abs(det - 1.0)
        if torch.any(drift > 1e-4):
            U, _, Vh = torch.linalg.svd(R)
            return torch.matmul(U, Vh)
        return R

    def compute_geodesic_curvature(self, R_seq: torch.Tensor) -> torch.Tensor:
        B, T, _, _ = R_seq.shape
        if T < 2:
            return torch.zeros((B, 1), device=R_seq.device, dtype=R_seq.dtype)
        R1 = R_seq[:, :-1]
        R2 = R_seq[:, 1:]
        R_rel = torch.matmul(R1.transpose(-1, -2), R2)
        tr = R_rel[..., 0, 0] + R_rel[..., 1, 1] + R_rel[..., 2, 2]
        cos_theta = torch.clamp((tr - 1.0) / 2.0, -1.0 + 1e-7, 1.0 - 1e-7)
        return torch.acos(cos_theta)

    def forward(self, points: torch.Tensor, poses: torch.Tensor):
        B, T, N, _ = points.shape
        R_seq = poses[:, :, :3, :3]
        t_seq = poses[:, :, :3, 3]

        R_seq_clean = self.verify_and_project_so3(R_seq)
        curv_raw = self.compute_geodesic_curvature(R_seq_clean)
        max_curv = torch.max(curv_raw)

        # 建議 2: EMA 平滑更新阻尼殘差，消除震盪
        current_res = max_curv.detach()
        self.ema_residual = (1.0 - self.ema_alpha) * self.ema_residual + self.ema_alpha * current_res

        is_damped = False
        is_fallback = False
        effective_damping = 1.0

        if self.ema_residual > 0.20:
            is_fallback = True
            self.fallback_counter += 1
        elif self.ema_residual > self.max_curvature_threshold:
            is_damped = True
            effective_damping = self.damping_factor
            self.fallback_counter = 0
        else:
            self.fallback_counter = 0

        # 建議 3: 連續逃生計數器 (N > 10 觸發重置警告)
        needs_reinit = self.fallback_counter >= self.max_fallback_frames

        point_centroids = points.mean(dim=2)
        spatiotemporal_coords = (point_centroids + t_seq) / effective_damping
        proj = self.spatiotemporal_proj(spatiotemporal_coords)
        out_features, _ = self.temporal_fusion(proj)

        metrics = {
            "raw_curvature": max_curv.item(),
            "ema_residual": self.ema_residual.item(),
            "is_damped": is_damped,
            "is_fallback": is_fallback,
            "damping_applied": effective_damping,
            "fallback_counter": self.fallback_counter,
            "needs_reinit": needs_reinit,
            "det_error_max": torch.max(torch.abs(torch.linalg.det(R_seq_clean) - 1.0)).item()
        }
        return out_features, metrics

