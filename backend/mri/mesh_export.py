from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import numpy as np

LABELS = ("necrotic", "edema", "enhancing")
COLORS = {
    "brain": (176, 189, 205, 255),
    "necrotic": (66, 133, 244, 255),
    "edema": (251, 188, 5, 255),
    "enhancing": (234, 67, 53, 255),
}


@dataclass
class MeshExportResult:
    meshes: Dict[str, str]
    stats: Dict[str, Dict[str, float]]


@dataclass(frozen=True)
class MeshQualityParams:
    step_size: int
    gaussian_sigma: float
    laplacian_iterations: int
    lambda_factor: float = 0.5


QUALITY_PRESETS: Dict[str, MeshQualityParams] = {
    "brain": MeshQualityParams(step_size=2, gaussian_sigma=1.2, laplacian_iterations=4, lambda_factor=0.4),
    "edema": MeshQualityParams(step_size=2, gaussian_sigma=1.0, laplacian_iterations=4, lambda_factor=0.5),
    "necrotic": MeshQualityParams(step_size=1, gaussian_sigma=0.8, laplacian_iterations=5, lambda_factor=0.5),
    "enhancing": MeshQualityParams(step_size=1, gaussian_sigma=0.8, laplacian_iterations=6, lambda_factor=0.5),
}


def export_mesh_bundle(
    masks: np.ndarray,
    probabilities: np.ndarray,
    brain_mask: np.ndarray,
    voxel_spacing: Tuple[float, float, float],
    output_dir: Path,
    request_id: str,
) -> MeshExportResult:
    """
    Convert binary masks to GLB meshes and compute tumor statistics.

    `masks` shape: (3, D, H, W)
    `probabilities` shape: (3, D, H, W)
    """

    if masks.shape != probabilities.shape:
        raise ValueError(f"Mask/probability shape mismatch: {masks.shape} vs {probabilities.shape}.")
    if masks.ndim != 4 or masks.shape[0] != 3:
        raise ValueError(f"Expected masks shape (3, D, H, W), got {masks.shape}.")

    output_dir.mkdir(parents=True, exist_ok=True)
    voxel_volume_mm3 = float(np.prod(voxel_spacing))

    mesh_urls: Dict[str, str] = {}
    stats: Dict[str, Dict[str, float]] = {}

    brain_url = _export_single_mask(
        mask=brain_mask.astype(np.uint8),
        label="brain",
        color=COLORS["brain"],
        voxel_spacing=voxel_spacing,
        output_path=output_dir / f"brain_{request_id}.glb",
    )
    mesh_urls["brain"] = _path_to_output_url(output_dir, brain_url)

    for class_index, label in enumerate(LABELS):
        class_mask = masks[class_index].astype(np.uint8)
        class_prob = probabilities[class_index].astype(np.float32)

        mesh_path = output_dir / f"{label}_{request_id}.glb"
        exported_path = _export_single_mask(
            mask=class_mask,
            label=label,
            color=COLORS[label],
            voxel_spacing=voxel_spacing,
            output_path=mesh_path,
        )
        mesh_urls[label] = _path_to_output_url(output_dir, exported_path)

        voxel_count = int(class_mask.sum())
        volume_cc = float(voxel_count * voxel_volume_mm3 / 1000.0)
        if voxel_count > 0:
            confidence = float(class_prob[class_mask > 0].mean())
        else:
            confidence = float(class_prob.max()) if class_prob.size else 0.0

        stats[label] = {
            "volume_cc": round(volume_cc, 4),
            "confidence": round(confidence, 4),
            "voxel_count": float(voxel_count),
            "voxels": float(voxel_count),
        }

    return MeshExportResult(meshes=mesh_urls, stats=stats)


def _export_single_mask(
    mask: np.ndarray,
    label: str,
    color: Tuple[int, int, int, int],
    voxel_spacing: Tuple[float, float, float],
    output_path: Path,
) -> Path | None:
    if int(mask.sum()) < 12:
        return None

    trimesh = _require_trimesh()
    quality = QUALITY_PRESETS.get(label, MeshQualityParams(step_size=2, gaussian_sigma=1.0, laplacian_iterations=3))
    mesh = _build_mesh(mask=mask, voxel_spacing=voxel_spacing, quality=quality, trimesh=trimesh)
    if mesh is None or len(mesh.vertices) == 0 or len(mesh.faces) == 0:
        return None

    mesh.visual.vertex_colors = np.tile(np.array(color, dtype=np.uint8), (len(mesh.vertices), 1))
    mesh.export(str(output_path), file_type="glb")
    return output_path


