from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import get_settings


@dataclass
class AdapterStatus:
    name: str
    enabled: bool
    reason: str


class ModelAdapters:
    """Lazy adapter registry for optional SOTA model runtimes.

    This class exposes a stable interface even when heavyweight packages are
    unavailable in the environment.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self.statuses = {
            "yolov8": self._probe("ultralytics", settings.yolov8_checkpoint),
            "vit": self._probe("transformers", settings.vit_checkpoint),
            "sam": self._probe("segment_anything", settings.sam_checkpoint),
            "convlstm": self._probe("torch", settings.convlstm_checkpoint),
            "bayesian_uq": self._probe("torch", settings.bayesian_checkpoint),
        }

    def _probe(self, module_name: str, checkpoint_path: str) -> AdapterStatus:
        checkpoint_exists = Path(checkpoint_path).exists()
        try:
            __import__(module_name)
            if checkpoint_exists:
                return AdapterStatus(name=module_name, enabled=True, reason="available+checkpoint")
            return AdapterStatus(name=module_name, enabled=False, reason="checkpoint-missing")
        except Exception:
            return AdapterStatus(name=module_name, enabled=False, reason="fallback")

    def registry_payload(self) -> dict[str, dict[str, Any]]:
        return {
            key: {"enabled": status.enabled, "reason": status.reason}
            for key, status in self.statuses.items()
        }
