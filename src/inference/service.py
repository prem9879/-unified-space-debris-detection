"""Unified inference helpers used by CLI and Streamlit app."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F

from src.data.synthetic_dataset import make_demo_sample
from src.models.unified_debris_net import UnifiedDebrisNet


@dataclass
class InferenceResult:
    detect_probability: float
    collision_probability: float
    class_probabilities: list[float]
    predicted_class: int
    orbit_vector: list[float]
    snr_prediction: float


@dataclass
class PreprocessOptions:
    image_size: int = 64
    optical_band: str = "rgb"
    normalize_mode: str = "unit"
    camera_threshold: float = 0.0


class UnifiedInferenceService:
    """High-level API for loading checkpoints and running robust inference."""

    def __init__(self, checkpoint_path: str | Path | None, device: str | None = None, allow_demo_mode: bool = True) -> None:
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.checkpoint_path = Path(checkpoint_path) if checkpoint_path is not None else None
        self.allow_demo_mode = allow_demo_mode
        self.demo_mode = False

        checkpoint: dict[str, object] = {}
        if self.checkpoint_path is not None and self.checkpoint_path.exists():
            checkpoint = torch.load(self.checkpoint_path, map_location=self.device)
        elif not allow_demo_mode:
            raise FileNotFoundError(f"Checkpoint not found at {self.checkpoint_path}")
        else:
            self.demo_mode = True

        self.checkpoint = checkpoint
        classes = checkpoint.get("classes") if checkpoint else None
        self.num_classes = int(checkpoint.get("num_classes", len(classes) if classes else 4))
        self.model = UnifiedDebrisNet(num_classes=self.num_classes).to(self.device)
        if checkpoint:
            state_dict = self._extract_state_dict(checkpoint)
            self.model.load_state_dict(state_dict, strict=False)
        self.model.eval()

    @staticmethod
    def _extract_state_dict(checkpoint: dict) -> dict[str, torch.Tensor]:
        for key in ("model_state", "state_dict", "model", "weights"):
            state_dict = checkpoint.get(key)
            if isinstance(state_dict, dict):
                cleaned = {}
                for name, value in state_dict.items():
                    if name.startswith("module."):
                        cleaned[name[len("module."):]] = value
                    else:
                        cleaned[name] = value
                return cleaned
        raise KeyError("Checkpoint does not contain a supported model state key")

    def list_layers(self) -> list[str]:
        layers = []
        for name, module in self.model.named_modules():
            if not name:
                continue
            if isinstance(module, (torch.nn.Conv2d, torch.nn.Linear, torch.nn.LSTM, torch.nn.MultiheadAttention)):
                layers.append(name)
        return layers

    @staticmethod
    def _normalize(arr: np.ndarray, mode: str) -> np.ndarray:
        if mode == "none":
            return np.clip(arr, 0.0, 1.0)
        if mode == "zscore":
            mean = float(arr.mean())
            std = float(arr.std()) + 1e-6
            arr = (arr - mean) / std
            arr = (arr - arr.min()) / (arr.max() - arr.min() + 1e-6)
            return arr
        return np.clip(arr, 0.0, 1.0)

    @staticmethod
    def _band_select(arr: np.ndarray, mode: str) -> np.ndarray:
        # Input arr shape: (H, W, 3)
        if mode == "r":
            ch = arr[..., 0:1]
            return np.repeat(ch, 3, axis=2)
        if mode == "g":
            ch = arr[..., 1:2]
            return np.repeat(ch, 3, axis=2)
        if mode == "b":
            ch = arr[..., 2:3]
            return np.repeat(ch, 3, axis=2)
        if mode == "rg":
            z = np.zeros_like(arr[..., 0:1])
            return np.concatenate([arr[..., 0:1], arr[..., 1:2], z], axis=2)
        if mode == "rb":
            z = np.zeros_like(arr[..., 0:1])
            return np.concatenate([arr[..., 0:1], z, arr[..., 2:3]], axis=2)
        if mode == "gb":
            z = np.zeros_like(arr[..., 0:1])
            return np.concatenate([z, arr[..., 1:2], arr[..., 2:3]], axis=2)
        return arr

    @staticmethod
    def _to_base64_png(image_arr: np.ndarray) -> str:
        image_arr = np.clip(image_arr * 255.0, 0.0, 255.0).astype(np.uint8)
        img = Image.fromarray(image_arr)
        buff = BytesIO()
        img.save(buff, format="PNG")
        encoded = base64.b64encode(buff.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"

    @staticmethod
    def _image_to_tensor(
        image: Image.Image,
        channels: int = 3,
        image_size: int = 64,
        optical_band: str = "rgb",
        normalize_mode: str = "unit",
        camera_threshold: float = 0.0,
    ) -> tuple[torch.Tensor, np.ndarray]:
        image = image.convert("RGB").resize((image_size, image_size))
        arr = np.asarray(image, dtype=np.float32) / 255.0
        arr = UnifiedInferenceService._band_select(arr, optical_band)
        arr = UnifiedInferenceService._normalize(arr, normalize_mode)
        if camera_threshold > 0.0:
            arr = np.where(arr >= camera_threshold, arr, 0.0)
        tensor = torch.from_numpy(arr).permute(2, 0, 1)
        if channels == 1:
            tensor = tensor.mean(dim=0, keepdim=True)
        return tensor, arr

    def prepare_inputs(
        self,
        optical_image: Image.Image | None = None,
        radar_image: Image.Image | None = None,
        physics_vector: np.ndarray | None = None,
        options: PreprocessOptions | None = None,
    ) -> dict[str, torch.Tensor]:
        options = options or PreprocessOptions()
        sample = make_demo_sample(device=self.device)

        if optical_image is not None:
            frame, _ = self._image_to_tensor(
                optical_image,
                channels=3,
                image_size=options.image_size,
                optical_band=options.optical_band,
                normalize_mode=options.normalize_mode,
                camera_threshold=options.camera_threshold,
            )
            frame = frame.to(self.device)
            sample["optical"] = frame.unsqueeze(0).unsqueeze(0).repeat(1, 4, 1, 1, 1)

        if radar_image is not None:
            radar, _ = self._image_to_tensor(
                radar_image,
                channels=1,
                image_size=options.image_size,
                optical_band="rgb",
                normalize_mode=options.normalize_mode,
                camera_threshold=options.camera_threshold,
            )
            radar = radar.to(self.device)
            sample["radar"] = radar.unsqueeze(0)

        if physics_vector is not None:
            vector = np.asarray(physics_vector, dtype=np.float32).reshape(-1)
            if vector.shape[0] != 16:
                fixed = np.zeros((16,), dtype=np.float32)
                fixed[: min(16, vector.shape[0])] = vector[:16]
                vector = fixed
            sample["physics"] = torch.from_numpy(vector).to(self.device).unsqueeze(0)

        return sample

    def prepare_inputs_with_visuals(
        self,
        optical_image: Image.Image | None = None,
        radar_image: Image.Image | None = None,
        physics_vector: np.ndarray | None = None,
        options: PreprocessOptions | None = None,
    ) -> tuple[dict[str, torch.Tensor], dict[str, str]]:
        options = options or PreprocessOptions()
        visuals: dict[str, str] = {}

        sample = make_demo_sample(device=self.device)

        if optical_image is not None:
            frame, arr = self._image_to_tensor(
                optical_image,
                channels=3,
                image_size=options.image_size,
                optical_band=options.optical_band,
                normalize_mode=options.normalize_mode,
                camera_threshold=options.camera_threshold,
            )
            frame = frame.to(self.device)
            sample["optical"] = frame.unsqueeze(0).unsqueeze(0).repeat(1, 4, 1, 1, 1)
            visuals["optical_preprocessed"] = self._to_base64_png(arr)

        if radar_image is not None:
            radar, arr = self._image_to_tensor(
                radar_image,
                channels=1,
                image_size=options.image_size,
                optical_band="rgb",
                normalize_mode=options.normalize_mode,
                camera_threshold=options.camera_threshold,
            )
            radar = radar.to(self.device)
            sample["radar"] = radar.unsqueeze(0)
            arr_rgb = np.repeat(arr[..., :1], 3, axis=2)
            visuals["radar_preprocessed"] = self._to_base64_png(arr_rgb)

        if physics_vector is not None:
            vector = np.asarray(physics_vector, dtype=np.float32).reshape(-1)
            if vector.shape[0] != 16:
                fixed = np.zeros((16,), dtype=np.float32)
                fixed[: min(16, vector.shape[0])] = vector[:16]
                vector = fixed
            sample["physics"] = torch.from_numpy(vector).to(self.device).unsqueeze(0)

        return sample, visuals

    def predict_with_layer(self, inputs: dict[str, torch.Tensor], layer_name: str | None = None) -> tuple[InferenceResult, str | None]:
        activation_b64: str | None = None
        hook = None
        captured: dict[str, torch.Tensor] = {}

        if layer_name:
            named = dict(self.model.named_modules())
            module = named.get(layer_name)
            if module is not None:
                def _hook(_module, _inp, out):
                    if isinstance(out, tuple):
                        out = out[0]
                    if torch.is_tensor(out):
                        captured["act"] = out.detach().cpu()

                hook = module.register_forward_hook(_hook)

        try:
            result = self.predict(inputs)
        finally:
            if hook is not None:
                hook.remove()

        if "act" in captured:
            act = captured["act"]
            if act.ndim >= 2:
                if act.ndim == 2:
                    vec = act[0].numpy()
                    size = int(np.ceil(np.sqrt(vec.shape[0])))
                    grid = np.zeros((size * size,), dtype=np.float32)
                    grid[: vec.shape[0]] = vec
                    grid = grid.reshape(size, size)
                    grid = (grid - grid.min()) / (grid.max() - grid.min() + 1e-6)
                    img = np.repeat(grid[..., None], 3, axis=2)
                    activation_b64 = self._to_base64_png(img)
                else:
                    feat = act[0]
                    if feat.ndim == 3:
                        heat = feat.mean(dim=0).numpy()
                    elif feat.ndim == 2:
                        heat = feat.numpy()
                    else:
                        flat = feat.flatten().numpy()
                        size = int(np.ceil(np.sqrt(flat.shape[0])))
                        grid = np.zeros((size * size,), dtype=np.float32)
                        grid[: flat.shape[0]] = flat
                        heat = grid.reshape(size, size)
                    heat = (heat - heat.min()) / (heat.max() - heat.min() + 1e-6)
                    img = np.repeat(heat[..., None], 3, axis=2)
                    activation_b64 = self._to_base64_png(img)

        return result, activation_b64

    def predict(self, inputs: dict[str, torch.Tensor]) -> InferenceResult:
        with torch.no_grad():
            out = self.model(inputs["radar"], inputs["optical"], inputs["physics"])

        detect_prob = torch.sigmoid(out["detect_logits"]).item()
        collision_prob = torch.sigmoid(out["collision_logits"]).item()
        class_probs = F.softmax(out["class_logits"], dim=-1).squeeze(0).cpu().tolist()
        predicted_class = int(np.argmax(class_probs))
        orbit = out["orbit_pred"].squeeze(0).cpu().tolist()
        snr_pred = out["snr_pred"].item()

        return InferenceResult(
            detect_probability=float(detect_prob),
            collision_probability=float(collision_prob),
            class_probabilities=[float(v) for v in class_probs],
            predicted_class=predicted_class,
            orbit_vector=[float(v) for v in orbit],
            snr_prediction=float(snr_pred),
        )
