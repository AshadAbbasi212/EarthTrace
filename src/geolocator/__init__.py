"""Global Photo Geolocator package."""
import torch

# Compatibility shim: PyTorch 2.5 does not have torch.accelerator (introduced in PyTorch 2.6)
# which is referenced by modern transformers flex_attention integrations.
if not hasattr(torch, "accelerator"):
    class _MockAccelerator:
        @staticmethod
        def current_accelerator():
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.accelerator = _MockAccelerator

__version__ = "0.1.0"

