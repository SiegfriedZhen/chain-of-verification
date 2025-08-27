#!/usr/bin/env python3
"""
Simple script to test imports for the Excel processor
"""

import sys
import os

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("Testing imports for the Excel processor...")
    
    # Import from excel_processor
    try:
        # For when running from src directory
        from excel_processor import ExcelProcessor, CoVeEvaluator
        print("✅ Successfully imported ExcelProcessor and CoVeEvaluator from excel_processor")
    except ImportError as e:
        try:
            # For when running from project root
            from src.excel_processor import ExcelProcessor, CoVeEvaluator
            print("✅ Successfully imported ExcelProcessor and CoVeEvaluator from src.excel_processor")
        except ImportError as e2:
            print(f"❌ Failed to import ExcelProcessor: {e2}")
    
    # Import config
    try:
        from config import ModelConfig
        print("✅ Successfully imported ModelConfig from config")
    except ImportError as e:
        try:
            from src.config import ModelConfig
            print("✅ Successfully imported ModelConfig from src.config")
        except ImportError as e2:
            print(f"❌ Failed to import ModelConfig: {e2}")
    
    # Import verification chain
    try:
        from osint_verification_chain import OSINTCOVEChain
        print("✅ Successfully imported OSINTCOVEChain from osint_verification_chain")
    except ImportError as e:
        try:
            from src.osint_verification_chain import OSINTCOVEChain
            print("✅ Successfully imported OSINTCOVEChain from src.osint_verification_chain")
        except ImportError as e2:
            print(f"❌ Failed to import OSINTCOVEChain: {e2}")
    
    # Import pandas
    try:
        import pandas as pd
        print("✅ Successfully imported pandas")
    except ImportError as e:
        print(f"❌ Failed to import pandas: {e}")
    
    # Import OpenAI
    try:
        from openai import OpenAI
        print("✅ Successfully imported OpenAI")
    except ImportError as e:
        print(f"❌ Failed to import OpenAI: {e}")
    
    # Import dotenv
    try:
        from dotenv import load_dotenv
        print("✅ Successfully imported load_dotenv from dotenv")
    except ImportError as e:
        print(f"❌ Failed to import from dotenv: {e}")
    
    print("\nImport test complete.")
    print("Run example_excel_processing.py to test the full functionality.")

if __name__ == "__main__":
    main() 