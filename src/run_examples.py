#!/usr/bin/env python3
"""
Run examples of processing knowledge base files
"""

import sys
import os
import argparse
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# 確保從專案根目錄載入 .env 檔案
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
env_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=env_path)

# Add the project root directory to the Python path
sys.path.insert(0, project_root)

# Import from the examples module
from src.excel_processing.examples import process_knowledge_base
from src.config import ModelConfig

def main():
    """Main entry point for running examples"""
    # Create argument parser
    parser = argparse.ArgumentParser(description='Run examples of knowledge base processing')
    
    # General arguments
    parser.add_argument('--limit', type=str, default='3',
                        help='Number of records to evaluate (default: 3, "all" to process all records)')
    parser.add_argument('--input-file', type=str, default='data/knowledge_base_v2.xlsx',
                        help='Input knowledge base file (default: data/knowledge_base_v2.xlsx)')
    parser.add_argument('--sheet', type=str, default='Sheet1',
                        help='Sheet name to process (default: Sheet1)')
    parser.add_argument('--output-dir', type=str, default='results',
                        help='Output directory (default: results)')
    parser.add_argument('--continue-from', type=str, default=None,
                        help='Path to existing results file to continue from')
    parser.add_argument('--concurrent-tasks', type=int, default=5,
                        help='Maximum number of concurrent tasks to run (default: 5)')
    
    # Model configuration arguments
    parser.add_argument('--max-questions', type=int, default=3, 
                        help='Maximum number of verification questions to generate (default: 3)')
    
    args = parser.parse_args()
    
    # 檢查環境變數是否存在，若不存在則提示使用者
    if not os.getenv("OPENAI_API_KEY"):
        print("\033[1;31mWARNING: OPENAI_API_KEY environment variable not found.\033[0m")
        print("Please set the OPENAI_API_KEY environment variable using one of these methods:")
        print("1. Export the API key in your terminal:")
        print("   export OPENAI_API_KEY=your-api-key-here")
        print("2. Add it to your .env file in the project root:")
        print("   OPENAI_API_KEY=your-api-key-here")
        print("3. Run the command with the API key:")
        print("   OPENAI_API_KEY=your-api-key-here python3 -m src.run_examples")
        print("\nExiting...")
        return
    
    # Convert limit to integer or None for all records
    limit = None if args.limit.lower() == 'all' else int(args.limit)
    
    # 使用預設配置
    # Create default model settings with custom max_questions
    default_settings = ModelConfig.DEFAULTS.copy()
    default_settings["verification_question"]["max_questions"] = args.max_questions
    
    model_config = ModelConfig(model_settings=default_settings)
    print("Using model configuration from config.py")
    
    print(f"\nRunning Excel processing example with {args.input_file}")
    print("This will:")
    print("1. Extract collection results from the knowledge base")
    print("2. Add iteration column based on timestamp")
    print(f"3. Run CoVe verification on {limit if limit is not None else 'ALL'} records")
    print(f"4. Using centralized model configuration from config.py")
    print(f"5. Maximum verification questions: {args.max_questions}")
    print(f"6. Maximum concurrent tasks: {args.concurrent_tasks}")
    if args.continue_from:
        print(f"7. Continuing from previous run: {args.continue_from}")
    print()
    print(f"Results will be saved in the '{args.output_dir}' directory")
    
    # Print the model configuration that will be used
    model_config.print_configuration()
    
    # Run the process_knowledge_base function with the model_config
    try:
        asyncio.run(process_knowledge_base(
            input_file=args.input_file,
            sheet_name=args.sheet,
            output_dir=args.output_dir,
            limit=limit,
            model_config=model_config,
            continue_from=args.continue_from,
            concurrent_tasks=args.concurrent_tasks
        ))
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. You can continue from the latest results file.")
        latest_file = find_latest_results_file(args.output_dir)
        if latest_file:
            print(f"To continue, use: --continue-from {latest_file}")
    except Exception as e:
        print(f"\nError occurred: {e}")
        import traceback
        traceback.print_exc()
        print("\nYou can continue from the latest results file.")
        latest_file = find_latest_results_file(args.output_dir)
        if latest_file:
            print(f"To continue, use: --continue-from {latest_file}")
            
def find_latest_results_file(output_dir):
    """Find the latest results file in the output directory"""
    import glob
    import os
    
    # Find all cove_results files
    result_files = glob.glob(os.path.join(output_dir, "cove_results_*.xlsx"))
    
    if not result_files:
        return None
        
    # Sort by modification time (newest first)
    result_files.sort(key=os.path.getmtime, reverse=True)
    
    # Return the newest file
    return result_files[0]

if __name__ == "__main__":
    main() 