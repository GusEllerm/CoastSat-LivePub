from typing import List
from rocrate.rocrate import ROCrate
from rocrate.model.person import Person
from rocrate.model.contextentity import ContextEntity
from rocrate.model.data_entity import DataEntity
from pathlib import Path
from collections import Counter

from helper import GitURL
from e1_crate import build_e1_crate
from e2_2_crate import build_e2_2_crate
from notebook_provenance.prospective_helper import (
    create_software_application,
    create_code_cell_steps,
    create_formal_parameters
)
from notebook_provenance.provenance_types import NotebookCellProvenance

import os
import re
import shutil
import argparse
import hashlib
from glob import glob

def build_e1(crate: ROCrate, coastsat_dir: str, URL: GitURL, E1, output_dir):
    """
    Build metadata for E1: Data Producer.
    - Identify and describe data production scripts and data outputs.
    - Describe external data sources used.
    """

    # Add Process Run Crate describing batch data production for NZ and Sardinia
    prc_dir = "batch_processes"
    prc_manifest = prc_dir + "/ro-crate-metadata.json"
    e1_output_dir = Path(output_dir) / prc_dir
    build_e1_crate(str(e1_output_dir), coastsat_dir)

    process_run_crate = crate.add(DataEntity(crate, prc_manifest, properties={
        "@type": ["RO-Crate", "ProcessRunCrate"],
        "name": "Data Producer Process Run",
        "description": "This Process Run represents the execution of the data production scripts.",
        "dateCreated": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "conformsTo": {"@id": "https://w3id.org/ro/wfrun/process/0.5"},
    }))

    # Add Pacific Rim data source
    # This is an external dataset used in the data production process
    # It is not part of the process run crate but is linked to E1
    pacific_rim_data = crate.add(ContextEntity(crate, "https://zenodo.org/records/15614554", properties={
        "@type": "Dataset",
        "name": "Pacific Rim Data",
        "description": "External data sources used in the data production process.",
        "encodingFormat": "text/csv",
        "sameAs": "https://doi.org/10.5281/zenodo.15614554"
    }))

    # Link E1 entity to the external crate directory
    existing_parts = crate.root_dataset.get("hasPart", [])
    if not isinstance(existing_parts, list):
        existing_parts = [existing_parts] if existing_parts else []
    crate.root_dataset["hasPart"] = existing_parts + [pacific_rim_data]

    E1["hasPart"] = [process_run_crate, pacific_rim_data]

def build_e2_1(crate: ROCrate, coastsat_dir: Path, URL: GitURL, E2_1):
    """
    Build metadata for E2.1: Workflow Infrastructure.
    - Identify infrastructure elements like Dockerfiles, Python packages, notebooks.
    """
    # TODO: implement infrastructure discovery
    pass

