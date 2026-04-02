"""Reusable image classification backbone registry for benchmark training."""

from __future__ import annotations

from collections.abc import Callable

from torch import nn
from torchvision import models


def _resolve_weights(weights_enum, pretrained: bool):
    if not pretrained or weights_enum is None:
        return None
    default_weights = getattr(weights_enum, "DEFAULT", None)
    if default_weights is None:
        return None
    return default_weights


def _build_with_fallback(builder: Callable, weights_enum, pretrained: bool):
    weights = _resolve_weights(weights_enum, pretrained)
    try:
        return builder(weights=weights)
    except Exception:
        return builder(weights=None)


def _replace_head(
    model: nn.Module, num_classes: int, head_attr: str, index: int | None = None
) -> nn.Module:
    head = getattr(model, head_attr)
    if index is None:
        in_features = getattr(head, "in_features", None)
        if in_features is None:
            raise AttributeError(
                f"{type(model).__name__}.{head_attr} has no in_features"
            )
        setattr(model, head_attr, nn.Linear(in_features, num_classes))
        return model

    if not isinstance(head, nn.Sequential):
        raise TypeError(
            f"Expected {head_attr} to be nn.Sequential for {type(model).__name__}"
        )
    in_features = head[index].in_features
    head[index] = nn.Linear(in_features, num_classes)
    return model


def build_image_backbone(
    name: str, num_classes: int, pretrained: bool = True
) -> nn.Module:
    name = name.lower().strip()

    registry: dict[str, Callable[[], nn.Module]] = {
        "resnet18": lambda: _replace_head(
            _build_with_fallback(models.resnet18, models.ResNet18_Weights, pretrained),
            num_classes,
            "fc",
        ),
        "resnet34": lambda: _replace_head(
            _build_with_fallback(models.resnet34, models.ResNet34_Weights, pretrained),
            num_classes,
            "fc",
        ),
        "resnet50": lambda: _replace_head(
            _build_with_fallback(models.resnet50, models.ResNet50_Weights, pretrained),
            num_classes,
            "fc",
        ),
        "resnext50_32x4d": lambda: _replace_head(
            _build_with_fallback(
                models.resnext50_32x4d, models.ResNeXt50_32X4D_Weights, pretrained
            ),
            num_classes,
            "fc",
        ),
        "wide_resnet50_2": lambda: _replace_head(
            _build_with_fallback(
                models.wide_resnet50_2, models.Wide_ResNet50_2_Weights, pretrained
            ),
            num_classes,
            "fc",
        ),
        "densenet121": lambda: _replace_head(
            _build_with_fallback(
                models.densenet121, models.DenseNet121_Weights, pretrained
            ),
            num_classes,
            "classifier",
        ),
        "efficientnet_b0": lambda: _replace_head(
            _build_with_fallback(
                models.efficientnet_b0, models.EfficientNet_B0_Weights, pretrained
            ),
            num_classes,
            "classifier",
            index=1,
        ),
        "efficientnet_b1": lambda: _replace_head(
            _build_with_fallback(
                models.efficientnet_b1, models.EfficientNet_B1_Weights, pretrained
            ),
            num_classes,
            "classifier",
            index=1,
        ),
        "efficientnet_v2_s": lambda: _replace_head(
            _build_with_fallback(
                models.efficientnet_v2_s, models.EfficientNet_V2_S_Weights, pretrained
            ),
            num_classes,
            "classifier",
            index=1,
        ),
        "mobilenet_v3_small": lambda: _replace_head(
            _build_with_fallback(
                models.mobilenet_v3_small, models.MobileNet_V3_Small_Weights, pretrained
            ),
            num_classes,
            "classifier",
            index=3,
        ),
        "shufflenet_v2_x1_0": lambda: _replace_head(
            _build_with_fallback(
                models.shufflenet_v2_x1_0, models.ShuffleNet_V2_X1_0_Weights, pretrained
            ),
            num_classes,
            "fc",
        ),
        "regnet_y_400mf": lambda: _replace_head(
            _build_with_fallback(
                models.regnet_y_400mf, models.RegNet_Y_400MF_Weights, pretrained
            ),
            num_classes,
            "fc",
        ),
        "convnext_tiny": lambda: _replace_head(
            _build_with_fallback(
                models.convnext_tiny, models.ConvNeXt_Tiny_Weights, pretrained
            ),
            num_classes,
            "classifier",
            index=2,
        ),
        "vit_b_16": lambda: _replace_head(
            _build_with_fallback(models.vit_b_16, models.ViT_B_16_Weights, pretrained),
            num_classes,
            "heads",
            index=0,
        ),
        "swin_t": lambda: _replace_head(
            _build_with_fallback(models.swin_t, models.Swin_T_Weights, pretrained),
            num_classes,
            "head",
        ),
        "swin_v2_t": lambda: _replace_head(
            _build_with_fallback(
                models.swin_v2_t, models.Swin_V2_T_Weights, pretrained
            ),
            num_classes,
            "head",
        ),
    }

    if name not in registry:
        raise ValueError(f"Unsupported model name: {name}")

    return registry[name]()


def available_image_backbones() -> list[str]:
    return [
        "resnet18",
        "resnet34",
        "resnet50",
        "resnext50_32x4d",
        "wide_resnet50_2",
        "densenet121",
        "efficientnet_b0",
        "efficientnet_b1",
        "efficientnet_v2_s",
        "mobilenet_v3_small",
        "shufflenet_v2_x1_0",
        "regnet_y_400mf",
        "convnext_tiny",
        "vit_b_16",
        "swin_t",
        "swin_v2_t",
    ]
