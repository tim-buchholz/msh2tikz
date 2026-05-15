import numpy as np
from typing import Optional, Tuple
import argparse


DEFAULT_SMALL_ELEMENT_STYLE = "fill=red!35,draw=red!70!black,thin"
DEFAULT_LARGE_ELEMENT_STYLE = "fill=blue!12,draw=blue!70!black,thin"
DEFAULT_MESH_STYLE = "thin"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert a .msh file to a compilable .tex file."
    )

    parser.add_argument(
        "filename",
        nargs="?",
        help="Input .msh file (without extension). If omitted, an example mesh will be generated.",
    )

    parser.add_argument(
        "--out", "-o", help="Output .tex file. Defaults to <filename>.tex"
    )

    parser.add_argument(
        "--print",
        action="store_true",
        help="Print the TeX code to stdout as well as writing to the file.",
    )

    parser.add_argument(
        "--plot",
        action="store_true",
        help="Plot the mesh as well as writing to the file.",
    )

    parser.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        metavar=("XMIN", "XMAX", "YMIN", "YMAX"),
        help=(
            "Restrict the exported mesh to the rectangular subsection "
            "[XMIN, XMAX] x [YMIN, YMAX]. Only triangles whose three vertices "
            "lie inside this box are written to the TikZ file."
        ),
    )

    parser.add_argument(
        "--tikz-scale",
        type=float,
        default=1.0,
        help=(
            "Additional TikZ scale factor applied in the tikzpicture options. "
            "Default: 1.0"
        ),
    )

    parser.add_argument(
        "--fit-width",
        type=float,
        default=None,
        metavar="W",
        help=(
            "Rescale the exported coordinates so that the mesh width becomes W "
            "TikZ units. Useful when the physical mesh coordinates are very small."
        ),
    )

    parser.add_argument(
        "--fit-height",
        type=float,
        default=None,
        metavar="H",
        help=(
            "Rescale the exported coordinates so that the mesh height becomes H "
            "TikZ units. If used together with --fit-width, the mesh is scaled "
            "uniformly to fit into the corresponding box."
        ),
    )

    parser.add_argument(
        "--keep-global-coordinates",
        action="store_true",
        help=(
            "Do not shift the exported coordinates to start at the origin. By default, "
            "the mesh is translated so that its lower-left corner is at (0,0)."
        ),
    )

    parser.add_argument(
        "--incircle-diameter-threshold",
        type=float,
        default=None,
        metavar="D",
        help=(
            "Color triangles according to whether their incircle diameter is below D. "
            "The threshold is evaluated in the original mesh coordinates, before any "
            "display rescaling by --fit-width, --fit-height, or --tikz-scale."
        ),
    )

    parser.add_argument(
        "--small-element-style",
        default=DEFAULT_SMALL_ELEMENT_STYLE,
        help=(
            "TikZ style for triangles with incircle diameter below the threshold. "
            f"Default: '{DEFAULT_SMALL_ELEMENT_STYLE}'"
        ),
    )

    parser.add_argument(
        "--large-element-style",
        default=DEFAULT_LARGE_ELEMENT_STYLE,
        help=(
            "TikZ style for triangles with incircle diameter at or above the threshold. "
            f"Default: '{DEFAULT_LARGE_ELEMENT_STYLE}'"
        ),
    )

    parser.add_argument(
        "--mesh-style",
        default=DEFAULT_MESH_STYLE,
        help=(
            "TikZ style used when no incircle threshold is supplied. "
            f"Default: '{DEFAULT_MESH_STYLE}'"
        ),
    )

    return parser.parse_args()


def generate_rectangle_mesh(h: float, filename: str) -> None:
    try:
        import gmsh
    except ImportError as exc:
        raise ImportError("gmsh is required to generate the example mesh.") from exc

    gmsh.initialize()
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
    filename = f"{filename}.msh"
    gmsh.write(filename)
    gmsh.finalize()
    print(f"Mesh {filename} generated and saved to file")


