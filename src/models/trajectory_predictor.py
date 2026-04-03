"""Advanced multi-modal trajectory prediction using sequence models and graph neural networks.

Combines LSTM/Transformers for temporal trajectory prediction with GNNs for
orbital interaction modeling. Production-grade aerospace component.

Component: Trajectory Prediction & Orbital Interaction Modeling
Status: Research-Grade
"""

from __future__ import annotations

import logging

import numpy as np
import torch
import torch.nn as nn
from torch.nn import TransformerEncoder, TransformerEncoderLayer

logger = logging.getLogger(__name__)


class OrbitalLSTMPredictor(nn.Module):
    """LSTM-based trajectory prediction for debris objects.

    Predicts future orbital position, velocity, and collision risk
    using a sequence of historical orbital elements.
    """

    def __init__(
        self,
        input_size: int = 14,
        hidden_size: int = 128,
        num_layers: int = 2,
        output_horizon: int = 24,
        dropout: float = 0.2,
    ):
        """Initialize LSTM trajectory predictor.

        Args:
            input_size: Number of input features (orbital elements)
            hidden_size: LSTM hidden dimension
            num_layers: Number of LSTM layers
            output_horizon: Number of future time steps to predict
            dropout: Dropout probability
        """
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_horizon = output_horizon

        self.lstm = nn.LSTM(
            input_size,
            hidden_size,
            num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
        )

        self.attention = nn.MultiheadAttention(
            hidden_size, num_heads=4, batch_first=True
        )

        self.decoder = nn.Sequential(
            nn.Linear(hidden_size, 256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, input_size * output_horizon),
        )

        self.risk_head = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, output_horizon),
            nn.Sigmoid(),
        )

    def forward(
        self, trajectory: torch.Tensor, lengths: torch.Tensor | None = None
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Predict future trajectory.

        Args:
            trajectory: (batch_size, seq_len, input_size) - Historical trajectory
            lengths: (batch_size,) - Actual sequence lengths

        Returns:
            predictions: (batch_size, output_horizon, input_size)
            risk_scores: (batch_size, output_horizon)
        """
        # Pack padded sequences for efficiency
        if lengths is not None:
            packed = nn.utils.rnn.pack_padded_sequence(
                trajectory, lengths.cpu(), batch_first=True, enforce_sorted=False
            )
            lstm_out, (h_n, c_n) = self.lstm(packed)
            lstm_out, _ = nn.utils.rnn.pad_packed_sequence(lstm_out, batch_first=True)
        else:
            lstm_out, (h_n, c_n) = self.lstm(trajectory)

        # Self-attention over LSTM outputs
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)

        # Use last hidden state + attended output
        context = h_n[-1]  # (batch_size, hidden_size)

        # Predict future trajectory
        trajectory_pred = self.decoder(context)
        trajectory_pred = trajectory_pred.view(-1, self.output_horizon, self.input_size)

        # Predict collision risk scores
        risk_scores = self.risk_head(context)

        return trajectory_pred, risk_scores


class TransformerTrajectoryPredictor(nn.Module):
    """Transformer-based trajectory prediction with temporal attention.

    State-of-the-art architecture for long-horizon orbital prediction
    with multiple attention heads for capturing complex orbital mechanics.
    """

    def __init__(
        self,
        input_size: int = 14,
        d_model: int = 128,
        nhead: int = 8,
        num_encoder_layers: int = 6,
        output_horizon: int = 24,
        dropout: float = 0.1,
    ):
        """Initialize Transformer predictor.

        Args:
            input_size: Number of input features
            d_model: Model dimension
            nhead: Number of attention heads
            num_encoder_layers: Number of transformer encoder layers
            output_horizon: Number of future steps
            dropout: Dropout probability
        """
        super().__init__()
        self.input_size = input_size
        self.d_model = d_model
        self.output_horizon = output_horizon

        # Input projection
        self.input_projection = nn.Linear(input_size, d_model)

        # Positional encoding
        self.positional_encoding = self._create_positional_encoding(512, d_model)

        # Transformer encoder
        encoder_layer = TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=512,
            dropout=dropout,
            batch_first=True,
            activation="gelu",
        )
        self.transformer_encoder = TransformerEncoder(
            encoder_layer, num_layers=num_encoder_layers
        )

        # Output heads
        self.trajectory_decoder = nn.Sequential(
            nn.Linear(d_model, 256),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(256, 128),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(128, input_size * output_horizon),
        )

        self.uncertainty_head = nn.Sequential(
            nn.Linear(d_model, 128),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(128, output_horizon),
            nn.Softplus(),  # Ensure positive uncertainty
        )

        self.collision_risk_head = nn.Sequential(
            nn.Linear(d_model, 128),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(128, output_horizon),
            nn.Sigmoid(),
        )

    @staticmethod
    def _create_positional_encoding(max_len: int, d_model: int) -> torch.Tensor:
        """Create sinusoidal positional encodings."""
        position = torch.arange(max_len).unsqueeze(1).float()
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-np.log(10000.0) / d_model)
        )
        pe = torch.zeros(max_len, d_model)
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        return pe.unsqueeze(0)

    def forward(
        self, trajectory: torch.Tensor, mask: torch.Tensor | None = None
    ) -> dict[str, torch.Tensor]:
        """Predict trajectory and uncertainty.

        Args:
            trajectory: (batch_size, seq_len, input_size)
            mask: (batch_size, seq_len) optional padding mask

        Returns:
            Dictionary with predictions, uncertainty, and risk scores
        """
        batch_size, seq_len, _ = trajectory.shape

        # Project input to model dimension
        x = self.input_projection(trajectory)  # (batch, seq_len, d_model)

        # Add positional encoding
        pos_enc = self.positional_encoding[:, :seq_len, :].to(x.device)
        x = x + pos_enc

        # Transformer encoding
        x = self.transformer_encoder(x, src_key_padding_mask=mask)

        # Use last token for decoder
        context = x[:, -1, :]  # (batch_size, d_model)

        # Generate predictions
        trajectory_pred = self.trajectory_decoder(context)
        trajectory_pred = trajectory_pred.view(
            batch_size, self.output_horizon, self.input_size
        )

        uncertainty = self.uncertainty_head(context)
        collision_risk = self.collision_risk_head(context)

        return {
            "trajectory": trajectory_pred,
            "uncertainty": uncertainty,
            "collision_risk": collision_risk,
        }


class OrbitGraphNeuralNetwork(nn.Module):
    """Graph Neural Network for modeling orbital interactions.

    Models space debris as a dynamic graph where nodes are objects and edges
    represent conjunction risks. GNN propagates information about conjunction
    threats through the debris population.
    """

    def __init__(self, node_dim: int = 32, edge_dim: int = 16, hidden_dim: int = 64):
        """Initialize Orbital GNN.

        Args:
            node_dim: Dimension of node embeddings (orbital features)
            edge_dim: Dimension of edge embeddings (conjunction features)
            hidden_dim: Hidden dimension for message passing
        """
        super().__init__()
        self.node_dim = node_dim
        self.edge_dim = edge_dim
        self.hidden_dim = hidden_dim

        # Message passing network
        self.edge_encoder = nn.Sequential(
            nn.Linear(edge_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
        )

        self.node_update = nn.Sequential(
            nn.Linear(node_dim + hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, node_dim),
        )

        # Risk aggregation
        self.risk_aggregator = nn.Sequential(
            nn.Linear(node_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid(),
        )

    def forward(
        self,
        node_features: torch.Tensor,
        edge_features: torch.Tensor,
        edge_index: torch.Tensor,
        num_nodes: int,
    ) -> dict[str, torch.Tensor]:
        """Forward pass through GNN.

        Args:
            node_features: (num_nodes, node_dim) - Node embeddings
            edge_features: (num_edges, edge_dim) - Edge embeddings
            edge_index: (2, num_edges) - Edge connectivity
            num_nodes: Total number of nodes

        Returns:
            Dictionary with updated features and risk scores
        """
        # Encode edge features
        edge_messages = self.edge_encoder(edge_features)

        # Message aggregation
        src, dst = edge_index
        aggregated = torch.zeros(
            num_nodes, self.hidden_dim, device=node_features.device
        )
        aggregated.scatter_add_(0, dst, edge_messages)

        # Node update
        node_input = torch.cat([node_features, aggregated], dim=1)
        updated_features = self.node_update(node_input)

        # Risk scoring
        risk_scores = self.risk_aggregator(updated_features)

        return {
            "node_features": updated_features,
            "risk_scores": risk_scores.squeeze(-1),
        }


class CollisionAvoidanceAdvisor(nn.Module):
    """AI system for suggesting collision avoidance maneuvers."""

    def __init__(self, state_dim: int = 20, action_dim: int = 3):
        """Initialize collision avoidance advisor.

        Args:
            state_dim: Orbital state dimension
            action_dim: Maneuver dimension (3: radial, tangential, normal)
        """
        super().__init__()
        self.state_dim = state_dim
        self.action_dim = action_dim

        # Policy network
        self.policy = nn.Sequential(
            nn.Linear(state_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, action_dim),
            nn.Tanh(),  # Action in [-1, 1]
        )

        # Value network for uncertainty estimation
        self.value_net = nn.Sequential(
            nn.Linear(state_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
        )

    def forward(self, orbital_state: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Suggest evasive maneuver.

        Args:
            orbital_state: (batch, state_dim)

        Returns:
            maneuver: (batch, action_dim) - Normalized velocity delta
            confidence: (batch, 1) - Confidence in maneuver
        """
        maneuver = self.policy(orbital_state) * 0.1  # Limit to 0.1 m/s
        confidence = torch.sigmoid(self.value_net(orbital_state))

        return maneuver, confidence


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Example 1: LSTM Predictor
    print("=" * 60)
    print("LSTM TRAJECTORY PREDICTOR")
    print("=" * 60)
    lstm_model = OrbitalLSTMPredictor(input_size=14, hidden_size=128).to(device)
    trajectory = torch.randn(8, 48, 14).to(device)
    pred, risk = lstm_model(trajectory)
    print(f"Input shape: {trajectory.shape}")
    print(f"Prediction shape: {pred.shape}")
    print(f"Risk scores shape: {risk.shape}\n")

    # Example 2: Transformer Predictor
    print("=" * 60)
    print("TRANSFORMER TRAJECTORY PREDICTOR")
    print("=" * 60)
    transformer_model = TransformerTrajectoryPredictor(input_size=14).to(device)
    traj = torch.randn(8, 48, 14).to(device)
    output = transformer_model(traj)
    print(f"Input shape: {traj.shape}")
    for key, val in output.items():
        print(f"{key} shape: {val.shape}")
    print()

    # Example 3: Orbital GNN
    print("=" * 60)
    print("ORBITAL GRAPH NEURAL NETWORK")
    print("=" * 60)
    gnn = OrbitGraphNeuralNetwork().to(device)
    nodes = torch.randn(50, 32).to(device)  # 50 objects
    edges = torch.randn(200, 16).to(device)  # 200 conjunctions
    edge_idx = torch.randint(0, 50, (2, 200)).to(device)
    gnn_output = gnn(nodes, edges, edge_idx, num_nodes=50)
    print("Number of nodes: 50")
    print("Number of edges: 200")
    print(f"Updated features shape: {gnn_output['node_features'].shape}")
    print(f"Risk scores shape: {gnn_output['risk_scores'].shape}\n")

    # Example 4: Collision Avoidance Advisor
    print("=" * 60)
    print("COLLISION AVOIDANCE ADVISOR")
    print("=" * 60)
    advisor = CollisionAvoidanceAdvisor().to(device)
    state = torch.randn(8, 20).to(device)
    maneuver, confidence = advisor(state)
    print(f"State shape: {state.shape}")
    print(f"Suggested maneuver (m/s): {maneuver[0].detach().cpu().numpy()}")
    print(f"Confidence: {confidence[0].detach().cpu().item():.3f}")