def parse_update_script(update_script_path: Path) -> tuple[list[str], list[str]]:
    comments = []
    step_files = []
    with open(update_script_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") and not line.startswith("#!"):
                comments.append(line)
            if line.startswith("jupyter nbconvert"):
                tokens = line.split()
                for token in tokens:
                    if token.endswith(".ipynb"):
                        step_files.append(token)
            elif line.startswith("./make_xlsx.py"):
                step_files.append("make_xlsx.py")
    return comments, step_files

def create_update_workflow_entity(crate: ROCrate, update_script_path: Path, comments: list[str], URL: GitURL) -> ContextEntity:
    programming_language = crate.add(ContextEntity(crate, "Bash", properties={
        "@type": "ComputerLanguage",
        "name": "Bash",
        "description": "Bash is a Unix shell and command language."
    }))

    return crate.add_file(
        update_script_path,
        properties={
            "@type": ["SoftwareSourceCode", "HowTo", "File"],
            "name": "CoastSat Update Script",
            "description": "This script updates the CoastSat project and executes the computational workflow.\n\nComments:\n" + "\n".join(comments),
            "programmingLanguage": programming_language,
            "encodingFormat": "text/x-sh",
            "codeRepository": URL.get("update.sh")["permalink_url"]
        }
    )

def compute_sha256(filepath: Path) -> str:
    """Compute the SHA256 hash of a file."""
    hash_sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def create_workflow_step_entities(crate: ROCrate, coastsat_dir: Path, step_files: list[str], URL: GitURL) -> list[dict]:

    python_language = crate.add(ContextEntity(crate, "Python", properties={
        "@type": "ComputerLanguage",
        "name": "Python",
        "url": "https://www.python.org/"
    }))

    counts = Counter(step_files)
    seen = {}
    notebook_entities = []

    for position, filename in enumerate(step_files):
        count = seen.get(filename, 0) + 1
        seen[filename] = count
        if counts[filename] > 1:
            stem, suffix = filename.rsplit('.', 1)
            identifier = f"{stem}-{count}.{suffix}"
        else:
            identifier = filename

        filepath = Path(coastsat_dir) / filename
        encoding = "application/x-ipynb+json" if filename.endswith(".ipynb") else "text/x-python"

        entity = crate.add_file(filepath, identifier, properties={
            "@type": ["File", "HowToStep", "SoftwareSourceCode"],
            "name": filename,
            "programmingLanguage": python_language,
            "encodingFormat": encoding,
            "codeRepository": URL.get(filename)["permalink_url"],
            "position": str(position),
            "sha256": compute_sha256(filepath) if filepath.is_file() else None,
        })
        notebook_entities.append({"@id": entity.id})

    return notebook_entities

def normalize_identifier(text):
    """
    Normalize strings like '#fp-transect_time_series_csv' or 'transect_time_series.csv'
    to enable fuzzy comparison.
    """
    if text.startswith('#fp-'):
        text = text[4:]
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '', text)  # Remove non-alphanumerics
    text = re.sub(r'(csv|geojson|json|txt)$', '', text)  # Remove extensions
    return text

def is_fuzzy_match(formal_param_id: str, filename: str) -> bool:
    """
    Returns True if the normalized formal param ID matches the filename.
    """
    norm_id = normalize_identifier(formal_param_id)
    norm_file = normalize_identifier(filename)
    return norm_id == norm_file

