import sys
from pathlib import Path

ROOT_DIR = Path.cwd()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from typing import Dict, Tuple

import torch
import torch.nn as nn

from src.governance.zdr_audit import ZDRAuditManager
from src.models.vram_guard_scheduler import VRAMGuardDynamicScheduler


class VRAMGuardPipelineAdapter(nn.Module):
    """VRAMGuard 調度器主管線適配器"""

    def __init__(self, hard_limit_gb=50.0, warning_limit_gb=35.0, default_chunk_size=2):
        super().__init__()
        self.scheduler = VRAMGuardDynamicScheduler(
            hard_limit_gb=hard_limit_gb,
            warning_limit_gb=warning_limit_gb,
            default_chunk_size=default_chunk_size,
        )

    def forward_step(self, fn, points: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, any]]:
        return self.scheduler.schedule_execution(fn, points)


def test_vram_guard_pipeline_zdr():
    print("\n" + "=" * 60)
    print(">> PHANToM Grid: VRAMGuard 適配與 ZDR/SHA-256 審計驗收 <<")
    print("=" * 60)

    adapter = VRAMGuardPipelineAdapter()
    zdr = ZDRAuditManager()

    B, T, N = 2, 6, 64
    points = torch.randn(B, T, N, 3)

    # 模擬幾何前向函式
    def forward_pass(x):
        return x * 1.0, {"step_loss": 0.005}

    # 模擬中介分塊緩衝區
    intermediate_chunk = torch.randn(B, 2, N, 3)
    zdr.register_intermediate(intermediate_chunk)

    # 執行調度運算
    adapter.scheduler.set_simulated_vram_gb(40.0)  # 黃區分塊
    out, metrics = adapter.forward_step(forward_pass, points)

    # ZDR 物理銷毀與 SHA-256 審計簽名
    audit_res = zdr.verify_and_audit(
        module_name="VRAMGuardDynamicScheduler",
        output_tensor=out,
        metrics=metrics,
        intermediates_to_wipe=[intermediate_chunk],
    )

    assert out.shape == points.shape
    assert intermediate_chunk.abs().max().item() == 0.0, "中介分塊未完成物理清零"
    assert audit_res["zdr_verified"] is True
    assert len(audit_res["sha256_fingerprint"]) == 64

    print(f"調度模式: {metrics['dispatch_mode']} (Chunk: {metrics['chunk_size']})")
    print(f"中介分塊物理清零 (Max Abs): {intermediate_chunk.abs().max().item():.1f}")
    print(f"ZDR 狀態驗收: {audit_res['zdr_verified']}")
    print(f"SHA-256 指紋: {audit_res['sha256_fingerprint']}")
    print("審計日誌已產出: logs/audit/audit_VRAMGuardDynamicScheduler.json")
    print("\n🔒 [ ALL PIPELINE & ZDR PHASES CLOSED - VERIFIED ]")
    print("=" * 60)


if __name__ == "__main__":
    test_vram_guard_pipeline_zdr()
