#!/bin/bash
# Master script to generate all RO-Crate metadata summaries
# Usage: ./generate_all_summaries.sh [interface_crate_path] [output_directory]

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Handle help request
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    cat << 'EOF'
RO-Crate Metadata Summary Generator
==================================

Usage: ./generate_all_summaries.sh [interface_crate_path] [output_directory]

This script generates summarized versions of all RO-Crate metadata files
from the LivePublication system and copies them to a single output directory.

Arguments:
  interface_crate_path   Path to interface.crate directory (default: ../interface.crate/)
  output_directory       Directory to store all summary files (default: ../summaries/)

Examples:
  ./generate_all_summaries.sh                               # Use default paths
  ./generate_all_summaries.sh ../interface.crate/           # Specify interface crate path
  ./generate_all_summaries.sh ../interface.crate/ /tmp/summaries  # Both paths

Generated Files:
  - interface-crate-summary.json         (Main interface crate summary)
  - batch-processes-summary.json         (Batch processing overview)
  - notebook-*-summary.json              (Individual notebook summaries)
  - summary-overview.md                  (Overview report with file sizes)

The script will:
1. Generate interface crate summary (99.9% size reduction)
2. Generate batch processes summary (100% size reduction)  
3. Generate all notebook summaries (40-65% size reduction)
4. Copy all summaries to output directory with descriptive names
5. Create an overview report with generation details

For individual generators, see:
  ./generate_interface_summary.sh --help
  ./generate_batch_summary.sh --help
  ./generate_notebook_summary.sh --help
EOF
    exit 0
fi

# Set default paths and parse arguments
DEFAULT_INTERFACE_CRATE="$SCRIPT_DIR/../interface.crate"
DEFAULT_OUTPUT_DIR="$SCRIPT_DIR/../summaries"

