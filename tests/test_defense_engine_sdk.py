import sys
from pathlib import Path

ROOT_DIR = Path.cwd()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import torch
from src.engine.defense_engine import PhantomDefenseEngine, DefenseOutput
from src.models.vram_guard_scheduler import MemoryBackoffReject

def run_sdk_tests():
    print("\n" + "=" * 65)
    print(">> PHANToM Grid: 統一防禦引擎 (PhantomDefenseEngine SDK) 驗收 <<")
    print("=" * 65)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    engine = PhantomDefenseEngine().to(device)

    B, T, N = 2, 6, 64
    t_steps = torch.linspace(0, 1, T, device=device).view(1, T, 1, 1).repeat(B, 1, N, 3)
    golden_points = t_steps + torch.randn(B, 1, N, 3, device=device) * 0.0001
    golden_poses = torch.eye(4, device=device).unsqueeze(0).repeat(B, T, 1, 1)

    # Task 1: 一鍵直通黃金調用
    engine.set_simulated_vram_gb(20.0)
    out1 = engine.protect_step(golden_points, golden_poses)
    assert out1.dispatch_mode == "DIRECT"
    assert not out1.is_damped
    assert out1.points.shape == golden_points.shape
    print(f"[TASK 1: PASS] protect_step 一鍵黃金調用 | 模式: {out1.dispatch_mode} | 阻尼觸發: {out1.is_damped}")

    # Task 2: 警戒顯存自適應分塊調用
    engine.set_simulated_vram_gb(42.0)
    out2 = engine.protect_step(golden_points, golden_poses)
    assert out2.dispatch_mode == "CHUNKED"
    assert out2.points.shape == golden_points.shape
    print(f"[TASK 2: PASS] protect_step 自適應分塊調用 | 模式: {out2.dispatch_mode} | 輸出維度完全對齊")

    # Task 3: 混沌擾動阻尼收縮 + 50GB 熔斷攔截驗證
    engine.set_simulated_vram_gb(22.0)
    chaos_points = golden_points.clone()
    chaos_points[:, 2:4] += torch.randn_like(chaos_points[:, 2:4]) * 0.9
    out3 = engine.protect_step(chaos_points, golden_poses)
    assert out3.is_damped
    print(f"[TASK 3a: PASS] 幾何擾動防禦成功 | 剛性阻尼標記: {out3.is_damped}")

    engine.set_simulated_vram_gb(52.0)
    rejected = False
    try:
        engine.protect_step(chaos_points, golden_poses)
    except MemoryBackoffReject:
        rejected = True
    assert rejected, "超標顯存未攔截"
    print(f"[TASK 3b: PASS] 50GB 熔斷警戒線攔截 | MemoryBackoffReject 拋出成功")

    # Task 4: 中介張量委託銷毀與 SHA-256 指紋驗收
    engine.set_simulated_vram_gb(15.0)
    user_intermediate = torch.randn(B, T, N, device=device)
    out4 = engine.protect_step(
        golden_points,
        golden_poses,
        intermediate_tensors_to_wipe=[user_intermediate]
    )
    assert user_intermediate.abs().max().item() == 0.0, "委託銷毀張量未清零"
    assert len(out4.sha256_fingerprint) == 64
    print(f"[TASK 4: PASS] Phase 4 委託 ZDR 銷毀完成: 0.0 | SHA-256: {out4.sha256_fingerprint}")
    print(f"審計日誌: logs/audit/audit_PhantomDefenseEngine.json")

    print("=" * 65)
    print("🎉 [ ALL SDK TASKS PASSED - ENGINE READY FOR PRODUCTION ]")
    print("=" * 65)

if __name__ == "__main__":
    run_sdk_tests()
