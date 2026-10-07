"""
PHANToM Grid - Core Backbone Integration
將 Ingress 幾何合約、VRAMGuard 熔斷、Critic 哨兵阻尼與 ZDR 物理銷毀插樁至骨幹推論
"""

import sys
import os
sys.path.append(os.path.abspath("."))

import torch
import torch.nn as nn
from src.guards.phantom_guard_pipeline import PhantomGuardPipeline, GuardConfig


class PhantomDiTBackbone(nn.Module):
    def __init__(self, d_model: int = 128):
        super().__init__()
        self.d_model = d_model
        # 示範核心神經層
        self.latent_proj = nn.Linear(4, d_model)
        self.transformer_block = nn.Sequential(
            nn.LayerNorm(d_model),
            nn.Linear(d_model, d_model),
            nn.GELU(),
            nn.Linear(d_model, d_model)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.latent_proj(x)
        return self.transformer_block(h)


def run_backbone_inference(camera_quaternion: torch.Tensor, guard_cfg: GuardConfig = None):
    """
    生產級骨幹推論封裝：整合全生命週期防護
    """
    guard = PhantomGuardPipeline(guard_cfg)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = PhantomDiTBackbone().to(device)
    
    # 透過 Context Manager 包裹推論生命週期
    with guard:
        # [TASK 1: Ingress] 輸入前置校驗相機四元數流形
        validated_q = guard.validate_ingress_quaternion(camera_quaternion.to(device))
        
        # [TASK 2: VRAMGuard] 檢測顯存水位
        guard.check_vram_watermark()
        
        # 執行骨幹運算
        latent_out = model(validated_q)
        guard.register_resource(latent_out)
        
        # [TASK 3: Critic] 模擬對極幾何誤差並套用 1.35x 動態阻尼
        mock_epipolar_err = torch.tensor([1.2e-4], device=device)  # 略高於 1e-4 門檻
        refined_latent = guard.apply_critic_damping(mock_epipolar_err, latent_out)
        
        print(">> [Backbone] 前向推論與 Critic 阻尼調控成功完成")
        return refined_latent.shape

# 快速自測
if __name__ == "__main__":
    # 測試合法四元數輸入 (||q|| = 1)
    test_q = torch.tensor([[0.0, 0.0, 0.0, 1.0]], dtype=torch.float32)
    shape_result = run_backbone_inference(test_q)
    print(f">> [Backbone Self-Check PASS] 輸出張量維度: {shape_result}")
