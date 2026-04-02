"""
UnifiedDebrisNet: Main model class combining all modules.
"""

import torch.nn as nn
from .radar_encoder import RadarEncoder
from .optical_encoder import TemporalOpticalEncoder
from .physics_encoder import PhysicsEncoder
from .fusion import CrossModalAttentionFusion
from .multitask_heads import MultiTaskHead


class UnifiedDebrisNet(nn.Module):
    """
    Unified multi-modal debris detection and characterization model.
    """

    def __init__(self, num_classes: int = 4):
        super().__init__()
        self.radar_encoder = RadarEncoder()
        self.optical_encoder = TemporalOpticalEncoder()
        self.physics_encoder = PhysicsEncoder()
        self.fusion = CrossModalAttentionFusion()
        self.heads = MultiTaskHead(num_classes=num_classes)

    def forward(self, radar, optical, physics):
        f_radar = self.radar_encoder(radar)
        f_optical = self.optical_encoder(optical)
        f_physics = self.physics_encoder(physics)
        fused = self.fusion(f_radar, f_optical, f_physics)
        outputs = self.heads(fused)
        return outputs
