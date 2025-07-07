from rocrate.rocrate import ROCrate
from rocrate.model.contextentity import ContextEntity
from helper import GitURL
import argparse
import os
from typing import Optional

def add_create_action(crate: ROCrate, action_id: str, name: str, description: str):
    """
    Helper function to create a CreateAction entity in the RO-Crate.
    """
    properties = {
        "@type": "CreateAction",
        "name": name,
        "description": description,
    }

    return crate.add(ContextEntity(crate, action_id, properties))

def add_software_application(crate: ROCrate, 
                             app_id: str, 
                             name: str, 
                             description: str, 
                             programming_language: str, 
                             code_repository):
    """
    Helper function to add a SoftwareApplication entity to the RO-Crate.
    """
    properties = {
        "@type": "SoftwareSourceCode",
        "name": name,
        "description": description,
        "programmingLanguage": programming_language,
        "codeRepository": code_repository
    }

    return crate.add(ContextEntity(crate, app_id, properties))


def add_person(crate: ROCrate, name: str, affiliation=None, orcid=None):
    """
    Helper function to add a Person entity to the RO-Crate.
    """
    properties = {
        "@type": "Person",
        "name": name,
        "affiliation": affiliation
    }

    return crate.add(ContextEntity(crate, orcid, properties))


def add_organization(crate: ROCrate, identifier: str, name: str):
    """
    Helper function to add an Organization entity to the RO-Crate.
    """
    properties = {
        "@id": identifier,
        "@type": "Organization",
        "name": name
    }

    return crate.add(ContextEntity(crate, identifier, properties))


def add_file_entity(crate: ROCrate, identifier: str, content_size, description, encoding_format: None):
    """
    Helper function to add a File entity to the RO-Crate.
    """
    properties = {
        "@type": "File",
        "encodingFormat": encoding_format,
        "contentSize": content_size,
        "description": description
    }

    return crate.add(ContextEntity(crate, identifier, properties))

def add_example_outputs_for_action(crate: ROCrate, limit: Optional[int], action: ContextEntity, URL: GitURL):
    """
    Adds up to 'limit' example transect_time_series.csv output files for the given CreateAction
    based on its @id (nz or sardinia) and sets a Dataset as its result.
    """
    action_id = action.id.lower()
    if "nz" in action_id:
        tag = "nzd"
        output_id = "#nz-transect-series"
        dataset_name = "NZ Transect Time Series Dataset"
    elif "sardinia" in action_id:
        tag = "sar"
        output_id = "#sardinia-transect-series"
        dataset_name = "Sardinia Transect Time Series Dataset"
    else:
        return  # unrecognized action id

    site_root = os.path.join(URL.repo_path, "data")
    matched_dirs = sorted([d for d in os.listdir(site_root) if d.startswith(tag)])
    selected = matched_dirs if limit is None else matched_dirs[:limit]

    file_entities = []
    for site_id in selected:
        remote_path = f"data/{site_id}/transect_time_series.csv"
        file_entity = add_file_entity(
            crate,
            identifier=URL.get(remote_path)["permalink_url"],
            content_size=URL.get_size(remote_path), 
            description=f"Transect time series for {site_id}",
            encoding_format="text/csv"
        )
        file_entities.append(file_entity)

    dataset = crate.add(ContextEntity(crate, output_id, {
        "@type": "Dataset",
        "name": dataset_name,
        "description": f"Representative output files for {tag.upper()} transects.",
        "hasPart": file_entities
    }))

    action["result"] = dataset

def build_e1_crate(output_dir: str, coastsat_dir: str):
    
    URL = GitURL(repo_path=coastsat_dir, remote_name="origin")
    crate = ROCrate()

    # Add minimal metadata
    crate.name = "E1: Data Producer"
    crate.description = "Process Run Crate representing the Data Producer layer."
    crate.metadata["conformsTo"] = {
        "@id": "https://w3id.org/ro/wfrun/process/0.5"
    }

    # Add create actions for batch processing
    actions = [
        add_create_action(crate,
            "#batch-process-nz",
            "Update NZ transect time series",
            "Batch process to update transect time series for New Zealand using Google Earth Engine."),
        add_create_action(crate,
            "#batch-process-sardinia",
            "Update Sardinia transect time series",
            "Batch process to update transect time series for Sardinia using Google Earth Engine.")
    ]
    nz_action, sardinia_action = actions  

    # Add software applications for each action
    software = [
        add_software_application(crate,
            "#batch-process-nz-app",
            "Batch Process NZ Application",
            "Application for batch processing New Zealand transect time series.",
            programming_language="Python",
            code_repository=URL.get("batch_process_NZ.py")['permalink_url']),
        add_software_application(crate,
            "#batch-process-sardinia-app",
            "Batch Process Sardinia Application",
            "Application for batch processing Sardinia transect time series.",
            programming_language="Python",
            code_repository=URL.get("batch_process_Sardinia.py")['permalink_url'])
    ]
    nz_app, sardinia_app = software

    # Add example outputs with limit = 1
    add_example_outputs_for_action(crate, limit=5, action=nz_action, URL=URL)
    add_example_outputs_for_action(crate, limit=5, action=sardinia_action, URL=URL)
    
    Organisation = add_organization(crate,
        "#university-of-auckland",
        "University of Auckland")
    
    Author = add_person(crate,
        "Example name",
        affiliation=Organisation,
        orcid="https://orcid.org/example")
    
    input_files = [
        add_file_entity(crate,
                        URL.get("polygons.geojson")['permalink_url'],
                        content_size=URL.get_size("polygons.geojson"),
                        description="Polygon bounding boxes defining where to download imagery.",
                        encoding_format="application/geo+json"),
        add_file_entity(crate,
                        URL.get("shorelines.geojson")['permalink_url'],
                        content_size=URL.get_size("shorelines.geojson"),
                        description="Reference shorelines for transects.",
                        encoding_format="application/geo+json"),
        add_file_entity(crate,
                        URL.get("transects_extended.geojson")['permalink_url'],
                        content_size=URL.get_size("transects_extended.geojson"),
                        description="Transects with extended geometry for processing.",
                        encoding_format="application/geo+json")
    ]
    polygon_file, shoreline_file, transects_file = input_files
   
    # Link CreateActions to root dataset
    root = crate.root_dataset
    root["mentions"] = [nz_action, sardinia_action]
    for action in actions:
        action["agent"] = [Author, Organisation]
        action["object"] = input_files
        if action == nz_action:
            action["instrument"] = nz_app
        else:
            action["instrument"] = sardinia_app

    # Write to output
    crate.write(output_dir)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, help="Output directory for E1 RO-Crate")
    args = parser.parse_args()

    output_path = os.path.abspath(args.output_dir)
    os.makedirs(output_path, exist_ok=True)

if __name__ == "__main__":
    main()