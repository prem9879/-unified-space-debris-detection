"""
Radar Preprocessing: CFAR, RDM generation, normalization
"""

import numpy as np


def cfar_1d(signal: np.ndarray, n_train: int, n_guard: int, p_fa: float) -> np.ndarray:
    """
    1D CA-CFAR thresholding for radar signal.
    """
    # TODO: Implement CA-CFAR
    pass


def generate_rdm(iq_matrix: np.ndarray) -> np.ndarray:
    """
    Generate range-Doppler map from IQ matrix.
    """
    # TODO: Implement STFT/FFT-based RDM
    pass


def normalize_rdm(rdm: np.ndarray) -> np.ndarray:
    """
    Normalize RDM to [0, 255] for YOLO input.
    """
    # TODO: Implement normalization
    pass
