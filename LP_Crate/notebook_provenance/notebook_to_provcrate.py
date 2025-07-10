from dataclasses import dataclass
import re
from typing import List, Optional, Any, Set, Tuple, Dict
import os
import json
from pathlib import Path
from rocrate.rocrate import ROCrate
from datetime import datetime
from rocrate.rocrate import DataEntity
from rocrate.model.contextentity import ContextEntity
from .prospective_helper import (
    create_software_application,
    create_code_cell_steps,
    link_steps_to_code_blocks,
    create_formal_parameters,
    add_create_actions,
    add_prov_results
)
from .provenance_types import ProspectiveIndex

def generate_prospective_entities(crate, notebook_path, crate_output_dir) -> ProspectiveIndex:
    notebook_file: Any = crate.add_file(
        source=notebook_path,
        properties={
            "@type": ["File", "SoftwareSourceCode", "HowTo"]
        }
    )
    crate.mainEntity = notebook_file

    software_app = create_software_application(crate, notebook_path)
    cell_entities = create_code_cell_steps(crate, software_app, notebook_path)
    print(f"Added {len(cell_entities)} HowToStep entities.")

    crate.update_jsonld({
        "@id": notebook_file.id,
        "step": [{"@id": cell.howto_step.id} for cell in cell_entities]
    })

    # Gather all source lines and create formal parameters
    source_lines = [cell.source for cell in cell_entities]
    formal_params = create_formal_parameters(crate, source_lines, notebook_file, software_app)
    link_steps_to_code_blocks(crate, crate_output_dir, notebook_path, notebook_file, cell_entities, formal_params)
    add_create_actions(crate, cell_entities, notebook_path)
    add_prov_results(crate, cell_entities, notebook_path, crate_output_dir)

    crate.mainEntity["targetProduct"] = software_app

    return ProspectiveIndex(
        main_workflow=notebook_file,
        software_app=software_app,
        steps=cell_entities,
        formal_params=formal_params
    )

def generate_provenance_crate_for_notebook(notebook_path, crate_path):
    crate = ROCrate()
    generate_prospective_entities(crate, notebook_path, crate_path)
    
    return crate

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate RO-Crate for Jupyter Notebook provenance.")
    parser.add_argument("notebook_path", type=Path, help="Path to the Jupyter Notebook file.")
    parser.add_argument("crate_path", type=Path, help="Output path for the RO-Crate.")

    args = parser.parse_args()

    generate_provenance_crate_for_notebook(args.notebook_path, args.crate_path)