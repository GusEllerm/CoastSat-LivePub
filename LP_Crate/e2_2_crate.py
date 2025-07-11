from notebook_provenance.notebook_to_provcrate import generate_provenance_crate_for_notebook
from notebook_provenance.provenance_types import NotebookCellProvenance

from rocrate.rocrate import ROCrate
from pathlib import Path
import argparse
from typing import List

def build_e2_2_crate(output_dir: str, coastsat_dir: str, notebook_path: str) -> List[NotebookCellProvenance]:
    """
    Build a provenance RO-Crate describing the WMS layer (E2.2).
    This crate may later be linked into the interface crate.
    """

    crate, cell_prov = generate_provenance_crate_for_notebook(notebook_path, output_dir)
    crate.write(output_dir)
    return cell_prov

def main():
    parser = argparse.ArgumentParser(description="Build LivePublication provenance crate.")
    parser.add_argument("--coastsat-dir", type=Path, required=True, help="Path to CoastSat project directory.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory to write the provenance RO-Crate.")
    args = parser.parse_args()

    coastsat_dir = args.coastsat_dir
    output_dir = args.output_dir

    # crate = build_provenance_crate(coastsat_dir)
    # crate.write(output_dir)

if __name__ == "__main__":
    main()