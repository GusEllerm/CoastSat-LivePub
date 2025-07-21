from rocrate.rocrate import ROCrate
from rocrate.model.contextentity import ContextEntity
from helper import GitURL
import argparse
import os
from typing import Optional
import requests
import hashlib

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

def get_or_create_gist(local_file_path: str, github_token: str) -> tuple[str, str]:
    """
    Checks for an existing Gist containing the file, or creates a new one.
    Returns (gist_url, embed_code).
    """
    filename = os.path.basename(local_file_path)
    with open(local_file_path, 'r', encoding='utf-8') as f:
        file_content = f.read()

    file_hash = hashlib.sha256(file_content.encode('utf-8')).hexdigest()
    description_marker = f"[RO-Crate] {filename} SHA256: {file_hash}"

    # Check existing Gists
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github+json"
    }
    response = requests.get("https://api.github.com/gists", headers=headers)
    if response.status_code == 200:
        gists = response.json()
        for gist in gists:
            if gist.get("description", "") == description_marker:
                gist_url = gist["html_url"]
                embed_code = f'<script src="{gist_url}.js"></script>'
                return gist_url, embed_code

    # Create a new Gist
    data = {
        "description": description_marker,
        "public": True,
        "files": {
            filename: {
                "content": file_content
            }
        }
    }
    create_response = requests.post("https://api.github.com/gists", headers=headers, json=data)
    if create_response.status_code == 201:
        gist = create_response.json()
        gist_url = gist["html_url"]
        embed_code = f'<script src="{gist_url}.js"></script>'
        return gist_url, embed_code
    else:
        raise RuntimeError(f"Failed to create Gist: {create_response.text}")

def add_software_application(crate: ROCrate, 
                             app_id: str, 
                             name: str, 
                             description: str, 
                             programming_language: str, 
                             code_repository: str,
                             local_file_path: str,
                             github_token: str):
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
    gist_url, embed_code = get_or_create_gist(local_file_path, github_token)
    properties["associatedMedia"] = gist_url
    properties["embedCode"] = embed_code

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


def add_file_entity(crate: ROCrate, identifier: str, content_size, description, name, encoding_format: None, sha_256: Optional[str] = None):
    """
    Helper function to add a File entity to the RO-Crate.
    """
    properties = {
        "@type": "File",
        "name": name,
        "encodingFormat": encoding_format,
        "contentSize": content_size,
        "sha256": sha_256,
        "description": description
    }
    file_entity = crate.add(ContextEntity(crate, identifier, properties))
    crate.root_dataset.append_to("hasPart", file_entity)
    
    return file_entity

def add_time_series_outputs(crate: ROCrate, limit: Optional[int], action: ContextEntity, URL: GitURL, coastsat_dir):
    """
    Adds up to 'limit' example transect_time_series.csv output files for the given CreateAction
    based on its @id (nz or sardinia) and sets a Dataset as its result.
    """
    action_id = action.id.lower()
    if "nz" in action_id:
        tag = "nzd"
    elif "sardinia" in action_id:
        tag = "sar"
    else:
        return  # unrecognized action id

    site_root = os.path.join(URL.repo_path, "data")
    matched_dirs = sorted([d for d in os.listdir(site_root) if d.startswith(tag)])
    selected = matched_dirs if limit is None else matched_dirs[:limit]

    file_entities = []
    for site_id in selected:        
        remote_path = f"data/{site_id}/transect_time_series.csv"
        local_path = f"{coastsat_dir}/data/{site_id}/transect_time_series.csv"
        file_entity = add_file_entity(
            crate,
            name=f"{site_id} transect time series",
            identifier=URL.get(remote_path)["permalink_url"],
            content_size=URL.get_size(remote_path), 
            description=f"Transect time series for {site_id}",
            sha_256=URL.get_file_hash(local_path),
            encoding_format="text/csv"
        )
        file_entities.append(file_entity)
        crate.root_dataset.append_to("hasPart", file_entity)

    return file_entities

