"""
SGP4 Propagator Residual Loss
Implements L_orbit as described in the system equations.
"""
import torch
import torch.nn as nn

class SGP4ResidualLoss(nn.Module):
    """
    Penalizes orbit predictions that violate SGP4 propagation.
    """
    def __init__(self):
        super().__init__()
        # TODO: Integrate with sgp4 package for differentiable propagation

    def forward(self, r_pred: torch.Tensor, r_sgp4: torch.Tensor) -> torch.Tensor:
        """
        Args:
            r_pred: Predicted position at t+Δt (batch, 3)
            r_sgp4: SGP4 propagated position at t+Δt (batch, 3)
        Returns:
            SGP4 residual loss (scalar)
        """
        loss = torch.norm(r_pred - r_sgp4, dim=-1).mean()
        return loss
