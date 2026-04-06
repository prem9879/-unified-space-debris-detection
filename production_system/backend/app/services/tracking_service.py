from __future__ import annotations

from dataclasses import dataclass, field
from time import time


@dataclass
class TrackState:
    object_id: str
    history: list[list[float]] = field(default_factory=list)
    last_seen: float = field(default_factory=time)


class TrackingService:
    def __init__(self, max_tracks: int = 100) -> None:
        self.max_tracks = max_tracks
        self.tracks: dict[str, TrackState] = {}

    def update(self, object_id: str, center_xy: list[float]) -> dict[str, object]:
        state = self.tracks.get(object_id)
        if state is None:
            if len(self.tracks) >= self.max_tracks:
                oldest = min(self.tracks.values(), key=lambda item: item.last_seen)
                self.tracks.pop(oldest.object_id, None)
            state = TrackState(object_id=object_id)
            self.tracks[object_id] = state

        state.history.append(center_xy)
        state.history = state.history[-120:]
        state.last_seen = time()

        return {
            "object_id": object_id,
            "history": state.history,
            "points": len(state.history),
        }
