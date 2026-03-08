from __future__ import annotations

import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Tuple

import numpy as np

EXPECTED_MODALITIES = ("t1", "t1ce", "t2", "flair")
DEFAULT_TARGET_SHAPE = (96, 96, 96)
_hdbet_predictor = None
_hdbet_lock = threading.Lock()


@dataclass
class PreprocessedMRI:
    volume: np.ndarray
    brain_mask: np.ndarray
    voxel_spacing: Tuple[float, float, float]
    affine: np.ndarray
    source_shape: Tuple[int, int, int]


def load_and_preprocess_modalities(
    file_paths: Dict[str, Path],
    target_shape: Tuple[int, int, int] = DEFAULT_TARGET_SHAPE,
    prefer_hdbet: bool = True,
) -> PreprocessedMRI:
    """
    Load and preprocess the 4 MRI modalities into a 4xDxHxW tensor.

    Preprocessing steps:
    - NIfTI load
    - modality-wise z-normalization in non-zero voxels
    - center crop or pad to target shape
    """

    nib = _require_nibabel()
    _validate_modalities(file_paths.keys())

    raw_volumes: Dict[str, np.ndarray] = {}
    affine = None
    voxel_spacing: Tuple[float, float, float] | None = None
    source_shape: Tuple[int, int, int] | None = None

    for modality in EXPECTED_MODALITIES:
        path = Path(file_paths[modality])
        image = nib.load(str(path))
        volume = np.asarray(image.get_fdata(dtype=np.float32), dtype=np.float32)
        if volume.ndim != 3:
            raise ValueError(f"Expected a 3D volume for modality '{modality}', got shape {volume.shape}.")

        if source_shape is None:
            source_shape = tuple(int(v) for v in volume.shape)
            affine = np.asarray(image.affine, dtype=np.float32)
            voxel_spacing = tuple(float(v) for v in image.header.get_zooms()[:3])
        elif tuple(int(v) for v in volume.shape) != source_shape:
            raise ValueError(
                "All modalities must have the same shape. "
                f"Expected {source_shape}, got {tuple(volume.shape)} for '{modality}'."
            )

        raw_volumes[modality] = volume

    brain_mask = _extract_brain_mask(
        flair_volume=raw_volumes["flair"],
        flair_path=Path(file_paths["flair"]),
        fallback_volumes=raw_volumes,
        prefer_hdbet=prefer_hdbet,
    )
    normalized = [_zscore_non_zero(raw_volumes[modality]) for modality in EXPECTED_MODALITIES]
    normalized_stack = np.stack(normalized, axis=0).astype(np.float32)

    cropped_stack = _center_crop_or_pad_4d(normalized_stack, target_shape=target_shape)
    cropped_mask = _center_crop_or_pad_3d(brain_mask, target_shape=target_shape).astype(np.uint8)

    return PreprocessedMRI(
        volume=cropped_stack,
        brain_mask=cropped_mask,
        voxel_spacing=voxel_spacing if voxel_spacing is not None else (1.0, 1.0, 1.0),
        affine=affine if affine is not None else np.eye(4, dtype=np.float32),
        source_shape=source_shape if source_shape is not None else target_shape,
    )


def _require_nibabel():
    try:
        import nibabel as nib  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency 'nibabel'. Install backend requirements before using MRI analysis."
        ) from exc
    return nib


def _validate_modalities(modality_keys: Iterable[str]) -> None:
    key_set = set(modality_keys)
    missing = [name for name in EXPECTED_MODALITIES if name not in key_set]
    if missing:
        raise ValueError(f"Missing required MRI modalities: {', '.join(missing)}.")


def _zscore_non_zero(volume: np.ndarray) -> np.ndarray:
    mask = volume > 0
    if not np.any(mask):
        return volume.astype(np.float32)

    region = volume[mask]
    mean = float(region.mean())
    std = float(region.std())
    if std < 1e-6:
        std = 1.0

    normalized = (volume - mean) / std
    normalized[~mask] = 0.0
    return normalized.astype(np.float32)


def _center_crop_or_pad_4d(volume: np.ndarray, target_shape: Tuple[int, int, int]) -> np.ndarray:
    if volume.ndim != 4:
        raise ValueError(f"Expected 4D tensor (C,D,H,W), got {volume.shape}.")
    channels = volume.shape[0]
    output = np.zeros((channels, *target_shape), dtype=volume.dtype)
    src_slices, dst_slices = _compute_center_slices(volume.shape[1:], target_shape)
    output[(slice(None), *dst_slices)] = volume[(slice(None), *src_slices)]
    return output


