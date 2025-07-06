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
from prospective_helper import (
    create_software_application,
    create_code_cell_steps,
    link_steps_to_code_blocks,
    create_formal_parameters
)
from provenance_types import ProspectiveIndex

def generate_prospective_entities(crate, notebook_path, file_index) -> ProspectiveIndex:
    notebook_file: Any = crate.add_file(
        source=notebook_path,
        properties={
            "@type": ["File", "SoftwareSourceCode", "ComputationalWorkflow", "HowTo"]
        }
    )
    crate.mainEntity = notebook_file

    # Add conformsTo entries to the root Dataset
    crate.root_dataset["conformsTo"] = [
        {"@id": "https://w3id.org/ro/wfrun/process/0.1"},
        {"@id": "https://w3id.org/ro/wfrun/workflow/0.1"},
        {"@id": "https://w3id.org/ro/wfrun/provenance/0.5"},
        {"@id": "https://w3id.org/workflowhub/workflow-ro-crate/1.0"}
    ]

    software_app = create_software_application(crate, notebook_path)
    cell_entities = create_code_cell_steps(crate, software_app, notebook_path)
    print(f"Added {len(cell_entities)} HowToStep entities.")

    crate.update_jsonld({
        "@id": notebook_file.id,
        "step": [{"@id": cell.howto_step.id} for cell in cell_entities]
    })


    # Gather all source lines and create formal parameters
    source_lines = [cell.source for cell in cell_entities]
    formal_params = create_formal_parameters(crate, source_lines, file_index, notebook_file, software_app)
    link_steps_to_code_blocks(crate, notebook_path, notebook_file, cell_entities, formal_params)


    return ProspectiveIndex(
        main_workflow=notebook_file,
        software_app=software_app,
        steps=cell_entities,
        formal_params=formal_params
    )

def generate_provenance_crate_for_notebook(notebook_path, crate_path, file_index):
    crate = ROCrate()
    index = generate_prospective_entities(crate, notebook_path, file_index)
    crate.write(crate_path)
