from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
import torch
import torch.nn as nn

from src.models.spatiotemporal_anchor import SpatiotemporalAnchor4D
from src.models.geodesic_curvature import GeodesicCurvatureEstimator
from src.models.epipolar_critic import EpipolarConsistencyCritic
from src.models.vram_guard_scheduler import VRAMGuardDynamicScheduler, MemoryBackoffReject
from src.governance.zdr_audit import ZDRAuditManager

@dataclass
class DefenseOutput:
    points: torch.Tensor
    critic_loss: torch.Tensor
    metrics: Dict[str, Any]
    sha256_fingerprint: str
    dispatch_mode: str
    is_damped: bool

class PhantomDefenseEngine(nn.Module):
    def __init__(
        self,
        hard_limit_gb: float = 50.0,
        warning_limit_gb: float = 35.0,
        default_chunk_size: int = 2,
        damping_factor: float = 1.35,
        log_dir: str = "logs/audit",
    ):
        super().__init__()
        self.scheduler = VRAMGuardDynamicScheduler(
            hard_limit_gb=hard_limit_gb,
            warning_limit_gb=warning_limit_gb,
            default_chunk_size=default_chunk_size,
        )
        # 使用模組原生預設參數初始化以確保完全相容
        self.anchor = SpatiotemporalAnchor4D(damping_factor=damping_factor)
        self.geodesic = GeodesicCurvatureEstimator(damping_factor=damping_factor)
        self.critic = EpipolarConsistencyCritic(damping_factor=damping_factor)
        self.zdr = ZDRAuditManager(log_dir=log_dir)

    def set_simulated_vram_gb(self, vram_gb: float) -> None:
        self.scheduler.set_simulated_vram_gb(vram_gb)

    def protect_step(
        self,
        points: torch.Tensor,
        camera_poses: Optional[torch.Tensor] = None,
        intermediate_tensors_to_wipe: Optional[list] = None,
    ) -> DefenseOutput:
        device = points.device
        B, T, N, _ = points.shape

        if camera_poses is None:
            camera_poses = torch.eye(4, device=device).unsqueeze(0).repeat(B, T, 1, 1)

        def _step_fn(sub_pts: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, Any]]:
            sub_T = sub_pts.shape[1]
            sub_poses = camera_poses[:, :sub_T]

            _, m_anchor = self.anchor(sub_pts, sub_poses)
            smoothed_pts, m_geodesic = self.geodesic(sub_pts)

            step_metrics = {
                "anchor_ema": m_anchor.get("ema_residual", 0.0),
                "geodesic_curv": m_geodesic.get("mean_curvature", 0.0),
                "anchor_damped": m_anchor.get("is_damped", False),
                "geodesic_damped": m_geodesic.get("is_damped", False),
            }
            return smoothed_pts, step_metrics

        out_pts, metrics = self.scheduler.schedule_execution(_step_fn, points)

        critic_loss, m_critic = self.critic(out_pts, camera_poses)
        metrics["epipolar_loss"] = m_critic.get("mean_residual", 0.0)
        metrics["critic_damped"] = m_critic.get("is_damped", False)

        is_damped = bool(
            metrics.get("anchor_damped", False)
            or metrics.get("geodesic_damped", False)
            or metrics.get("critic_damped", False)
        )

        wipe_list = intermediate_tensors_to_wipe if intermediate_tensors_to_wipe else []
        audit_record = self.zdr.verify_and_audit(
            module_name="PhantomDefenseEngine",
            output_tensor=out_pts,
            metrics=metrics,
            intermediates_to_wipe=wipe_list,
        )

        return DefenseOutput(
            points=out_pts,
            critic_loss=critic_loss,
            metrics=metrics,
            sha256_fingerprint=audit_record["sha256_fingerprint"],
            dispatch_mode=metrics.get("dispatch_mode", "DIRECT"),
            is_damped=is_damped,
        )

    def reset_state(self) -> None:
        self.scheduler.reset_state()
        self.anchor.reset_state()
        self.geodesic.reset_state()
        self.critic.reset_state()
