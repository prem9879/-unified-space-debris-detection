"""
Main Training Loop for UnifiedDebrisNet
Handles mixed precision, GradNorm, logging, and checkpointing.
"""

import torch
from src.models.unified_debris_net import UnifiedDebrisNet


class Trainer:
    """
    Training loop for UnifiedDebrisNet with multi-task loss and logging.
    """

    def __init__(
        self,
        model: UnifiedDebrisNet,
        dataloaders: dict,
        optimizer,
        loss_fn,
        aux_losses: dict | None = None,
        device: str = "cuda",
    ):
        self.model = model.to(device)
        self.dataloaders = dataloaders
        self.optimizer = optimizer
        self.loss_fn = loss_fn
        self.aux_losses = aux_losses or {}
        self.device = device
        self.bce = torch.nn.BCEWithLogitsLoss()
        self.ce = torch.nn.CrossEntropyLoss()
        self.mse = torch.nn.MSELoss()

    def _move_batch(self, batch: dict) -> dict:
        return {
            k: v.to(self.device) if torch.is_tensor(v) else v for k, v in batch.items()
        }

    def _compute_loss(self, outputs: dict, batch: dict) -> torch.Tensor:
        l_detect = self.bce(outputs["detect_logits"], batch["detect"])
        l_class = self.ce(outputs["class_logits"], batch["class"])
        l_orbit = self.mse(outputs["orbit_pred"], batch["orbit"])
        l_collision = self.bce(outputs["collision_logits"], batch["collision"])

        total = self.loss_fn(l_detect, l_class, l_orbit, l_collision)

        if "physics" in self.aux_losses:
            total = total + 0.1 * self.aux_losses["physics"](
                outputs["snr_pred"], batch["sigma_rcs"], batch["range"]
            )
        if "sgp4" in self.aux_losses:
            total = total + 0.1 * self.aux_losses["sgp4"](
                outputs["orbit_pred"], batch["orbit_sgp4"]
            )
        if "ece" in self.aux_losses:
            probs = torch.sigmoid(outputs["collision_logits"])
            total = total + 0.1 * self.aux_losses["ece"](probs, batch["collision"])
        return total

    def train_epoch(self):
        self.model.train()
        running = 0.0
        batches = 0
        for batch in self.dataloaders["train"]:
            batch = self._move_batch(batch)
            self.optimizer.zero_grad(set_to_none=True)
            outputs = self.model(batch["radar"], batch["optical"], batch["physics"])
            loss = self._compute_loss(outputs, batch)
            loss.backward()
            self.optimizer.step()
            running += loss.item()
            batches += 1
        return running / max(1, batches)

    def validate(self):
        self.model.eval()
        running = 0.0
        batches = 0
        with torch.no_grad():
            for batch in self.dataloaders["val"]:
                batch = self._move_batch(batch)
                outputs = self.model(batch["radar"], batch["optical"], batch["physics"])
                loss = self._compute_loss(outputs, batch)
                running += loss.item()
                batches += 1
        return running / max(1, batches)

    def fit(self, epochs: int):
        history = {"train_loss": [], "val_loss": []}
        for epoch in range(epochs):
            train_loss = self.train_epoch()
            val_loss = self.validate()
            history["train_loss"].append(train_loss)
            history["val_loss"].append(val_loss)
            print(
                f"Epoch {epoch + 1}/{epochs} - train_loss: {train_loss:.4f} - val_loss: {val_loss:.4f}"
            )
        return history
