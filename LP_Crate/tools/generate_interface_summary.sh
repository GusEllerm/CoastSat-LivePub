#!/bin/bash
# Generate RO-Crate metadata summary
# Usage: ./generate_summary.sh [output_file]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_FILE="${1:-../interface.crate/ro-crate-metadata.summary.json}"

echo "Generating RO-Crate metadata summary..."
python3 "$SCRIPT_DIR/generate_interface_summary.py" --output "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
    echo "Summary generation completed successfully!"
    echo "Output: $OUTPUT_FILE"
else
    echo "Error: Summary generation failed!"
    exit 1
fi
