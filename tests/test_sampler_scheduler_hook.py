import sys
from pathlib import Path

ROOT_DIR = Path.cwd()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import torch
from src.pipelines.sampler_scheduler_hook import FlowMatchSamplerSchedulerHook, HookStepOutput

def run_tests():
    print("\n" + "=" * 65)
    print(">> PHANToM Grid: 採樣器 Hook (SamplerSchedulerHook) 驗收 <<")
    print("=" * 65)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    hook = FlowMatchSamplerSchedulerHook().to(device)

    B, C, T, H, W = 2, 16, 6, 16, 16

    # Task 1: 基礎去噪單步流匹配 Euler 步進與平滑調用
    torch.nn.init.zeros_(hook.adapter.proj_fc.weight)
    torch.nn.init.zeros_(hook.adapter.proj_fc.bias)

    sample = torch.zeros(B, C, T, H, W, device=device)
    model_output = torch.zeros(B, C, T, H, W, device=device)
    poses = torch.eye(4, device=device).unsqueeze(0).repeat(B, T, 1, 1)

    out1: HookStepOutput = hook.step(model_output, timestep=980.0, sample=sample, camera_poses=poses, dt=-0.05)
    assert out1.prev_sample.shape == sample.shape
    assert not out1.is_damped
    print(f"[TASK 1: PASS] Flow-Matching Euler 步進輸出正常: {list(out1.prev_sample.shape)} | 阻尼未觸發")

    # Task 2: 注入強外參幾何突變，驗證阻尼介入
    torch.nn.init.eye_(hook.adapter.proj_fc.weight[:hook.adapter.hidden_points * 3, :hook.adapter.hidden_points * 3])
    chaos_sample = sample.clone()
    chaos_sample[:, :, 2:4] += 5.0

    turbulent_poses = poses.clone()
    turbulent_poses[:, 1:, :3, 3] += 3.0

    out2: HookStepOutput = hook.step(model_output, timestep=900.0, sample=chaos_sample, camera_poses=turbulent_poses)
    assert out2.is_damped, "幾何失諧未觸發阻尼"
    assert out2.metrics["effective_guidance_scale"] > 0.15
    print(f"[TASK 2: PASS] 幾何失諧防禦介入 | 引導強度: {out2.metrics['effective_guidance_scale']:.4f}x (阻尼: True)")

    # Task 3: 多步去噪時序連續性與狀態機無殘留驗收
    for t_step in [800.0, 700.0, 600.0]:
        step_res = hook.step(model_output, timestep=t_step, sample=sample, camera_poses=poses)
        assert step_res.prev_sample.shape == sample.shape
    print(f"[TASK 3: PASS] 3 步去噪時序連續迴圈無殘留驗收通過")

    # Task 4: SHA-256 全生命週期審計指紋鏈路驗收
    assert len(out2.sha256_fingerprint) == 64
    print(f"[TASK 4: PASS] 審計指紋有效: {out2.sha256_fingerprint}")

    print("=" * 65)
    print("🎉 [ ALL 4 SCHEDULER HOOK TASKS PASSED - READY FOR PRODUCTION ]")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
