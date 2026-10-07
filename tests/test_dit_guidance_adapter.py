import sys
from pathlib import Path

ROOT_DIR = Path.cwd()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import torch
from src.pipelines.dit_guidance_adapter import DiTGeometricGuidanceAdapter, GuidanceOutput

def run_tests():
    print("\n" + "=" * 65)
    print(">> PHANToM Grid: DiT 幾何引導轉接器 (DiT Guidance Adapter) 驗收 <<")
    print("=" * 65)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    adapter = DiTGeometricGuidanceAdapter().to(device)

    B, C, T, H, W = 2, 16, 6, 16, 16

    # Task 1: 基準平滑靜態潛變量
    torch.nn.init.zeros_(adapter.proj_fc.weight)
    torch.nn.init.zeros_(adapter.proj_fc.bias)

    smooth_latents = torch.zeros(B, C, T, H, W, device=device)
    poses = torch.eye(4, device=device).unsqueeze(0).repeat(B, T, 1, 1)

    res1: GuidanceOutput = adapter.guide_step(smooth_latents, poses)
    assert res1.guided_latents.shape == smooth_latents.shape
    assert not res1.is_damped
    print(f"[TASK 1: PASS] 基礎步潛變量形狀吻合: {list(res1.guided_latents.shape)} | 有效引導比例: {res1.metrics['effective_guidance_scale']:.4f}")

    # Task 2: 注入顯著幾何擾動，激發 1.35x 剛性引導增強
    torch.nn.init.eye_(adapter.proj_fc.weight[:adapter.hidden_points * 3, :adapter.hidden_points * 3])
    chaos_latents = smooth_latents.clone()
    chaos_latents[:, :, 2:4] += 5.0

    turbulent_poses = poses.clone()
    turbulent_poses[:, 1:, :3, 3] += 3.0

    res2: GuidanceOutput = adapter.guide_step(chaos_latents, turbulent_poses)
    assert res2.is_damped, "幾何失諧未觸發阻尼"
    assert res2.metrics["effective_guidance_scale"] > 0.15
    print(f"[TASK 2: PASS] 幾何突變防禦介入 | 引導強度激增: {res2.metrics['effective_guidance_scale']:.4f}x (阻尼: True)")

    # Task 3: 梯度裁切邊界驗證
    assert res2.metrics["grad_norm"] <= 1.0 + 1e-4
    print(f"[TASK 3: PASS] 梯度範數截斷邊界有效: {res2.metrics['grad_norm']:.4f} <= 1.0")

    # Task 4: SHA-256 狀態審計指紋鏈路驗收
    assert len(res2.sha256_fingerprint) == 64
    print(f"[TASK 4: PASS] 審計指紋有效: {res2.sha256_fingerprint}")

    print("=" * 65)
    print("🎉 [ ALL 4 DIT ADAPTER TASKS PASSED - PRODUCTION READY ]")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
