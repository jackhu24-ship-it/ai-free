import sys
from pathlib import Path

ROOT_DIR = Path.cwd()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import torch

from src.models.vram_guard_scheduler import MemoryBackoffReject, VRAMGuardDynamicScheduler


def dummy_compute(x: torch.Tensor):
    # 模擬幾何算子前向傳播
    return x * 1.0, {"dummy_metric": 0.001}


def run_tests():
    print("\n" + "=" * 65)
    print(">> PHANToM Grid: 顯存熔斷調度器 (VRAMGuard) 升級驗收 <<")
    print("=" * 65)

    scheduler = VRAMGuardDynamicScheduler(
        hard_limit_gb=50.0, warning_limit_gb=35.0, default_chunk_size=2
    )
    B, T, N = 2, 6, 64
    points = torch.randn(B, T, N, 3)

    # Task 1: 綠區正常直通模式 (< 35GB)
    scheduler.set_simulated_vram_gb(20.0)
    out1, m1 = scheduler.schedule_execution(dummy_compute, points)
    assert m1["dispatch_mode"] == "DIRECT"
    assert out1.shape == points.shape
    print(
        f"[TASK 1: PASS] 綠區安全水位 (20GB) | 模式: {m1['dispatch_mode']} | 形狀吻合: {list(out1.shape)}"
    )

    # Task 2: 黃區自適應分塊調度 (35GB ~ 50GB)
    scheduler.set_simulated_vram_gb(42.0)
    out2, m2 = scheduler.schedule_execution(dummy_compute, points)
    assert m2["dispatch_mode"] == "CHUNKED"
    assert m2["chunk_size"] == 2
    assert out2.shape == points.shape
    print(
        f"[TASK 2: PASS] 黃區警戒水位 (42GB) | 自適應分塊啟動: {m2['dispatch_mode']} (Chunk: {m2['chunk_size']})"
    )

    # Task 3: 紅區 50GB 熔斷攔截 (>= 50GB)
    scheduler.set_simulated_vram_gb(52.5)
    reject_triggered = False
    try:
        scheduler.schedule_execution(dummy_compute, points)
    except MemoryBackoffReject:
        reject_triggered = True

    assert reject_triggered, "超標顯存未觸發熔斷拒絕！"
    assert scheduler.rejections_count.item() == 1
    print("[TASK 3: PASS] 紅區極限水位 (52.5GB) | 熔斷拒絕成功觸發: MemoryBackoffReject (計數: 1)")

    # Task 4: 狀態復位與記憶體乾淨度驗證
    scheduler.reset_state()
    assert scheduler.rejections_count.item() == 0
    assert scheduler.simulated_vram_gb.item() == 0.0
    print("[TASK 4: PASS] 調度器狀態重置閉環完成 | 計數歸零: True")

    print("=" * 65)
    print("🎉 [ ALL 4 ENHANCED TASKS PASSED - UPGRADE SUCCESSFUL ]")
    print("=" * 65)


if __name__ == "__main__":
    run_tests()
