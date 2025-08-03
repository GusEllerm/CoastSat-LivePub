# RO-Crate Metadata Summary Tools

# RO-Crate Metadata Summary Tools

This directory contains tools for generating summarized versions of RO-Crate metadata files from the LivePublication system. All tools now support flexible interface-crate path specification for maximum portability.

## Quick Start

To generate all summaries at once:

```bash
cd tools/
# Use default interface crate (../interface.crate)
./generate_all_summaries.sh

# Use custom interface crate path
./generate_all_summaries.sh /path/to/interface.crate

# Use custom interface crate and output directory
./generate_all_summaries.sh /path/to/interface.crate /custom/output/
```

This will create summaries and an overview report in the specified output directory.

## Path Handling

All tools now intelligently handle interface crate paths:

1. **Automatic Detection**: If an argument contains `ro-crate-metadata.json`, it's treated as an interface crate path
2. **Relative Path Support**: Relative paths are automatically converted to absolute paths
3. **Default Fallback**: If no path is specified, defaults to `../interface.crate`
4. **Path Validation**: Scripts verify the interface crate directory exists and contains metadata

## Individual Tools

### Master Script
- **`generate_all_summaries.sh`** - Generates all summaries and copies them to a single output directory
  ```bash
  # Default paths
  ./generate_all_summaries.sh
  
  # Custom interface crate
  ./generate_all_summaries.sh /path/to/interface.crate
  
  # Custom interface crate and output directory
  ./generate_all_summaries.sh /path/to/interface.crate /custom/output/
  ```

### Individual Generators

#### Interface Crate Summaries
- **`generate_interface_summary.py`** - Python script for interface crate summaries
- **`generate_interface_summary.sh`** - Shell wrapper
  ```bash
  # Default interface crate
  ./generate_interface_summary.sh
  
  # Custom interface crate path
  ./generate_interface_summary.sh /path/to/interface.crate
  
  # Custom interface crate and output file
  ./generate_interface_summary.sh /path/to/interface.crate /custom/output.json
  
  # Direct Python usage
  python3 generate_interface_summary.py --input /path/to/ro-crate-metadata.json --output summary.json
  ```

#### Batch Processes Summaries  
- **`generate_batch_summary.py`** - Python script for batch processes summaries
- **`generate_batch_summary.sh`** - Shell wrapper
  ```bash
  # Default interface crate
  ./generate_batch_summary.sh
  
  # Custom interface crate path
  ./generate_batch_summary.sh /path/to/interface.crate
  
  # Custom interface crate and output file
  ./generate_batch_summary.sh /path/to/interface.crate /custom/output.json
  
  # Direct Python usage
  python3 generate_batch_summary.py --input /path/to/batch_processes/ro-crate-metadata.json --output summary.json
  ```

#### Notebook Summaries
- **`generate_notebook_summary.py`** - Python script for notebook provenance summaries
- **`generate_notebook_summary.sh`** - Shell wrapper
  ```bash
  # Generate all notebook summaries (default interface crate)
  ./generate_notebook_summary.sh
  
  # Generate all notebook summaries (custom interface crate)
  ./generate_notebook_summary.sh /path/to/interface.crate
  
  # Generate specific notebook summary
  ./generate_notebook_summary.sh /path/to/interface.crate slope_estimation
  
  # Legacy usage - specific notebook with default interface crate
  ./generate_notebook_summary.sh slope_estimation
  
  # Direct Python usage
  python3 generate_notebook_summary.py --interface-crate /path/to/interface.crate --all
  ```

## Output Files

When using `generate_all_summaries.sh`, the following files are created:

### Summary Files
- **interface-crate-summary.json** - Main interface crate summary (5-6KB, 99.9% reduction)
- **batch-processes-summary.json** - Batch processing overview (2KB, 100% reduction)
- **notebook-linear-models-summary.json** - Linear models workflow (9KB, 61.7% reduction)
- **notebook-slope-estimation-summary.json** - Slope estimation workflow (4KB, 41.8% reduction)
- **notebook-tidal-correction-1-summary.json** - Tidal correction workflow instance 1 (6KB, 50% reduction)
- **notebook-tidal-correction-2-summary.json** - Tidal correction workflow instance 2 (6KB, 50% reduction)

### Documentation
- **summary-overview.md** - Comprehensive overview with file sizes and generation details

## Summary Features

### Interface Crate Summaries
- Enumerates workflow steps and formal parameters
- Preserves experiment components (E1, E2.1, E2.2, E3)
- Summarizes large file collections
- 75-80% typical size reduction

### Batch Processes Summaries
- Preserves CreateAction and ControlAction entities
- File pattern analysis (transect_time_series.csv, etc.)
- Extreme compression (99.9%+ reduction)
- Workflow overview focus

### Notebook Summaries
- Complete workflow structure preservation
- HowToStep enumeration with position information
- FormalParameter details for inputs/outputs
- Code cell analysis with I/O distribution
- Media object preservation (Plotly charts)
- 40-65% size reduction maintaining computational narrative

## Requirements

- Python 3.6+
- Bash shell
- Access to the `../interface.crate/` directory structure

## Directory Structure

```
tools/
├── generate_all_summaries.sh       # Master script
├── generate_interface_summary.py   # Interface crate generator
├── generate_interface_summary.sh   # Interface crate wrapper
├── generate_batch_summary.py       # Batch processes generator  
├── generate_batch_summary.sh       # Batch processes wrapper
├── generate_notebook_summary.py    # Notebook generator
├── generate_notebook_summary.sh    # Notebook wrapper
└── SUMMARY_README.md               # Detailed documentation
```

## Use Cases

- **Documentation**: Lightweight metadata for papers and reports
- **Analysis**: Quick overview of workflow structures
- **Distribution**: Reduced file sizes for sharing
- **Development**: Fast metadata inspection during development
- **Archive**: Compact representations for long-term storage

All tools maintain the essential scientific workflow information while dramatically reducing file sizes for practical use.
