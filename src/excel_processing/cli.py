"""
Command-line interface for Excel processing functionality

This module provides command-line scripts for:
1. Running the Excel processor
2. Processing knowledge base files
"""

import os
import sys
import argparse
import asyncio
from datetime import datetime
from dotenv import load_dotenv

from .processor import ExcelProcessor, CoVeEvaluator

async def process_excel(args):
    """
    Process Excel file and run CoVe evaluation
    
    Args:
        args: Command-line arguments
    """
    # Load environment variables
    load_dotenv()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Process Excel file
    print(f"Processing Excel file: {args.input}")
    processor = ExcelProcessor(args.input, args.sheet, args.timestamp_column)
    processor.add_iteration_column()
    
    # Save processed data
    processed_file = os.path.join(args.output_dir, f"processed_data_{timestamp}.xlsx")
    processor.save_processed_data(processed_file)
    
    # Run CoVe evaluation
    print(f"\nRunning CoVe evaluation with {args.model} model and {args.reasoning_effort} reasoning effort")
    print(f"Evaluating {args.limit} records")
    
    evaluator = CoVeEvaluator(
        data_path=processed_file,
        model=args.model,
        reasoning_effort=args.reasoning_effort,
        evidence_column=args.evidence_column
    )
    
    results_df = await evaluator.evaluate_data(limit=args.limit)
    
    # Save evaluation results
    results_file = os.path.join(args.output_dir, f"cove_results_{timestamp}.xlsx")
    results_df.to_excel(results_file, index=False)
    
    print(f"\nEvaluation results saved to {results_file}")
    return results_file

def main():
    """Main entry point for the command-line interface"""
    parser = argparse.ArgumentParser(description='Process Excel and run CoVe evaluation')
    parser.add_argument('--input', type=str, required=True,
                      help='Path to input Excel file')
    parser.add_argument('--sheet', type=str, required=True,
                      help='Sheet name to process')
    parser.add_argument('--timestamp-column', type=str, required=True,
                      help='Name of timestamp column for iteration ordering')
    parser.add_argument('--evidence-column', type=str, default='found_evidence',
                      help='Name of evidence column for CoVe evaluation')
    parser.add_argument('--output-dir', type=str, default='results',
                      help='Directory to save output files')
    parser.add_argument('--model', type=str, default='o3-mini',
                      help='Model to use for evaluation')
    parser.add_argument('--reasoning-effort', type=str, default='high',
                      choices=['low', 'medium', 'high'],
                      help='Reasoning effort level for the model')
    parser.add_argument('--limit', type=int, default=3,
                      help='Number of records to evaluate (default: 3)')
    
    args = parser.parse_args()
    
    # Run the process_excel function
    asyncio.run(process_excel(args))

if __name__ == "__main__":
    main() 