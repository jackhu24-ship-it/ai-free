import sys
from pathlib import Path

ROOT_DIR = Path.cwd()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.engine.orchestrator_dashboard import OrchestratorMetricsDashboard, DashboardSnapshot

def run_tests():
    print("\n" + "=" * 65)
    print(">> PHANToM Grid: 監控大盤 (Metrics Dashboard) 驗收 <<")
    print("=" * 65)

    dash = OrchestratorMetricsDashboard(vram_limit_gb=50.0, curvature_threshold=0.08)

    # Task 1: 正常平穩去噪遙測記錄與 ASCII 渲染 (Golden Path)
    out1: DashboardSnapshot = dash.record_step(vram_gb=12.5, curvature=0.02, is_damped=False)
    assert out1.status_label == "SYSTEM_HEALTHY_NORMAL"
    assert "PHANToM GRID ORCHESTRATOR REAL-TIME DASHBOARD" in out1.ascii_table
    assert not out1.is_damped
    print(f"[TASK 1: PASS] 正常遙測渲染成功 | 狀態: {out1.status_label} | VRAM: {out1.vram_peak_gb:.1f}GB")
    print(out1.ascii_table)

    # Task 2: 幾何失諧觸發 1.35x 剛性阻尼標記
    out2: DashboardSnapshot = dash.record_step(vram_gb=28.0, curvature=1.45, is_damped=True)
    assert "DAMPED_ACTIVE" in out2.status_label
    assert out2.is_damped
    print(f"[TASK 2: PASS] 幾何失諧阻尼介入渲染成功 | 狀態: {out2.status_label} (曲率: {out2.metrics['curvature']})")

    # Task 3: 顯存超標達 50GB 極限熔斷狀態機警報
    out3: DashboardSnapshot = dash.record_step(vram_gb=51.2, curvature=0.05, is_damped=False)
    assert out3.status_label == "CIRCUIT_BREAKER_TRIPPED"
    print(f"[TASK 3: PASS] 50GB 顯存熔斷狀態機警報觸發: {out3.status_label}")

    # Task 4: Phase 4 治理層 SHA-256 狀態簽名鏈路驗收
    assert len(out1.sha256_fingerprint) == 64
    assert len(out3.sha256_fingerprint) == 64
    print(f"[TASK 4: PASS] SHA-256 指紋簽名有效: {out1.sha256_fingerprint}")
    print(f"審計日誌: logs/audit/audit_OrchestratorMetricsDashboard.json")

    print("=" * 65)
    print("🎉 [ ALL 4 DASHBOARD TASKS PASSED - PRODUCTION READY ]")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