def _center_crop_or_pad_3d(volume: np.ndarray, target_shape: Tuple[int, int, int]) -> np.ndarray:
    if volume.ndim != 3:
        raise ValueError(f"Expected 3D volume, got {volume.shape}.")
    output = np.zeros(target_shape, dtype=volume.dtype)
    src_slices, dst_slices = _compute_center_slices(volume.shape, target_shape)
    output[dst_slices] = volume[src_slices]
    return output


def _compute_center_slices(
    source_shape: Tuple[int, int, int],
    target_shape: Tuple[int, int, int],
) -> Tuple[Tuple[slice, slice, slice], Tuple[slice, slice, slice]]:
    src = []
    dst = []

    for src_dim, tgt_dim in zip(source_shape, target_shape):
        if src_dim >= tgt_dim:
            src_start = (src_dim - tgt_dim) // 2
            src_end = src_start + tgt_dim
            dst_start = 0
            dst_end = tgt_dim
        else:
            src_start = 0
            src_end = src_dim
            dst_start = (tgt_dim - src_dim) // 2
            dst_end = dst_start + src_dim

        src.append(slice(src_start, src_end))
        dst.append(slice(dst_start, dst_end))

    return (src[0], src[1], src[2]), (dst[0], dst[1], dst[2])


def _build_brain_mask(flair_volume: np.ndarray, fallback_volumes: Dict[str, np.ndarray]) -> np.ndarray:
    """
    Build a robust brain mask from FLAIR with morphology refinement.

    The flow follows the Kaggle prototype:
    - adaptive threshold on non-zero FLAIR intensities
    - morphological closing + hole filling
    - keep largest connected component
    - light erosion/dilation to smooth shell
    """
    flair_non_zero = flair_volume[flair_volume > 0]
    if flair_non_zero.size > 0:
        threshold = float(np.percentile(flair_non_zero, 30) * 0.4)
        mask = flair_volume > threshold

        try:
            from scipy import ndimage  # type: ignore

            structure = np.ones((5, 5, 5), dtype=bool)
            mask = ndimage.binary_closing(mask, structure=structure)
            mask = ndimage.binary_fill_holes(mask)

            labeled, num_features = ndimage.label(mask)
            if num_features > 1:
                sizes = ndimage.sum(mask, labeled, range(1, num_features + 1))
                largest_label = int(np.argmax(sizes)) + 1
                mask = labeled == largest_label

            mask = ndimage.binary_erosion(mask, iterations=2)
            mask = ndimage.binary_dilation(mask, iterations=2)
        except Exception:
            # Keep threshold mask if scipy is unavailable.
            pass

        if np.any(mask):
            return mask.astype(np.uint8)

    fallback = np.logical_or.reduce([volume > 0 for volume in fallback_volumes.values()])
    return fallback.astype(np.uint8)


def _non_zero_support(fallback_volumes: Dict[str, np.ndarray]) -> np.ndarray:
    return np.logical_or.reduce([volume > 0 for volume in fallback_volumes.values()])


def _mask_fraction(mask: np.ndarray) -> float:
    if mask.size == 0:
        return 0.0
    return float(np.count_nonzero(mask)) / float(mask.size)


def _is_plausible_brain_mask(mask: np.ndarray, support: np.ndarray) -> bool:
    voxel_count = int(np.count_nonzero(mask))
    if voxel_count < 512:
        return False

    fraction = _mask_fraction(mask)
    if fraction < 0.02 or fraction > 0.75:
        return False

    support_voxels = int(np.count_nonzero(support))
    if support_voxels == 0:
        return True

    overlap = int(np.count_nonzero((mask > 0) & support))
    support_recall = overlap / float(support_voxels)
    return support_recall >= 0.35


