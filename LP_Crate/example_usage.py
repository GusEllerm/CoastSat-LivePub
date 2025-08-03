#!/usr/bin/env python3
"""
Example script demonstrating how to use the global configuration
to set file limits for all LP_Crate operations.
"""

from config import set_file_limit, get_file_limit
from e1_crate import build_e1_crate
from interface_crate import main as build_interface_crate  # Import the main function
import argparse
import os
from pathlib import Path
import sys

def main():
    parser = argparse.ArgumentParser(description="Build LP_Crate with configurable limits")
    parser.add_argument(
        "--coastsat-dir",
        type=Path,
        required=False,
        default=Path(__file__).parent.parent / "CoastSat",
        help="Path to CoastSat project directory."
    )
    parser.add_argument(
        "--output-dir", 
        type=Path, 
        required=False, 
        default=Path(__file__).parent / "interface.crate", 
        help="Directory to write the interface RO-Crate."
    )
    parser.add_argument("--limit", type=str, default=None, 
                       help="Maximum number of files to include. Use 'none' for no limit (default: use config.py setting)")
    
    args = parser.parse_args()
    
    # Set the global limit if provided
    if args.limit is not None:
        if args.limit.lower() in ['none', 'null', 'unlimited']:
            print("Setting global file limit to: None (unlimited)")
            set_file_limit(None)
        else:
            try:
                limit_value = int(args.limit)
                print(f"Setting global file limit to: {limit_value}")
                set_file_limit(limit_value)
            except ValueError:
                print(f"Error: Invalid limit value '{args.limit}'. Use an integer or 'none'.")
                return 1
    else:
        print(f"Using default file limit from config: {get_file_limit()}")
    
    # Now all functions will use the configured limit
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"CoastSat directory: {args.coastsat_dir}")
    print(f"Output directory: {args.output_dir}")
    
    # Build the full interface crate (which includes E1, E2.2 subcrates, etc.)
    print(f"Building interface crate with limit {get_file_limit()}...")
    
    # Temporarily override sys.argv to pass arguments to interface_crate.main()
    original_argv = sys.argv
    sys.argv = [
        'interface_crate.py',
        '--coastsat-dir', str(args.coastsat_dir),
        '--output-dir', str(args.output_dir)
    ]
    
    try:
        build_interface_crate()  # This builds the main interface crate with all subcrates
    finally:
        sys.argv = original_argv
    
    print("Done! Interface crate built with all subcrates using the global limit setting.")

if __name__ == "__main__":
    main()
