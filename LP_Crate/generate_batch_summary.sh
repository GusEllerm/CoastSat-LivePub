#!/bin/bash
# Generate batch processes RO-Crate metadata summary
# Usage: ./generate_batch_summary.sh [output_file]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_FILE="${1:-interface.crate/batch_processes/ro-crate-metadata.summary.json}"

echo "Generating batch processes metadata summary..."
python3 "$SCRIPT_DIR/generate_batch_summary.py" --output "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
    echo "Batch summary generation completed successfully!"
    echo "Output: $OUTPUT_FILE"
else
    echo "Error: Batch summary generation failed!"
    exit 1
fi
