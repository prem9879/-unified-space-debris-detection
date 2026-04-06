from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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
        self.statuses = {
            "yolov8": self._probe("ultralytics"),
            "vit": self._probe("transformers"),
            "sam": self._probe("segment_anything"),
            "convlstm": self._probe("torch"),
            "bayesian_uq": self._probe("torch"),
        }

    def _probe(self, module_name: str) -> AdapterStatus:
        try:
            __import__(module_name)
            return AdapterStatus(name=module_name, enabled=True, reason="available")
        except Exception:
            return AdapterStatus(name=module_name, enabled=False, reason="fallback")

    def registry_payload(self) -> dict[str, dict[str, Any]]:
        return {
            key: {"enabled": status.enabled, "reason": status.reason}
            for key, status in self.statuses.items()
        }
