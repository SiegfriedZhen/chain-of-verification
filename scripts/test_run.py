#!/usr/bin/env python3
"""
Test script to validate the new module structure
"""

import os
import sys

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Now try to import our modules
try:
    from src.excel_processing import ExcelProcessor, CoVeEvaluator
    print("✅ Successfully imported ExcelProcessor and CoVeEvaluator")
    
    from src.excel_processing.examples import process_knowledge_base, preprocess_knowledge_base
    print("✅ Successfully imported example functions")
    
    from src.excel_processing.cli import process_excel
    print("✅ Successfully imported CLI functions")
    
    print("\nAll imports successful! The new module structure is working correctly.")
    print("\nYou can now run the examples with:")
    print("  python3 src/run_examples.py")
    print("\nOr use the command-line interface with:")
    print("  python3 src/run_excel_processor.py --input data/knowledge_base_v2.xlsx --sheet Sheet1 --timestamp-column timestamp")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nThere may be an issue with the Python path. Try running:")
    print("  PYTHONPATH=. python3 src/run_examples.py")
    
    # Print debugging information
    print("\nDebugging information:")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    print(f"Available files in src/: {os.listdir('src') if os.path.exists('src') else 'src/ not found'}")
    print(f"Available files in src/excel_processing/: {os.listdir('src/excel_processing') if os.path.exists('src/excel_processing') else 'src/excel_processing/ not found'}") 