def generate_formal_parameters(crate: ROCrate, cell_provenance: dict[str, List[NotebookCellProvenance]], coastsat_dir, URL: GitURL, limit=5):

    workflow_entity = crate.get("update.sh") # An assumption is made that the update script is the main workflow entity
    if not workflow_entity:
        raise ValueError("Workflow entity (update.sh) not found in the crate.")

    # Add unique formal parameters from all cells
    seen_input_ids = set()
    seen_output_ids = set()
    seen_files = set()
    input_files = set()
    output_files = set()

    for notebook, cells in cell_provenance.items():
        for cell in cells:
            for param in (cell.input_params or []):
                param_id = param["@id"]
                if param_id not in seen_input_ids:
                    seen_input_ids.add(param_id)
                    formal_param = crate.add_formal_parameter(
                        name=param_id, 
                        additionalType="File",  
                        identifier=param_id,
                        valueRequired=True,
                        properties={}
                    )
                notebook_entity = crate.get(notebook)
                notebook_input_list = notebook_entity.get("input", [])
                workflow_input_list = workflow_entity.get("input", [])
                param_entity = crate.get(param_id)
                # Check if param_entity is already in the input list
                if param_entity not in notebook_input_list:
                    notebook_entity.append_to("input", param_entity)
                if param_entity not in workflow_input_list:
                    workflow_entity.append_to("input", param_entity)

            for param in (cell.output_params or []):
                param_id = param["@id"]
                if param_id not in seen_output_ids:
                    seen_output_ids.add(param_id)
                    formal_param = crate.add_formal_parameter(name=param_id, 
                                               additionalType="File",  
                                               identifier=param_id,
                                               valueRequired=True,
                                               properties={})
                notebook_entity = crate.get(notebook)
                notebook_output_list = notebook_entity.get("output", [])
                workflow_output_list = workflow_entity.get("output", [])
                param_entity = crate.get(param_id)
                # Check if param_entity is already in the output list
                if param_entity not in notebook_output_list:
                    notebook_entity.append_to("output", param_entity)
                if param_entity not in workflow_output_list:
                    workflow_entity.append_to("output", param_entity)

            for file in (cell.input_files or []):
                file_name = Path(file).name
                if file_name not in seen_files:
                    seen_files.add(file_name)
                    file_path = coastsat_dir / file
                    if "*" in str(file_path):
                        pattern_parts = Path(str(file_path)).parts
                        for i, matched_path in enumerate(glob(str(file_path))):
                            if limit is not None and i >= limit:
                                break
                            matched_parts = Path(matched_path).parts
                            # Find which part(s) of the pattern are wildcards and what they matched
                            wildcard_values = []
                            for p_part, m_part in zip(pattern_parts, matched_parts):
                                if "*" in p_part:
                                    wildcard_values.append(m_part)
                            # If there are wildcard values, append them to the name
                            name_with_wildcard = file_name
                            if wildcard_values:
                                name_with_wildcard = f"{file_name} ({', '.join(wildcard_values)})"
                            prev_info = URL.get(matched_path)
                            props = {
                                "@type": "File",
                                "name": name_with_wildcard,
                                "sha256": URL.get_file_hash(matched_path),
                                "size": URL.get_size_at_commit(matched_path, prev_info['commit_hash'])
                            }
                            if not prev_info.get("exists", True):
                                props["description"] = (
                                    "This file did not exist in the previous git commit; "
                                    "indicating changes happened between major releases."
                                )
                            file_entity = crate.add(ContextEntity(crate, prev_info["permalink_url"], properties=props))

                            existing_parts = crate.root_dataset.get("hasPart", [])
                            if not isinstance(existing_parts, list):
                                existing_parts = [existing_parts] if existing_parts else []
                            crate.root_dataset["hasPart"] = existing_parts + [file_entity]

                            input_files.add(file_entity)
                    else:
                        prev_info = URL.get(file_path)
                        props = {
                            "@type": "File",
                            "name": file_name,
                            "sha256": URL.get_file_hash(file_path),
                            "size": URL.get_size_at_commit(file_path, prev_info['commit_hash'])
                        }
                        if not prev_info.get("exists", True):
                            props["description"] = (
                                "This file did not exist in the previous git commit; "
                                "indicating changes happened between major releases."
                            )
                        file_entity = crate.add(ContextEntity(crate, prev_info["permalink_url"], properties=props))

                        existing_parts = crate.root_dataset.get("hasPart", [])
                        if not isinstance(existing_parts, list):
                            existing_parts = [existing_parts] if existing_parts else []
                        crate.root_dataset["hasPart"] = existing_parts + [file_entity]

                        input_files.add(file_entity)

            for file in (cell.output_files or []):
                file_name = Path(file).name
                if file_name not in seen_files:
                    seen_files.add(file_name)
                    file_path = coastsat_dir / file
                    if "*" in str(file_path):
                        pattern_parts = Path(str(file_path)).parts
                        for i, matched_path in enumerate(glob(str(file_path))):
                            if limit is not None and i >= limit:
                                break
                            matched_parts = Path(matched_path).parts
                            wildcard_values = []
                            for p_part, m_part in zip(pattern_parts, matched_parts):
                                if "*" in p_part:
                                    wildcard_values.append(m_part)
                            name_with_wildcard = file_name
                            if wildcard_values:
                                name_with_wildcard = f"{file_name} ({', '.join(wildcard_values)})"
                            info = URL.get(matched_path)
                            props = {
                                "@type": "File",
                                "name": name_with_wildcard,
                                "sha256": URL.get_file_hash(matched_path),
                                "size": URL.get_size_at_commit(matched_path, info['commit_hash'])
                            }
                            if not info.get("exists", True):
                                props["description"] = (
                                    "This file did not exist in the current git commit; "
                                    "indicating changes happened between major releases."
                                )
                            file_entity = crate.add(ContextEntity(crate, info["permalink_url"], properties=props))

                            existing_parts = crate.root_dataset.get("hasPart", [])
                            if not isinstance(existing_parts, list):
                                existing_parts = [existing_parts] if existing_parts else []
                            crate.root_dataset["hasPart"] = existing_parts + [file_entity]

                            output_files.add(file_entity)
                    else:
                        info = URL.get(file_path)
                        props = {
                            "@type": "File",
                            "name": file_name,
                            "sha256": URL.get_file_hash(file_path),
                            "size": URL.get_size_at_commit(file_path, info['commit_hash'])
                        }
                        if not info.get("exists", True):
                            props["description"] = (
                                "This file did not exist in the current git commit; "
                                "indicating changes happened between major releases."
                            )
                        file_entity = crate.add(ContextEntity(crate, info["permalink_url"], properties=props))

                        existing_parts = crate.root_dataset.get("hasPart", [])
                        if not isinstance(existing_parts, list):
                            existing_parts = [existing_parts] if existing_parts else []
                        crate.root_dataset["hasPart"] = existing_parts + [file_entity]

                        output_files.add(file_entity)
                    
        
        formal_param_entities = [e for e in crate.get_entities() if "FormalParameter" in (e.get("@type") or [])]
        for file in input_files:
            for param in formal_param_entities:
                if is_fuzzy_match(Path(file["@id"]).name, param["@id"]):
                    if param not in file.get("exampleOfWork", []):
                        file.append_to("exampleOfWork", param)

        for file in output_files:
            for param in formal_param_entities:
                if is_fuzzy_match(Path(file["@id"]).name, param["@id"]):
                    if param not in file.get("exampleOfWork", []):
                        file.append_to("exampleOfWork", param)
    

