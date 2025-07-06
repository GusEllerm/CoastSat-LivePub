#!/bin/bash
set -e


# Configuration
COASTSAT_DIR="./CoastSat"
OUTPUT_DIR="LP_Crate/interface_crate_output"

echo "[🧹] Resetting build environment..."
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

echo "[⚙️ ] Building provenance crate..."
python3 LP_Crate/provenance_crate.py --coastsat-dir "$COASTSAT_DIR" --output-dir "$OUTPUT_DIR/provenance"

echo "[📦] Building interface crate..."
python3 LP_Crate/interface_crate.py --coastsat-dir "$COASTSAT_DIR" --output-dir "$OUTPUT_DIR"

echo "[✅] Done."