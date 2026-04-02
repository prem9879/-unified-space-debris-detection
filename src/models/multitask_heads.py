"""
MultiTaskHead: Detection, classification, orbit, and collision risk heads.
"""

import torch
import torch.nn as nn


class MultiTaskHead(nn.Module):
    """
    Multi-task output heads for detection, classification, orbit estimation, and collision risk.
    """

    def __init__(self, num_classes: int = 4):
        super().__init__()
        self.detect = nn.Linear(256, 1)
        self.classify = nn.Linear(256, num_classes)
        self.orbit = nn.Linear(256, 3)
        self.collision = nn.Linear(256, 1)
        self.snr = nn.Sequential(
            nn.Linear(256, 64), nn.ReLU(inplace=True), nn.Linear(64, 1)
        )

    def forward(self, fused: torch.Tensor) -> dict:
        """Forward pass for all heads. Returns dict of outputs."""
        return {
            "detect_logits": self.detect(fused).squeeze(-1),
            "class_logits": self.classify(fused),
            "orbit_pred": self.orbit(fused),
            "collision_logits": self.collision(fused).squeeze(-1),
            "snr_pred": self.snr(fused).squeeze(-1),
        }
