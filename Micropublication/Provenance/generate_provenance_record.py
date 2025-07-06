import os
import re
from pathlib import Path
from typing import Any, Dict, Tuple, List
from collections import defaultdict
from notebook_to_provcrate import generate_provenance_crate_for_notebook

def index_project_directory(root_dir: str) -> Tuple[Path, Dict[str, Any]]:
    root = Path(root_dir)
    update_sh_path = None
    file_tree = {}

    def walk_directory(current_path: Path) -> Dict[str, Any]:
        tree: Dict[str, Any] = {}
        for item in sorted(current_path.iterdir()):
            if item.name.startswith('.'):
                continue  # Skip hidden files/folders
            if item.is_dir():
                tree[item.name] = walk_directory(item)
            else:
                tree[item.name] = item.resolve()
                if item.name == "update.sh":
                    nonlocal update_sh_path
                    update_sh_path = item.resolve()
        return tree

    file_tree = walk_directory(root)

    if not update_sh_path:
        raise FileNotFoundError("update.sh not found in the project directory.")

    return update_sh_path, file_tree

def parse_notebook_execution_order(update_sh_path: Path) -> List[str]:
    notebook_files = []
    with open(update_sh_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("jupyter nbconvert") and "--execute" in line:
                # extract all .ipynb filenames using regex
                notebook_files = re.findall(r'\S+\.ipynb', line)
                break  # assume only one such line
    return notebook_files

if __name__ == "__main__":

    project_path = Path("/Users/eller/Projects/CoastSat_Implementation/CoastSat")
    update_sh, file_index = index_project_directory(str(project_path.absolute()))
    notebooks = parse_notebook_execution_order(update_sh)

    # Create a directory to hold all the crates
    crate_output_dir = Path("generated_crates")
    crate_output_dir.mkdir(exist_ok=True)

    execution_counter = defaultdict(int)
    subcrate_paths = []

    for idx, notebook in enumerate(notebooks):

        execution_counter[notebook] += 1
        run_number = execution_counter[notebook]
        
        notebook_path = project_path / notebook
        crate_name = f"{notebook_path.stem}_run{run_number}_crate"
        crate_path = crate_output_dir / crate_name

        
        generate_provenance_crate_for_notebook(notebook_path, crate_path, file_index)
        subcrate_paths.append((crate_path, notebook, run_number))
            