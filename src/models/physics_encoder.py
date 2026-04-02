"""
PhysicsEncoder: TLE MLP + SGP4 embedding for orbital catalog features.
"""

import torch
import torch.nn as nn


class PhysicsEncoder(nn.Module):
    """
    Encodes TLE and engineered features, embeds SGP4 propagation.
    Output: (B, 256)
    """

    def __init__(self):
        super().__init__()
        self.mlp = nn.Sequential(
            nn.Linear(16, 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, 256),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass for physics encoder."""
        return self.mlp(x)