if [ $# -eq 0 ]; then
    # No arguments - use defaults
    INTERFACE_CRATE_PATH="$DEFAULT_INTERFACE_CRATE"
    OUTPUT_DIR="$DEFAULT_OUTPUT_DIR"
elif [ $# -eq 1 ]; then
    # One argument - could be interface crate path or output dir
    if [ -d "$1" ] && [ -f "$1/ro-crate-metadata.json" ]; then
        # Looks like interface crate path
        INTERFACE_CRATE_PATH="$1"
        OUTPUT_DIR="$DEFAULT_OUTPUT_DIR"
    else
        # Treat as output directory
        INTERFACE_CRATE_PATH="$DEFAULT_INTERFACE_CRATE"
        OUTPUT_DIR="$1"
    fi
elif [ $# -eq 2 ]; then
    # Two arguments - interface crate path and output dir
    INTERFACE_CRATE_PATH="$1"
    OUTPUT_DIR="$2"
else
    echo "Error: Too many arguments. See --help for usage."
    exit 1
fi

# Convert to absolute paths and validate
if [ ! -d "$INTERFACE_CRATE_PATH" ]; then
    echo "Error: Interface crate directory not found: $INTERFACE_CRATE_PATH"
    exit 1
fi

if [ ! -f "$INTERFACE_CRATE_PATH/ro-crate-metadata.json" ]; then
    echo "Error: Interface crate metadata not found: $INTERFACE_CRATE_PATH/ro-crate-metadata.json"
    exit 1
fi

INTERFACE_CRATE_PATH="$(cd "$INTERFACE_CRATE_PATH" && pwd)"
OUTPUT_DIR="$(mkdir -p "$OUTPUT_DIR" && cd "$OUTPUT_DIR" && pwd)"

echo "==============================================="
echo "RO-Crate Metadata Summary Generator"
echo "==============================================="
echo "Interface crate path: $INTERFACE_CRATE_PATH"
echo "Output directory: $OUTPUT_DIR"
echo

# Function to copy summary file with better naming
copy_summary() {
    local source_file="$1"
    local dest_name="$2"
    
    if [ -f "$source_file" ]; then
        cp "$source_file" "$OUTPUT_DIR/$dest_name"
        echo "  ✓ Copied to: $OUTPUT_DIR/$dest_name"
    else
        echo "  ✗ Warning: $source_file not found"
    fi
}

# Generate interface crate summary
echo "1. Generating Interface Crate Summary..."
echo "----------------------------------------"
cd "$SCRIPT_DIR"
python3 generate_interface_summary.py --input "$INTERFACE_CRATE_PATH/ro-crate-metadata.json" --output "$INTERFACE_CRATE_PATH/ro-crate-metadata.summary.json"

# Copy interface summary
copy_summary "$INTERFACE_CRATE_PATH/ro-crate-metadata.summary.json" "interface-crate-summary.json"
echo

# Generate batch processes summary  
echo "2. Generating Batch Processes Summary..."
echo "----------------------------------------"
BATCH_INPUT="$INTERFACE_CRATE_PATH/batch_processes/ro-crate-metadata.json"
BATCH_OUTPUT="$INTERFACE_CRATE_PATH/batch_processes/ro-crate-metadata.summary.json"

if [ -f "$BATCH_INPUT" ]; then
    python3 generate_batch_summary.py --input "$BATCH_INPUT" --output "$BATCH_OUTPUT"
    copy_summary "$BATCH_OUTPUT" "batch-processes-summary.json"
else
    echo "  Warning: Batch processes metadata not found at $BATCH_INPUT"
fi
echo

# Generate notebook summaries
echo "3. Generating Notebook Summaries..."
echo "-----------------------------------"
NOTEBOOKS_DIR="$INTERFACE_CRATE_PATH/notebooks"

if [ -d "$NOTEBOOKS_DIR" ]; then
    python3 generate_notebook_summary.py --interface-crate "$INTERFACE_CRATE_PATH" --all
    
    # Copy notebook summaries with descriptive names
    echo "  Copying notebook summaries..."
    for notebook_dir in "$NOTEBOOKS_DIR"/*; do
        if [ -d "$notebook_dir" ]; then
            notebook_name="$(basename "$notebook_dir")"
            summary_file="$notebook_dir/ro-crate-metadata.summary.json"
            copy_summary "$summary_file" "notebook-${notebook_name}-summary.json"
        fi
    done
else
    echo "  Warning: Notebooks directory not found at $NOTEBOOKS_DIR"
fi
echo

# Generate overview report
echo "4. Generating Overview Report..."
echo "--------------------------------"

OVERVIEW_FILE="$OUTPUT_DIR/summary-overview.md"

cat > "$OVERVIEW_FILE" << 'EOF'
# RO-Crate Metadata Summaries Overview

This directory contains summarized versions of all RO-Crate metadata files from the LivePublication system.

## Summary Files

### Interface Crate
- **interface-crate-summary.json** - Main interface crate with workflow steps and formal parameters
  - Contains workflow steps, formal parameters, and experiment components (E1, E2.1, E2.2, E3)
  - Typical size reduction: 75-80%

### Batch Processes  
- **batch-processes-summary.json** - Batch processing workflow overview
  - Focuses on CreateAction entities and file pattern analysis
  - Achieves 99.9%+ size reduction due to high file count

### Notebook Provenance
- **notebook-*-summary.json** - Individual notebook workflow summaries
  - Each preserves complete workflow structure with HowToSteps and formal parameters
  - Size reduction: 40-65% while maintaining computational narrative

## Generation Details

EOF

# Add generation timestamp and source path
echo "Generated on: $(date)" >> "$OVERVIEW_FILE"
echo "Source interface crate: $INTERFACE_CRATE_PATH" >> "$OVERVIEW_FILE"
echo "" >> "$OVERVIEW_FILE"
echo "## File Sizes" >> "$OVERVIEW_FILE"
echo "" >> "$OVERVIEW_FILE"

for file in "$OUTPUT_DIR"/*.json; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "unknown")
        echo "- **$filename**: $size bytes" >> "$OVERVIEW_FILE"
    fi
done

echo "  ✓ Generated: $OVERVIEW_FILE"
echo

# Final summary
echo "==============================================="
echo "Summary Generation Complete!"
echo "==============================================="
echo "Source: $INTERFACE_CRATE_PATH"
echo "Output: $OUTPUT_DIR"
echo
echo "Files generated:"
ls -la "$OUTPUT_DIR" | grep -E '\.(json|md)$' | awk '{print "  " $9 " (" $5 " bytes)"}'
echo
echo "Use these summaries for documentation, analysis, or"
echo "as lightweight representations of the full metadata."
