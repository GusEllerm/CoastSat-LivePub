#!/bin/bash
# Generate batch processes RO-Crate metadata summary
# Usage: ./generate_batch_summary.sh [interface_crate_path] [output_file]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse arguments
INTERFACE_CRATE_PATH="${1:-../interface.crate}"
OUTPUT_FILE="${2:-$INTERFACE_CRATE_PATH/batch_processes/ro-crate-metadata.summary.json}"

# Convert to absolute path if needed
if [[ "$INTERFACE_CRATE_PATH" != /* ]]; then
    INTERFACE_CRATE_PATH="$SCRIPT_DIR/$INTERFACE_CRATE_PATH"
fi

echo "Generating batch processes metadata summary..."
echo "Interface crate: $INTERFACE_CRATE_PATH"
echo "Output file: $OUTPUT_FILE"

python3 "$SCRIPT_DIR/generate_batch_summary.py" \
    --input "$INTERFACE_CRATE_PATH/batch_processes/ro-crate-metadata.json" \
    --output "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
    echo "Batch summary generation completed successfully!"
    echo "Output: $OUTPUT_FILE"
else
    echo "Error: Batch summary generation failed!"
    exit 1
fi
