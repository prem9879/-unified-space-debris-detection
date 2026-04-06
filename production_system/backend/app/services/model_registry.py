from __future__ import annotations


class ModelRegistryService:
    def __init__(self) -> None:
        self.models = [
            {"name": "yolov8", "version": "8.2.0", "role": "real-time detection", "status": "active"},
            {"name": "vit", "version": "1.1.0", "role": "high-accuracy classification", "status": "active"},
            {"name": "sam", "version": "2.0.0", "role": "segmentation", "status": "active"},
            {"name": "convlstm", "version": "0.9.2", "role": "trajectory prediction", "status": "shadow"},
            {"name": "bayesian_uq", "version": "0.7.1", "role": "uncertainty quantification", "status": "active"},
        ]

    def list_models(self) -> list[dict[str, str]]:
        return self.models

    def promote(self, name: str, version: str) -> dict[str, str]:
        for model in self.models:
            if model["name"] == name and model["version"] == version:
                model["status"] = "active"
                return model
        raise ValueError("Model version not found")
