from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import torch

from mri.unet3d import UNet3D


@dataclass
class PredictionOutput:
    logits: np.ndarray
    probabilities: np.ndarray
    masks: np.ndarray


class TumorSegmentationPredictor:
    """Lazy-loading wrapper around the 3D U-Net checkpoint."""

    def __init__(self, model_path: Path) -> None:
        self.model_path = Path(model_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: Optional[UNet3D] = None
        self._load_lock = threading.Lock()

    def load_model(self) -> None:
        if self.model is not None:
            return

        with self._load_lock:
            if self.model is not None:
                return

            if not self.model_path.exists():
                raise FileNotFoundError(f"MRI model checkpoint not found: {self.model_path}")

            checkpoint = torch.load(str(self.model_path), map_location=self.device)
            state_dict = _extract_state_dict(checkpoint)

            model = UNet3D(in_channels=4, out_channels=3, features=(16, 32, 64, 128))
            try:
                model.load_state_dict(state_dict, strict=True)
            except RuntimeError as exc:
                raise RuntimeError(
                    "Failed to load best_model.pth into UNet3D. "
                    "If your Kaggle model class differs, update backend/mri/unet3d.py to match it exactly."
                ) from exc

            model.to(self.device)
            model.eval()
            self.model = model

    def predict(self, volume: np.ndarray, threshold: float = 0.5) -> PredictionOutput:
        if volume.ndim != 4 or volume.shape[0] != 4:
            raise ValueError(
                "Expected input volume shape (4, D, H, W) for modalities (T1, T1ce, T2, FLAIR), "
                f"got {volume.shape}."
            )

        self.load_model()
        assert self.model is not None

        input_tensor = torch.from_numpy(volume.astype(np.float32, copy=False)).unsqueeze(0).to(self.device)

        with torch.inference_mode():
            logits_tensor = self.model(input_tensor)
            probs_tensor = torch.sigmoid(logits_tensor)

        logits = logits_tensor.squeeze(0).detach().cpu().numpy().astype(np.float32)
        probabilities = probs_tensor.squeeze(0).detach().cpu().numpy().astype(np.float32)
        masks = (probabilities >= float(threshold)).astype(np.uint8)

        return PredictionOutput(logits=logits, probabilities=probabilities, masks=masks)


_predictors: Dict[str, TumorSegmentationPredictor] = {}
_predictor_lock = threading.Lock()


def get_predictor(model_path: Path) -> TumorSegmentationPredictor:
    path_key = str(Path(model_path).resolve())
    with _predictor_lock:
        if path_key not in _predictors:
            _predictors[path_key] = TumorSegmentationPredictor(Path(path_key))
        return _predictors[path_key]


def _extract_state_dict(checkpoint: object) -> Dict[str, torch.Tensor]:
    if isinstance(checkpoint, dict):
        for key in ("model_state_dict", "state_dict", "model_state", "model"):
            candidate = checkpoint.get(key)
            if isinstance(candidate, dict):
                return candidate
        if checkpoint and all(isinstance(v, torch.Tensor) for v in checkpoint.values()):
            return checkpoint  # raw state dict format

    raise ValueError("Checkpoint format not recognized. Expected a dict with model weights.")