def read_mesh(filename: str, dim=2) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    try:
        import meshio
    except ImportError as exc:
        raise ImportError("meshio is required to read .msh files.") from exc

    mesh = meshio.read(
        f"{filename}.msh",
    )
    points_3d = mesh.points
    points = points_3d[:, :dim]
    cell_dofmap = mesh.cells_dict["triangle"]
    cells = np.arange(len(cell_dofmap[:,]), dtype=int)
    return points, cells, cell_dofmap


def validate_bbox(bbox: Optional[Tuple[float, float, float, float]]) -> Optional[Tuple[float, float, float, float]]:
    if bbox is None:
        return None

    xmin, xmax, ymin, ymax = bbox
    if xmin > xmax:
        raise ValueError(f"Invalid bounding box: xmin ({xmin}) must not exceed xmax ({xmax}).")
    if ymin > ymax:
        raise ValueError(f"Invalid bounding box: ymin ({ymin}) must not exceed ymax ({ymax}).")
    return xmin, xmax, ymin, ymax


def restrict_to_bbox(
    points: np.ndarray,
    cells: np.ndarray,
    cell_dofmap: np.ndarray,
    bbox: Optional[Tuple[float, float, float, float]],
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    if bbox is None:
        return points, cells, cell_dofmap

    xmin, xmax, ymin, ymax = validate_bbox(bbox)

    triangle_points = points[cell_dofmap]
    inside_mask = (
        (triangle_points[:, :, 0] >= xmin)
        & (triangle_points[:, :, 0] <= xmax)
        & (triangle_points[:, :, 1] >= ymin)
        & (triangle_points[:, :, 1] <= ymax)
    )
    keep_cells_mask = np.all(inside_mask, axis=1)
    filtered_cell_dofmap = cell_dofmap[keep_cells_mask]

    if filtered_cell_dofmap.size == 0:
        return np.empty((0, points.shape[1])), np.empty((0,), dtype=int), np.empty((0, 3), dtype=int)

    used_point_indices = np.unique(filtered_cell_dofmap)
    old_to_new = {old_idx: new_idx for new_idx, old_idx in enumerate(used_point_indices)}
    remapped_cell_dofmap = np.vectorize(old_to_new.get, otypes=[int])(filtered_cell_dofmap)
    filtered_points = points[used_point_indices]
    filtered_cells = np.arange(len(remapped_cell_dofmap), dtype=int)

    return filtered_points, filtered_cells, remapped_cell_dofmap


def transform_points_for_tikz(
    points: np.ndarray,
    fit_width: Optional[float] = None,
    fit_height: Optional[float] = None,
    shift_to_origin: bool = True,
) -> Tuple[np.ndarray, float, np.ndarray, np.ndarray]:
    if len(points) == 0:
        return points.copy(), 1.0, np.zeros(2), np.zeros(2)

    transformed = points.astype(float).copy()

    mins = transformed.min(axis=0)
    if shift_to_origin:
        transformed -= mins

    spans = transformed.max(axis=0) - transformed.min(axis=0)

    candidates = []
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

    return transformed, scale_factor, mins, spans


def plot_mesh_2D(points: np.ndarray, cell_dofmap: np.ndarray):
    import matplotlib.pyplot as plt
    import matplotlib.tri as tri

    triangles = cell_dofmap[:, 0:3]
    triangulation = tri.Triangulation(points[:, 0], points[:, 1], triangles)
    fig = plt.figure()
    plt.title("Simple mesh from gmsh")
    plt.triplot(triangulation, color="gray")
    plt.show()


def get_coordinate_definition(points: np.ndarray) -> str:
    out_str = ""
    for idx, point in enumerate(points):
        out_str += f"\\coordinate (P{idx}) at ({point[0]},{point[1]});\n"
    out_str = out_str[:-1]
    return out_str


def get_all_coordinates(points: np.ndarray) -> str:
    out_str = ""
    for idx, _ in enumerate(points):
        out_str += f"P{idx},"
    out_str = out_str[:-1]
    return out_str


def get_triangle_definition(cell_dofmap: np.ndarray) -> str:
    out_str = ""
    for cell in cell_dofmap:
        out_str += f"P{cell[0]}/P{cell[1]}/P{cell[2]},"
    out_str = out_str[:-1]
    return out_str


def get_triangle_incircle_diameters(points: np.ndarray, cell_dofmap: np.ndarray) -> np.ndarray:
    if len(cell_dofmap) == 0:
        return np.empty((0,), dtype=float)

    triangles = points[cell_dofmap]
    e01 = np.linalg.norm(triangles[:, 1] - triangles[:, 0], axis=1)
    e12 = np.linalg.norm(triangles[:, 2] - triangles[:, 1], axis=1)
    e20 = np.linalg.norm(triangles[:, 0] - triangles[:, 2], axis=1)
    perimeter = e01 + e12 + e20

    cross_vals = (
        (triangles[:, 1, 0] - triangles[:, 0, 0]) * (triangles[:, 2, 1] - triangles[:, 0, 1])
        - (triangles[:, 1, 1] - triangles[:, 0, 1]) * (triangles[:, 2, 0] - triangles[:, 0, 0])
    )
    area = 0.5 * np.abs(cross_vals)

    diameters = np.zeros_like(area)
    nondegenerate = perimeter > 0
    diameters[nondegenerate] = 4.0 * area[nondegenerate] / perimeter[nondegenerate]
    return diameters


def split_cells_by_incircle_diameter(
    points: np.ndarray,
    cell_dofmap: np.ndarray,
    threshold: Optional[float],
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray]]:
    if threshold is None:
        return None, None, None
    if threshold < 0:
        raise ValueError("--incircle-diameter-threshold must be nonnegative.")

    diameters = get_triangle_incircle_diameters(points, cell_dofmap)
    small_mask = diameters < threshold
    large_mask = ~small_mask
    return diameters, cell_dofmap[small_mask], cell_dofmap[large_mask]


