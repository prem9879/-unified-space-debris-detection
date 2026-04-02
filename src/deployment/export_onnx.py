"""
Export UnifiedDebrisNet to ONNX for FPGA deployment.
"""
import torch
from src.models.unified_debris_net import UnifiedDebrisNet

def export_to_onnx(model: UnifiedDebrisNet, filepath: str):
    """
    Export model to ONNX format.
    """
    # TODO: Prepare dummy input, export with torch.onnx.export
    pass
