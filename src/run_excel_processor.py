#!/usr/bin/env python3
"""
Command-line script to run the Excel processor for OSINT Chain-of-Verification

Usage:
    python run_excel_processor.py --input data/your_data.xlsx --sheet Sheet1 --timestamp-column timestamp
"""

import sys
import os

# Add the project root directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Add the main entry point for the excel_processing package
from src.excel_processing.cli import main

if __name__ == "__main__":
    # Display help message if no arguments provided
    if len(sys.argv) == 1:
        print("""
Usage example:
    python run_excel_processor.py --input data/knowledge_base_v2.xlsx --sheet Sheet1 --timestamp-column timestamp
    
Required arguments:
    --input             Path to input Excel file
    --sheet             Sheet name to process
    --timestamp-column  Name of timestamp column for iteration ordering
    
Optional arguments:
    --evidence-column   Name of evidence column (default: found_evidence)
    --output-dir        Directory to save output files (default: results)
    --model             Model to use for evaluation (default: o3-mini)
    --reasoning-effort  Reasoning level (low, medium, high) (default: high)
    --limit             Number of records to evaluate (default: 3)
""")
        sys.exit(1)
    
    # Run the main function from excel_processing.cli
    main() 