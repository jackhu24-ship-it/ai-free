import sys
from pathlib import Path

ROOT_DIR = Path.cwd()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import torch

from src.pipelines.pipeline_integration import AnchorPipelineAdapter


def run_integration_test():
    print("\n" + "=" * 55)
    print(">> 主管線雙流適配器整合驗收 (4D Spatiotemporal Anchor) <<")
    print("=" * 55)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    adapter = AnchorPipelineAdapter().to(device)

    B, T, N = 2, 5, 64
    points = torch.randn(B, T, N, 3, device=device)
    poses = torch.eye(4, device=device).unsqueeze(0).repeat(B, T, 1, 1)

    out, metrics = adapter.forward_step(points, poses)

    # out 形狀為幾何約束殘差特徵 (B, T, N)
    assert out.shape == (B, T, N), f"特徵維度不匹配: {out.shape} vs {(B, T, N)}"
    assert "ema_residual" in metrics, "缺少 ema_residual 指標"

    print(f"運行裝置: {device}")
    print(f"輸入點雲形狀: {list(points.shape)} (B, T, N, 3)")
    print(f"約束輸出特徵: {list(out.shape)} (B, T, N)")
    print(f"EMA 殘差: {metrics['ema_residual']:.4f}")
    print(f"阻尼觸發狀態: {metrics.get('is_damped', False)}")
    print("\n🎉 [ ALL TASKS PASSED - PIPELINE READY ]")
    print("=" * 55)


if __name__ == "__main__":
    run_integration_test()
