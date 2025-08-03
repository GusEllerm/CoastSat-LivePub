# RO-Crate Metadata Summary Generators

This directory contains scripts to generate summarized versions of RO-Crate metadata files for different components of the LivePublication system.

## Files

### Interface Crate Summaries
- `generate_interface_summary.py` - Python script for generating interface crate summaries
- `generate_interface_summary.sh` - Shell script wrapper for interface summaries

### Batch Processes Summaries  
- `generate_batch_summary.py` - Python script for generating batch processes summaries
- `generate_batch_summary.sh` - Shell script wrapper for batch summaries

### Notebook Summaries
- `generate_notebook_summary.py` - Python script for generating notebook provenance summaries
- `generate_notebook_summary.sh` - Shell script wrapper for notebook summaries

## Usage

### Interface Crate Summaries

```bash
# Generate interface summary with default settings
python generate_interface_summary.py

# Custom input/output files
python generate_interface_summary.py --input custom-metadata.json --output custom-summary.json

# Shell script wrapper
./generate_interface_summary.sh
```

### Batch Processes Summaries

```bash
# Generate batch summary with default settings
python generate_batch_summary.py

# Custom input/output files  
python generate_batch_summary.py --input custom-batch-metadata.json --output custom-batch-summary.json

# Shell script wrapper
./generate_batch_summary.sh
```

### Notebook Summaries

```bash
# Generate summary for specific notebook
python generate_notebook_summary.py linear_models

# Generate summaries for all notebooks
python generate_notebook_summary.py --all

# Direct file input/output
python generate_notebook_summary.py --input path/to/notebook/ro-crate-metadata.json --output summary.json

# Shell script wrappers
./generate_notebook_summary.sh linear_models
./generate_notebook_summary.sh --all
```

## Summary Features

### Interface Crate Summaries
- **Enumerates workflow steps** - Full details for HowToStep entities including position, programming language, and input/output counts
- **Enumerates formal parameters** - Full details for FormalParameter entities including names and valueRequired flags
- **Preserves key entities** - Keeps root dataset, main entity, and experiment components (E1, E2.1, E2.2, E3) as-is
- **Summarizes collections** - Replaces hasPart arrays with count summaries
- **Counts files and other entities** - Provides count summaries for remaining items

### Batch Processes Summaries
- **Preserves workflow actions** - Keeps CreateAction and ControlAction entities with summarized object/result arrays
- **Enumerates formal parameters** - Full details for FormalParameter entities when present
- **File pattern analysis** - Groups files by type (transect_time_series.csv, other CSV, JSON, etc.)
- **Workflow overview** - Maintains key batch processing workflow structure
- **Size optimization** - Extreme compression (99.9%+ reduction) while preserving essential workflow information

### Notebook Summaries
- **Preserves notebook structure** - Keeps root dataset, notebook file, and Jupyter kernel information
- **Enumerates workflow steps** - Full details for all HowToStep entities with position and tool information
- **Enumerates formal parameters** - Complete FormalParameter details for notebook inputs/outputs
- **Summarizes code cells** - Counts code cells with input/output distribution analysis
- **Preserves key CreateActions** - Shows first/last few CreateActions with count summary for large numbers
- **Includes media objects** - Preserves Plotly charts and other visualization outputs
- **Workflow-focused** - Optimized for notebook provenance and reproducibility documentation

## Size Reduction

- **Interface Crate**: Typical size reduction is 75-80% compared to the original metadata file
- **Batch Processes**: Achieves 99.9%+ size reduction (6.5MB → 2KB) due to high file count
- **Notebook Crates**: Achieves 40-65% size reduction while preserving complete workflow structure

All maintain essential workflow and parameter information for documentation purposes.

## Requirements

- Python 3.6+
- Standard library only (no external dependencies)