def get_tex_str(
    points: np.ndarray,
    cells: np.ndarray,
    cell_dofmap: np.ndarray,
    out: str,
    print_to_terminal: bool = False,
    tikz_scale: float = 1.0,
    incircle_diameter_threshold: Optional[float] = None,
    small_element_style: str = DEFAULT_SMALL_ELEMENT_STYLE,
    large_element_style: str = DEFAULT_LARGE_ELEMENT_STYLE,
    mesh_style: str = DEFAULT_MESH_STYLE,
    classification_points: Optional[np.ndarray] = None,
) -> None:
    if tikz_scale <= 0:
        raise ValueError("--tikz-scale must be positive.")

    if classification_points is None:
        classification_points = points

    if len(cell_dofmap) == 0:
        write_lines = [
            "\\documentclass[tikz]{standalone}\n",
            "\\usepackage{tikz}\n",
            "\\begin{document}\n",
            f"\\begin{{tikzpicture}}[scale={tikz_scale}]\n",
            "% No triangles were found in the selected subsection.\n",
            "\\end{tikzpicture}\n",
            "\\end{document}\n",
        ]
    else:
        write_lines = [
            "\\documentclass[tikz]{standalone}\n",
            "\\usepackage{tikz}\n",
            "\\usetikzlibrary{calc}\n",
            "\\begin{document}\n",
            f"\\begin{{tikzpicture}}[scale={tikz_scale}]\n",
            "% --- Define all coordinates manually ---\n",
            f"{get_coordinate_definition(points=points)}\n",
        ]

        diameters, small_cells, large_cells = split_cells_by_incircle_diameter(
            classification_points,
            cell_dofmap,
            incircle_diameter_threshold,
        )

        if incircle_diameter_threshold is None:
            write_lines.extend([
                "\\foreach \\a/\\b/\\c in {\n",
                f"{get_triangle_definition(cell_dofmap=cell_dofmap)}}}{{\n",
                f"\\draw[{mesh_style}] (\\a) -- (\\b) -- (\\c) -- cycle;}}\n",
            ])
        else:
            write_lines.append(
                f"% Triangles with incircle diameter < {incircle_diameter_threshold:g}\n"
            )
            if len(small_cells) > 0:
                write_lines.extend([
                    "\\foreach \\a/\\b/\\c in {\n",
                    f"{get_triangle_definition(cell_dofmap=small_cells)}}}{{\n",
                    f"\\path[{small_element_style}] (\\a) -- (\\b) -- (\\c) -- cycle;}}\n",
                ])
            else:
                write_lines.append("% No triangles below the incircle-diameter threshold.\n")

            write_lines.append(
                f"% Triangles with incircle diameter >= {incircle_diameter_threshold:g}\n"
            )
            if len(large_cells) > 0:
                write_lines.extend([
                    "\\foreach \\a/\\b/\\c in {\n",
                    f"{get_triangle_definition(cell_dofmap=large_cells)}}}{{\n",
                    f"\\path[{large_element_style}] (\\a) -- (\\b) -- (\\c) -- cycle;}}\n",
                ])
            else:
                write_lines.append("% No triangles at or above the incircle-diameter threshold.\n")

        write_lines.extend([
            "\n",
            "% Label nodes (only for creation process)\n",
            f"% \\foreach \\a in {{{get_all_coordinates(points=points)}}}{{\n",
            "%     \\node[blue!80!black, font=\\normalsize] at (\\a) {\\a};\n",
            "% }\n",
            "\\end{tikzpicture}\n",
            "\\end{document}\n",
        ])

    with open(out, "w") as texfile:
        if print_to_terminal:
            for line in write_lines:
                print(line, end="")
        texfile.writelines(write_lines)


