"""
Multi-Task Loss with GradNorm Dynamic Weighting
Implements L_total as described in the system equations.
"""

import torch
import torch.nn as nn


class MultiTaskLoss(nn.Module):
    """
    Combines detection, classification, orbit, and collision losses with dynamic weights.
    """

    def __init__(self, alpha=1.0, beta=1.0, gamma=1.0, delta=1.0):
        super().__init__()
        self.alpha = nn.Parameter(torch.tensor(alpha, dtype=torch.float32))
        self.beta = nn.Parameter(torch.tensor(beta, dtype=torch.float32))
        self.gamma = nn.Parameter(torch.tensor(gamma, dtype=torch.float32))
        self.delta = nn.Parameter(torch.tensor(delta, dtype=torch.float32))
        # TODO: Implement GradNorm update

    def forward(self, l_detect, l_classify, l_orbit, l_collision):
        """
        Args:
            l_detect: Detection loss
            l_classify: Classification loss
            l_orbit: Orbit estimation loss
            l_collision: Collision risk loss
        Returns:
            Total multi-task loss (scalar)
        """
        total = (
            self.alpha * l_detect
            + self.beta * l_classify
            + self.gamma * l_orbit
            + self.delta * l_collision
        )
        return total
