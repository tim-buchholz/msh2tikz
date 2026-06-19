"""Mesh and file I/O helpers for ``msh2tikz``."""

from pathlib import Path

import numpy as np

from geometry import Mesh2D


def append_msh_suffix(path_str: str) -> Path:
    """Return a path with a ``.msh`` suffix, preserving existing ``.msh`` paths."""
    path = Path(path_str)
    return path if path.suffix == ".msh" else Path(f"{path_str}.msh")


def generate_rectangle_mesh(h: float, output_path: Path) -> None:
    """Generate the built-in example rectangle mesh and write it to disk.

    Raises:
        ImportError: If ``gmsh`` is unavailable.
    """
    try:
        import gmsh
    except ImportError as exc:
        raise ImportError("gmsh is required to generate the example mesh.") from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)

    initialized = False
    try:
        gmsh.initialize()
        initialized = True
        gmsh.option.setNumber("General.Terminal", 0)
        a2 = gmsh.model.geo.addPoint(0.0, 0.0, 0.0, h)
        a3 = gmsh.model.geo.addPoint(8.0, 0.0, 0.0, h)
        a4 = gmsh.model.geo.addPoint(8.0, 5.0, 0.0, h)
        a5 = gmsh.model.geo.addPoint(0.0, 5.0, 0.0, h)
        l2 = gmsh.model.geo.addLine(a2, a3)
        l3 = gmsh.model.geo.addLine(a3, a4)
        l4 = gmsh.model.geo.addLine(a4, a5)
        l5 = gmsh.model.geo.addLine(a5, a2)
        cl = gmsh.model.geo.addCurveLoop([l2, l3, l4, l5])
        pl = gmsh.model.geo.addPlaneSurface([cl])
        gmsh.model.geo.addPhysicalGroup(1, [l2, l3, l4, l5], tag=1)
        gmsh.model.geo.addPhysicalGroup(2, [pl], tag=0)
        gmsh.model.geo.synchronize()
        gmsh.model.mesh.generate(2)
        gmsh.write(str(output_path))
    finally:
        if initialized:
            gmsh.finalize()

    print(f"Mesh {output_path} generated and saved to file")


def read_mesh(input_path: Path) -> Mesh2D:
    """Read a 2D triangular mesh from a ``.msh`` file.

    Raises:
        ImportError: If ``meshio`` is unavailable.
        ValueError: If the mesh is not a supported 2D triangular mesh.
    """
    try:
        import meshio
    except ImportError as exc:
        raise ImportError("meshio is required to read .msh files.") from exc

    mesh = meshio.read(str(input_path))
    if mesh.points.ndim != 2 or mesh.points.shape[1] < 2:
        raise ValueError(
            "Mesh points must provide at least x and y coordinates; only 2D "
            "triangular meshes are supported."
        )

    if "triangle" not in mesh.cells_dict:
        raise ValueError(
            "Mesh contains no triangle elements; only 2D triangular meshes are supported."
        )

    triangles = np.asarray(mesh.cells_dict["triangle"], dtype=int)
    if triangles.ndim != 2 or triangles.shape[1] != 3:
        raise ValueError(
            "Triangle connectivity must have shape (n, 3); only 2D triangular "
            "meshes are supported."
        )

    points = np.asarray(mesh.points[:, :2], dtype=float)
    return Mesh2D(points=points, triangles=triangles)


def write_text_file(path: Path, content: str) -> None:
    """Write UTF-8 text content to disk, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")