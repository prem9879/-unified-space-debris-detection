from __future__ import annotations

from datetime import datetime, timezone


class ExternalSourceService:
    def pull_tle_snapshot(self) -> dict[str, object]:
        return {
            "source": "nasa+space-track",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "objects": 12874,
            "status": "ok",
        }

    def pull_esa_optical_feed(self) -> dict[str, object]:
        return {
            "source": "esa_optical",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "frames": 22,
            "status": "ok",
        }

    def synthetic_blender_job(self, scenes: int) -> dict[str, object]:
        return {
            "generator": "blender",
            "scenes_requested": scenes,
            "status": "queued",
            "estimated_duration_min": max(1, scenes // 2),
        }
