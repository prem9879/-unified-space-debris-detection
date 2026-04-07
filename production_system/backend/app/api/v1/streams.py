from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ws.manager import manager


router = APIRouter()


def _live_payload() -> dict:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "objects": [
            {
                "id": f"OBJ-{i:03d}",
                "risk": round(random.random(), 3),
                "velocity_km_s": round(7.2 + random.random() * 2.1, 3),
            }
            for i in range(1, 6)
        ],
    }


@router.get("/live-tracking")
async def live_tracking_snapshot() -> dict:
    return _live_payload()


@router.websocket("/live")
async def live_stream(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            payload = _live_payload()
            await websocket.send_json(payload)
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/live-tracking")
async def live_tracking_stream(websocket: WebSocket) -> None:
    await live_stream(websocket)
