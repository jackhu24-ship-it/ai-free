import hashlib
import json
import weakref
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import torch

class ZDRAuditManager:
    """
    PHANToM Grid 零數據殘留 (ZDR) 與 SHA-256 稽核存證管理器
    """
    def __init__(self, log_dir: str = "logs/audit"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._tracked_refs: List[weakref.ref] = []

    def register_intermediate(self, tensor: torch.Tensor) -> None:
        """註冊需要被嚴格銷毀的中介張量弱引用"""
        if isinstance(tensor, torch.Tensor):
            self._tracked_refs.append(weakref.ref(tensor))

    def compute_fingerprint(self, tensor: torch.Tensor, prefix_bytes: int = 64) -> str:
        """計算張量前 N bytes 之 SHA-256 狀態指紋"""
        cpu_tensor = tensor.detach().contiguous().cpu()
        byte_data = cpu_tensor.numpy().tobytes()[:prefix_bytes]
        return hashlib.sha256(byte_data).hexdigest()

    def wipe_tensor(self, tensor: Optional[torch.Tensor]) -> None:
        """物理就地擦除張量記憶體 (zero_ 原地清零)"""
        if tensor is not None and isinstance(tensor, torch.Tensor):
            if tensor.is_floating_point() or tensor.is_complex():
                tensor.detach().zero_()
            else:
                tensor.detach().fill_(0)

    def verify_and_audit(
        self,
        module_name: str,
        output_tensor: torch.Tensor,
        metrics: Dict[str, Any],
        intermediates_to_wipe: Optional[List[torch.Tensor]] = None,
    ) -> Dict[str, Any]:
        """
        執行物理銷毀、弱引用檢驗與日誌持久化
        """
        # 1. 物理清零中介張量
        if intermediates_to_wipe:
            for t in intermediates_to_wipe:
                self.wipe_tensor(t)

        # 2. 檢驗中介張量是否已歸零或失去強引用
        all_cleared = True
        for ref in self._tracked_refs:
            obj = ref()
            if obj is not None:
                # 若物件尚未被 GC，確認其數值已被清零
                if obj.abs().max().item() > 0.0:
                    all_cleared = False

        # 3. 計算輸出狀態指紋
        sha256_hash = self.compute_fingerprint(output_tensor)

        # 4. 生成審計紀錄
        audit_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "module": module_name,
            "zdr_verified": all_cleared,
            "sha256_fingerprint": sha256_hash,
            "output_shape": list(output_tensor.shape),
            "output_dtype": str(output_tensor.dtype),
            "metrics": {k: float(v) if isinstance(v, (int, float, torch.Tensor)) else str(v) for k, v in metrics.items()},
        }

        # 5. 寫入審計 JSON 日誌
        log_file = self.log_dir / f"audit_{module_name}.json"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(audit_record, f, indent=2, ensure_ascii=False)

        return audit_record