def _synthesize_brain_mask(
    fallback_volumes: Dict[str, np.ndarray],
    expected_shape: Tuple[int, int, int],
) -> np.ndarray:
    support = _non_zero_support(fallback_volumes)
    if not np.any(support):
        return np.zeros(expected_shape, dtype=np.uint8)

    coords = np.argwhere(support)
    shape = np.asarray(expected_shape, dtype=np.float32)
    support_fraction = _mask_fraction(support)

    if support_fraction >= 0.02:
        lower = np.percentile(coords, 2.0, axis=0)
        upper = np.percentile(coords, 98.0, axis=0)
        center = (lower + upper) / 2.0
        extent = np.maximum(upper - lower + 1.0, 1.0)
    else:
        center = (shape - 1.0) / 2.0
        extent = np.maximum(shape * 0.52, 1.0)

    min_radii = shape * np.array([0.28, 0.32, 0.28], dtype=np.float32)
    max_radii = shape * 0.48
    radii = np.clip(extent * 0.72, min_radii, max_radii)

    zz, yy, xx = np.ogrid[: expected_shape[0], : expected_shape[1], : expected_shape[2]]
    ellipsoid = (
        ((zz - center[0]) / max(radii[0], 1.0)) ** 2
        + ((yy - center[1]) / max(radii[1], 1.0)) ** 2
        + ((xx - center[2]) / max(radii[2], 1.0)) ** 2
    ) <= 1.0

    try:
        from scipy import ndimage  # type: ignore

        ellipsoid = ndimage.binary_fill_holes(ellipsoid)
        support_shell = ndimage.binary_dilation(support, iterations=4)
        mask = ndimage.binary_closing(ellipsoid | support_shell, structure=np.ones((5, 5, 5), dtype=bool))
        mask = ndimage.binary_fill_holes(mask)
    except Exception:
        mask = ellipsoid | support

    return mask.astype(np.uint8)


def _extract_brain_mask(
    flair_volume: np.ndarray,
    flair_path: Path,
    fallback_volumes: Dict[str, np.ndarray],
    prefer_hdbet: bool,
) -> np.ndarray:
    support = _non_zero_support(fallback_volumes)

    if prefer_hdbet:
        try:
            hdbet_mask = _extract_brain_mask_hdbet(flair_path, expected_shape=flair_volume.shape)
            if _is_plausible_brain_mask(hdbet_mask, support):
                return hdbet_mask.astype(np.uint8)
            print("[MRI] HD-BET mask rejected as implausibly small or incomplete; using fallback.")
        except Exception as exc:
            print(f"[MRI] HD-BET failed; using morphology fallback. Reason: {exc}")

    fallback_mask = _build_brain_mask(flair_volume=flair_volume, fallback_volumes=fallback_volumes)
    if _is_plausible_brain_mask(fallback_mask, support):
        return fallback_mask.astype(np.uint8)

    synthetic_mask = _synthesize_brain_mask(fallback_volumes=fallback_volumes, expected_shape=flair_volume.shape)
    if np.any(synthetic_mask):
        print("[MRI] Using synthesized whole-brain envelope to keep tumor visualization in anatomical context.")
        return synthetic_mask.astype(np.uint8)

    return fallback_mask.astype(np.uint8)


def _extract_brain_mask_hdbet(flair_path: Path, expected_shape: Tuple[int, int, int]) -> np.ndarray:
    """
    HD-BET-based brain extraction (CPU mode), with global predictor cache.
    """
    nib = _require_nibabel()
    predictor, hdbet_predict = _get_hdbet_predictor_and_runner()

    with tempfile.TemporaryDirectory(prefix="hdbet_") as temp_dir:
        output_file = Path(temp_dir) / "flair_brain.nii.gz"
        hdbet_predict(
            input_file_or_folder=str(flair_path),
            output_file_or_folder=str(output_file),
            predictor=predictor,
            keep_brain_mask=True,
            compute_brain_extracted_image=False,
        )

        mask_file = output_file.with_name(output_file.name[:-7] + "_bet.nii.gz")
        if not mask_file.exists():
            raise RuntimeError(f"HD-BET mask file not found: {mask_file}")

        mask = np.asarray(nib.load(str(mask_file)).get_fdata(), dtype=np.float32)
        if mask.ndim != 3:
            raise RuntimeError(f"HD-BET mask is not 3D: {mask.shape}")
        if tuple(mask.shape) != tuple(expected_shape):
            raise RuntimeError(
                f"HD-BET mask shape mismatch. Expected {expected_shape}, got {tuple(mask.shape)}."
            )

    return (mask > 0).astype(np.uint8)


def _get_hdbet_predictor_and_runner():
    global _hdbet_predictor
    with _hdbet_lock:
        if _hdbet_predictor is None:
            try:
                import torch
                from HD_BET.entry_point import get_hdbet_predictor, hdbet_predict
            except ImportError as exc:
                raise RuntimeError(
                    "Missing dependency 'hd-bet'. Install with: pip install hd-bet"
                ) from exc

            _hdbet_predictor = {
                "predictor": get_hdbet_predictor(
                    use_tta=False,
                    device=torch.device("cpu"),
                    verbose=False,
                ),
                "runner": hdbet_predict,
            }

        return _hdbet_predictor["predictor"], _hdbet_predictor["runner"]
