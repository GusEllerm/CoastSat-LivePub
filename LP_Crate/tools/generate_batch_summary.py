#!/usr/bin/env python3
"""
Generate a summarized version of the batch processes RO-Crate metadata file.

This script creates a collapsed/summarized version of batch_processes/ro-crate-metadata.json
that provides an overview of the batch processing workflow while keeping file counts
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


def create_batch_summary(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a batch processes summary focused on workflow overview."""
    summary = {
        "@context": data.get("@context"),
        "@graph": []
    }
    
    graph = data.get("@graph", [])
    
    # Track what we've processed
    workflow_entities = []
    action_entities = []
    formal_parameters = []
    files = []
    other_entities = []
    
    for item in graph:
        item_id = item.get("@id", "")
        item_types = item.get("@type", [])
        if isinstance(item_types, str):
            item_types = [item_types]
        
        # Keep root dataset and important workflow entities
        if (item_id in ["./", "ro-crate-metadata.json"] or 
            "CreateAction" in item_types or 
            "ControlAction" in item_types or
            "SoftwareApplication" in item_types):
            
            # Summarize large hasPart arrays
            summary_item = item.copy()
            if "hasPart" in summary_item and isinstance(summary_item["hasPart"], list):
                part_count = len(summary_item["hasPart"])
                if part_count > 10:  # Only summarize if more than 10 items
                    summary_item["hasPart"] = f"... {part_count} items ..."
            
            # Summarize large input/output arrays for actions
            for key in ["object", "result", "input", "output"]:
                if key in summary_item and isinstance(summary_item[key], list):
                    if len(summary_item[key]) > 10:
                        summary_item[key] = f"... {len(summary_item[key])} items ..."
            
            if "CreateAction" in item_types or "ControlAction" in item_types:
                action_entities.append(summary_item)
            else:
                workflow_entities.append(summary_item)
        
        # Enumerate formal parameters (keep full details)
        elif "FormalParameter" in item_types:
            formal_param = {
                "@id": item_id,
                "@type": item_types,
                "name": item.get("name", ""),
                "valueRequired": item.get("valueRequired", False),
                "description": item.get("description", "")
            }
            formal_parameters.append(formal_param)
        
        # Count files and other entities
        elif "File" in item_types:
            files.append(item)
        else:
            other_entities.append(item)
    
    # Add workflow entities first (root dataset, etc.)
    summary["@graph"].extend(workflow_entities)
    
    # Add action entities (CreateAction, ControlAction)
    summary["@graph"].extend(action_entities)
    
    # Add enumerated formal parameters
    if formal_parameters:
        summary["@graph"].extend(formal_parameters)
    
    # Add file examples with summary (similar to notebook workflow steps)
    if files:
        # Group files by type/pattern for the summary
        file_patterns = {}
        for file_item in files:
            file_id = file_item.get("@id", "")
            if "transect_time_series.csv" in file_id:
                file_patterns["transect_time_series"] = file_patterns.get("transect_time_series", 0) + 1
            elif ".csv" in file_id:
                file_patterns["other_csv"] = file_patterns.get("other_csv", 0) + 1
            elif ".json" in file_id:
                file_patterns["json"] = file_patterns.get("json", 0) + 1
            else:
                file_patterns["other"] = file_patterns.get("other", 0) + 1
        
        # Apply the same pattern as notebook summaries: first few + summary + last few
        if len(files) <= 10:
            # For small numbers, show all files
            summary["@graph"].extend(files)
        else:
            # For large numbers, show first 3, summary of middle files, last 3
            first_files = files[:3]
            last_files = files[-3:]
            collapsed_count = len(files) - 6  # Total minus first 3 and last 3
            
            # Add first 3 files
            summary["@graph"].extend(first_files)
            
            # Create summary for the collapsed middle files
            file_summary = {
                "@id": "... files ...",
                "@type": "FileSummary",
                "count": collapsed_count,
                "total_files": len(files),
                "breakdown": file_patterns,
                "note": f"Collapsed {collapsed_count} middle file entities (showing first 3 and last 3)"
            }
            
            # Add summary only if there are actually middle files to collapse
            if collapsed_count > 0:
                summary["@graph"].append(file_summary)
            
            # Add last 3 files
            summary["@graph"].extend(last_files)
    
    # Add other entities count summary
    if other_entities:
        summary["@graph"].append({
            "@id": "... other entities ...",
            "count": len(other_entities)
        })
    
    return summary


def main():
    """Main function to generate batch processes summary."""
    parser = argparse.ArgumentParser(
        description="Generate a summarized version of batch processes RO-Crate metadata"
    )
    parser.add_argument(
        "--input", "-i",
        default="../interface.crate/batch_processes/ro-crate-metadata.json",
        help="Input batch processes metadata file (default: ../interface.crate/batch_processes/ro-crate-metadata.json)"
    )
    parser.add_argument(
        "--output", "-o",
        default="../interface.crate/batch_processes/ro-crate-metadata.summary.json",
        help="Output summary file (default: ../interface.crate/batch_processes/ro-crate-metadata.summary.json)"
    )
    parser.add_argument(
        "--indent", "-t",
        type=int,
        default=2,
        help="JSON indentation (default: 2)"
    )
    
    args = parser.parse_args()
    
    # Resolve paths relative to script location
    script_dir = Path(__file__).parent
    input_path = script_dir / args.input
    output_path = script_dir / args.output
    
    # Check if input file exists
    if not input_path.exists():
        print(f"Error: Input file '{input_path}' not found.")
        return 1
    
    try:
        # Load the original metadata
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create batch summary
        summary = create_batch_summary(data)
        
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
        
        print(f"Batch processes summary generated successfully!")
        print(f"Input file: {input_path} ({original_size:,} bytes)")
        print(f"Output file: {output_path} ({summary_size:,} bytes)")
        print(f"Size reduction: {reduction:.1f}%")
        
        # Count different entity types in summary
        action_count = sum(1 for item in summary["@graph"] 
                          if isinstance(item.get("@type"), list) and 
                          ("CreateAction" in item["@type"] or "ControlAction" in item["@type"]))
        param_count = sum(1 for item in summary["@graph"] 
                         if isinstance(item.get("@type"), list) and "FormalParameter" in item["@type"])
        
        print(f"Summarized: {action_count} workflow actions, {param_count} formal parameters")
        
        return 0
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
