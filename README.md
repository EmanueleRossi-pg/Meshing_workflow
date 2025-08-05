# Automated OpenFOAM Mesh Generation

This repository provides a Python-driven workflow to automate the creation of a high-quality OpenFOAM mesh (blockMesh + snappyHexMesh) for any STL geometry.

## Key Features

- **Single‐case pipeline**  
  Automatically detects one STL file in `inputSTL/` and builds a complete case in `case/`.

- **Dynamic blockMesh creation**  
  Generates `blockMeshDict` based on STL bounding box and user-specified cell sizes.

- **Automated snappyHexMesh refinement**  
  Inserts a refinement box around the STL geometry, sets `locationInMesh` dynamically, and runs snappyHexMesh in single-core or multi-cores.

- **Easy cleanup**  
  Provides `clear_all.py` to remove `case/` and any intermediate output directories.
