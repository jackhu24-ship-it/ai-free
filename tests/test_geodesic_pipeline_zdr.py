import sys
from pathlib import Path

ROOT_DIR = Path.cwd()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from typing import Dict, Optional, Tuple

import torch
import torch.nn as nn

from src.governance.zdr_audit import ZDRAuditManager
from src.models.geodesic_curvature import GeodesicCurvatureEstimator


class GeodesicPipelineAdapter(nn.Module):
    """測地曲率估算器主管線雙流適配器"""

    def __init__(
        self,
        damping_factor=1.35,
        max_curvature_threshold=0.08,
        ema_alpha=0.3,
        max_fallback_frames=5,
        enable_cuda_stream=True,
    ):
        super().__init__()
        self.estimator = GeodesicCurvatureEstimator(
            damping_factor=damping_factor,
            max_curvature_threshold=max_curvature_threshold,
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
        self, points: torch.Tensor, current_stream: Optional[torch.cuda.Stream] = None
    ) -> Tuple[torch.Tensor, Dict[str, any]]:
        if not self.enable_cuda_stream or not points.is_cuda:
            return self.estimator(points)

        if current_stream is None:
            current_stream = torch.cuda.current_stream()

        current_stream.record_event(self.event)
        with torch.cuda.stream(self.stream):
            self.stream.wait_event(self.event)
            out_points, metrics = self.estimator(points)
            self.stream.record_event(self.event)

        current_stream.wait_event(self.event)
        return out_points, metrics


def test_geodesic_pipeline_and_zdr():
    print("\n" + "=" * 60)
    print(">> PHANToM Grid: 測地曲率雙流適配與 ZDR/SHA-256 審計驗收 <<")
    print("=" * 60)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    adapter = GeodesicPipelineAdapter().to(device)
    zdr = ZDRAuditManager()

    B, T, N = 2, 6, 64
    t_steps = torch.linspace(0, 1, T, device=device).view(1, T, 1, 1).repeat(B, 1, N, 3)
    points = t_steps + torch.randn(B, 1, N, 3, device=device) * 0.0001

    # 模擬建立中介流形差分緩衝區
    intermediate_v = torch.randn(B, T - 1, N, 3, device=device)
    zdr.register_intermediate(intermediate_v)

    # 執行主管線前向運算
    out, metrics = adapter.forward_step(points)

    # 執行 ZDR 物理銷毀與 SHA-256 狀態簽署
    audit_res = zdr.verify_and_audit(
        module_name="GeodesicCurvatureEstimator",
        output_tensor=out,
        metrics=metrics,
        intermediates_to_wipe=[intermediate_v],
    )

    # 嚴格驗收斷言
    assert out.shape == points.shape, f"維度不匹配: {out.shape} vs {points.shape}"
    assert intermediate_v.abs().max().item() == 0.0, "中介張量未完成物理清零！"
    assert audit_res["zdr_verified"] is True, "ZDR 驗證失敗！"
    assert len(audit_res["sha256_fingerprint"]) == 64, "SHA-256 指紋格式錯誤！"

    print(f"運行裝置: {device}")
    print(f"輸出形狀: {list(out.shape)} (B, T, N, 3)")
    print(f"中介張量物理清零 (Max Abs): {intermediate_v.abs().max().item():.1f}")
    print(f"ZDR 狀態驗收: {audit_res['zdr_verified']}")
    print(f"SHA-256 指紋: {audit_res['sha256_fingerprint']}")
    print("審計日誌已產出: logs/audit/audit_GeodesicCurvatureEstimator.json")
    print("\n🔒 [ ALL PIPELINE & ZDR PHASES CLOSED - VERIFIED ]")
    print("=" * 60)


if __name__ == "__main__":
    test_geodesic_pipeline_and_zdr()
