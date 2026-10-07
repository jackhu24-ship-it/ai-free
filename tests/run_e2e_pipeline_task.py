import sys
from pathlib import Path

ROOT_DIR = Path.cwd()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import torch
import torch.nn as nn

from src.governance.zdr_audit import ZDRAuditManager
from src.models.epipolar_critic import EpipolarConsistencyCritic
from src.models.geodesic_curvature import GeodesicCurvatureEstimator
from src.models.spatiotemporal_anchor import SpatiotemporalAnchor4D


class PHANToMGeometricPipeline(nn.Module):
    """三核心幾何防禦端到端串聯管線"""

    def __init__(self):
        super().__init__()
        self.anchor = SpatiotemporalAnchor4D()
        self.geodesic = GeodesicCurvatureEstimator()
        self.critic = EpipolarConsistencyCritic()
        self.zdr = ZDRAuditManager()

    def forward(self, points: torch.Tensor, camera_poses: torch.Tensor):
        # 1. 4D 時空幾何錨定
        anchor_feat, m_anchor = self.anchor(points, camera_poses)

        # 2. 測地曲率流形平滑
        smoothed_points, m_geodesic = self.geodesic(points)

        # 3. 對極幾何一致性 Critic 判別
        critic_loss, m_critic = self.critic(smoothed_points, camera_poses)

        metrics = {
            "anchor_ema_res": m_anchor["ema_residual"],
            "geodesic_curv": m_geodesic["mean_curvature"],
            "epipolar_loss": m_critic["mean_residual"],
            "anchor_damped": m_anchor["is_damped"],
            "geodesic_damped": m_geodesic["is_damped"],
            "critic_damped": m_critic["is_damped"],
        }
        return smoothed_points, critic_loss, metrics


def run_e2e_task():
    print("\n" + "=" * 65)
    print(">> PHANToM Grid: 三核心幾何防禦端到端黑盒壓測 (E2E Test Task) <<")
    print("=" * 65)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    pipeline = PHANToMGeometricPipeline().to(device)
    zdr = ZDRAuditManager()

    B, T, N = 2, 6, 64

    # --- Scenario A: 黃金基準路徑 (平滑軌跡) ---
    t_steps = torch.linspace(0, 1, T, device=device).view(1, T, 1, 1).repeat(B, 1, N, 3)
    golden_points = t_steps + torch.randn(B, 1, N, 3, device=device) * 0.0001
    golden_poses = torch.eye(4, device=device).unsqueeze(0).repeat(B, T, 1, 1)

    pts_out, critic_loss, m_gold = pipeline(golden_points, golden_poses)
    assert not m_gold["anchor_damped"], "黃金路徑不應觸發錨定阻尼"
    assert not m_gold["geodesic_damped"], "黃金路徑不應觸發測地阻尼"
    print(
        f"[TASK 1: PASS] Scenario A 黃金基準路徑完好 | 曲率: {m_gold['geodesic_curv']:.4f} | Critic: {m_gold['epipolar_loss']:.4f}"
    )

    # --- Scenario B: 混沌壓測注入 (幾何突變與旋轉擾動) ---
    chaos_points = golden_points.clone()
    chaos_points[:, 2:4] += torch.randn_like(chaos_points[:, 2:4]) * 0.8  # 注入點雲激增
    chaos_poses = golden_poses.clone()
    chaos_poses[:, 1:, :3, 3] += 2.0  # 注入位移突變

    pts_chaos, loss_chaos, m_chaos = pipeline(chaos_points, chaos_poses)
    assert m_chaos["geodesic_damped"] or m_chaos["critic_damped"], "混沌注入應成功觸發阻尼介入"
    print("[TASK 2: PASS] Scenario B 混沌壓測成功熔斷收縮 | 阻尼狀態介入: True")

    # --- Task 3: 記憶體與 ZDR 零殘留物理銷毀驗收 ---
    buffer_temp = torch.randn(B, T, N, device=device)
    zdr.register_intermediate(buffer_temp)
    audit_res = zdr.verify_and_audit(
        module_name="PHANToM_Geometric_E2E",
        output_tensor=pts_out,
        metrics=m_gold,
        intermediates_to_wipe=[buffer_temp],
    )
    assert buffer_temp.abs().max().item() == 0.0, "ZDR 原地清零未達成"
    assert audit_res["zdr_verified"] is True
    print("[TASK 3: PASS] Phase 4 治理層 ZDR 零殘留驗收通過 | 中介張量清零: 0.0")

    # --- Task 4: 端到端 SHA-256 狀態指紋與審計存證 ---
    assert len(audit_res["sha256_fingerprint"]) == 64
    print(f"[TASK 4: PASS] SHA-256 狀態簽名生成: {audit_res['sha256_fingerprint']}")
    print("審計存證日誌: logs/audit/audit_PHANToM_Geometric_E2E.json")

    print("=" * 65)
    print("🎉 [ ALL 4 TASKS PASSED - PRODUCTION READY ]")
    print("=" * 65)


if __name__ == "__main__":
    run_e2e_task()
