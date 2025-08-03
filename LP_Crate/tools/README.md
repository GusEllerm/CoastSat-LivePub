# RO-Crate Metadata Summary Tools

This directory contains tools for generating summarized versions of RO-Crate metadata files from the LivePublication system.

## Quick Start

To generate all summaries at once:

```bash
cd tools/
./generate_all_summaries.sh
```

This will create a `../summaries/` directory with all generated summary files and an overview report.

## Individual Tools

### Master Script
- **`generate_all_summaries.sh`** - Generates all summaries and copies them to a single output directory
  ```bash
  # Use default output directory (../summaries/)
  ./generate_all_summaries.sh
  
  # Use custom output directory
  ./generate_all_summaries.sh /path/to/output
  ```

### Individual Generators

#### Interface Crate Summaries
- **`generate_interface_summary.py`** - Python script for interface crate summaries
- **`generate_interface_summary.sh`** - Shell wrapper
  ```bash
  ./generate_interface_summary.sh
  python3 generate_interface_summary.py --help
  ```

#### Batch Processes Summaries  
- **`generate_batch_summary.py`** - Python script for batch processes summaries
- **`generate_batch_summary.sh`** - Shell wrapper
  ```bash
  ./generate_batch_summary.sh
  python3 generate_batch_summary.py --help
  ```

#### Notebook Summaries
- **`generate_notebook_summary.py`** - Python script for notebook provenance summaries
- **`generate_notebook_summary.sh`** - Shell wrapper
  ```bash
  # Generate all notebook summaries
  ./generate_notebook_summary.sh --all
  
  # Generate specific notebook summary
  ./generate_notebook_summary.sh linear_models
  
  python3 generate_notebook_summary.py --help
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
