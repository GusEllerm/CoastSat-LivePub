import json
import subprocess
from pathlib import Path
from jinja2 import Template


def write_feature_jsons(transects_path: Path, output_dir: Path):
    """
    Extract each feature's properties from the GeoJSON and save as separate JSON files.

    Args:
        transects_path (Path): Path to the input GeoJSON file.
        output_dir (Path): Directory where individual feature JSON files will be saved.
    """
    output_dir.mkdir(exist_ok=True)
    with open(transects_path, 'r', encoding='utf-8') as f:
        transects = json.load(f)

    for feature in transects.get('features', []):
        props = feature["properties"]
        feature_id = props["id"]
        output_file = output_dir / f"{feature_id}.json"
        with open(output_file, 'w', encoding='utf-8') as out:
            json.dump(props, out, indent=2)
        print(f"Wrote JSON for feature: {feature_id}")


def render_micropublications_jinja(template_path: Path, json_dir: Path, output_dir: Path):
    """
    Render micropublications using a Jinja2 template and feature-specific JSON files.

    Args:
        template_path (Path): Path to the .smd Jinja2 template.
        json_dir (Path): Directory containing individual feature JSON files.
        output_dir (Path): Directory where rendered Markdown files will be saved.
    """
    output_dir.mkdir(exist_ok=True)
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    template = Template(template_content)

    for json_file in json_dir.glob("*.json"):
        with open(json_file, 'r', encoding='utf-8') as f:
            props = json.load(f)
        feature_id = props["id"]
        print(f"Rendering micropublication for {json_file.stem}")

        # Render the template with props
        rendered_smd = template.render(**props)

        # Write the rendered template to a temporary .smd file
        temp_smd_path = output_dir / f"{feature_id}_temp.smd"
        with open(temp_smd_path, 'w', encoding='utf-8') as temp_file:
            temp_file.write(rendered_smd)

        # Define output markdown file path
        output_json_path = output_dir / f"{feature_id}.json"

        # Run stencila render on the rendered template, output to markdown file
        with open(output_json_path, 'w', encoding='utf-8') as out_md:
            subprocess.run([
                "stencila", "render", "--no-save",
                str(temp_smd_path),
                str(output_json_path)

            ], stdout=out_md)

        # Remove the temporary .smd file
        temp_smd_path.unlink()


if __name__ == "__main__":
    """
    Generate and render micropublications for each feature in a GeoJSON file.
    """

    transects_path = Path("transects_extended.geojson")
    template_path = Path("micropublication.smd")
    feature_data_dir = Path("feature_data")
    output_dir = Path("micropublications")

    if not transects_path.exists():
        print(f"Transects file not found at {transects_path}")
    elif not template_path.exists():
        print(f"Template file not found at {template_path}")
    else:
        write_feature_jsons(transects_path, feature_data_dir)
        render_micropublications_jinja(template_path, feature_data_dir, output_dir)