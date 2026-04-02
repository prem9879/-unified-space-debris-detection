"""
TemporalOpticalEncoder: compact CNN stem plus temporal self-attention for optical frames.
"""

import torch
import torch.nn as nn


class TemporalOpticalEncoder(nn.Module):
    """
    Encodes sequences of optical frames using a CNN stem and transformer encoder.
    Output: (B, 512)
    """

    def __init__(self):
        super().__init__()
        self.frame_cnn = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.GELU(),
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.GELU(),
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.GELU(),
            nn.AdaptiveAvgPool2d((1, 1)),
        )
        self.frame_proj = nn.Sequential(
            nn.Linear(128, 256),
            nn.LayerNorm(256),
            nn.GELU(),
        )
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=256,
            nhead=8,
            dim_feedforward=512,
            dropout=0.1,
            batch_first=True,
            activation="gelu",
        )
        self.temporal_encoder = nn.TransformerEncoder(encoder_layer, num_layers=2)
        self.temporal_positional = nn.Parameter(torch.randn(1, 16, 256) * 0.02)
        self.output_head = nn.Sequential(
            nn.Linear(256, 512),
            nn.GELU(),
            nn.LayerNorm(512),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass for optical encoder."""
        b, t, c, h, w = x.shape
        frames = x.view(b * t, c, h, w)
        feats = self.frame_cnn(frames).flatten(1)
        feats = self.frame_proj(feats).view(b, t, -1)
        pos = self.temporal_positional[:, :t, :]
        encoded = self.temporal_encoder(feats + pos)
        pooled = encoded.mean(dim=1)
        return self.output_head(pooled)
