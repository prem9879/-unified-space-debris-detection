"""
Orbit Estimation Metrics: Position/velocity RMSE, element errors
"""

import numpy as np


def position_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return np.sqrt(np.mean((y_true - y_pred) ** 2))


def velocity_rmse(v_true: np.ndarray, v_pred: np.ndarray) -> float:
    return np.sqrt(np.mean((v_true - v_pred) ** 2))


def element_errors(elements_true: np.ndarray, elements_pred: np.ndarray) -> dict:
    return {
        f"delta_{i}": np.mean(np.abs(elements_true[:, i] - elements_pred[:, i]))
        for i in range(elements_true.shape[1])
    }
