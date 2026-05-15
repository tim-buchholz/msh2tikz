"""Geometry data structures and mesh transformation helpers for ``msh2tikz``."""

from dataclasses import dataclass
from typing import Optional

import numpy as np


BoundingBox = tuple[float, float, float, float]


@dataclass(frozen=True)
class Mesh2D:
    """Represent a 2D triangular mesh with point coordinates and connectivity."""

    points: np.ndarray
    triangles: np.ndarray


@dataclass(frozen=True)
class TransformResult:
    """Store transformed points together with the applied geometry metadata."""

    points: np.ndarray
    scale_factor: float
    mins: np.ndarray
    spans: np.ndarray


def validate_bbox(bbox: Optional[BoundingBox]) -> Optional[BoundingBox]:
    """Validate a bounding box tuple and return it unchanged when valid."""
    if bbox is None:
        return None

    xmin, xmax, ymin, ymax = bbox
    if xmin > xmax:
        raise ValueError(
            f"Invalid bounding box: xmin ({xmin}) must not exceed xmax ({xmax})."
        )
    if ymin > ymax:
        raise ValueError(
            f"Invalid bounding box: ymin ({ymin}) must not exceed ymax ({ymax})."
        )
    return xmin, xmax, ymin, ymax


def restrict_to_bbox(mesh: Mesh2D, bbox: Optional[BoundingBox]) -> Mesh2D:
    """Return the submesh whose triangles lie fully inside the given bounding box."""
    if bbox is None:
        return mesh

    xmin, xmax, ymin, ymax = validate_bbox(bbox)

    triangle_points = mesh.points[mesh.triangles]
    inside_mask = (
        (triangle_points[:, :, 0] >= xmin)
        & (triangle_points[:, :, 0] <= xmax)
        & (triangle_points[:, :, 1] >= ymin)
        & (triangle_points[:, :, 1] <= ymax)
    )
    keep_triangles_mask = np.all(inside_mask, axis=1)
    filtered_triangles = mesh.triangles[keep_triangles_mask]

    if filtered_triangles.size == 0:
        empty_points = np.empty((0, mesh.points.shape[1]), dtype=mesh.points.dtype)
        empty_triangles = np.empty((0, 3), dtype=int)
        return Mesh2D(points=empty_points, triangles=empty_triangles)

    used_point_indices = np.unique(filtered_triangles)
    remap = np.full(used_point_indices.max() + 1, -1, dtype=int)
    remap[used_point_indices] = np.arange(len(used_point_indices), dtype=int)

    remapped_triangles = remap[filtered_triangles]
    filtered_points = mesh.points[used_point_indices]
    return Mesh2D(points=filtered_points, triangles=remapped_triangles)


def transform_points_for_tikz(
    points: np.ndarray,
    fit_width: Optional[float] = None,
    fit_height: Optional[float] = None,
    shift_to_origin: bool = True,
) -> TransformResult:
    """Translate and uniformly scale mesh points for TikZ export.

    Raises:
        ValueError: If ``fit_width`` or ``fit_height`` is non-positive.
    """
    if len(points) == 0:
        return TransformResult(
            points=points.astype(float, copy=True),
            scale_factor=1.0,
            mins=np.zeros(2),
            spans=np.zeros(2),
        )

    transformed = points.astype(float, copy=True)

    mins = transformed.min(axis=0)
    if shift_to_origin:
        transformed -= mins

    spans = transformed.max(axis=0) - transformed.min(axis=0)

    candidates: list[float] = []
    if fit_width is not None:
        if fit_width <= 0:
            raise ValueError("--fit-width must be positive.")
        if spans[0] > 0:
            candidates.append(fit_width / spans[0])

    if fit_height is not None:
        if fit_height <= 0:
            raise ValueError("--fit-height must be positive.")
        if spans[1] > 0:
            candidates.append(fit_height / spans[1])

    scale_factor = min(candidates) if candidates else 1.0
    transformed *= scale_factor

    return TransformResult(
        points=transformed,
        scale_factor=scale_factor,
        mins=mins,
        spans=spans,
    )


def get_triangle_incircle_diameters(
    mesh: Mesh2D,
) -> np.ndarray:
    """Compute the incircle diameter for each triangle in the mesh."""
    if len(mesh.triangles) == 0:
        return np.empty((0,), dtype=float)

    triangle_points = mesh.points[mesh.triangles]
    e01 = np.linalg.norm(triangle_points[:, 1] - triangle_points[:, 0], axis=1)
    e12 = np.linalg.norm(triangle_points[:, 2] - triangle_points[:, 1], axis=1)
    e20 = np.linalg.norm(triangle_points[:, 0] - triangle_points[:, 2], axis=1)
    perimeter = e01 + e12 + e20

    cross_vals = (
        (triangle_points[:, 1, 0] - triangle_points[:, 0, 0])
        * (triangle_points[:, 2, 1] - triangle_points[:, 0, 1])
        - (triangle_points[:, 1, 1] - triangle_points[:, 0, 1])
        * (triangle_points[:, 2, 0] - triangle_points[:, 0, 0])
    )
    area = 0.5 * np.abs(cross_vals)

    diameters = np.zeros_like(area)
    nondegenerate = perimeter > 0
    diameters[nondegenerate] = 4.0 * area[nondegenerate] / perimeter[nondegenerate]
    return diameters


def split_mesh_by_incircle_diameter(
    mesh: Mesh2D,
    threshold: Optional[float],
) -> tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray]]:
    """Split triangles into groups below and at/above an incircle threshold.

    Returns:
        A tuple ``(diameters, small_triangles, large_triangles)``. If ``threshold``
        is ``None``, all three entries are ``None``.

    Raises:
        ValueError: If ``threshold`` is negative.
    """
    if threshold is None:
        return None, None, None
    if threshold < 0:
        raise ValueError("--incircle-diameter-threshold must be nonnegative.")

    diameters = get_triangle_incircle_diameters(mesh)
    small_mask = diameters < threshold
    large_mask = ~small_mask
    return diameters, mesh.triangles[small_mask], mesh.triangles[large_mask]