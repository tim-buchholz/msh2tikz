import gmsh
import meshio
import numpy as np
from typing import Tuple
import argparse
import sys


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
        "-p",
        action="store_true",
        help="Print the TeX code to stdout as well as writing to the file.",
    )

    return parser.parse_args()


def generate_rectangle_mesh(h:float, filename:str) -> None:
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal",0)
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

def read_mesh(filename:str, dim=2) -> Tuple[np.ndarray,np.ndarray,np.ndarray]:
    mesh = meshio.read(
        f"{filename}.msh",
    )
    points_3d = mesh.points
    points = points_3d[:, :dim]
    cell_dofmap = mesh.cells_dict["triangle"]
    cells = np.arange(len(cell_dofmap[:,]), dtype=int)
    return points, cells, cell_dofmap

def plot_mesh_2D(points:np.ndarray, cell_dofmap:np.ndarray):
    import matplotlib.pyplot as plt
    import matplotlib.tri as tri

    triangles = cell_dofmap[:, 0:3]
    triangulation = tri.Triangulation(points[:, 0], points[:, 1], triangles)
    fig = plt.figure()
    plt.title("Simple mesh from gmsh")
    plt.triplot(triangulation, color="gray")
    plt.show()

def get_coordinate_definition(points:np.ndarray) -> str:
    out_str = "" 
    for idx,point in enumerate(points):
        out_str += f"\\coordinate (P{idx}) at ({point[0]},{point[1]});\n"
    out_str = out_str[:-1]
    return out_str

def get_all_coordinates(points:np.ndarray) -> str:
    out_str = ""
    for idx,_ in enumerate(points):
        out_str += f"P{idx},"
    out_str = out_str[:-1]
    return out_str

def get_triangle_definition(cell_dofmap:np.ndarray) -> str:
    out_str = ""
    for cell in cell_dofmap:
        out_str += f"P{cell[0]}/P{cell[1]}/P{cell[2]},"
    out_str = out_str[:-1]
    return out_str

def get_tex_str(points: np.ndarray, cells:np.ndarray, cell_dofmap:np.ndarray, out:str, print_to_terminal=False) -> None:
    write_lines = [
        "\\documentclass[tikz]{standalone}\n",
        "\\usepackage{tikz}\n",
        "\\usetikzlibrary{calc}\n",
        "\\begin{document}\n",
        "\\begin{tikzpicture}[scale=1.0]\n",
        "% --- Define all coordinates manually ---\n",
        f"{get_coordinate_definition(points=points)}\n",
        "\\foreach \\a/\\b/\\c in {\n",
        f"{get_triangle_definition(cell_dofmap=cell_dofmap)}}}{{\n",
        "\\draw[thin,opacity=0.5] (\\a) -- (\\b) -- (\\c) -- cycle;}\n",
        "\n",
        "% Label nodes (only for creation process)\n",
        f"% \\foreach \\a in {get_all_coordinates(points=points)}}}{{\n",
        "%     \\node[blue!80!black, font=\\tiny] at (\\a) {\\a};\n",
        "% }\n",
        "\\end{tikzpicture}\n",
        "\\end{document}\n"
    ]
    with open(out,'w') as texfile: 
        if print_to_terminal:
            for line in write_lines:
                print(line,end='')
        texfile.writelines(write_lines)


def main():
    args = parse_args()

    if args.filename:
        filename = args.filename
    else:
        filename = "example_mesh"
        print("No filename provided. Generating example mesh...")
        generate_rectangle_mesh(h=0.75, filename=filename)

    out_file = args.out if args.out else f"{filename}.tex"

    points, cells, cell_dofmap = read_mesh(filename)
    get_tex_str(points, cells, cell_dofmap, out=out_file, print_to_terminal=args.print)

    print(f"TeX file written to {out_file}")


if __name__ == '__main__':
    main()
