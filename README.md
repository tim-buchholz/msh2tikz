# Mesh to TikZ Converter

This script converts a 2D triangular mesh in `.msh` format (from Gmsh) into a standalone LaTeX `.tex` file using TikZ. It can also generate an example mesh and visualize it. Useful for embedding computational meshes in academic papers or documentation.

![Example Output](example/example_mesh.svg)

---

## 🔧 Features

- Converts `.msh` mesh files (Gmsh 2.2 format) into TikZ code.
- Optionally prints the generated TikZ code to the terminal.
- Automatically generates a sample rectangle mesh if no file is provided.
- Clean and minimal LaTeX/TikZ output.
- In case you need to make adjustments to your mesh, the nodes are already ready to get labeled in the .tex file. You just need to uncomment the commented lines of tikz-code.

---

## 📦 Setup (with Conda & Miniforge)

We recommend using [Miniforge](https://github.com/conda-forge/miniforge) to create a clean environment:

```bash
# Create environment
conda create -n msh2tikz python=3.11

# Activate environment
conda activate msh2tikz

# Install required packages
conda install -c conda-forge python-gmsh meshio numpy matplotlib


## 💡 Examples

```bash
# Convert an existing mesh to TikZ
python msh2tikz.py my_mesh -o my_mesh_output.tex

# Generate a sample rectangle mesh and convert to TikZ
python msh2tikz.py

# Convert a mesh and print the TikZ code to terminal
python msh2tikz.py my_mesh -p


