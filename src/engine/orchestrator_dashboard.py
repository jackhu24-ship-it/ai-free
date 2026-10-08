"""
PHANToM Grid: Orchestrator Real-time Metrics Dashboard
全生命週期即時可視化監控大盤：
統一聚合 50GB 顯存水位、二階測地曲率、跨卡損失、剛性阻尼標記與 SHA-256 存證鏈
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import torch
import torch.nn as nn
from src.governance.zdr_audit import ZDRAuditManager

@dataclass
class DashboardSnapshot:
    step_count: int
    vram_peak_gb: float
    mean_curvature: float
    is_damped: bool
    status_label: str
    ascii_table: str
    metrics: Dict[str, Any]
    sha256_fingerprint: str

class OrchestratorMetricsDashboard(nn.Module):
    def __init__(self, vram_limit_gb: float = 50.0, curvature_threshold: float = 0.08, max_history: int = 100):
        super().__init__()
        self.vram_limit_gb = float(vram_limit_gb)
        self.curvature_threshold = float(curvature_threshold)
        self.max_history = int(max_history)
        self.zdr = ZDRAuditManager()

        self.history_vram: List[float] = []
        self.history_curvature: List[float] = []
        self.history_damped: List[bool] = []
        self.step_counter = 0

    def _phase1_ingress(self, vram_gb: float, curvature: float) -> None:
        if vram_gb < 0.0 or curvature < 0.0:
            raise ValueError(f"[Dashboard Ingress] 數值不可為負數: VRAM={vram_gb}, Curv={curvature}")

    def _phase2_staging(self, vram_gb: float, curvature: float, is_damped: bool) -> None:
        self.history_vram.append(float(vram_gb))
        self.history_curvature.append(float(curvature))
        self.history_damped.append(bool(is_damped))

        if len(self.history_vram) > self.max_history:
            self.history_vram.pop(0)
            self.history_curvature.pop(0)
            self.history_damped.pop(0)

        self.step_counter += 1

    def _phase3_compute(self, vram_gb: float, curvature: float, is_damped: bool) -> Tuple[str, str, Dict[str, Any]]:
        if vram_gb >= self.vram_limit_gb:
            status = "CIRCUIT_BREAKER_TRIPPED"
        elif is_damped or (curvature > self.curvature_threshold):
            status = "DAMPED_ACTIVE (1.35x)"
        elif vram_gb >= 35.0:
            status = "ATTENTION_VRAM_HIGH"
        else:
            status = "SYSTEM_HEALTHY_NORMAL"

        vram_peak = max(self.history_vram) if self.history_vram else vram_gb
        mean_curv = sum(self.history_curvature) / len(self.history_curvature) if self.history_curvature else curvature

        panel_lines = [
            "+-------------------------------------------------------------------+",
            "|           PHANToM GRID ORCHESTRATOR REAL-TIME DASHBOARD           |",
            "+-------------------------------------------------------------------+",
            f"| Step: {self.step_counter:04d}   | Status: {status:<24} |",
            f"| VRAM Used: {vram_gb:6.2f} GB / {self.vram_limit_gb:.1f} GB (Peak: {vram_peak:6.2f} GB)            |",
            f"| Geodesic Curvature: {curvature:6.4f} (Threshold: {self.curvature_threshold:.2f}, Mean: {mean_curv:6.4f}) |",
            f"| Damping Active: {str(is_damped):<5} | History Depth: {len(self.history_vram):03d} frames                |",
            "+-------------------------------------------------------------------+",
        ]
        ascii_table = "\n".join(panel_lines)

        metrics = {
            "step": self.step_counter,
            "vram_gb": vram_gb,
            "vram_peak_gb": vram_peak,
            "curvature": curvature,
            "mean_curvature": mean_curv,
            "is_damped": is_damped,
            "status": status,
        }

        return status, ascii_table, metrics

    def record_step(
        self,
        vram_gb: float,
        curvature: float,
        is_damped: bool = False,
    ) -> DashboardSnapshot:
        self._phase1_ingress(vram_gb, curvature)
        self._phase2_staging(vram_gb, curvature, is_damped)
        status, ascii_table, metrics = self._phase3_compute(vram_gb, curvature, is_damped)

        audit_tensor = torch.tensor([vram_gb, curvature, float(is_damped)], dtype=torch.float32)
        staging_buf = audit_tensor.clone()

        audit_res = self.zdr.verify_and_audit(
            module_name="OrchestratorMetricsDashboard",
            output_tensor=audit_tensor,
            metrics=metrics,
            intermediates_to_wipe=[staging_buf],
        )

        return DashboardSnapshot(
            step_count=self.step_counter,
            vram_peak_gb=metrics["vram_peak_gb"],
            mean_curvature=metrics["mean_curvature"],
            is_damped=is_damped,
            status_label=status,
            ascii_table=ascii_table,
            metrics=metrics,
            sha256_fingerprint=audit_res["sha256_fingerprint"],
        )

    def reset_state(self) -> None:
        self.history_vram.clear()
        self.history_curvature.clear()
        self.history_damped.clear()
        self.step_counter = 0
