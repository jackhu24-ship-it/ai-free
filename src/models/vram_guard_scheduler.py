"""
PHANToM Grid: VRAMGuard Dynamic Scheduler (動態顯存熔斷調度器)
規格先行架構：50GB 警戒防線、自適應 Chunking 切片、熔斷退避與 ZDR 接口
"""
from typing import Callable, Dict, Tuple, Optional
import gc
import torch
import torch.nn as nn

class MemoryBackoffReject(Exception):
    """當顯存超越 50GB 臨界熔斷線時拋出的非阻塞退避異常"""
    pass

class VRAMGuardDynamicScheduler(nn.Module):
    def __init__(
        self,
        hard_limit_gb: float = 50.0,
        warning_limit_gb: float = 35.0,
        default_chunk_size: int = 2,
    ):
        super().__init__()
        self.hard_limit_gb = float(hard_limit_gb)
        self.warning_limit_gb = float(warning_limit_gb)
        self.default_chunk_size = int(default_chunk_size)

        self.register_buffer("simulated_vram_gb", torch.tensor(0.0))
        self.register_buffer("rejections_count", torch.tensor(0, dtype=torch.long))

    def _get_current_vram_gb(self) -> float:
        if torch.cuda.is_available():
            return torch.cuda.memory_allocated() / (1024 ** 3)
        return self.simulated_vram_gb.item()

    def set_simulated_vram_gb(self, vram_gb: float) -> None:
        """用於 CPU 或模擬環境下的壓力測試顯存設定"""
        self.simulated_vram_gb.copy_(torch.tensor(float(vram_gb)))

    def _phase1_ingress_check(self, vram_gb: float) -> str:
        if vram_gb >= self.hard_limit_gb:
            self.rejections_count += 1
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()
            raise MemoryBackoffReject(
                f"[Phase 1 Ingress] 顯存水位 ({vram_gb:.2f} GB) 超越熔斷警戒線 ({self.hard_limit_gb} GB)！"
            )
        if vram_gb >= self.warning_limit_gb:
            return "CHUNKED"
        return "DIRECT"

    def schedule_execution(
        self,
        tensor_fn: Callable[[torch.Tensor], Tuple[torch.Tensor, Dict[str, any]]],
        points: torch.Tensor,
    ) -> Tuple[torch.Tensor, Dict[str, any]]:
        current_vram = self._get_current_vram_gb()
        mode = self._phase1_ingress_check(current_vram)

        B, T, N, _ = points.shape

        if mode == "DIRECT":
            # 顯存安全：直通運算
            out, metrics = tensor_fn(points)
            metrics.update({
                "vram_gb": current_vram,
                "dispatch_mode": "DIRECT",
                "chunk_size": T,
                "rejections_count": self.rejections_count.item(),
            })
            return out, metrics

        # 顯存警戒：自適應沿時間維度分塊
        chunk_size = self.default_chunk_size
        out_chunks = []
        last_metrics = {}

        for start_idx in range(0, T, chunk_size):
            end_idx = min(start_idx + chunk_size, T)
            sub_points = points[:, start_idx:end_idx]
            sub_out, sub_metrics = tensor_fn(sub_points)
            out_chunks.append(sub_out)
            last_metrics = sub_metrics

        out = torch.cat(out_chunks, dim=1) if out_chunks[0].dim() == points.dim() else torch.cat(out_chunks, dim=-1)
        
        last_metrics.update({
            "vram_gb": current_vram,
            "dispatch_mode": "CHUNKED",
            "chunk_size": chunk_size,
            "rejections_count": self.rejections_count.item(),
        })
        return out, last_metrics

    def reset_state(self) -> None:
        self.simulated_vram_gb.zero_()
        self.rejections_count.zero_()