def create_notebook_provenance_crates(crate: ROCrate, step_entities: list[dict], coastsat_dir: Path, output_dir: Path):
    notebook_crates = []
    cell_prov: dict[str, List[NotebookCellProvenance]] = {}
    for i, filename in enumerate(step_entities):
        fileid = filename["@id"]
        if not fileid.endswith(".ipynb"):
            continue
        stem, suffix = fileid.rsplit(".", 1)

        e2_2_directory = "notebooks"
        e2_2_subdirectory = Path(output_dir) / e2_2_directory / stem
        e2_2_subdirectory.mkdir(parents=True, exist_ok=True)
        notebook_path = coastsat_dir / crate.get(fileid)["name"]
        result = build_e2_2_crate(str(e2_2_subdirectory), coastsat_dir, notebook_path)
        cell_prov[fileid] = result
        crate_manifest_path = Path(e2_2_subdirectory) / "ro-crate-metadata.json"
        crate_manifest = crate_manifest_path.relative_to(output_dir).as_posix()
        notebook_crate_entity = crate.add(DataEntity(crate, crate_manifest, properties={
            "@type": "RO-Crate",
            "name": f"{fileid} Provenance Crate",
            "description": f"Provenance RO-Crate for notebook/script {fileid}."        
        }))
        notebook_crates.append(notebook_crate_entity)
        
        # Link the notebook crate to its associated step entity
        step_entity = crate.get(fileid)
        step_entity["exampleOfWork"] = notebook_crate_entity
    return notebook_crates, cell_prov

def build_e2_2(crate: ROCrate, coastsat_dir: Path, URL: GitURL, E2_2, output_dir):
    """
    Build metadata for E2.2: Workflow Management System.
    - Link to external provenance crate or describe internal WMS behavior.
    """
    update_script_path = Path(coastsat_dir) / "update.sh"
    comments, step_files = parse_update_script(update_script_path)

    workflow_entity = create_update_workflow_entity(crate, update_script_path, comments, URL)
    step_entities = create_workflow_step_entities(crate, coastsat_dir, step_files, URL)

    workflow_entity["step"] = step_entities

    # --- Add notebook provenance crates for each step file ---
    notebook_crates, cell_prov = create_notebook_provenance_crates(crate, step_entities, coastsat_dir, output_dir)

    formal_params = generate_formal_parameters(crate, cell_prov, coastsat_dir, URL, limit=None)

    # Remove code_blocks directory from {output_dir}/notebooks if it exists
    code_blocks_dir = Path(output_dir) / "notebooks" / "code_blocks"
    if code_blocks_dir.exists() and code_blocks_dir.is_dir():
        shutil.rmtree(code_blocks_dir)

    # Remove plotly_results directory from {output_dir}/notebooks if it exists
    plotly_results_dir = Path(output_dir) / "notebooks" / "plotly_results"
    if plotly_results_dir.exists() and plotly_results_dir.is_dir():
        shutil.rmtree(plotly_results_dir)

    # Also link workflow_entity (update.sh) to E2_2
    if "hasPart" in E2_2:
        E2_2["hasPart"].append(workflow_entity)
    else:
        E2_2["hasPart"] = [workflow_entity]
    

