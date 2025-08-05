#!/usr/bin/env python3
"""
Single-case OpenFOAM Meshing & Simulation Pipeline in Python
"""
import os
import re
import shutil
import subprocess
from pathlib import Path

#-----------------------------------------------------------------
# CONFIGURATION
#-----------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_DIR = SCRIPT_DIR / 'inputSTL'
MESH_TMPL = SCRIPT_DIR / 'mesh'
SCRIPTS = SCRIPT_DIR / 'scripts'
TEMPLATE_CASE = SCRIPT_DIR / 'templateCase'
CASE = SCRIPT_DIR / 'case'

IMPORT_SCRIPT = SCRIPTS / 'import_geometry.py'
BMD_SCRIPT = SCRIPTS / 'generate_blockMeshDict.py'
CASE_SCRIPT = SCRIPTS / 'case_structure.py'

#-----------------------------------------------------------------
# UTILITY FUNCTIONS
#-----------------------------------------------------------------
def print_section(title: str):
    print(f"\n{'='*60}\n==> {title}\n{'='*60}")

def run_and_log(cmd: str, cwd: Path, log_file: str):
    print(f"⌛ Running in {cwd.name}: {cmd}")
    log_path = cwd / log_file
    with open(log_path, 'wb') as log:
        proc = subprocess.run(cmd, cwd=cwd, shell=True, stdout=log, stderr=log)
        proc.check_returncode()
    print(f"✔️  Completed: {cmd}")

#-----------------------------------------------------------------
# MAIN PIPELINE
#-----------------------------------------------------------------
def main():
    os.chdir(SCRIPT_DIR)

    # detect single STL in inputSTL folder
    stl_files = list(INPUT_DIR.glob('*.stl'))
    if not stl_files:
        print(f"❌ No .stl files found in {INPUT_DIR}")
        return
    if len(stl_files) > 1:
        print(f"⚠️  Multiple .stl files found, using first: {stl_files[0].name}")
    INPUT_STL = stl_files[0]

    # Ensure single case dir
    if CASE.exists():
        print_section("Cleaning existing case directory")
        shutil.rmtree(CASE)
    CASE.mkdir()

    # 1) Prepare case structure
    print_section(f"1. Generating case structure for {INPUT_STL.name}")
    subprocess.run(['python3', str(CASE_SCRIPT)], check=True)
    print(f"✔️  Case structure generated for {INPUT_STL.name}")

    # 2) blockMesh & surfaceFeatureExtract
    print_section("2. Running blockMesh & surfaceFeatureExtract")
    run_and_log('blockMesh', CASE, 'log_blockMesh.txt')
    run_and_log('surfaceFeatureExtract', CASE, 'log_surfaceFeatureExtract.txt')

    # 3) snappyHexMesh
    print_section("3. Running snappyHexMesh")
    runParallel = input("Run snappyHexMesh in multi_cores? [y/N]: ").strip().lower() == 'y'
    nproc = int(input("Number of cores [default 4]: ").strip() or 4) if runParallel else 1
    if runParallel:
        run_and_log('decomposePar', CASE, 'log_decomposePar.txt')
        run_and_log(
            f"mpirun -np {nproc} snappyHexMesh -dict system/snappyHexMeshDict -parallel -overwrite",
            CASE, 'log_snappyHexMesh.txt'
        )
        run_and_log('reconstructParMesh -constant', CASE, 'log_reconstructParMesh.txt')
        for procdir in CASE.glob('processor*'):
            shutil.rmtree(procdir, ignore_errors=True)
    else:
        run_and_log('snappyHexMesh -dict system/snappyHexMeshDict -overwrite', CASE, 'log_snappyHexMesh.txt')
    print(f"✔️  snappyHexMesh completed ({'parallel' if runParallel else 'single-core'})")

    # 4) Finalize mesh & create .foam file
    print_section("4. Finalizing mesh")
    foamfile = CASE / f"{CASE.name}.foam"
    if not foamfile.exists():
        foamfile.touch()
        print(f"✔️  Created foam file: {foamfile.name}")

    # 5) Run CFD solver
    print_section("5. Running CFD solver")
    ctrl = TEMPLATE_CASE / 'system' / 'controlDict'
    solver = 'simpleFoam'
    if ctrl.is_file():
        for line in ctrl.read_text().splitlines():
            m = re.match(r'^\s*application\s+(\S+)', line)
            if m:
                solver = m.group(1).rstrip(';')
                break
    runSol = input("Run solver in multi-cores? [y/N]: ").strip().lower() == 'y'
    if runSol:
        run_and_log('decomposePar', CASE, 'log_decomposePar_sim.txt')
        run_and_log(f"mpirun -np {nproc} {solver} -parallel", CASE, 'log_solver.txt')
        run_and_log('reconstructPar', CASE, 'log_reconstructSim.txt')
    else:
        run_and_log(solver, CASE, 'log_solver.txt')

    print_section("PIPELINE COMPLETED SUCCESSFULLY!")

if __name__ == '__main__':
    main()
