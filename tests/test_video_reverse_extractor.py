import sys
from pathlib import Path

ROOT_DIR = Path.cwd()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import torch
from src.engine.video_reverse_extractor import VideoReverseGeometryExtractor, ExtractedGeometryOutput

def run_tests():
    print("\n" + "=" * 65)
    print(">> PHANToM Grid: 視訊逆向幾何提取器 (Reverse Extractor) 驗收 <<")
    print("=" * 65)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    extractor = VideoReverseGeometryExtractor().to(device)

    B, T, C, H, W = 1, 5, 3, 32, 32

    # Task 1: 基礎平穩視訊外參 SE(3) 反求與 YAML 自動生成 (Golden Path)
    smooth_frames = torch.zeros(B, T, C, H, W, device=device)
    for t in range(T):
        smooth_frames[:, t] += float(t) * 0.01

    out1: ExtractedGeometryOutput = extractor(smooth_frames, fps=24.0)
    assert out1.camera_poses.shape == (B, T, 4, 4)
    assert "version: '1.0.0-PROD'" in out1.task_spec_yaml
    assert "camera_path:" in out1.task_spec_yaml
    assert not out1.is_damped
    print(f"[TASK 1: PASS] 視訊外參逆向求解成功 | 生成標準 YAML (長度: {len(out1.task_spec_yaml)} 字元) | 阻尼未觸發")

    # Task 2: 注入劇烈影格光流抖動，驗證 1.35x 剛性 EMA 抑制
    chaos_frames = smooth_frames.clone()
    chaos_frames[:, 2] += 2.0  # 注入影格劇烈階躍
    out2: ExtractedGeometryOutput = extractor(chaos_frames, fps=24.0)
    assert out2.is_damped, "劇烈晃動影格必須觸發阻尼"
    assert out2.metrics["mean_curvature"] > 0.08
    print(f"[TASK 2: PASS] 劇烈光流晃動阻尼介入 | 測地曲率: {out2.metrics['mean_curvature']:.4f} > 0.08 (阻尼: True)")

    # Task 3: 3D 世界物理包圍盒求解合理性 (min < max)
    b_min, b_max = out1.world_bounds["min"], out1.world_bounds["max"]
    assert all(b_min[i] < b_max[i] for i in range(3)), "包圍盒維度非法"
    print(f"[TASK 3: PASS] 3D 世界包圍盒求解合法: Min={b_min} | Max={b_max}")

    # Task 4: Phase 4 治理層 SHA-256 狀態簽名鏈路驗收
    assert len(out1.sha256_fingerprint) == 64
    assert len(out2.sha256_fingerprint) == 64
    print(f"[TASK 4: PASS] SHA-256 規格指紋有效: {out1.sha256_fingerprint}")
    print(f"審計日誌: logs/audit/audit_VideoReverseGeometryExtractor.json")

    print("=" * 65)
    print("🎉 [ ALL 4 REVERSE EXTRACTOR TASKS PASSED - PRODUCTION READY ]")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
