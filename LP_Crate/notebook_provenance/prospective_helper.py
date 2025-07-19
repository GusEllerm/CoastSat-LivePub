import re
import os
import nbformat
import json
import hashlib
from pathlib import Path
from glob import glob
from typing import List, Dict, Set, Tuple, Any
from rocrate.rocrate import ROCrate
from rocrate.model.contextentity import ContextEntity
from .provenance_types import NotebookCellProvenance


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
    read_patterns = [
        r'read_csv\((?:f)?["\']([^"\']+)["\']',
        r'read_file\((?:f)?["\']([^"\']+)["\']',
        r'glob\((?:f)?["\']([^"\']+)["\']'
    ]
    write_patterns = [
        r'to_csv\((?:f)?["\']([^"\']+)["\']',
        r'to_file\((?:f)?["\']([^"\']+)["\']'
    ]

    input_paths, output_paths = set(), set()
    for line in sources:
        for pattern in read_patterns:
            for match in re.findall(pattern, line):
                input_paths.add(_normalize_interpolated_path(match))
        for pattern in write_patterns:
            for match in re.findall(pattern, line):
                output_paths.add(_normalize_interpolated_path(match))

    return input_paths, output_paths

def _normalize_interpolated_path(path: str) -> str:
    """
    Normalize interpolated or globbed paths by:
    - Replacing string interpolation like {sitename} with '*'
    - Replacing any explicit globs like 'nzd*' with '*'
    - Collapsing multiple adjacent wildcards
    """
    # Replace interpolated values like {var} with *
    path = re.sub(r'{[^}]+}', '*', path)

    # Replace glob patterns like nzd* with *
    path = re.sub(r'\b\w*\*\w*\b', '*', path)

    # Replace any remaining sequences like */*/ to */ and similar
    path = re.sub(r'\*+', '*', path)

    return path

def file_sha256(filepath: str) -> str:
    """
    Compute the SHA256 hash of a file.

    Parameters:
        filepath (str): Path to the file.

    Returns:
        str: SHA256 hex digest of the file.
    """
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def link_steps_to_code_blocks(crate: ROCrate, crate_output_dir: Path, notebook_path, notebook_file, cell_entities, formal_params):
    
    code_blocks_dir = Path(crate_output_dir).parent / "code_blocks"
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
                "@type": ["SoftwareApplication", "File"],
                "name": f"Code Cell {i+1}",
                "sha256": file_sha256(str(code_path)),
            }
        )
        cell.software_app = code_file
        cell.howto_step["workExample"] = {"@id": code_file.id}

        # Match file paths used in this code block
        input_paths, output_paths = extract_unique_file_paths([cell.source])
        cell.input_params = [formal_params[os.path.basename(p)] for p in sorted(set(input_paths)) if os.path.basename(p) in formal_params]
        cell.output_params = [formal_params[os.path.basename(p)] for p in sorted(set(output_paths)) if os.path.basename(p) in formal_params]

        cell.input_files = sorted(set(input_paths))
        cell.output_files = sorted(set(output_paths))

        # Add reference to parent notebook
        cell.notebook_path = notebook_path

        # Attach formal parameters to this code file (avoid duplicates, use basename as key)
        code_file["input"] = [
            {"@id": formal_params[os.path.basename(p)].id}
            for p in sorted(set(input_paths))
            if os.path.basename(p) in formal_params
        ] if input_paths else []
        code_file["output"] = [
            {"@id": formal_params[os.path.basename(p)].id}
            for p in sorted(set(output_paths))
            if os.path.basename(p) in formal_params
        ] if output_paths else []

    return cell_entities


