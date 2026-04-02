"""
Collision Risk Metrics: ECE, Brier, reliability diagram, AUC-ROC
"""
from sklearn.metrics import brier_score_loss, roc_auc_score
import numpy as np

def compute_ece(y_true, y_prob, n_bins=15):
    y_true = np.asarray(y_true, dtype=np.float32)
    y_prob = np.asarray(y_prob, dtype=np.float32)

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_ids = np.digitize(y_prob, bins) - 1
    bin_ids = np.clip(bin_ids, 0, n_bins - 1)

    ece = 0.0
    for b in range(n_bins):
        mask = bin_ids == b
        if not np.any(mask):
            continue
        conf = float(np.mean(y_prob[mask]))
        acc = float(np.mean(y_true[mask]))
        weight = float(np.mean(mask))
        ece += weight * abs(acc - conf)
    return float(ece)

def compute_brier(y_true, y_prob):
    return brier_score_loss(y_true, y_prob)

def compute_auc_roc(y_true, y_prob):
    return roc_auc_score(y_true, y_prob)
