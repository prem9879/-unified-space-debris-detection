from __future__ import annotations

from app.schemas.trajectory import TrajectoryPoint, TrajectoryRequest, TrajectoryResponse


class TrajectoryService:
    def predict(self, payload: TrajectoryRequest) -> TrajectoryResponse:
        points = payload.history
        if len(points) < 2:
            return TrajectoryResponse(
                object_id=payload.object_id,
                method="convlstm-fallback-linear",
                predicted=points,
                uncertainty_band_km=4.0,
            )

        last = points[-1]
        prev = points[-2]
        dt = max(1.0, last.t_s - prev.t_s)
        vx = (last.x_km - prev.x_km) / dt
        vy = (last.y_km - prev.y_km) / dt
        vz = (last.z_km - prev.z_km) / dt

        step = 30
        horizon = max(step, payload.horizon_s)
        predicted: list[TrajectoryPoint] = []
        t_cursor = last.t_s
        x = last.x_km
        y = last.y_km
        z = last.z_km

        while t_cursor < last.t_s + horizon:
            t_cursor += step
            x += vx * step
            y += vy * step
            z += vz * step
            predicted.append(TrajectoryPoint(t_s=t_cursor, x_km=x, y_km=y, z_km=z))

        return TrajectoryResponse(
            object_id=payload.object_id,
            method="convlstm-fallback-linear",
            predicted=predicted,
            uncertainty_band_km=2.5,
        )
