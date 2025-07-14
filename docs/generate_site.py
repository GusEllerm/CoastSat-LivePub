import os
import shutil
import glob
from pathlib import Path
from jinja2 import Template
from jinja2 import Environment, FileSystemLoader

DOCS_DIR = Path("docs")
CRATES_SRC_DIR = Path("LP_Crate/interface.crate")  # source of RO-Crate directories
CRATES_DST_DIR = DOCS_DIR / "interface.crate"

HTML_PREVIEW_NAME = "ro-crate-preview.html"

def move_crates():
    """Copy all crate folders into the docs/crates/ directory."""
    if CRATES_DST_DIR.exists():
        shutil.rmtree(CRATES_DST_DIR)
    shutil.copytree(CRATES_SRC_DIR, CRATES_DST_DIR)

import subprocess

def generate_previews():
    """
    Recursively find all directories with a ro-crate-metadata.json file and run rochtml.
    """
    for root, dirs, files in os.walk(CRATES_DST_DIR):
        if "ro-crate-metadata.json" in files:
            print(f"Generating preview for {root}")
            metadata_path = Path(root) / "ro-crate-metadata.json"
            try:
                subprocess.run(["rochtml", str(metadata_path)], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Failed to generate preview for {metadata_path.parent.name}: {e}")

def create_index():
    """Generate an index.html file linking to each RO-Crate preview using Jinja2."""
    links = []
    for root, dirs, files in os.walk(CRATES_DST_DIR):
        if "ro-crate-metadata.json" in files:
            rel_path = Path(root).relative_to(DOCS_DIR)
            preview_path = rel_path / HTML_PREVIEW_NAME
            crate_name = Path(root).name
            links.append({"name": crate_name, "href": str(preview_path)})

    content_path = DOCS_DIR / "templates" / "content.html"
    content = content_path.read_text()
    env = Environment(loader=FileSystemLoader("docs/templates"))
    template = env.get_template("base.html")
    rendered_html = template.render(links=links, content=content)
    (DOCS_DIR / "index.html").write_text(rendered_html)

def main():
    move_crates()
    generate_previews()
    create_index()
    print("Site generated in docs/")

if __name__ == "__main__":
    main()