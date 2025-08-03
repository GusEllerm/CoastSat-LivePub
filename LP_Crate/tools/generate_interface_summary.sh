#!/bin/bash
# Generate RO-Crate metadata summary
# Usage: ./generate_interface_summary.sh [interface_crate_path] [output_file]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse arguments
INTERFACE_CRATE_PATH="${1:-../interface.crate}"
OUTPUT_FILE="${2:-$INTERFACE_CRATE_PATH/ro-crate-metadata.summary.json}"

# Convert to absolute path if needed
if [[ "$INTERFACE_CRATE_PATH" != /* ]]; then
    INTERFACE_CRATE_PATH="$SCRIPT_DIR/$INTERFACE_CRATE_PATH"
fi

echo "Generating RO-Crate metadata summary..."
echo "Interface crate: $INTERFACE_CRATE_PATH"
echo "Output file: $OUTPUT_FILE"

python3 "$SCRIPT_DIR/generate_interface_summary.py" \
    --input "$INTERFACE_CRATE_PATH/ro-crate-metadata.json" \
    --output "$OUTPUT_FILE"sh
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
