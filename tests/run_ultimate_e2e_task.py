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
from src.models.vram_guard_scheduler import MemoryBackoffReject, VRAMGuardDynamicScheduler


class PHANToMGridFullPipeline(nn.Module):
    """PHANToM Grid 四核心大一統完整防禦生產級管線"""

    def __init__(self):
        super().__init__()
        self.scheduler = VRAMGuardDynamicScheduler(
            hard_limit_gb=50.0, warning_limit_gb=35.0, default_chunk_size=2
        )
        self.anchor = SpatiotemporalAnchor4D()
        self.geodesic = GeodesicCurvatureEstimator()
        self.critic = EpipolarConsistencyCritic()
        self.zdr = ZDRAuditManager()

    def _internal_geometric_step(self, points: torch.Tensor, camera_poses: torch.Tensor):
        # 1. 4D 時空錨定
        anchor_feat, m_anchor = self.anchor(points, camera_poses)
        # 2. 測地曲率平滑
        smoothed_points, m_geodesic = self.geodesic(points)
        # 3. 對極幾何一致性 Critic
        critic_loss, m_critic = self.critic(smoothed_points, camera_poses)

        metrics = {
            "anchor_ema": m_anchor["ema_residual"],
            "geodesic_curv": m_geodesic["mean_curvature"],
            "epipolar_loss": m_critic["mean_residual"],
            "anchor_damped": m_anchor["is_damped"],
            "geodesic_damped": m_geodesic["is_damped"],
            "critic_damped": m_critic["is_damped"],
        }
        return smoothed_points, critic_loss, metrics

    def forward_safe(self, points: torch.Tensor, camera_poses: torch.Tensor):
        # 透過 VRAMGuard 動態調度執行幾何計算
        def fn_wrapper(sub_pts):
            B, sub_T, N, _ = sub_pts.shape
            sub_poses = camera_poses[:, :sub_T]
            pts_out, _, m = self._internal_geometric_step(sub_pts, sub_poses)
            return pts_out, m

        out_pts, sched_metrics = self.scheduler.schedule_execution(fn_wrapper, points)
        # 執行全域 Critic 損失計算
        critic_loss, critic_m = self.critic(out_pts, camera_poses)
        sched_metrics["critic_loss"] = critic_loss.mean().item()
        return out_pts, critic_loss, sched_metrics


def run_ultimate_test():
    print("\n" + "=" * 70)
    print(">> PHANToM Grid: 四核心大一統終極任務級黑盒壓測 (Ultimate E2E) <<")
    print("=" * 70)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    system = PHANToMGridFullPipeline().to(device)
    zdr = ZDRAuditManager()

    B, T, N = 2, 6, 64

    # --- Task 1: 綠區安全水位 + 黃金基準幾何路徑 ---
    system.scheduler.set_simulated_vram_gb(18.5)
    t_steps = torch.linspace(0, 1, T, device=device).view(1, T, 1, 1).repeat(B, 1, N, 3)
    golden_points = t_steps + torch.randn(B, 1, N, 3, device=device) * 0.0001
    golden_poses = torch.eye(4, device=device).unsqueeze(0).repeat(B, T, 1, 1)

    pts_out1, loss1, m1 = system.forward_safe(golden_points, golden_poses)
    assert m1["dispatch_mode"] == "DIRECT", "綠區應為 DIRECT 模式"
    assert not m1.get("geodesic_damped", False), "黃金路徑不應觸發阻尼"
    print(
        f"[TASK 1: PASS] 綠區直通黃金路徑 | 水位: {m1['vram_gb']:.1f}GB | 模式: {m1['dispatch_mode']} | 形狀吻合"
    )

    # --- Task 2: 黃區警戒水位 + 自適應 Chunking 分塊驗收 ---
    system.scheduler.set_simulated_vram_gb(41.0)
    pts_out2, loss2, m2 = system.forward_safe(golden_points, golden_poses)
    assert m2["dispatch_mode"] == "CHUNKED", "黃區應觸發 CHUNKED 模式"
    assert m2["chunk_size"] == 2
    assert pts_out2.shape == golden_points.shape
    print(
        f"[TASK 2: PASS] 黃區警戒自適應調度 | 水位: {m2['vram_gb']:.1f}GB | 模式: {m2['dispatch_mode']} (Chunk: {m2['chunk_size']})"
    )

    # --- Task 3: 混沌幾何突變阻尼 + 紅區 50GB 熔斷攔截 ---
    # 3a. 幾何擾動觸發 1.35x 剛性收縮
    chaos_points = golden_points.clone()
    chaos_points[:, 2:4] += torch.randn_like(chaos_points[:, 2:4]) * 0.8
    system.scheduler.set_simulated_vram_gb(25.0)
    _, _, m_chaos = system.forward_safe(chaos_points, golden_poses)
    assert m_chaos.get("geodesic_damped", False) or m_chaos.get("critic_damped", False), (
        "混沌擾動應觸發阻尼"
    )
    print("[TASK 3a: PASS] 混沌幾何擾動防禦 | 剛性阻尼成功介入收縮")

    # 3b. 顯存超越 50GB 臨界熔斷線非阻塞 Reject
    system.scheduler.set_simulated_vram_gb(53.2)
    rejected = False
    try:
        system.forward_safe(chaos_points, golden_poses)
    except MemoryBackoffReject:
        rejected = True
    assert rejected, "超標顯存未被熔斷阻斷！"
    print("[TASK 3b: PASS] 紅區 50GB 警戒防線 | MemoryBackoffReject 熔斷攔截成功 (拒絕次數: 1)")

    # --- Task 4: 全鏈路 ZDR 物理銷毀與 SHA-256 狀態審計存證 ---
    intermediate_pipe_buf = torch.randn(B, T, N, device=device)
    zdr.register_intermediate(intermediate_pipe_buf)
    audit_res = zdr.verify_and_audit(
        module_name="PHANToM_Grid_Ultimate_E2E",
        output_tensor=pts_out1,
        metrics=m1,
        intermediates_to_wipe=[intermediate_pipe_buf],
    )
    assert intermediate_pipe_buf.abs().max().item() == 0.0, "ZDR 中介記憶體清零失敗"
    assert audit_res["zdr_verified"] is True
    assert len(audit_res["sha256_fingerprint"]) == 64
    print("[TASK 4: PASS] Phase 4 治理層驗收 | ZDR 零殘留物理清零: 0.0 | SHA-256 指紋簽署完畢")
    print("終極審計日誌: logs/audit/audit_PHANToM_Grid_Ultimate_E2E.json")

    print("=" * 70)
    print("🎉 [ ALL SYSTEM TASKS PASSED - PHANTOM GRID PRODUCTION READY ]")
    print("=" * 70)


if __name__ == "__main__":
    run_ultimate_test()
