#!/bin/bash
# Generate notebook RO-Crate metadata summaries
# Usage: ./generate_notebook_summary.sh [notebook_dir|--all]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$1" = "--all" ] || [ "$1" = "-a" ]; then
    echo "Generating summaries for all notebook directories..."
    python3 "$SCRIPT_DIR/generate_notebook_summary.py" --all
elif [ -n "$1" ]; then
    echo "Generating summary for notebook: $1"
    python3 "$SCRIPT_DIR/generate_notebook_summary.py" "$1"
else
    echo "Generating summaries for all notebook directories..."
    python3 "$SCRIPT_DIR/generate_notebook_summary.py" --all
fi

if [ $? -eq 0 ]; then
    echo "Notebook summary generation completed successfully!"
else
    echo "Error: Notebook summary generation failed!"
    exit 1
fi
