from __future__ import annotations

from datetime import datetime, timezone


class AlertService:
    def __init__(self) -> None:
        self.history: list[dict[str, object]] = []

    def trigger(self, channel: str, risk: float, message: str) -> dict[str, object]:
        event = {
            "id": f"ALERT-{len(self.history)+1:05d}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "channel": channel,
            "risk": risk,
            "message": message,
            "status": "sent",
        }
        self.history.append(event)
        self.history = self.history[-2000:]
        return event

    def list_history(self) -> list[dict[str, object]]:
        return list(reversed(self.history[-200:]))
