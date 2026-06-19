"""TikZ rendering helpers for ``msh2tikz``."""

from typing import Optional

import numpy as np

from geometry import Mesh2D, split_mesh_by_incircle_diameter


DEFAULT_SMALL_ELEMENT_STYLE = "fill=red!35,draw=red!70!black,thin"
DEFAULT_LARGE_ELEMENT_STYLE = "fill=blue!12,draw=blue!70!black,thin"
DEFAULT_MESH_STYLE = "thin"


def format_coordinate_definitions(points: np.ndarray) -> str:
    r"""Format TikZ ``\coordinate`` declarations for all mesh points."""
    return "\n".join(
        f"\\coordinate (P{idx}) at ({point[0]},{point[1]});"
        for idx, point in enumerate(points)
    )


def format_coordinate_names(points: np.ndarray) -> str:
    """Format the comma-separated TikZ node names for all mesh points."""
    return ",".join(f"P{idx}" for idx, _ in enumerate(points))


def format_triangle_definitions(triangles: np.ndarray) -> str:
    r"""Format triangle connectivity for use in a TikZ ``\foreach`` loop."""
    return ",".join(
        f"P{triangle[0]}/P{triangle[1]}/P{triangle[2]}" for triangle in triangles
    )


def build_tikz_document(
    points: np.ndarray,
    triangles: np.ndarray,
    tikz_scale: float = 1.0,
    incircle_diameter_threshold: Optional[float] = None,
    small_element_style: str = DEFAULT_SMALL_ELEMENT_STYLE,
    large_element_style: str = DEFAULT_LARGE_ELEMENT_STYLE,
    mesh_style: str = DEFAULT_MESH_STYLE,
    classification_points: Optional[np.ndarray] = None,
) -> str:
    """Build a standalone TikZ document for the supplied mesh.

    Args:
        points: Exported point coordinates in TikZ space.
        triangles: Triangle connectivity referencing ``points``.
        tikz_scale: Additional TikZ picture scale factor.
        incircle_diameter_threshold: Optional threshold for triangle classification.
        small_element_style: TikZ style for triangles below the threshold.
        large_element_style: TikZ style for triangles at or above the threshold.
        mesh_style: TikZ style used when no threshold is supplied.
        classification_points: Coordinates used for incircle classification.

    Raises:
        ValueError: If ``tikz_scale`` is not positive.
    """
    if tikz_scale <= 0:
        raise ValueError("--tikz-scale must be positive.")

    if classification_points is None:
        classification_points = points

    if len(triangles) == 0:
        lines = [
            "\\documentclass[tikz]{standalone}\n",
            "\\usepackage{tikz}\n",
            "\\begin{document}\n",
            f"\\begin{{tikzpicture}}[scale={tikz_scale}]\n",
            "% No triangles were found in the selected subsection.\n",
            "\\end{tikzpicture}\n",
            "\\end{document}\n",
        ]
        return "".join(lines)

    lines = [
        "\\documentclass[tikz]{standalone}\n",
        "\\usepackage{tikz}\n",
        "\\begin{document}\n",
        f"\\begin{{tikzpicture}}[scale={tikz_scale}]\n",
        "% --- Define all coordinates manually ---\n",
        f"{format_coordinate_definitions(points)}\n",
    ]

    classification_mesh = Mesh2D(points=classification_points, triangles=triangles)
    _, small_triangles, large_triangles = split_mesh_by_incircle_diameter(
        classification_mesh,
        incircle_diameter_threshold,
    )

    if incircle_diameter_threshold is None:
        lines.extend(
            [
                "\\foreach \\a/\\b/\\c in {\n",
                format_triangle_definitions(triangles) + "}{\n",
                f"\\draw[{mesh_style}] (\\a) -- (\\b) -- (\\c) -- cycle;}}\n",
            ]
        )
    else:
        lines.append(
            f"% Triangles with incircle diameter < {incircle_diameter_threshold:g}\n"
        )
        if len(small_triangles) > 0:
            lines.extend(
                [
                    "\\foreach \\a/\\b/\\c in {\n",
                    format_triangle_definitions(small_triangles) + "}{\n",
                    f"\\path[{small_element_style}] (\\a) -- (\\b) -- (\\c) -- cycle;}}\n",
                ]
            )
        else:
            lines.append("% No triangles below the incircle-diameter threshold.\n")

        lines.append(
            f"% Triangles with incircle diameter >= {incircle_diameter_threshold:g}\n"
        )
        if len(large_triangles) > 0:
            lines.extend(
                [
                    "\\foreach \\a/\\b/\\c in {\n",
                    format_triangle_definitions(large_triangles) + "}{\n",
                    f"\\path[{large_element_style}] (\\a) -- (\\b) -- (\\c) -- cycle;}}\n",
                ]
            )
        else:
            lines.append(
                "% No triangles at or above the incircle-diameter threshold.\n"
            )

    lines.extend(
        [
            "\n",
            "% Label nodes (only for creation process)\n",
            f"% \\foreach \\a in {{{format_coordinate_names(points)}}}{{\n",
            "%     \\node[blue!80!black, font=\\normalsize] at (\\a) {\\a};\n",
            "% }\n",
            "\\end{tikzpicture}\n",
            "\\end{document}\n",
        ]
    )
    return "".join(lines)