"""
PHANToM Grid - Production Guard Pipeline Wrapper
封裝四大生產級約束：Ingress 幾何合約、VRAMGuard 熔斷、Critic 哨兵阻尼、ZDR 物理銷毀
"""

import sys
import gc
import weakref
import hashlib
from typing import Optional
from dataclasses import dataclass
import torch


@dataclass
class GuardConfig:
    norm_tolerance: float = 1e-5
    vram_max_gb: float = 50.0
    critic_damping: float = 1.35
    critic_epipolar_thresh: float = 1e-4
    secure_zero: bool = True


class IngressContractViolation(ValueError):
    pass


class VRAMGuardBreachError(RuntimeError):
    pass


class PhantomGuardPipeline:
    def __init__(self, config: Optional[GuardConfig] = None):
        self.cfg = config or GuardConfig()
        self._tracked_tensors = weakref.WeakSet()
        self._audit_hash = hashlib.sha256()

    def validate_ingress_quaternion(self, q: torch.Tensor) -> torch.Tensor:
        if q.dim() < 1 or q.shape[-1] != 4:
            raise IngressContractViolation(f"輸入四元數形狀不符，預期最後維度為 4，實得 {q.shape}")
        
        norm = torch.linalg.norm(q, dim=-1, keepdim=True)
        violation = torch.abs(norm - 1.0)
        
        if torch.any(violation > self.cfg.norm_tolerance):
            max_drift = violation.max().item()
            raise IngressContractViolation(
                f"[TASK 1] 幾何流形奇異點漂移: 最大偏差 {max_drift:.3e} > 閾值 {self.cfg.norm_tolerance}"
            )
        return q

    def check_vram_watermark(self):
        if torch.cuda.is_available():
            allocated_gb = torch.cuda.memory_allocated() / (1024 ** 3)
            if allocated_gb >= self.cfg.vram_max_gb:
                raise VRAMGuardBreachError(
                    f"[TASK 2] VRAMGuard 熔斷觸發！當前顯存 {allocated_gb:.2f}GB 已達警戒線 {self.cfg.vram_max_gb}GB"
                )

    def apply_critic_damping(self, epipolar_error: torch.Tensor, update_tensor: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            mean_error = epipolar_error.mean().item()
            if mean_error > self.cfg.critic_epipolar_thresh:
                return update_tensor / self.cfg.critic_damping
        return update_tensor

    def register_resource(self, tensor: torch.Tensor):
        if isinstance(tensor, torch.Tensor) and tensor.is_cuda:
            self._tracked_tensors.add(tensor)
            self._audit_hash.update(str(tensor.shape).encode("utf-8"))

    def zdr_secure_purge(self) -> str:
        if self.cfg.secure_zero:
            for t in list(self._tracked_tensors):
                if t is not None and hasattr(t, "data"):
                    try:
                        t.detach_()
                        t.zero_()
                    except Exception:
                        pass
        
        self._tracked_tensors.clear()
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        return self._audit_hash.hexdigest()[:16]

    def __enter__(self):
        self.check_vram_watermark()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.zdr_secure_purge()
        return False