def main():
    args = parse_args()

    if args.filename:
        filename = args.filename
    else:
        filename = "example_mesh"
        print("No filename provided. Generating example mesh...")
        generate_rectangle_mesh(h=0.5, filename=filename)

    if filename.endswith('.msh'):
        filename = filename.removesuffix('.msh')
        print(f"Filename provided: {filename}")

    out_file = args.out if args.out else f"{filename}.tex"

    points, cells, cell_dofmap = read_mesh(filename)
    points, cells, cell_dofmap = restrict_to_bbox(points, cells, cell_dofmap, args.bbox)
    classification_points = points.copy()
    points, geom_scale, mins, spans = transform_points_for_tikz(
        points,
        fit_width=args.fit_width,
        fit_height=args.fit_height,
        shift_to_origin=not args.keep_global_coordinates,
    )

    get_tex_str(
        points,
        cells,
        cell_dofmap,
        out=out_file,
        print_to_terminal=args.print,
        tikz_scale=args.tikz_scale,
        incircle_diameter_threshold=args.incircle_diameter_threshold,
        small_element_style=args.small_element_style,
        large_element_style=args.large_element_style,
        mesh_style=args.mesh_style,
        classification_points=classification_points,
    )

    if args.bbox is not None:
        xmin, xmax, ymin, ymax = validate_bbox(tuple(args.bbox))
        print(
            "Applied rectangular subsection "
            f"[xmin, xmax] x [ymin, ymax] = [{xmin}, {xmax}] x [{ymin}, {ymax}]"
        )
    
    if args.incircle_diameter_threshold is not None and len(cell_dofmap) > 0:
        diameters = get_triangle_incircle_diameters(classification_points, cell_dofmap)
        n_small = int(np.sum(diameters < args.incircle_diameter_threshold))
        n_large = int(len(diameters) - n_small)
        print(
            "Applied incircle-diameter coloring with threshold "
            f"{args.incircle_diameter_threshold:g}: {n_small} triangle(s) below threshold, "
            f"{n_large} triangle(s) at or above threshold."
        )

    if len(points) > 0:
        width = points[:, 0].max() - points[:, 0].min()
        height = points[:, 1].max() - points[:, 1].min()
        print(
            f"Exported mesh extent in TikZ coordinates: width = {width:g}, height = {height:g}"
        )
        if not args.keep_global_coordinates:
            print(
                f"Shifted exported coordinates by subtracting xmin = {mins[0]:g}, ymin = {mins[1]:g}."
            )
        if args.fit_width is not None or args.fit_height is not None:
            print(f"Applied geometric rescaling factor {geom_scale:g} to the coordinates.")
        elif max(spans[0], spans[1]) < 1.0:
            print(
                "Note: the original mesh coordinates are smaller than 1 TikZ unit. "
                "Use --fit-width or --tikz-scale to enlarge the picture."
            )

    print(f"TeX file written to {out_file}")

    if args.plot:
        plot_mesh_2D(points, cell_dofmap)


if __name__ == '__main__':
    main()