def build_e3(crate: ROCrate, coastsat_dir: Path, URL: GitURL, E3):
    """
    Build metadata for E3: Experimental Results and Outcomes.
    - Describe result datasets, outputs, plots, etc.
    """
    # TODO: implement result detection and metadata description
    pass

def add_metadata(crate: ROCrate):
    author_1 = crate.add(Person(crate, "#uoa-coastsat", {"name": "example"}))
    UoA_org = crate.add(ContextEntity(crate, "University of Auckland", properties={
        "@type": "Organization",
        "name": "University of Auckland",
        "url": "https://www.auckland.ac.nz"
        }))
    
    return {
        "author": author_1,
        "organisation": UoA_org
    }
    
def add_aggregate_entities(crate: ROCrate, URL: GitURL):

    crate.name = "LivePublication Interface Crate"

    crate.mainEntity = crate.add(ContextEntity(crate, "livepublication-interface", properties={
        "@type": "Thing",
        "name": "LivePublication Interface Outputs",
        "description": "This entity represents the outputs of the Experiment Infrastructure required by the LivePublication interface. It includes references to data produced by E1 (Data Producer), E2.1 (Workflow Infrastructure), E2.2 (Workflow Management System), and E3 (Experimental Results and Outcomes).",
        "datePublished": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "version": URL.get_commit_info_for_file("update.sh")["commit_url"]}
        ))
    
    E1 = crate.add(ContextEntity(crate, "E1-data-producer", properties={
        "@type": "Thing",
        "name": "E1: Data Producer",
        "description": "This Collection includes both the process run metadata and external data sources relevant to data production."
    }))
    E2_1 = crate.add(ContextEntity(crate, "E2.1-workflow-infrastructure", properties={
        "@type": "Thing", 
        "name": "E2.1: Workflow Infrastructure", 
        "description": "Description of hardware and software environments used."
    }))
    E2_2 = crate.add(ContextEntity(crate, "E2.2-wms", properties={
        "@type": "Thing", 
        "name": "E2.2: Workflow Management System", 
        "description": "Provenance of workflow execution including workflow steps and parameters."
    }))
    E3 = crate.add(ContextEntity(crate, "E3-experimental-results", properties={
        "@type": "Thing", 
        "name": "E3: Experimental Results and Outcomes", 
        "description": "Results of the executed workflow, such as figures and summary data products."
    }))
    
    crate.mainEntity["hasPart"] = [E1, E2_1, E2_2, E3]

    return {
        "E1": E1,
        "E2_1": E2_1,
        "E2_2": E2_2,
        "E3": E3
    }

def get_parser() -> argparse.ArgumentParser:
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Build LivePublication interface crate.")
    parser.add_argument(
        "--coastsat-dir",
        type=Path,
        required=False,
        default=Path(__file__).parent.parent / "CoastSat",
        help="Path to CoastSat project directory."
    )  
    parser.add_argument(
        "--output-dir", 
        type=Path, 
        required=False, 
        default=Path(__file__).parent / "interface.crate", 
        help="Directory to write the interface RO-Crate."
    ) 
    return parser

def main():
    
    # Parse command line arguments
    parser = get_parser()
    args = parser.parse_args()
    coastsat_dir = args.coastsat_dir
    output_dir = args.output_dir

    # Setup GitURL for the repo
    URL = GitURL(repo_path=args.coastsat_dir, remote_name="origin")

    crate = ROCrate()
    
    infrastructure_entities = add_aggregate_entities(crate, URL)
    contextual_entities = add_metadata(crate)

    # Build experiment infrastructure layers
    build_e1(crate, coastsat_dir, URL, infrastructure_entities["E1"], output_dir)
    build_e2_1(crate, coastsat_dir, URL, infrastructure_entities["E2_1"])
    build_e2_2(crate, coastsat_dir, URL, infrastructure_entities["E2_2"], output_dir)
    build_e3(crate, coastsat_dir, URL, infrastructure_entities["E3"])

    # Write crate to specified output directory
    crate.write(output_dir)

if __name__ == "__main__":
    main()