def add_time_series_inputs(crate: ROCrate, limit: Optional[int], action: ContextEntity, URL: GitURL, coastsat_dir):
    """
    Adds up to 'limit' example transect_time_series.csv output files for the given CreateAction
    based on its @id (nz or sardinia) and sets a Dataset as its result.
    """
    action_id = action.id.lower()
    if "nz" in action_id:
        tag = "nzd"
        output_id = "#nz-transect-series-input"
        dataset_name = "NZ Transect Time Series Input Dataset"
    elif "sardinia" in action_id:
        tag = "sar"
        output_id = "#sardinia-transect-series-input"
        dataset_name = "Sardinia Transect Time Series Input Dataset"
    else:
        return  # unrecognized action id

    site_root = os.path.join(URL.repo_path, "data")
    matched_dirs = sorted([d for d in os.listdir(site_root) if d.startswith(tag)])
    selected = matched_dirs if limit is None else matched_dirs[:limit]

    file_entities = []
    for site_id in selected:
        remote_path = f"data/{site_id}/transect_time_series.csv"
        local_path = f"data/{site_id}/transect_time_series.csv"
        file_entity = add_file_entity(
            crate,
            name=f"{site_id} transect time series",
            identifier=URL.get_previous(remote_path)["permalink_url"],
            content_size=URL.get_size_at_commit(remote_path, URL.get_previous(remote_path)['commit_hash']), 
            description=f"Transect time series for {site_id}",
            sha_256=URL.get_file_hash(local_path, "previous"),
            encoding_format="text/csv"
        )
        file_entities.append(file_entity)
        crate.root_dataset.append_to("hasPart", file_entity)

    return file_entities

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
            code_repository=URL.get("batch_process_NZ.py")['permalink_url'],
            local_file_path=os.path.join(coastsat_dir, "batch_process_NZ.py"),
            github_token=os.environ.get("GITHUB_TOKEN", "")
            ),
        add_software_application(crate,
            "#batch-process-sardinia-app",
            "Batch Process Sardinia Application",
            "Application for batch processing Sardinia transect time series.",
            programming_language="Python",
            code_repository=URL.get("batch_process_sar.py")['permalink_url'],
            local_file_path=os.path.join(coastsat_dir, "batch_process_sar.py"),
            github_token=os.environ.get("GITHUB_TOKEN", "")
            )
    ]
    nz_app, sardinia_app = software

    # Add example inputs. This draws from the previous commit's data files
    # to ensure reproducibility, as the current commit may not have the same files.
    limit = None
    nz_timeseries_inputs = add_time_series_inputs(crate, limit, nz_action, URL, coastsat_dir)
    sar_timeseries_inputs = add_time_series_inputs(crate, limit, sardinia_action, URL, coastsat_dir)

    # Add example outputs. This draws from the current commit's data files
    nz_timeseries_outputs = add_time_series_outputs(crate, limit, nz_action, URL, coastsat_dir)
    sar_timeseries_outputs = add_time_series_outputs(crate, limit, sardinia_action, URL, coastsat_dir)
    
    Organisation = add_organization(crate,
        "#university-of-auckland",
        "University of Auckland")
    
    Author = add_person(crate,
        "Example name",
        affiliation=Organisation,
        orcid="https://orcid.org/example")
    
    input_files = [
        add_file_entity(
            crate=crate,
            name="Polygons GeoJSON",
            identifier=URL.get_previous("polygons.geojson")['permalink_url'],
            content_size=URL.get_size_at_commit("polygons.geojson", URL.get_previous("polygons.geojson")['commit_hash']),
            description="Polygon bounding boxes defining where to download imagery.",
            sha_256=URL.get_file_hash("polygons.geojson", "previous"),
            encoding_format="application/geo+json"),
        add_file_entity(
            crate=crate,
            name="Shorelines GeoJSON",
            identifier=URL.get_previous("shorelines.geojson")['permalink_url'],
            content_size=URL.get_size_at_commit("shorelines.geojson", URL.get_previous("shorelines.geojson")['commit_hash']),
            description="Reference shorelines for transects.",
            sha_256=URL.get_file_hash("shorelines.geojson", "previous"),
            encoding_format="application/geo+json"
            ),
        add_file_entity(
            crate=crate,
            name="Transects Extended GeoJSON",
            identifier=URL.get_previous("transects_extended.geojson")['permalink_url'],
            content_size=URL.get_size_at_commit("transects_extended.geojson", URL.get_previous("transects_extended.geojson")['commit_hash']),
            description="Transects with extended geometry for processing.",
            sha_256=URL.get_file_hash("transects_extended.geojson"),
            encoding_format="application/geo+json")
    ]
    polygon_file, shoreline_file, transects_file = input_files
   
    # Link CreateActions to root dataset
    root = crate.root_dataset
    root["mentions"] = [nz_action, sardinia_action]
    root["conformsTo"] = "https://w3id.org/ro/wfrun/process/0.5"
    for action in actions:
        action["agent"] = [Author, Organisation]
        if action == nz_action:
            action["instrument"] = nz_app
            action["object"] = input_files + nz_timeseries_inputs
            action["result"] = nz_timeseries_outputs
        else:
            action["instrument"] = sardinia_app
            action["object"] = input_files + sar_timeseries_inputs
            action["result"] = sar_timeseries_outputs

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