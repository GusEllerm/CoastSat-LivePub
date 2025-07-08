import re
import os
import nbformat
import json
from pathlib import Path
from glob import glob
from typing import List, Dict, Set, Tuple, Any
from rocrate.rocrate import ROCrate
from rocrate.model.contextentity import ContextEntity
from provenance_types import NotebookCellProvenance

def parse_notebook_cells(notebook_path: str) -> List[str]:
    with open(notebook_path, "r", encoding="utf-8") as f:
        notebook = nbformat.read(f, as_version=4)
    return [cell["source"] for cell in notebook.cells if cell.cell_type == "code"]

def create_code_cell_steps(crate: ROCrate, software_app: ContextEntity, notebook_path: str) -> List[NotebookCellProvenance]:
    sources = parse_notebook_cells(notebook_path)
    cell_entities = []
    for i, src in enumerate(sources):
        step: Any = crate.add(ContextEntity(crate, f"#step-{i+1}", properties={
            "@type": "HowToStep",
            "position": i + 1,
            "name": f"Code cell {i+1}",
            "tool": {"@id": software_app.id}
        }))
        cell_entities.append(NotebookCellProvenance(source=src, howto_step=step))
    return cell_entities

def create_software_application(crate: ROCrate, notebook_path: str) -> ContextEntity:
    

    with open(notebook_path, 'r', encoding='utf-8') as f:
      nb_data = json.load(f)
      nb_metadata = nb_data.get("metadata", {})
      kernel_info = nb_metadata.get("kernelspec", {})
      kernel_name = kernel_info.get("name", "python3")
      kernel_display_name = kernel_info.get("display_name", "Python 3")
      kernel_version = nb_metadata.get("language_info", {}).get("version", "unknown")

    
    software_app: Any = crate.add(ContextEntity(crate, "#jupyter-kernel", properties={
        "@type": "SoftwareApplication",
        "name": "Jupyter Notebook Kernel",
        "version": kernel_version,
        "programmingLanguage": kernel_name,
        "description": f"Jupyter Notebook kernel for {kernel_display_name}",
        "identifier": kernel_name,
        "softwareVersion": kernel_version
    }))
    return software_app

def extract_unique_file_paths(sources: List[str]) -> Tuple[Set[str], Set[str]]:
    read_patterns = [r'read_csv\(["\']([^"\']+)["\']', r'read_file\(["\']([^"\']+)["\']', r'glob\(["\']([^"\']+)["\']']
    write_patterns = [r'to_csv\(["\']([^"\']+)["\']', r'to_file\(["\']([^"\']+)["\']']

    input_paths, output_paths = set(), set()
    for line in sources:
        for pattern in read_patterns:
            input_paths.update(re.findall(pattern, line))
        for pattern in write_patterns:
            output_paths.update(re.findall(pattern, line))
    return input_paths, output_paths

def link_steps_to_code_blocks(crate, notebook_path, notebook_file, cell_entities, formal_params):
    code_blocks_dir = Path(notebook_path).parent / "code_blocks"
    code_blocks_dir.mkdir(parents=True, exist_ok=True)

    for i, cell in enumerate(cell_entities):
        code_filename = f"cell_{i+1}.py"
        code_path = code_blocks_dir / code_filename

        with open(code_path, "w", encoding="utf-8") as f:
            f.write(cell.source)

        code_file = crate.add_file(
            source=str(code_path),
            dest_path=f"code_blocks/{code_filename}",
            properties={
                "@type": ["File", "SoftwareSourceCode"],
                "name": f"Code Cell {i+1}"
            }
        )

        cell.howto_step["workExample"] = {"@id": code_file.id}

        # Match file paths used in this code block
        input_paths, output_paths = extract_unique_file_paths([cell.source])

        # Attach formal parameters to this code file
        if input_paths:
            code_file["input"] = [{"@id": formal_params[p].id} for p in input_paths if p in formal_params]
        if output_paths:
            code_file["output"] = [{"@id": formal_params[p].id} for p in output_paths if p in formal_params]


def create_formal_parameters(crate, source_lines: List[str], file_index: List[str], notebook_file, software_app) -> Dict[str, ContextEntity]:
    input_paths, output_paths = extract_unique_file_paths(source_lines)
    formal_params = {}

    for path in sorted(input_paths | output_paths):
        param = crate.add(ContextEntity(crate, f"#fp-{re.sub(r'[^a-zA-Z0-9_-]', '_', path)}", properties={
            "@type": "FormalParameter",
            "name": os.path.basename(path)
        }))
        formal_params[path] = param

    notebook_file["input"] = [{"@id": formal_params[p].id} for p in input_paths]
    notebook_file["output"] = [{"@id": formal_params[p].id} for p in output_paths]
    software_app["input"] = [{"@id": formal_params[p].id} for p in input_paths]
    software_app["output"] = [{"@id": formal_params[p].id} for p in output_paths]

    return formal_params