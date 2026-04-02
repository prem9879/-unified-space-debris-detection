"""
CrossModalAttentionFusion: attention-based cross-modal fusion with modality gating.
"""
import torch
import torch.nn as nn


class CrossModalAttentionFusion(nn.Module):
    """
    Fuses radar, optical, and physics features with attention, gating, and residual mixing.
    Output: (B, 256)
    """

    def __init__(self):
        super().__init__()
        self.radar_proj = nn.Sequential(nn.Linear(512, 256), nn.LayerNorm(256), nn.GELU(), nn.Dropout(0.1))
        self.optical_proj = nn.Sequential(nn.Linear(512, 256), nn.LayerNorm(256), nn.GELU(), nn.Dropout(0.1))
        self.physics_proj = nn.Sequential(nn.Linear(256, 256), nn.LayerNorm(256), nn.GELU(), nn.Dropout(0.1))
        self.attn = nn.MultiheadAttention(embed_dim=256, num_heads=8, batch_first=True)
        self.gate = nn.Sequential(
            nn.Linear(256 * 3, 256),
            nn.GELU(),
            nn.Linear(256, 3),
        )
        self.ffn = nn.Sequential(
            nn.Linear(256, 512),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(512, 256),
        )
        self.norm1 = nn.LayerNorm(256)
        self.norm2 = nn.LayerNorm(256)

    def forward(self, radar: torch.Tensor, optical: torch.Tensor, physics: torch.Tensor) -> torch.Tensor:
        """Forward pass for fusion module."""
        radar_token = self.radar_proj(radar)
        optical_token = self.optical_proj(optical)
        physics_token = self.physics_proj(physics)

        tokens = torch.stack([radar_token, optical_token, physics_token], dim=1)
        attended, _ = self.attn(tokens, tokens, tokens)

        gate_weights = torch.softmax(self.gate(torch.cat([radar_token, optical_token, physics_token], dim=-1)), dim=-1)
        gated = (
            gate_weights[:, 0:1] * radar_token
            + gate_weights[:, 1:2] * optical_token
            + gate_weights[:, 2:3] * physics_token
        )

        fused = self.norm1(gated + attended.mean(dim=1))
        fused = self.norm2(fused + self.ffn(fused))
        return fused
