"""CLI parsing and top-level orchestration for ``msh2tikz``."""

import argparse
import sys
from pathlib import Path

from geometry import Mesh2D, transform_points_for_tikz, restrict_to_bbox, validate_bbox
from mesh_io import (
    append_msh_suffix,
    generate_rectangle_mesh,
    read_mesh,
    write_text_file,
)
from rendering import (
    DEFAULT_LARGE_ELEMENT_STYLE,
    DEFAULT_MESH_STYLE,
    DEFAULT_SMALL_ELEMENT_STYLE,
    build_tikz_document,
)
from reporting import plot_mesh_2d, print_export_summary


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the mesh-to-TikZ converter."""
    parser = argparse.ArgumentParser(
        description="Convert a .msh file to a compilable .tex file."
    )

    parser.add_argument(
        "filename",
        nargs="?",
        help=(
            "Input .msh file (without extension). If omitted, an example mesh "
            "will be generated."
        ),
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
            "Do not shift the exported coordinates to start at the origin. By "
            "default, the mesh is translated so that its lower-left corner is at "
            "(0,0)."
        ),
    )

    parser.add_argument(
        "--incircle-diameter-threshold",
        type=float,
        default=None,
        metavar="D",
        help=(
            "Color triangles according to whether their incircle diameter is below "
            "D. The threshold is evaluated in the original mesh coordinates, before "
            "any display rescaling by --fit-width, --fit-height, or --tikz-scale."
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
            "TikZ style for triangles with incircle diameter at or above the "
            f"threshold. Default: '{DEFAULT_LARGE_ELEMENT_STYLE}'"
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


def main() -> int:
    """Run the command-line mesh conversion workflow and return an exit code."""
    args = parse_args()

    try:
        bbox = validate_bbox(tuple(args.bbox)) if args.bbox is not None else None

        if args.filename:
            input_path = append_msh_suffix(args.filename)
        else:
            input_path = Path("example_mesh.msh")
            print("No filename provided. Generating example mesh...")
            generate_rectangle_mesh(h=0.5, output_path=input_path)

        output_path = Path(args.out) if args.out else input_path.with_suffix(".tex")

        mesh = read_mesh(input_path)
        mesh = restrict_to_bbox(mesh, bbox)
        classification_points = mesh.points.copy()
        transformed = transform_points_for_tikz(
            mesh.points,
            fit_width=args.fit_width,
            fit_height=args.fit_height,
            shift_to_origin=not args.keep_global_coordinates,
        )

        tex_document = build_tikz_document(
            transformed.points,
            mesh.triangles,
            tikz_scale=args.tikz_scale,
            incircle_diameter_threshold=args.incircle_diameter_threshold,
            small_element_style=args.small_element_style,
            large_element_style=args.large_element_style,
            mesh_style=args.mesh_style,
            classification_points=classification_points,
        )

        if args.print:
            print(tex_document, end="")
        write_text_file(output_path, tex_document)

        print_export_summary(
            output_path=output_path,
            bbox=bbox,
            classification_points=classification_points,
            transformed=transformed,
            triangles=mesh.triangles,
            args=args,
        )

        if args.plot:
            plot_mesh_2d(Mesh2D(points=transformed.points, triangles=mesh.triangles))

    except (ImportError, FileNotFoundError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
