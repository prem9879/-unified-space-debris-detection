"""
Detection Metrics: ROC, AUC, TPR@FPR=1e-5
"""
import numpy as np
from sklearn.metrics import roc_curve, auc, average_precision_score

def compute_roc(y_true, y_scores):
    fpr, tpr, thresholds = roc_curve(y_true, y_scores)
    return fpr, tpr, thresholds

def compute_auc(y_true, y_scores):
    return auc(*roc_curve(y_true, y_scores)[:2])

def tpr_at_fpr(y_true, y_scores, target_fpr=1e-5):
    fpr, tpr, _ = roc_curve(y_true, y_scores)
    idx = np.searchsorted(fpr, target_fpr, side='left')
    return tpr[idx] if idx < len(tpr) else tpr[-1]
