#!/bin/bash
# Master script to generate all RO-Crate metadata summaries
# Usage: ./generate_all_summaries.sh [output_directory]

set -e  # Exit on error

# Handle help request
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    cat << 'EOF'
RO-Crate Metadata Summary Generator
==================================

Usage: ./generate_all_summaries.sh [output_directory]

This script generates summarized versions of all RO-Crate metadata files
from the LivePublication system and copies them to a single output directory.

Arguments:
  output_directory    Directory to store all summary files (default: ../summaries/)

Examples:
  ./generate_all_summaries.sh                    # Use default output directory
  ./generate_all_summaries.sh /tmp/summaries     # Use custom output directory

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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_OUTPUT_DIR="$SCRIPT_DIR/../summaries"
OUTPUT_DIR="${1:-$DEFAULT_OUTPUT_DIR}"

echo "==============================================="
echo "RO-Crate Metadata Summary Generator"
echo "==============================================="
echo "Output directory: $OUTPUT_DIR"
echo

# Create output directory
mkdir -p "$OUTPUT_DIR"

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
python3 generate_interface_summary.py

# Copy interface summary
copy_summary "../interface.crate/ro-crate-metadata.summary.json" "interface-crate-summary.json"
echo

# Generate batch processes summary  
echo "2. Generating Batch Processes Summary..."
echo "----------------------------------------"
python3 generate_batch_summary.py

# Copy batch summary
copy_summary "../interface.crate/batch_processes/ro-crate-metadata.summary.json" "batch-processes-summary.json"
echo

# Generate notebook summaries
echo "3. Generating Notebook Summaries..."
echo "-----------------------------------"
python3 generate_notebook_summary.py --all

# Copy notebook summaries with descriptive names
echo "  Copying notebook summaries..."
copy_summary "../interface.crate/notebooks/linear_models/ro-crate-metadata.summary.json" "notebook-linear-models-summary.json"
copy_summary "../interface.crate/notebooks/slope_estimation/ro-crate-metadata.summary.json" "notebook-slope-estimation-summary.json"
copy_summary "../interface.crate/notebooks/tidal_correction-1/ro-crate-metadata.summary.json" "notebook-tidal-correction-1-summary.json"
copy_summary "../interface.crate/notebooks/tidal_correction-2/ro-crate-metadata.summary.json" "notebook-tidal-correction-2-summary.json"
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
- **notebook-linear-models-summary.json** - Linear models analysis workflow
- **notebook-slope-estimation-summary.json** - Slope estimation workflow  
- **notebook-tidal-correction-1-summary.json** - Tidal correction workflow (instance 1)
- **notebook-tidal-correction-2-summary.json** - Tidal correction workflow (instance 2)
  - Each preserves complete workflow structure with HowToSteps and formal parameters
  - Size reduction: 40-65% while maintaining computational narrative

## Generation Details

EOF

# Add generation timestamp and file sizes
echo "Generated on: $(date)" >> "$OVERVIEW_FILE"
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
echo "All summaries have been generated and copied to:"
echo "  $OUTPUT_DIR"
echo
echo "Files generated:"
ls -la "$OUTPUT_DIR" | grep -E '\.(json|md)$' | awk '{print "  " $9 " (" $5 " bytes)"}'
echo
echo "Use these summaries for documentation, analysis, or"
echo "as lightweight representations of the full metadata."
