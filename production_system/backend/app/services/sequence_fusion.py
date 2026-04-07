from __future__ import annotations

import numpy as np

from app.schemas.collision import CollisionHistoryPoint


class SequenceFusionEngine:
    """Lightweight sequence adapters that emulate GRU/LSTM and Transformer behavior.

    This module is intentionally deterministic and dependency-light for backend reliability.
    It can be replaced with trained model adapters later without changing the collision API contract.
    """

    @staticmethod
    def _history_to_arrays(history: list[CollisionHistoryPoint]) -> tuple[np.ndarray, np.ndarray] | None:
        if len(history) < 2:
            return None

        times = np.asarray([point.t_s for point in history], dtype=np.float64)
        xyz = np.asarray([[point.x_km, point.y_km, point.z_km] for point in history], dtype=np.float64)
        return times, xyz

    @staticmethod
    def _lstm_gru_velocity(history: list[CollisionHistoryPoint]) -> np.ndarray | None:
        arrays = SequenceFusionEngine._history_to_arrays(history)
        if arrays is None:
            return None

        times, xyz = arrays
        dts = np.diff(times)
        dts = np.where(dts <= 0.0, 1.0, dts)
        velocities = np.diff(xyz, axis=0) / dts[:, None]

        # Exponential smoothing to mimic gated recurrent memory.
        alpha = 0.65
        smoothed = velocities[0]
        for vec in velocities[1:]:
            smoothed = alpha * vec + (1.0 - alpha) * smoothed
        return smoothed

    @staticmethod
    def _transformer_velocity(history: list[CollisionHistoryPoint]) -> np.ndarray | None:
        arrays = SequenceFusionEngine._history_to_arrays(history)
        if arrays is None:
            return None

        times, xyz = arrays
        dts = np.diff(times)
        dts = np.where(dts <= 0.0, 1.0, dts)
        velocities = np.diff(xyz, axis=0) / dts[:, None]

        idx = np.arange(1, len(velocities) + 1, dtype=np.float64)
        weights = idx / idx.sum()
        return np.sum(velocities * weights[:, None], axis=0)

    @staticmethod
    def fused_relative_velocity(
        history_a: list[CollisionHistoryPoint],
        history_b: list[CollisionHistoryPoint],
        fallback_rel_velocity: np.ndarray,
    ) -> tuple[np.ndarray, dict[str, object]]:
        lstm_a = SequenceFusionEngine._lstm_gru_velocity(history_a)
        lstm_b = SequenceFusionEngine._lstm_gru_velocity(history_b)
        tr_a = SequenceFusionEngine._transformer_velocity(history_a)
        tr_b = SequenceFusionEngine._transformer_velocity(history_b)

        if lstm_a is None or lstm_b is None or tr_a is None or tr_b is None:
            return fallback_rel_velocity, {
                "fusion_method": "fallback-relative-velocity",
                "lstm_gru_available": False,
                "transformer_available": False,
            }

        rel_lstm = lstm_b - lstm_a
        rel_transformer = tr_b - tr_a
        fused = 0.55 * rel_lstm + 0.45 * rel_transformer

        return fused, {
            "fusion_method": "gru-lstm-transformer-adapter",
            "lstm_gru_available": True,
            "transformer_available": True,
            "lstm_relative_speed": float(np.linalg.norm(rel_lstm)),
            "transformer_relative_speed": float(np.linalg.norm(rel_transformer)),
        }

    @staticmethod
    def ai_probability_from_forecast(
        relative_position: np.ndarray,
        fused_relative_velocity: np.ndarray,
        horizon_s: int,
    ) -> float:
        horizon = max(60, int(horizon_s))
        sample_times = np.linspace(0.0, float(horizon), num=25)

        min_distance = float("inf")
        for t_val in sample_times:
            pos = relative_position + fused_relative_velocity * t_val
            distance = float(np.linalg.norm(pos))
            if distance < min_distance:
                min_distance = distance

        relative_speed = float(np.linalg.norm(fused_relative_velocity))
        speed_term = np.clip(relative_speed / 10.0, 0.15, 1.0)
        return float(np.clip(np.exp(-min_distance / 9.0) * speed_term, 0.0, 1.0))
