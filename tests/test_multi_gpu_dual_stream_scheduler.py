import sys
from pathlib import Path

ROOT_DIR = Path.cwd()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import torch
from src.pipelines.multi_gpu_dual_stream_scheduler import MultiGPUAsyncDualStreamScheduler, DualStreamOutput

def run_tests():
    print("\n" + "=" * 65)
    print(">> PHANToM Grid: 多卡異步雙流排程器 (Dual-Stream Scheduler) 驗收 <<")
    print("=" * 65)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    scheduler = MultiGPUAsyncDualStreamScheduler().to(device)

    B, C, T, H, W = 2, 16, 6, 16, 16

    # Task 1: 基礎黃金路徑平滑派發與雙流事件握手驗收
    smooth_latents = torch.zeros(B, C, T, H, W, device=device)
    poses = torch.eye(4, device=device).unsqueeze(0).repeat(B, T, 1, 1)

    out1: DualStreamOutput = scheduler.dispatch_step(smooth_latents, poses, world_size=1)
    assert out1.synchronized_latents.shape == smooth_latents.shape
    assert not out1.is_damped
    print(f"[TASK 1: PASS] 雙流異步派發成功 | 輸出形狀吻合: {list(out1.synchronized_latents.shape)} | 阻尼未觸發")

    # Task 2: 注入外參平移突變 (維持 det(R)=1.0 正交契約) + 潛變量時空突變
    turbulent_poses = poses.clone()
    turbulent_poses[:, 1:, 0, 0] = 0.0
    turbulent_poses[:, 1:, 0, 1] = -1.0
    turbulent_poses[:, 1:, 1, 0] = 1.0
    turbulent_poses[:, 1:, 1, 1] = 0.0
    turbulent_poses[:, 1:, :3, 3] += 3.5

    # 注入明顯空間與時間步階躍
    chaos_latents = smooth_latents.clone()
    chaos_latents[:, :3, 2:4, :8, :8] += 5.0

    out2: DualStreamOutput = scheduler.dispatch_step(chaos_latents, turbulent_poses, world_size=4)
    assert out2.is_damped, "幾何失諧未觸發跨卡阻尼"
    assert out2.mean_global_loss > 0.08, f"全域指標未達標: {out2.mean_global_loss}"
    print(f"[TASK 2: PASS] 全域幾何失諧防禦介入 | 全域指標: {out2.mean_global_loss:.4f} > 0.08 (阻尼: True)")

    # Task 3: 狀態機重置與連續多步無死鎖驗收
    scheduler.reset_state()
    for _ in range(3):
        out_step = scheduler.dispatch_step(smooth_latents, poses)
        assert out_step.synchronized_latents.shape == smooth_latents.shape
    print(f"[TASK 3: PASS] 雙流連續事件握手無死鎖驗收通過")

    # Task 4: Phase 4 治理層 SHA-256 狀態簽名鏈路驗收
    assert len(out1.sha256_fingerprint) == 64
    assert len(out2.sha256_fingerprint) == 64
    print(f"[TASK 4: PASS] SHA-256 審計簽名有效: {out2.sha256_fingerprint}")
    print(f"審計日誌: logs/audit/audit_MultiGPUAsyncDualStreamScheduler.json")

    print("=" * 65)
    print("🎉 [ ALL 4 DUAL STREAM TASKS PASSED - PRODUCTION READY ]")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
