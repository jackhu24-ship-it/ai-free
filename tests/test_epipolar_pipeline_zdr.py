import sys
from pathlib import Path

ROOT_DIR = Path.cwd()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from typing import Dict, Optional, Tuple

import torch
import torch.nn as nn

from src.governance.zdr_audit import ZDRAuditManager
from src.models.epipolar_critic import EpipolarConsistencyCritic


class EpipolarPipelineAdapter(nn.Module):
    """對極幾何 Critic 主管線雙流適配器"""

    def __init__(
        self,
        damping_factor=1.35,
        max_residual_threshold=0.08,
        ema_alpha=0.3,
        max_fallback_frames=5,
        enable_cuda_stream=True,
    ):
        super().__init__()
        self.critic = EpipolarConsistencyCritic(
            damping_factor=damping_factor,
            max_residual_threshold=max_residual_threshold,
            ema_alpha=ema_alpha,
            max_fallback_frames=max_fallback_frames,
        )
        self.enable_cuda_stream = enable_cuda_stream and torch.cuda.is_available()
        if self.enable_cuda_stream:
            self.stream = torch.cuda.Stream()
            self.event = torch.cuda.Event()
        else:
            self.stream = None
            self.event = None

    def forward_step(
        self,
        points: torch.Tensor,
        camera_poses: torch.Tensor,
        current_stream: Optional[torch.cuda.Stream] = None,
    ) -> Tuple[torch.Tensor, Dict[str, any]]:
        if not self.enable_cuda_stream or not points.is_cuda:
            return self.critic(points, camera_poses)

        if current_stream is None:
            current_stream = torch.cuda.current_stream()

        current_stream.record_event(self.event)
        with torch.cuda.stream(self.stream):
            self.stream.wait_event(self.event)
            critic_loss, metrics = self.critic(points, camera_poses)
            self.stream.record_event(self.event)

        current_stream.wait_event(self.event)
        return critic_loss, metrics


def test_epipolar_pipeline_and_zdr():
    print("\n" + "=" * 60)
    print(">> PHANToM Grid: 對極 Critic 雙流適配與 ZDR/SHA-256 審計驗收 <<")
    print("=" * 60)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    adapter = EpipolarPipelineAdapter().to(device)
    zdr = ZDRAuditManager()

    B, T, N = 2, 5, 64
    points = torch.randn(B, T, N, 3, device=device)
    poses = torch.eye(4, device=device).unsqueeze(0).repeat(B, T, 1, 1)

    # 模擬建立中介本質矩陣與外參差分緩衝區
    intermediate_E = torch.randn(B, T - 1, 3, 3, device=device)
    zdr.register_intermediate(intermediate_E)

    # 執行主管線前向運算
    out, metrics = adapter.forward_step(points, poses)

    # 執行 ZDR 物理清零與 SHA-256 狀態簽署
    audit_res = zdr.verify_and_audit(
        module_name="EpipolarConsistencyCritic",
        output_tensor=out,
        metrics=metrics,
        intermediates_to_wipe=[intermediate_E],
    )

    # 斷言驗收條件
    assert out.shape == (B, T, N), f"維度不匹配: {out.shape} vs {(B, T, N)}"
    assert intermediate_E.abs().max().item() == 0.0, "中介張量未完成物理清零！"
    assert audit_res["zdr_verified"] is True, "ZDR 驗證失敗！"
    assert len(audit_res["sha256_fingerprint"]) == 64, "SHA-256 指紋格式錯誤！"

    print(f"運行裝置: {device}")
    print(f"輸出形狀: {list(out.shape)} (B, T, N)")
    print(f"中介張量物理清零 (Max Abs): {intermediate_E.abs().max().item():.1f}")
    print(f"ZDR 狀態驗收: {audit_res['zdr_verified']}")
    print(f"SHA-256 指紋: {audit_res['sha256_fingerprint']}")
    print("審計日誌已產出: logs/audit/audit_EpipolarConsistencyCritic.json")
    print("\n🔒 [ ALL PIPELINE & ZDR PHASES CLOSED - VERIFIED ]")
    print("=" * 60)


if __name__ == "__main__":
    test_epipolar_pipeline_and_zdr()
