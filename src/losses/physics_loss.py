"""
Physics-Informed Radar SNR Constraint Loss
Implements L_physics_radar as described in the system equations.
"""

import torch
import torch.nn as nn


class PhysicsRadarLoss(nn.Module):
    """
    Penalizes predictions that violate radar SNR physical constraints.
    """

    def __init__(
        self,
        pt: float,
        g: float,
        lamb: float,
        l_val: float,
        k_b: float,
        t: float,
        b: float,
        nf: float,
    ):
        super().__init__()
        self.pt = pt
        self.g = g
        self.lamb = lamb
        self.l = l_val
        self.k_b = k_b
        self.t = t
        self.b = b
        self.nf = nf

    def forward(
        self, snr_pred: torch.Tensor, sigma_rcs: torch.Tensor, r: torch.Tensor
    ) -> torch.Tensor:
        """
        Args:
            snr_pred: Predicted SNR (batch,)
            sigma_rcs: Radar cross-section (batch,)
            r: Range (batch,)
        Returns:
            Physics-informed loss (scalar)
        """
        snr_required = (self.pt * self.g**2 * self.lamb**2 * sigma_rcs) / (
            (4 * torch.pi) ** 3 * r**4 * self.l * self.k_b * self.t * self.b * self.nf
        )
        loss = torch.relu(snr_required - snr_pred).mean()
        return loss
