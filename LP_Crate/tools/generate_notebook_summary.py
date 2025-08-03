#!/usr/bin/env python3
"""
Generate a summarized version of notebook RO-Crate metadata files.

This script creates a collapsed/summarized version of notebook ro-crate-metadata.json
files that preserves the notebook workflow structure while keeping code cell counts
as summaries for documentation purposes.
"""

import json
import argparse
import os
from pathlib import Path
from typing import Dict, Any, List


def compact_simple_objects(json_str: str) -> str:
    """
    Post-process JSON string to inline simple objects and arrays.
    Converts patterns like:
    
    "key": [
     {
      "@id": "value"
     }
    ],
    
    To: "key": [{"@id": "value"}],
    
    And:
    
    "@type": [
     "FormalParameter"
    ],
    
    To: "@type": ["FormalParameter"],
    """
    import re
    
    # Pattern 1: Simple single-property objects in arrays
    pattern1 = re.compile(
        r'("[\w@-]+"):\s*\[\s*\n\s*{\s*\n\s*("@id"):\s*("[^"]*")\s*\n\s*}\s*\n\s*\],?',
        re.MULTILINE
    )
    json_str = pattern1.sub(r'\1: [{\2: \3}],', json_str)
    
    # Pattern 2: Simple single-property objects (not in arrays)
    pattern2 = re.compile(
        r'("[\w@-]+"):\s*{\s*\n\s*("@id"):\s*("[^"]*")\s*\n\s*},?',
        re.MULTILINE
    )
    json_str = pattern2.sub(r'\1: {\2: \3},', json_str)
    
    # Pattern 3: Simple single-string arrays
    # Matches: "key": [\n  "value"\n ],
    pattern3 = re.compile(
        r'("[\w@-]+"):\s*\[\s*\n\s*("[^"]*")\s*\n\s*\],?',
        re.MULTILINE
    )
    json_str = pattern3.sub(r'\1: [\2],', json_str)
    
    # Pattern 4: Multi-string arrays on separate lines (common for @type arrays)
    # Matches: "key": [\n  "value1",\n  "value2",\n  "value3"\n ],
    pattern4 = re.compile(
        r'("[\w@-]+"):\s*\[\s*\n((?:\s*"[^"]*",?\s*\n)+)\s*\],?',
        re.MULTILINE
    )
    
    def inline_array_items(match):
        key = match.group(1)
        items_text = match.group(2)
        # Extract all quoted strings from the items
        items = re.findall(r'"[^"]*"', items_text)
        items_str = ', '.join(items)
        return f'{key}: [{items_str}],'
    
    json_str = pattern4.sub(inline_array_items, json_str)
    
    # Clean up any trailing commas before closing brackets/braces
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
    
    return json_str


