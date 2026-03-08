"""
Generate Plotly Mesh3d-compatible mesh data from raw MRI + segmentation.

Brain surface: marching cubes on raw FLAIR intensity at full resolution.
Tumor surfaces: marching cubes on smoothed binary masks per label.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Label mapping from this nnU-Net model's dataset.json:
#   0 = background, 1 = edema, 2 = nonenhancing (necrotic), 3 = empty, 4 = enhancing
TUMOR_LABELS = {
    1: "edema",
    2: "necrotic",
    4: "enhancing",
}

TUMOR_COLORS = {
    "brain": "rgba(120,180,220,0.15)",
    "necrotic": "rgb(224,48,80)",
    "edema": "rgb(232,168,0)",
    "enhancing": "rgb(128,64,224)",
}


def generate_meshes(
    flair_raw: np.ndarray,
    segmentation: np.ndarray,
    spacing: Tuple[float, float, float],
) -> Dict[str, Optional[dict]]:
    """
    Generate all meshes for Plotly visualization.

    Args:
        flair_raw: 3D array (D, H, W) — raw FLAIR intensity (NOT normalized)
        segmentation: 3D array (D, H, W) — integer labels (0,1,2,4)
        spacing: voxel spacing in mm

    Returns:
        Dict mapping name -> {x,y,z,i,j,k,vertex_count,face_count} or None
    """
    from scipy import ndimage
    from skimage import measure

    meshes: Dict[str, Optional[dict]] = {}

    # ── Brain isosurface from raw FLAIR ──
    logger.info("Generating brain isosurface from raw FLAIR...")
    meshes["brain"] = _brain_mesh(flair_raw, spacing, measure, ndimage)

    # ── Tumor meshes from segmentation labels ──
    for label_val, label_name in TUMOR_LABELS.items():
        mask = (segmentation == label_val).astype(np.uint8)
        voxel_count = int(mask.sum())
        logger.info(f"Generating {label_name} mesh ({voxel_count} voxels)...")
        meshes[label_name] = _tumor_mesh(mask, label_name, spacing, measure, ndimage)

    return meshes


def compute_stats(
    segmentation: np.ndarray,
    spacing: Tuple[float, float, float],
) -> Dict[str, Dict[str, float]]:
    """Compute volume statistics for each tumor region."""
    voxel_vol_mm3 = float(np.prod(spacing))
    stats = {}

    for label_val, label_name in TUMOR_LABELS.items():
        mask = segmentation == label_val
        voxel_count = int(mask.sum())
        volume_cc = voxel_count * voxel_vol_mm3 / 1000.0
        stats[label_name] = {
            "volume_cc": round(volume_cc, 2),
            "voxel_count": voxel_count,
        }

    # Total tumor
    total_tumor = int((segmentation > 0).sum())
    total_cc = total_tumor * voxel_vol_mm3 / 1000.0
    stats["total_tumor"] = {
        "volume_cc": round(total_cc, 2),
        "voxel_count": total_tumor,
    }

    return stats


def _brain_mesh(
    flair: np.ndarray,
    spacing: Tuple[float, float, float],
    measure,
    ndimage,
) -> Optional[dict]:
    """Build brain surface from raw FLAIR intensity using marching cubes."""
    non_zero = flair[flair > 0]
    if len(non_zero) < 500:
        logger.warning("FLAIR volume nearly empty")
        return None

    # Threshold: low percentile to capture full brain extent
    threshold = float(np.percentile(non_zero, 8))

    # Downsample for performance — full BraTS volumes are 240x240x155
    step = 2
    downsampled = flair[::step, ::step, ::step].astype(np.float32)
    adjusted_spacing = tuple(s * step for s in spacing)

    # Smooth for clean surface
    smoothed = ndimage.gaussian_filter(downsampled, sigma=1.5)

    try:
        verts, faces, _, _ = measure.marching_cubes(
            smoothed,
            level=threshold,
            spacing=adjusted_spacing,
            allow_degenerate=False,
        )
    except (RuntimeError, ValueError) as e:
        logger.warning(f"Brain marching cubes failed: {e}")
        return None

    if len(verts) < 100 or len(faces) < 100:
        logger.warning(f"Brain mesh too small: {len(verts)} verts")
        return None

    # Smooth for organic look
    verts = _laplacian_smooth(verts, faces, iterations=15, lam=0.5)

    # Decimate for browser
    verts, faces = _decimate(verts, faces, max_faces=60000)

    logger.info(f"Brain mesh: {len(verts)} verts, {len(faces)} faces")
    return _to_plotly(verts, faces)


def _tumor_mesh(
    mask: np.ndarray,
    name: str,
    spacing: Tuple[float, float, float],
    measure,
    ndimage,
) -> Optional[dict]:
    """Build mesh from a binary tumor mask."""
    if int(mask.sum()) < 10:
        logger.info(f"{name}: too few voxels, skipping")
        return None

    # Smooth binary mask for cleaner surface
    smoothed = ndimage.gaussian_filter(mask.astype(np.float32), sigma=1.2)

    try:
        verts, faces, _, _ = measure.marching_cubes(
            smoothed,
            level=0.5,
            spacing=tuple(float(s) for s in spacing),
            allow_degenerate=False,
        )
    except (RuntimeError, ValueError) as e:
        logger.warning(f"{name} marching cubes failed: {e}")
        return None

    if len(verts) < 10 or len(faces) < 10:
        return None

    verts = _laplacian_smooth(verts, faces, iterations=8, lam=0.5)
    verts, faces = _decimate(verts, faces, max_faces=50000)

    logger.info(f"{name} mesh: {len(verts)} verts, {len(faces)} faces")
    return _to_plotly(verts, faces)


def _laplacian_smooth(
    vertices: np.ndarray,
    faces: np.ndarray,
    iterations: int = 10,
    lam: float = 0.5,
) -> np.ndarray:
    """Laplacian smoothing for organic surfaces."""
    verts = vertices.copy()
    n = len(verts)
    if n == 0:
        return verts

    # Build adjacency
    adj: list[set] = [set() for _ in range(n)]
    for f in faces:
        for i in range(3):
            a, b = int(f[i]), int(f[(i + 1) % 3])
            adj[a].add(b)
            adj[b].add(a)

    for _ in range(iterations):
        new_v = verts.copy()
        for i, nbrs in enumerate(adj):
            if nbrs:
                centroid = verts[list(nbrs)].mean(axis=0)
                new_v[i] = verts[i] + lam * (centroid - verts[i])
        verts = new_v

    return verts


def _decimate(
    verts: np.ndarray,
    faces: np.ndarray,
    max_faces: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """Simple uniform face subsampling if over budget."""
    if len(faces) <= max_faces:
        return verts, faces

    step = max(1, len(faces) // max_faces)
    subset = faces[::step]

    used = np.unique(subset.ravel())
    remap = np.full(len(verts), -1, dtype=np.int64)
    remap[used] = np.arange(len(used))

    return verts[used], remap[subset].astype(np.int64)


def _to_plotly(verts: np.ndarray, faces: np.ndarray) -> dict:
    """Convert to Plotly Mesh3d format."""
    return {
        "x": verts[:, 0].tolist(),
        "y": verts[:, 1].tolist(),
        "z": verts[:, 2].tolist(),
        "i": faces[:, 0].tolist(),
        "j": faces[:, 1].tolist(),
        "k": faces[:, 2].tolist(),
        "vertex_count": len(verts),
        "face_count": len(faces),
    }