def _build_mesh(mask: np.ndarray, voxel_spacing: Tuple[float, float, float], quality: MeshQualityParams, trimesh):
    smooth_mesh = _try_build_smooth_mesh(
        mask=mask,
        voxel_spacing=voxel_spacing,
        quality=quality,
        trimesh=trimesh,
    )
    if smooth_mesh is not None:
        return smooth_mesh
    return _build_voxel_surface_mesh(mask=mask, voxel_spacing=voxel_spacing, trimesh=trimesh)


def _try_build_smooth_mesh(
    mask: np.ndarray,
    voxel_spacing: Tuple[float, float, float],
    quality: MeshQualityParams,
    trimesh,
):
    try:
        from skimage import measure  # type: ignore
        from scipy import ndimage  # type: ignore
    except ImportError:
        return None

    if mask.max() == 0:
        return None

    volume = mask.astype(np.float32, copy=False)
    if quality.step_size > 1:
        volume = ndimage.zoom(volume, 1.0 / float(quality.step_size), order=1)

    volume = ndimage.gaussian_filter(volume, sigma=quality.gaussian_sigma)
    if volume.max() == 0:
        return None

    spacing = tuple(float(v) * float(quality.step_size) for v in voxel_spacing)
    try:
        verts, faces, _, _ = measure.marching_cubes(
            volume,
            level=0.5,
            step_size=1,
            allow_degenerate=False,
            spacing=spacing,
        )
    except TypeError:
        verts, faces, _, _ = measure.marching_cubes(
            volume,
            level=0.5,
            step_size=1,
            spacing=spacing,
        )

    if len(verts) == 0 or len(faces) == 0:
        return None

    if quality.laplacian_iterations > 0:
        verts = _laplacian_smooth(
            vertices=verts,
            faces=faces,
            iterations=quality.laplacian_iterations,
            lambda_factor=quality.lambda_factor,
        )

    return trimesh.Trimesh(vertices=verts, faces=faces, process=False)


def _laplacian_smooth(
    vertices: np.ndarray,
    faces: np.ndarray,
    iterations: int = 3,
    lambda_factor: float = 0.5,
) -> np.ndarray:
    """
    Lightweight Laplacian smoothing for cleaner and more organic surfaces.
    """
    verts = vertices.copy()
    n_verts = len(verts)
    if n_verts == 0 or len(faces) == 0:
        return verts

    adjacency = [set() for _ in range(n_verts)]
    for face in faces:
        for idx in range(3):
            a = int(face[idx])
            b = int(face[(idx + 1) % 3])
            adjacency[a].add(b)
            adjacency[b].add(a)

    for _ in range(max(0, int(iterations))):
        next_verts = verts.copy()
        for idx, neighbors in enumerate(adjacency):
            if not neighbors:
                continue
            neighbor_ids = list(neighbors)
            centroid = verts[neighbor_ids].mean(axis=0)
            next_verts[idx] = verts[idx] + float(lambda_factor) * (centroid - verts[idx])
        verts = next_verts

    return verts


def _build_voxel_surface_mesh(mask: np.ndarray, voxel_spacing: Tuple[float, float, float], trimesh):
    occupancy = mask.astype(bool)
    if not np.any(occupancy):
        return None

    padded = np.pad(occupancy, 1, mode="constant", constant_values=False)
    interior = (
        padded[1:-1, 1:-1, 1:-1]
        & padded[:-2, 1:-1, 1:-1]
        & padded[2:, 1:-1, 1:-1]
        & padded[1:-1, :-2, 1:-1]
        & padded[1:-1, 2:, 1:-1]
        & padded[1:-1, 1:-1, :-2]
        & padded[1:-1, 1:-1, 2:]
    )
    surface = occupancy & ~interior
    centers = np.argwhere(surface)
    if len(centers) == 0:
        centers = np.argwhere(occupancy)
    if len(centers) == 0:
        return None

    max_voxels = 120_000
    if len(centers) > max_voxels:
        step = int(np.ceil(len(centers) / max_voxels))
        centers = centers[::step]

    centers = centers.astype(np.float32) + 0.5
    mesh = trimesh.voxel.ops.multibox(centers=centers, pitch=1.0)
    mesh.apply_scale(np.asarray(voxel_spacing, dtype=np.float32))
    return mesh


def _require_trimesh():
    try:
        import trimesh  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency 'trimesh'. Install backend requirements before using MRI mesh export."
        ) from exc

    return trimesh


def _path_to_output_url(output_dir: Path, path: Path | None) -> str:
    if path is None:
        return ""
    outputs_root = output_dir.parent
    relative = path.relative_to(outputs_root)
    return f"/outputs/{relative.as_posix()}"