def count_items_by_type(graph: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count items by their @type."""
    type_counts = {}
    for item in graph:
        item_types = item.get("@type", [])
        if isinstance(item_types, str):
            item_types = [item_types]
        
        for item_type in item_types:
            type_counts[item_type] = type_counts.get(item_type, 0) + 1
    
    return type_counts


def create_notebook_summary(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a notebook summary focused on workflow and provenance."""
    summary = {
        "@context": data.get("@context"),
        "@graph": []
    }
    
    graph = data.get("@graph", [])
    
    # Track what we've processed
    core_entities = []  # Root dataset, metadata, main notebook
    workflow_steps = []  # HowToSteps
    formal_parameters = []  # FormalParameters
    jupyter_kernel = None
    create_actions = []  # CreateActions (limited)
    code_cells = []  # SoftwareApplication + File entities
    media_objects = []  # MediaObject entities (plots, etc.)
    other_entities = []
    
    for item in graph:
        item_id = item.get("@id", "")
        item_types = item.get("@type", [])
        if isinstance(item_types, str):
            item_types = [item_types]
        
        # Keep core entities (root dataset, metadata, main notebook file)
        if (item_id in ["./", "ro-crate-metadata.json"] or 
            item_id.endswith(".ipynb") or
            item_id == "#jupyter-kernel"):
            
            if item_id == "#jupyter-kernel":
                jupyter_kernel = item
            else:
                # Summarize step arrays for notebooks
                summary_item = item.copy()
                if "step" in summary_item and isinstance(summary_item["step"], list):
                    step_count = len(summary_item["step"])
                    summary_item["step"] = f"... {step_count} steps ..."
                
                # Summarize hasPart arrays
                if "hasPart" in summary_item and isinstance(summary_item["hasPart"], list):
                    part_count = len(summary_item["hasPart"])
                    if part_count > 10:  # Only summarize if many items
                        summary_item["hasPart"] = f"... {part_count} items ..."
                
                core_entities.append(summary_item)
        
        # Enumerate workflow steps (keep full details)
        elif "HowToStep" in item_types:
            workflow_steps.append(item)
        
        # Enumerate formal parameters (keep full details)
        elif "FormalParameter" in item_types:
            formal_parameters.append(item)
        
        # Keep some CreateActions (limit to first few)
        elif "CreateAction" in item_types:
            create_actions.append(item)
        
        # Count code cells
        elif ("SoftwareApplication" in item_types and "File" in item_types and 
              item_id.startswith("code_blocks/")):
            code_cells.append(item)
        
        # Keep media objects (plots, charts, etc.)
        elif "MediaObject" in item_types:
            media_objects.append(item)
        
        else:
            other_entities.append(item)
    
    # Add core entities first
    summary["@graph"].extend(core_entities)
    
    # Add Jupyter kernel if present
    if jupyter_kernel:
        summary["@graph"].append(jupyter_kernel)
    
    # Add collapsed workflow steps summary instead of individual steps
    if workflow_steps:
        # Analyze workflow step patterns
        step_positions = [step.get("position", 0) for step in workflow_steps]
        step_names = [step.get("name", "Unknown") for step in workflow_steps]
        step_tools = set()
        step_actions = set()
        
        for step in workflow_steps:
            tool_id = step.get("tool", {}).get("@id", "")
            if tool_id:
                step_tools.add(tool_id)
            
            about_id = step.get("about", {}).get("@id", "")
            if about_id:
                step_actions.add(about_id)
        
        # Create summary representation
        workflow_summary = {
            "@id": "... workflow steps ...",
            "@type": "HowToStepSummary",
            "count": len(workflow_steps),
            "position_range": [min(step_positions), max(step_positions)] if step_positions else [0, 0],
            "step_pattern": f"{step_names[0]} to {step_names[-1]}" if len(step_names) > 1 else step_names[0] if step_names else "No steps",
            "tools_used": list(step_tools),
            "actions_referenced": len(step_actions),
            "note": f"Collapsed {len(workflow_steps)} HowToStep entities for readability"
        }
        
        # Keep first and last few steps if there are many
        if len(workflow_steps) <= 6:
            # For small numbers, show all steps individually
            summary["@graph"].extend(workflow_steps)
        else:
            # For large numbers, show first 2, summary of middle steps, last 2
            first_steps = workflow_steps[:2]
            last_steps = workflow_steps[-2:]
            collapsed_count = len(workflow_steps) - 4  # Total minus first 2 and last 2
            
            # Add first 2 steps
            summary["@graph"].extend(first_steps)
            
            # Create summary for the collapsed middle steps
            workflow_summary = {
                "@id": "... workflow steps ...",
                "@type": "HowToStepSummary", 
                "count": collapsed_count,
                "position_range": [workflow_steps[2].get("position", 0), workflow_steps[-3].get("position", 0)] if len(workflow_steps) > 4 else [0, 0],
                "step_pattern": f"{workflow_steps[2].get('name', 'Unknown')} to {workflow_steps[-3].get('name', 'Unknown')}" if len(workflow_steps) > 4 else "No middle steps",
                "tools_used": list(step_tools),
                "actions_referenced": len(step_actions),
                "note": f"Collapsed {collapsed_count} middle HowToStep entities (showing first 2 and last 2)"
            }
            
            # Add summary only if there are actually middle steps to collapse
            if collapsed_count > 0:
                summary["@graph"].append(workflow_summary)
            
            # Add last 2 steps
            summary["@graph"].extend(last_steps)
    
    # Add enumerated formal parameters
    summary["@graph"].extend(formal_parameters)
    
    # Add limited CreateActions (first 3 and last 3 if more than 6)
    if create_actions:
        if len(create_actions) <= 6:
            summary["@graph"].extend(create_actions)
        else:
            summary["@graph"].extend(create_actions[:3])
            summary["@graph"].append({
                "@id": "... create actions ...",
                "count": len(create_actions) - 6,
                "note": f"Showing first 3 and last 3 of {len(create_actions)} CreateActions"
            })
            summary["@graph"].extend(create_actions[-3:])
    
    # Add media objects (plots, charts)
    if media_objects:
        summary["@graph"].extend(media_objects)
    
    # Add code cell count summary
    if code_cells:
        # Analyze code cell patterns
        input_counts = {}
        output_counts = {}
        
        for cell in code_cells:
            input_count = len(cell.get("input", []))
            output_count = len(cell.get("output", []))
            
            input_counts[input_count] = input_counts.get(input_count, 0) + 1
            output_counts[output_count] = output_counts.get(output_count, 0) + 1
        
        summary["@graph"].append({
            "@id": "... code cells ...",
            "count": len(code_cells),
            "input_distribution": input_counts,
            "output_distribution": output_counts
        })
    
    # Add other entities count summary
    if other_entities:
        summary["@graph"].append({
            "@id": "... other entities ...",
            "count": len(other_entities)
        })
    
    return summary


def main():
    """Main function to generate notebook summary."""
    parser = argparse.ArgumentParser(
        description="Generate a summarized version of notebook RO-Crate metadata"
    )
    parser.add_argument(
        "notebook_dir",
        nargs="?",
        default=None,
        help="Notebook directory name (e.g., 'linear_models'). If not provided, will process all notebook directories."
    )
    parser.add_argument(
        "--input", "-i",
        default=None,
        help="Input notebook metadata file (overrides notebook_dir)"
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output summary file (auto-generated if not provided)"
    )
    parser.add_argument(
        "--indent", "-t",
        type=int,
        default=2,
        help="JSON indentation (default: 2)"
    )
    parser.add_argument(
        "--interface-crate", "-c",
        default=None,
        help="Path to interface.crate directory (overrides default path resolution)"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Process all notebook directories"
    )
    
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    
    # Determine which notebooks to process
    notebooks_to_process = []
    
    if args.input:
        # Direct file input
        input_path = Path(args.input)
        if not input_path.is_absolute():
            input_path = script_dir / input_path
        
        output_path = Path(args.output) if args.output else input_path.parent / "ro-crate-metadata.summary.json"
        if not output_path.is_absolute():
            output_path = script_dir / output_path
            
        notebooks_to_process.append((input_path, output_path))
    
    elif args.all or args.notebook_dir is None:
        # Process all notebook directories
        if args.interface_crate:
            notebooks_base = Path(args.interface_crate) / "notebooks"
        else:
            notebooks_base = script_dir / ".." / "interface.crate" / "notebooks"
        if notebooks_base.exists():
            for nb_dir in notebooks_base.iterdir():
                if nb_dir.is_dir():
                    metadata_file = nb_dir / "ro-crate-metadata.json"
                    if metadata_file.exists():
                        output_file = nb_dir / "ro-crate-metadata.summary.json"
                        notebooks_to_process.append((metadata_file, output_file))
    
    else:
        # Process specific notebook directory
        if args.interface_crate:
            input_path = Path(args.interface_crate) / "notebooks" / args.notebook_dir / "ro-crate-metadata.json"
        else:
            input_path = script_dir / ".." / "interface.crate" / "notebooks" / args.notebook_dir / "ro-crate-metadata.json"
        output_path = input_path.parent / "ro-crate-metadata.summary.json"
        
        if args.output:
            output_path = Path(args.output)
            if not output_path.is_absolute():
                output_path = script_dir / output_path
        
        notebooks_to_process.append((input_path, output_path))
    
    if not notebooks_to_process:
        print("No notebook metadata files found to process.")
        return 1
    
    total_reduction = 0
    processed_count = 0
    
    for input_path, output_path in notebooks_to_process:
        # Check if input file exists
        if not input_path.exists():
            print(f"Warning: Input file '{input_path}' not found, skipping.")
            continue
        
        try:
            # Load the original metadata
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Create notebook summary
            summary = create_notebook_summary(data)
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write summary
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=1, ensure_ascii=False, separators=(',', ': '))
            
            # Post-process to inline simple objects
            with open(output_path, 'r', encoding='utf-8') as f:
                json_content = f.read()
            
            compact_content = compact_simple_objects(json_content)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(compact_content)
            
            # Print statistics
            original_size = input_path.stat().st_size
            summary_size = output_path.stat().st_size
            reduction = ((original_size - summary_size) / original_size) * 100
            
            print(f"Notebook summary: {input_path.parent.name}")
            print(f"  Input: {original_size:,} bytes")
            print(f"  Output: {summary_size:,} bytes") 
            print(f"  Reduction: {reduction:.1f}%")
            
            # Count summary contents  
            workflow_count = sum(1 for item in summary["@graph"] 
                               if "HowToStep" in (item.get("@type", []) if isinstance(item.get("@type"), list) else [item.get("@type", "")]))
            param_count = sum(1 for item in summary["@graph"] 
                            if "FormalParameter" in (item.get("@type", []) if isinstance(item.get("@type"), list) else [item.get("@type", "")]))
            action_count = sum(1 for item in summary["@graph"] 
                             if "CreateAction" in (item.get("@type", []) if isinstance(item.get("@type"), list) else [item.get("@type", "")]))
            
            print(f"  Contains: {workflow_count} workflow steps, {param_count} formal parameters, {action_count} create actions")
            print()
            
            total_reduction += reduction
            processed_count += 1
            
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {input_path}: {e}")
            continue
        except Exception as e:
            print(f"Error processing {input_path}: {e}")
            continue
    
    if processed_count > 0:
        avg_reduction = total_reduction / processed_count
        print(f"Processed {processed_count} notebook(s) with average {avg_reduction:.1f}% size reduction")
        return 0
    else:
        print("No files were successfully processed.")
        return 1


if __name__ == "__main__":
    exit(main())