def create_formal_parameters(crate, source_lines: List[str], notebook_file, software_app, collapse_formal_parameters: bool = True) -> Dict[str, ContextEntity]:
    """
    Create FormalParameter entities for input/output file paths found in the notebook source lines.

    Parameters:
    - collapse_formal_parameters (bool): If True, paths are collapsed by their filename (basename),
      meaning different paths with the same filename are treated as the same FormalParameter.
      Set to False for stricter provenance recording that preserves full path information.
    """
    input_paths, output_paths = extract_unique_file_paths(source_lines)
    formal_params = {}

    # If collapse_formal_parameters is True, use just the filename (basename) as the key.
    # This collapses different paths with the same filename to the same FormalParameter entity.
    def get_fp_key(path: str) -> str:
        return os.path.basename(path) if collapse_formal_parameters else path

    for path in sorted(input_paths | output_paths):
        key = get_fp_key(path)
        if key not in formal_params:
            param = crate.add(ContextEntity(crate, f"#fp-{re.sub(r'[^a-zA-Z0-9_-]', '_', key)}", properties={
                "@type": "FormalParameter",
                "name": os.path.basename(path)
            }))
            formal_params[key] = param

    # Avoid duplicate entries by using set of IDs and sorting for consistency
    input_ids = sorted({formal_params[get_fp_key(p)].id for p in input_paths if get_fp_key(p) in formal_params})
    output_ids = sorted({formal_params[get_fp_key(p)].id for p in output_paths if get_fp_key(p) in formal_params})

    notebook_file["input"] = [{"@id": i} for i in input_ids] if input_ids else []
    notebook_file["output"] = [{"@id": i} for i in output_ids] if output_ids else []

    return formal_params

def get_matching_notebook_cell(cell_entity: NotebookCellProvenance, notebook_path: str) -> Dict:
    """
    Given a NotebookCellProvenance object and a notebook path, return the matching notebook cell.
    Assumes that the code in `cell_entity.source` matches exactly the source in the notebook cell.
    """
    with open(notebook_path, "r", encoding="utf-8") as f:
        notebook = nbformat.read(f, as_version=4)
        for cell in notebook.cells:
            if cell.cell_type == "code" and cell.get("source", "") == cell_entity.source:
                return cell
    return {}


def add_create_actions(crate: ROCrate, cell_entities: List[NotebookCellProvenance], notebook_path):
    """
    Add CreateAction entities for each code cell step, linking them to the notebook file.
    """
    for cell in cell_entities:
        action = crate.add(ContextEntity(crate, f"#create-action-{cell.howto_step.id.split('-')[-1]}", properties={
            "@type": "CreateAction",
            "instrument": {"@id": cell.software_app.id},
        }))
        
        cell.create_action = action
        cell.howto_step["about"] = {"@id": action.id}

    return cell_entities

def add_prov_results(crate: ROCrate, cell_entities: List[NotebookCellProvenance], notebook_path, crate_output_dir):
    """
    Add ProvResult entities for each CreateAction, scraping the jupyter notebook for Plotly results. 
    """
    # Open the notebook
    with open(notebook_path, "r", encoding="utf-8") as f:
        notebook = nbformat.read(f, as_version=4)

    # Find crate output directory
    crate_output_dir = Path(crate_output_dir).parent
    plotly_output_dir = crate_output_dir / "plotly_results"
    plotly_output_dir.mkdir(parents=True, exist_ok=True)

    for cell in cell_entities:
        # Find the matching cell in the notebook
        matched_cell = get_matching_notebook_cell(cell, notebook_path)
        if not matched_cell:
            continue

        outputs = matched_cell.get("outputs", [])
        for j, output in enumerate(outputs):
            if (
                output.get("output_type") == "display_data" and
                "application/vnd.plotly.v1+json" in output.get("data", {})
            ):
                plot_data = output["data"]["application/vnd.plotly.v1+json"]
                # Compose result filename
                result_filename = f"{cell.howto_step.id.strip('#')}_plotly_{j+1}.json"
                result_path = plotly_output_dir / result_filename

                # Save Plotly JSON to file
                with open(result_path, "w", encoding="utf-8") as f:
                    json.dump(plot_data, f)

                # Add file to crate and link as result
                result_file = crate.add_file(
                    source=str(result_path),
                    dest_path=f"plotly_results/{result_filename}",
                    properties={
                        "@type": "MediaObject",
                        "encodingFormat": "application/vnd.plotly.v1+json",
                        "name": f"Plotly chart from {cell.howto_step.id}"
                    }
                )

                cell.prov_result = result_file
                cell.create_action["result"] = {"@id": result_file.id}

    return cell_entities

