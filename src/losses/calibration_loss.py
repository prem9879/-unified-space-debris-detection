"""
Calibration Loss for Collision Probability (ECE)
Implements Expected Calibration Error minimization.
"""

import torch
import torch.nn as nn


class ECELoss(nn.Module):
    """
    Computes Expected Calibration Error (ECE) for probabilistic outputs.
    """

    def __init__(self, n_bins: int = 15):
        super().__init__()
        self.n_bins = n_bins

    def forward(self, probs: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        """
        Args:
            probs: Predicted probabilities (batch,)
            labels: True binary labels (batch,)
        Returns:
            ECE loss (scalar)
        """
        bins = torch.linspace(0, 1, self.n_bins + 1)
        ece = torch.zeros(1, device=probs.device)
        for i in range(self.n_bins):
            mask = (probs > bins[i]) & (probs <= bins[i + 1])
            if mask.sum() > 0:
                acc = labels[mask].float().mean()
                conf = probs[mask].mean()
                ece += (mask.float().mean()) * torch.abs(acc - conf)
        return ece
