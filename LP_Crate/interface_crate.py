

from rocrate.rocrate import ROCrate
from rocrate.model.person import Person
from rocrate.model.contextentity import ContextEntity
from pathlib import Path

from helper import GitURL
from e1_crate import build_e1_crate

import os
import argparse

def build_e1(crate: ROCrate, coastsat_dir: str, URL: GitURL, E1, output_dir):
    """
    Build metadata for E1: Data Producer.
    - Identify and describe data production scripts and data outputs.
    - Describe external data sources used.
    """
    e1_output_dir = Path(output_dir) / "E1-data-producer"
    build_e1_crate(str(e1_output_dir), coastsat_dir)

    # Link E1 entity to the external crate directory
    E1["conformsTo"] = {"@id": "https://w3id.org/ro/wfrun/process/0.5"}
    E1["hasPart"] = [{"@id": "E1-data-producer/ro-crate-metadata.json"}]

def build_e2_1(crate: ROCrate, coastsat_dir: Path, URL: GitURL, E2_1):
    """
    Build metadata for E2.1: Workflow Infrastructure.
    - Identify infrastructure elements like Dockerfiles, Python packages, notebooks.
    """
    # TODO: implement infrastructure discovery
    pass

def build_e2_2(crate: ROCrate, coastsat_dir: Path, URL: GitURL, E2_2):
    """
    Build metadata for E2.2: Workflow Management System.
    - Link to external provenance crate or describe internal WMS behavior.
    """
    # TODO: implement or link to provenance crate integration
    pass

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
    
def add_aggregate_entities(crate: ROCrate):
    crate.mainEntity = crate.add(ContextEntity(crate, "livepublication-interface", properties={
        "@type": "Dataset",
        "name": "LivePublication Interface Outputs",
        "description": "This Dataset represents the outputs of the Experiment Infrastructure required by the LivePublication interface. It includes references to data produced by E1 (Data Producer), E2.1 (Workflow Infrastructure), E2.2 (Workflow Management System), and E3 (Experimental Results and Outcomes).",
        "datePublished": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()}
        ))
    
    E1 = crate.add(ContextEntity(crate, "E1-data-producer", properties={"@type": "RO-Crate", "name": "E1: Data Producer", "description": "Metadata and references to acquired raw data products."}))
    E2_1 = crate.add(ContextEntity(crate, "E2.1-workflow-infrastructure", properties={"@type": "Dataset", "name": "E2.1: Workflow Infrastructure", "description": "Description of hardware and software environments used."}))
    E2_2 = crate.add(ContextEntity(crate, "E2.2-wms", properties={"@type": "Dataset", "name": "E2.2: Workflow Management System", "description": "Provenance of workflow execution including workflow steps and parameters."}))
    E3 = crate.add(ContextEntity(crate, "E3-experimental-results", properties={"@type": "Dataset", "name": "E3: Experimental Results and Outcomes", "description": "Results of the executed workflow, such as figures and summary data products."}))
    
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
        default=Path(__file__).parent / "output", 
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
    
    infrastructure_entities = add_aggregate_entities(crate)
    contextual_entities = add_metadata(crate)

    # Build experiment infrastructure layers
    build_e1(crate, coastsat_dir, URL, infrastructure_entities["E1"], output_dir)
    build_e2_1(crate, coastsat_dir, URL, infrastructure_entities["E2_1"])
    build_e2_2(crate, coastsat_dir, URL, infrastructure_entities["E2_2"])
    build_e3(crate, coastsat_dir, URL, infrastructure_entities["E3"])

    # Write crate to specified output directory
    crate.write(output_dir)

if __name__ == "__main__":
    main()