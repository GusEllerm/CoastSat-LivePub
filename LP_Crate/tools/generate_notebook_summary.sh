#!/bin/bash
# Generate notebook RO-Crate metadata summaries
# Usage: ./generate_notebook_summary.sh [interface_crate_path] [notebook_dir|--all]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse arguments - first argument can be interface crate path
if [ $# -eq 0 ]; then
    INTERFACE_CRATE_PATH="../interface.crate"
    NOTEBOOK_ARG="--all"
elif [ $# -eq 1 ]; then
    # Check if first argument is interface crate path
    if [ -f "$1/ro-crate-metadata.json" ]; then
        INTERFACE_CRATE_PATH="$1"
        NOTEBOOK_ARG="--all"
    else
        INTERFACE_CRATE_PATH="../interface.crate"
        NOTEBOOK_ARG="$1"
    fi
else
    INTERFACE_CRATE_PATH="$1"
    NOTEBOOK_ARG="$2"
fi

# Convert to absolute path if needed
if [[ "$INTERFACE_CRATE_PATH" != /* ]]; then
    INTERFACE_CRATE_PATH="$SCRIPT_DIR/$INTERFACE_CRATE_PATH"
fi

echo "Generating notebook metadata summaries..."
echo "Interface crate: $INTERFACE_CRATE_PATH"

if [ "$NOTEBOOK_ARG" = "--all" ] || [ "$NOTEBOOK_ARG" = "-a" ]; then
    echo "Generating summaries for all notebook directories..."
    python3 "$SCRIPT_DIR/generate_notebook_summary.py" --interface-crate "$INTERFACE_CRATE_PATH" --all
elif [ -n "$NOTEBOOK_ARG" ]; then
    echo "Generating summary for notebook: $NOTEBOOK_ARG"
    python3 "$SCRIPT_DIR/generate_notebook_summary.py" --interface-crate "$INTERFACE_CRATE_PATH" "$NOTEBOOK_ARG"
else
    echo "Generating summaries for all notebook directories..."
    python3 "$SCRIPT_DIR/generate_notebook_summary.py" --interface-crate "$INTERFACE_CRATE_PATH" --all
fi

if [ $? -eq 0 ]; then
    echo "Notebook summary generation completed successfully!"
else
    echo "Error: Notebook summary generation failed!"
    exit 1
fi
