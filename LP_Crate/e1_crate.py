

from rocrate.rocrate import ROCrate
import argparse
import os

def build_e1_crate(output_dir: str):
    crate = ROCrate()

    # Add minimal metadata
    crate.name = "E1: Data Producer"
    crate.description = "Process Run Crate representing the Data Producer layer."
    crate.metadata["conformsTo"] = {
        "@id": "https://w3id.org/ro/wfrun/process/0.5"
    }

    # Write to output
    crate.write(output_dir)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, help="Output directory for E1 RO-Crate")
    args = parser.parse_args()

    output_path = os.path.abspath(args.output_dir)
    os.makedirs(output_path, exist_ok=True)

    build_e1_crate(output_path)

if __name__ == "__main__":
    main()