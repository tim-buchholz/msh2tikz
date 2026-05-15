"""Reporting and visualization helpers for ``msh2tikz``."""

import argparse
from pathlib import Path

import numpy as np

from geometry import (
    BoundingBox,
    Mesh2D,
    TransformResult,
    get_triangle_incircle_diameters,
)


def plot_mesh_2d(mesh: Mesh2D) -> None:
    """Display the mesh using Matplotlib for quick visual inspection."""
    import matplotlib.pyplot as plt
    import matplotlib.tri as tri

    if len(mesh.triangles) == 0:
        print("No triangles to plot.")
        return

    triangulation = tri.Triangulation(
        mesh.points[:, 0], mesh.points[:, 1], mesh.triangles
    )
    plt.figure()
    plt.title("Mesh")
    plt.triplot(triangulation, color="gray")
    plt.show()


def print_export_summary(
    output_path: Path,
    bbox: BoundingBox | None,
    classification_points: np.ndarray,
    transformed: TransformResult,
    triangles: np.ndarray,
    args: argparse.Namespace,
) -> None:
    """Print a user-facing summary of the performed export."""
    if bbox is not None:
        xmin, xmax, ymin, ymax = bbox
        print(
            "Applied rectangular subsection "
            f"[xmin, xmax] x [ymin, ymax] = [{xmin}, {xmax}] x [{ymin}, {ymax}]"
        )

    if args.incircle_diameter_threshold is not None and len(triangles) > 0:
        classification_mesh = Mesh2D(
            points=classification_points,
            triangles=triangles,
        )
        diameters = get_triangle_incircle_diameters(classification_mesh)
        n_small = int(np.sum(diameters < args.incircle_diameter_threshold))
        n_large = int(len(diameters) - n_small)
        print(
            "Applied incircle-diameter coloring with threshold "
            f"{args.incircle_diameter_threshold:g}: {n_small} triangle(s) below "
            f"threshold, {n_large} triangle(s) at or above threshold."
        )

    if len(transformed.points) > 0:
        width = transformed.points[:, 0].max() - transformed.points[:, 0].min()
        height = transformed.points[:, 1].max() - transformed.points[:, 1].min()
        print(
            f"Exported mesh extent in TikZ coordinates: width = {width:g}, height = {height:g}"
        )
        if not args.keep_global_coordinates:
            print(
                "Shifted exported coordinates by subtracting "
                f"xmin = {transformed.mins[0]:g}, ymin = {transformed.mins[1]:g}."
            )
        if args.fit_width is not None or args.fit_height is not None:
            print(
                "Applied geometric rescaling factor "
                f"{transformed.scale_factor:g} to the coordinates."
            )
        elif max(transformed.spans[0], transformed.spans[1]) < 1.0:
            print(
                "Note: the original mesh coordinates are smaller than 1 TikZ unit. "
                "Use --fit-width or --tikz-scale to enlarge the picture."
            )

    print(f"TeX file written to {output_path}")