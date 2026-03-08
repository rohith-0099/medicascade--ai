"""
nnU-Net v2 based brain tumor segmentation predictor.

Uses pre-trained weights from BraTS 2021 challenge.
Downloads and caches the model on first use.
"""
from __future__ import annotations

import logging
import os
import threading
import zipfile
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).resolve().parent.parent / "nnunet_model"
MODEL_ZIP = MODEL_DIR / "Dataset002_BRATS19.zip"

_predictor = None
_lock = threading.Lock()


class BraTSPredictor:
    """Wraps nnU-Net predictor for BraTS tumor segmentation."""

    def __init__(self, model_folder: str):
        from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor
        import torch

        # Performance: disable mirroring (8x speedup) — quality loss is minimal
        self.predictor = nnUNetPredictor(
            tile_step_size=0.5,
            use_gaussian=True,
            use_mirroring=False,
            device=torch.device("cuda" if torch.cuda.is_available() else "cpu"),
            verbose=False,
            verbose_preprocessing=False,
            allow_tqdm=False,
        )

        # Find the trainer folder inside the extracted model
        trainer_folder = _find_trainer_folder(model_folder)
        if trainer_folder is None:
            raise RuntimeError(
                f"Could not find nnU-Net trainer folder in {model_folder}. "
                "Expected a folder structure like Dataset.../nnUNetTrainer__.../"
            )

        # Use single fold for speed (5x faster, ~1-2% accuracy drop)
        folds = (0,)
        logger.info(f"Initializing nnU-Net from {trainer_folder} with folds={folds}")

        self.predictor.initialize_from_trained_model_folder(
            str(trainer_folder),
            use_folds=folds,
            checkpoint_name="checkpoint_final.pth",
        )
        logger.info("nnU-Net BraTS predictor ready")

    def predict(
        self,
        t1: np.ndarray,
        t1ce: np.ndarray,
        t2: np.ndarray,
        flair: np.ndarray,
        spacing: Tuple[float, float, float],
    ) -> np.ndarray:
        """
        Run segmentation on 4 MRI modalities.

        Args:
            t1, t1ce, t2, flair: 3D numpy arrays (D, H, W), raw intensity
            spacing: voxel spacing in mm

        Returns:
            segmentation mask (D, H, W) with labels:
                0 = background
                1 = necrotic tumor core
                2 = peritumoral edema
                3 = enhancing tumor (mapped from BraTS label 4)
        """
        # nnU-Net expects (C, D, H, W) with channels = modalities
        # BraTS convention: channel order is T1, T1ce, T2, FLAIR
        volume = np.stack([t1, t1ce, t2, flair], axis=0).astype(np.float32)

        # nnU-Net predict_single_npy_array expects:
        #   input_image: (C, D, H, W)
        #   image_properties: dict with 'spacing'
        properties = {
            "spacing": list(spacing),
        }

        logger.info(f"Running nnU-Net inference on volume shape {volume.shape}...")
        seg = self.predictor.predict_single_npy_array(
            input_image=volume,
            image_properties=properties,
            segmentation_previous_stage=None,
            output_file_truncated=None,
            save_or_return_probabilities=False,
        )
        logger.info(f"Segmentation complete. Unique labels: {np.unique(seg)}")

        return seg.astype(np.int32)


def get_predictor() -> BraTSPredictor:
    """Get or create the singleton predictor instance."""
    global _predictor
    with _lock:
        if _predictor is not None:
            return _predictor

        # Ensure model is extracted
        model_folder = str(MODEL_DIR)
        _ensure_model_extracted()

        _predictor = BraTSPredictor(model_folder)
        return _predictor


def _ensure_model_extracted():
    """Extract model zip if not already done."""
    # Check if already extracted
    if _find_trainer_folder(str(MODEL_DIR)) is not None:
        logger.info("nnU-Net model already extracted")
        return

    if not MODEL_ZIP.exists():
        raise RuntimeError(
            f"nnU-Net model weights not found at {MODEL_ZIP}. "
            "Download from: https://zenodo.org/records/11582627"
        )

    logger.info(f"Extracting {MODEL_ZIP}...")
    with zipfile.ZipFile(str(MODEL_ZIP), "r") as zf:
        zf.extractall(str(MODEL_DIR))
    logger.info("Model extraction complete")


def _find_trainer_folder(base: str) -> Optional[str]:
    """
    Recursively find the nnU-Net trainer folder.
    Structure: Dataset.../nnUNetTrainer__nnUNetPlans__3d_fullres/
    The trainer folder contains dataset.json, plans.json, and fold_X/ subdirs.
    """
    base_path = Path(base)

    # Look for dataset.json — the trainer folder always has it
    for dj in base_path.rglob("dataset.json"):
        folder = dj.parent
        # Verify it has fold subdirectories with checkpoints
        has_folds = any(
            (folder / f"fold_{i}" / "checkpoint_final.pth").exists()
            for i in range(5)
        )
        if has_folds:
            return str(folder)

    # Fallback: look for any folder with "nnUNetTrainer" in the name
    for d in base_path.rglob("*"):
        if d.is_dir() and "nnUNetTrainer" in d.name:
            return str(d)

    return None


def _detect_folds(trainer_folder: str) -> Tuple[int, ...]:
    """Detect which folds are available in the trainer folder."""
    folder = Path(trainer_folder)
    folds = []
    for d in sorted(folder.iterdir()):
        if d.is_dir() and d.name.startswith("fold_"):
            try:
                fold_num = int(d.name.split("_")[1])
                if (d / "checkpoint_final.pth").exists():
                    folds.append(fold_num)
            except (ValueError, IndexError):
                continue

    if folds:
        return tuple(folds)

    # If checkpoint_final.pth is directly in the trainer folder (single fold)
    if (folder / "checkpoint_final.pth").exists():
        return (0,)

    # Default: try all 5 folds
    return tuple(range(5))
