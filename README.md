# Mesh to TikZ Converter

`msh2tikz.py` converts a 2D triangular mesh in Gmsh `.msh` format into a standalone LaTeX `.tex` file containing TikZ code. The generated document can be compiled directly or embedded into larger LaTeX workflows.

The tool can also generate a built-in example mesh when no input file is given, crop the exported mesh to a rectangular region, rescale coordinates for better visibility in TikZ, and optionally classify elements by incircle diameter.

![Example Output](example/example_mesh.svg)

---

## 🔧 Features

- Convert 2D triangular Gmsh meshes (Gmsh 2.2 format) to standalone TikZ/LaTeX documents.
- Generate a sample rectangular mesh when no input mesh is provided.
- Export only a rectangular subsection of the mesh with `--bbox`.
- Rescale geometry with `--fit-width` / `--fit-height`.
- Apply an additional TikZ picture scale via `--tikz-scale`.
- Keep original coordinates or shift the exported mesh to start at `(0,0)`.
- Highlight small elements using an incircle-diameter threshold.
- Print the generated TeX to the terminal and/or preview the mesh with Matplotlib.
- Generated TikZ files already include commented node-label code that can be enabled for manual inspection.

---

## Requirements

- Python 3.11 or newer recommended
- `numpy`
- `meshio`
- `matplotlib` (only needed for `--plot`)
- `gmsh` / `python-gmsh` (only needed when generating the built-in example mesh)

---

## 📦 Setup

### Conda / Miniforge

We recommend using [Miniforge](https://github.com/conda-forge/miniforge):

```bash
# Create environment
conda create -n msh2tikz python=3.11

# Activate environment
conda activate msh2tikz

# Install dependencies
conda install -c conda-forge python-gmsh meshio numpy matplotlib
```

---

## Basic usage

```bash
python msh2tikz.py [filename] [options]
```

- If `filename` is omitted, the script generates `example_mesh.msh` and converts it.
- If `filename` is given without a suffix, `.msh` is appended automatically.
- If `--out` is omitted, the output defaults to the input name with a `.tex` suffix.

Examples:

```bash
# Read my_mesh.msh and write my_mesh.tex
python msh2tikz.py my_mesh

# Read an explicit .msh filename and write a custom output file
python msh2tikz.py meshes/domain.msh --out exports/domain_tikz.tex

# Generate the built-in example mesh and convert it
python msh2tikz.py
```

---

## Command-line options

### General output

- `-o, --out PATH`  
  Output `.tex` file. Defaults to `<input>.tex`.

- `--print`  
  Print the generated TeX document to standard output in addition to writing it to a file.

- `--plot`  
  Show a Matplotlib preview of the exported mesh.

### Geometric filtering and scaling

- `--bbox XMIN XMAX YMIN YMAX`  
  Export only the triangles whose three vertices lie inside the rectangular box `[XMIN, XMAX] x [YMIN, YMAX]`.

- `--fit-width W`  
  Uniformly rescale the exported coordinates so that the resulting mesh width becomes `W` TikZ units.

- `--fit-height H`  
  Uniformly rescale the exported coordinates so that the resulting mesh height becomes `H` TikZ units.

- `--tikz-scale S`  
  Apply an additional TikZ-scale factor to the whole `tikzpicture`. Default: `1.0`.

- `--keep-global-coordinates`  
  By default, the exported mesh is shifted so that its lower-left corner is at `(0,0)`. Use this flag to keep the original coordinate system.

### Element classification and styling

- `--incircle-diameter-threshold D`  
  Split triangles into two groups depending on whether their incircle diameter is below `D`.

- `--small-element-style STYLE`  
  TikZ style used for triangles below the threshold.  
  Default: `fill=red!35,draw=red!70!black,thin`

- `--large-element-style STYLE`  
  TikZ style used for triangles at or above the threshold.  
  Default: `fill=blue!12,draw=blue!70!black,thin`

- `--mesh-style STYLE`  
  TikZ style used when no threshold is provided.  
  Default: `thin`

---

## Examples

### 1. Convert a mesh with default settings

```bash
python msh2tikz.py example/example_mesh
```

This writes `example/example_mesh.tex`.

### 2. Print the generated TikZ document to the terminal

```bash
python msh2tikz.py example/example_mesh --print
```

### 3. Export only a bounding box of the mesh

```bash
python msh2tikz.py example/example_mesh \
  --bbox 1.0 6.0 1.0 4.0 \
  --out example/example_mesh_cropped.tex
```

This keeps only triangles fully contained in the rectangle `[1,6] x [1,4]`.

### 4. Fit the exported mesh to a target width

```bash
python msh2tikz.py example/example_mesh \
  --fit-width 10 \
  --out example/example_mesh_w10.tex
```

This rescales the coordinates so the exported mesh width becomes `10` TikZ units.

### 5. Fit into a width/height box while preserving aspect ratio

```bash
python msh2tikz.py example/example_mesh \
  --fit-width 8 \
  --fit-height 4 \
  --out example/example_mesh_fitbox.tex
```

If both options are used, scaling remains uniform and the mesh is scaled to fit inside the requested box.

### 6. Keep original mesh coordinates

```bash
python msh2tikz.py example/example_mesh \
  --keep-global-coordinates \
  --out example/example_mesh_global_coords.tex
```

By default, the exporter shifts the mesh so that the lower-left corner is at `(0,0)`. This flag disables that shift.

### 7. Apply an additional TikZ picture scale

```bash
python msh2tikz.py example/example_mesh \
  --fit-width 8 \
  --tikz-scale 0.75 \
  --out example/example_mesh_scaled_picture.tex
```

Use `--fit-width` / `--fit-height` to change coordinates themselves, and `--tikz-scale` to scale the rendered picture at the TikZ level.

### 8. Highlight small elements by incircle diameter

```bash
python msh2tikz.py example/example_mesh_local_refinement \
  --incircle-diameter-threshold 0.2 \
  --small-element-style 'fill=orange!50,draw=orange!80!black,thin' \
  --large-element-style 'fill=blue!15,draw=black!50,thin' \
  --out example/example_mesh_local_refinement_quality.tex
```

The threshold is evaluated in the original mesh coordinates, before any display rescaling.

### 9. Plot the exported mesh for a quick visual check

```bash
python msh2tikz.py example/example_mesh --plot
```

---

## Notes on generated TikZ

- The output is a complete standalone LaTeX document using the `standalone` class.
- All points are written as named TikZ coordinates like `P0`, `P1`, `P2`, ...
- The generated file includes commented code for node labels, for example:

```tex
% \foreach \a in {P0,P1,P2}{
%     \node[blue!80!black, font=\normalsize] at (\a) {\a};
% }
```

Uncomment and adapt those lines if you want to inspect node names while editing the figure.

---

## Example output files

The repository already contains example files in `example/`:

- `example/example_mesh.msh`
- `example/example_mesh.tex`
- `example/example_mesh.pdf`
- `example/example_mesh.svg`

---

## Limitations

- Only 2D triangular meshes are supported.
- Bounding-box export keeps only triangles fully inside the box; partially intersecting triangles are omitted.
- Runtime examples that generate meshes require `gmsh` to be installed in the active Python environment.
