#!/usr/bin/env python3
"""
Generate a summarized version of the RO-Crate metadata file.

This script creates a collapsed/summarized version of ro-crate-metadata.json
that enumerates workflow steps and formal parameters while keeping file counts
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
    # Matches: "key": [\n {whitespace}\n {whitespace}"@id": "value"\n {whitespace}\n ],
    pattern1 = re.compile(
        r'("[\w@-]+"):\s*\[\s*\n\s*{\s*\n\s*("@id"):\s*("[^"]*")\s*\n\s*}\s*\n\s*\],?',
        re.MULTILINE
    )
    json_str = pattern1.sub(r'\1: [{\2: \3}],', json_str)
    
    # Pattern 2: Simple single-property objects (not in arrays)
    # Matches: "key": {\n {whitespace}"@id": "value"\n },
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


def create_enhanced_summary(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create an enhanced summary that enumerates workflows and formal parameters."""
    summary = {
        "@context": data.get("@context"),
        "@graph": []
    }
    
    graph = data.get("@graph", [])
    
    # Track what we've processed
    workflow_steps = []
    formal_parameters = []
    other_entities = []
    files = []
    
    for item in graph:
        item_id = item.get("@id", "")
        item_types = item.get("@type", [])
        if isinstance(item_types, str):
            item_types = [item_types]
        
        # Enumerate workflow steps (HowToStep)
        if "HowToStep" in item_types:
            workflow_step = {
                "@id": item_id,
                "@type": item_types,
                "name": item.get("name", ""),
                "position": item.get("position", ""),
                "programmingLanguage": item.get("programmingLanguage", ""),
            }
            
            # Add input/output counts if available
            if "input_count" in item:
                workflow_step["input_count"] = item["input_count"]
            if "output_count" in item:
                workflow_step["output_count"] = item["output_count"]
                
            workflow_steps.append(workflow_step)
        
        # Enumerate formal parameters
        elif "FormalParameter" in item_types:
            formal_param = {
                "@id": item_id,
                "@type": item_types,
                "name": item.get("name", ""),
                "valueRequired": item.get("valueRequired", False)
            }
            formal_parameters.append(formal_param)
        
        # Keep important entities as-is (root dataset, main entity, etc.)
        elif (item_id in ["./", "ro-crate-metadata.json", "livepublication-interface"] or 
              item_id.startswith("E1-") or item_id.startswith("E2.") or item_id.startswith("E3-")):
            
            # Summarize hasPart arrays for these entities
            summary_item = item.copy()
            if "hasPart" in summary_item and isinstance(summary_item["hasPart"], list):
                part_count = len(summary_item["hasPart"])
                summary_item["hasPart"] = f"... {part_count} items ..."
            
            summary["@graph"].append(summary_item)
        
        # Collect files and other entities for counting
        elif "File" in item_types:
            files.append(item)
        else:
            other_entities.append(item)
    
    # Add enumerated workflow steps
    summary["@graph"].extend(workflow_steps)
    
    # Add formal parameters with examples (similar to workflow steps pattern)
    if formal_parameters:
        if len(formal_parameters) <= 10:
            # For small numbers, show all parameters
            summary["@graph"].extend(formal_parameters)
        else:
            # For large numbers, show first 3, summary of middle parameters, last 3
            first_params = formal_parameters[:3]
            last_params = formal_parameters[-3:]
            collapsed_count = len(formal_parameters) - 6  # Total minus first 3 and last 3
            
            # Add first 3 parameters
            summary["@graph"].extend(first_params)
            
            # Create summary for the collapsed middle parameters
            required_count = sum(1 for p in formal_parameters if p.get("valueRequired", False))
            optional_count = len(formal_parameters) - required_count
            
            params_summary = {
                "@id": "... formal parameters ...",
                "@type": "FormalParameterSummary",
                "count": collapsed_count,
                "total_parameters": len(formal_parameters),
                "required_parameters": required_count,
                "optional_parameters": optional_count,
                "note": f"Collapsed {collapsed_count} middle FormalParameter entities (showing first 3 and last 3)"
            }
            
            # Add summary only if there are actually middle parameters to collapse
            if collapsed_count > 0:
                summary["@graph"].append(params_summary)
            
            # Add last 3 parameters
            summary["@graph"].extend(last_params)
    
    # Add file examples with summary (similar to batch processes pattern)
    if files:
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
            
            # Analyze file types for the summary
            file_types = {}
            for file_item in files:
                file_type = file_item.get("@type", [])
                if isinstance(file_type, list):
                    file_type = ", ".join(file_type)
                file_types[file_type] = file_types.get(file_type, 0) + 1
            
            file_summary = {
                "@id": "... files ...",
                "@type": "FileSummary",
                "count": collapsed_count,
                "total_files": len(files),
                "type_breakdown": file_types,
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
    """Main function to generate summary."""
    parser = argparse.ArgumentParser(
        description="Generate a summarized version of RO-Crate metadata"
    )
    parser.add_argument(
        "--input", "-i",
        default="../interface.crate/ro-crate-metadata.json",
        help="Input RO-Crate metadata file (default: ../interface.crate/ro-crate-metadata.json)"
    )
    parser.add_argument(
        "--output", "-o",
        default="../interface.crate/ro-crate-metadata.summary.json",
        help="Output summary file (default: ../interface.crate/ro-crate-metadata.summary.json)"
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
        
        # Create enhanced summary
        summary = create_enhanced_summary(data)
        
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
        
        print(f"Summary generated successfully!")
        print(f"Input file: {input_path} ({original_size:,} bytes)")
        print(f"Output file: {output_path} ({summary_size:,} bytes)")
        print(f"Size reduction: {reduction:.1f}%")
        
        # Count workflow steps and formal parameters
        workflow_count = sum(1 for item in summary["@graph"] 
                           if isinstance(item.get("@type"), list) and "HowToStep" in item["@type"])
        param_count = sum(1 for item in summary["@graph"] 
                         if isinstance(item.get("@type"), list) and "FormalParameter" in item["@type"])
        
        print(f"Enumerated: {workflow_count} workflow steps, {param_count} formal parameters")
        
        return 0
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
