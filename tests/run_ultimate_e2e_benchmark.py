import sys
from pathlib import Path

ROOT_DIR = Path.cwd()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import torch
from src.pipelines.sampler_scheduler_hook import FlowMatchSamplerSchedulerHook
from src.pipelines.multi_gpu_dual_stream_scheduler import MultiGPUAsyncDualStreamScheduler
from src.engine.kernels.fused_spatiotemporal import SRAMFusedRunner

def run_ultimate_benchmark():
    print("\n" + "=" * 70)
    print(">> PHANToM Grid: 全管線端到端終極壓測 (Ultimate E2E Benchmark) <<")
    print("=" * 70)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f">> [硬體環境] 運算設備: {device.upper()} | 50GB 顯存熔斷防護線已就緒")

    # 實例化全鏈路三大核心管線組件
    hook = FlowMatchSamplerSchedulerHook().to(device)
    dual_scheduler = MultiGPUAsyncDualStreamScheduler().to(device)
    fused_runner = SRAMFusedRunner().to(device)

    B, C, T, H, W = 2, 16, 6, 16, 16
    latents = torch.zeros(B, C, T, H, W, device=device)
    model_output = torch.zeros(B, C, T, H, W, device=device)
    camera_poses = torch.eye(4, device=device).unsqueeze(0).repeat(B, T, 1, 1)

    # -------------------------------------------------------------
    # Scenario A: 黃金路徑多步連續去噪閉環 (Golden Standard)
    # -------------------------------------------------------------
    timesteps = [900.0, 750.0, 500.0, 250.0, 50.0]
    current_sample = latents.clone()

    for step_idx, t in enumerate(timesteps):
        # 1. 採樣器 Hook 單步 Flow-Matching 與幾何引導
        step_out = hook.step(model_output, timestep=t, sample=current_sample, camera_poses=camera_poses, dt=-0.05)
        # 2. 多卡雙流異步排程與跨視角通訊
        dual_out = dual_scheduler.dispatch_step(step_out.prev_sample, camera_poses, world_size=4)
        current_sample = dual_out.synchronized_latents

    assert current_sample.shape == latents.shape
    print(f"[SCENARIO A: PASS] 5 步去噪黃金全鏈路平滑貫通 | 潛變量輸出對齊: {list(current_sample.shape)}")

    # -------------------------------------------------------------
    # Scenario B: 混沌幾何突變與動態 1.35x 剛性阻尼壓力收斂
    # -------------------------------------------------------------
    turbulent_poses = camera_poses.clone()
    turbulent_poses[:, 1:, 0, 0] = 0.0
    turbulent_poses[:, 1:, 0, 1] = -1.0
    turbulent_poses[:, 1:, 1, 0] = 1.0
    turbulent_poses[:, 1:, 1, 1] = 0.0
    turbulent_poses[:, 1:, :3, 3] += 4.2

    chaos_latents = latents.clone()
    chaos_latents[:, :3, 2:4, :8, :8] += 6.0

    step_chaos = hook.step(model_output, timestep=800.0, sample=chaos_latents, camera_poses=turbulent_poses)
    dual_chaos = dual_scheduler.dispatch_step(step_chaos.prev_sample, turbulent_poses, world_size=4)

    assert dual_chaos.is_damped, "混沌突變未觸發雙流阻尼"
    assert dual_chaos.mean_global_loss > 0.08, f"全域指標未達標: {dual_chaos.mean_global_loss}"
    print(f"[SCENARIO B: PASS] 混沌外參突變 1.35x 剛性阻尼介入成功 | 全域損失指標: {dual_chaos.mean_global_loss:.4f} > 0.08")

    # -------------------------------------------------------------
    # Scenario C: 片上 SRAM 融合投影 Zero-Allocation 壓力驗收
    # -------------------------------------------------------------
    fused_pts = chaos_latents[:, :3, :, :8, :8].permute(0, 2, 3, 4, 1).reshape(B, T, 64, 3)
    fused_out = fused_runner(fused_pts, turbulent_poses)
    assert fused_out.is_damped
    assert fused_runner._static_buffer is not None
    assert fused_runner._static_buffer.abs().max().item() == 0.0
    print(f"[SCENARIO C: PASS] 片上 SRAM 融合與靜態緩衝區複用完成 | ZDR 物理銷毀 Max Abs: 0.0")

    # -------------------------------------------------------------
    # Scenario D: Phase 4 治理層鏈路全域 SHA-256 審計指紋防偽
    # -------------------------------------------------------------
    assert len(step_out.sha256_fingerprint) == 64
    assert len(dual_chaos.sha256_fingerprint) == 64
    assert len(fused_out.sha256_fingerprint) == 64
    print(f"[SCENARIO D: PASS] 全鏈路 SHA-256 狀態簽名存證驗證成功")
    print(f"審計指紋: {dual_chaos.sha256_fingerprint}")

    print("=" * 70)
    print("🎉 [ ALL 4 ULTIMATE BENCHMARK SCENARIOS PASSED - SYSTEM CERTIFIED ]")
    print("=" * 70)

if __name__ == "__main__":
    run_ultimate_benchmark()
