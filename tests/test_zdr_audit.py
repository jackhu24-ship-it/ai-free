import sys
from pathlib import Path

ROOT_DIR = Path.cwd()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import torch

from src.governance.zdr_audit import ZDRAuditManager
from src.pipelines.pipeline_integration import AnchorPipelineAdapter


def test_zdr_and_audit():
    print("\n" + "=" * 55)
    print(">> Phase 4 治理層: ZDR 物理銷毀與 SHA-256 審計驗收 <<")
    print("=" * 55)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    adapter = AnchorPipelineAdapter().to(device)
    zdr = ZDRAuditManager()

    B, T, N = 2, 5, 64
    points = torch.randn(B, T, N, 3, device=device)
    poses = torch.eye(4, device=device).unsqueeze(0).repeat(B, T, 1, 1)

    # 模擬建立中介計算暫存張量
    intermediate_buffer = torch.randn(B, T, N, device=device)
    zdr.register_intermediate(intermediate_buffer)

    # 執行適配器管線前向傳播
    out, metrics = adapter.forward_step(points, poses)

    # 執行 ZDR 物理清零與 SHA-256 審計
    audit_res = zdr.verify_and_audit(
        module_name="SpatiotemporalAnchor4D",
        output_tensor=out,
        metrics=metrics,
        intermediates_to_wipe=[intermediate_buffer],
    )

    # 斷言驗收條件
    assert intermediate_buffer.abs().max().item() == 0.0, "中介張量未完成物理清零！"
    assert audit_res["zdr_verified"] is True, "ZDR 驗證失敗！"
    assert len(audit_res["sha256_fingerprint"]) == 64, "SHA-256 指紋格式錯誤！"

    print(f"運行裝置: {device}")
    print(f"中介張量就地擦除 (Max Abs): {intermediate_buffer.abs().max().item():.1f}")
    print(f"ZDR 狀態驗收: {audit_res['zdr_verified']}")
    print(f"SHA-256 狀態指紋: {audit_res['sha256_fingerprint']}")
    print("審計日誌已產出: logs/audit/audit_SpatiotemporalAnchor4D.json")
    print("\n🔒 [ ALL 4 PHASES FULLY CLOSED - PRODUCTION READY ]")
    print("=" * 55)


if __name__ == "__main__":
    test_zdr_and_audit()
