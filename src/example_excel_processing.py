#!/usr/bin/env python3
"""
Example usage of the excel_processor.py script for OSINT verification

This script demonstrates how to:
1. Parse an Excel file and add iteration column based on timestamp
2. Run CoVe verification on the processed data
3. Limit processing to 3 records with o3-mini model and high reasoning effort
"""

import asyncio
import os
import sys
import pandas as pd
from datetime import datetime

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our Excel processor and CoVe evaluator
try:
    # When running from src directory
    from excel_processor import ExcelProcessor, CoVeEvaluator
except ImportError:
    # When running from project root
    from src.excel_processor import ExcelProcessor, CoVeEvaluator

async def preprocess_knowledge_base():
    """Preprocess knowledge base to extract collection results as evidence"""
    input_file = "data/knowledge_base_v2.xlsx"
    sheet_name = "Sheet1"
    output_dir = "results"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate timestamp for output files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"Loading Excel file: {input_file}")
    
    # Load the knowledge base
    df = pd.read_excel(input_file, sheet_name=sheet_name)
    
    # Filter for collection results only
    collection_results = df[df['content_type'] == 'collection_result'].copy()
    print(f"Found {len(collection_results)} collection results")
    
    # Rename 'content' to 'found_evidence' for compatibility with our script
    collection_results.rename(columns={'content': 'found_evidence'}, inplace=True)
    
    # Save the preprocessed data
    preprocessed_file = os.path.join(output_dir, f"preprocessed_data_{timestamp}.xlsx")
    collection_results.to_excel(preprocessed_file, index=False)
    print(f"Preprocessed data saved to {preprocessed_file}")
    
    return preprocessed_file

async def main():
    # Preprocess the knowledge base to extract collection results
    preprocessed_file = await preprocess_knowledge_base()
    
    # Initialize Excel processor with preprocessed data
    print(f"\nProcessing Excel file: {preprocessed_file}")
    processor = ExcelProcessor(
        input_file=preprocessed_file,
        sheet_name="Sheet1",
        timestamp_column="timestamp"
    )
    
    # Add iteration column based on timestamp
    processor.add_iteration_column()
    
    # Save processed data
    output_dir = "results"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    processed_file = os.path.join(output_dir, f"processed_data_{timestamp}.xlsx")
    processor.save_processed_data(processed_file)
    
    # Run CoVe evaluation with o3-mini model and high reasoning effort
    print("\nRunning CoVe evaluation with o3-mini model and high reasoning effort")
    print("Evaluating 3 records")
    
    evaluator = CoVeEvaluator(
        data_path=processed_file,
        model="o3-mini",
        reasoning_effort="high"
    )
    
    # Evaluate data with limit of 3 records
    results_df = await evaluator.evaluate_data(limit=3)
    
    # Save evaluation results
    results_file = os.path.join(output_dir, f"cove_results_{timestamp}.xlsx")
    results_df.to_excel(results_file, index=False)
    
    print(f"\nEvaluation results saved to {results_file}")
    
    # Print summary of results
    print("\nSummary of evaluation results:")
    for _, row in results_df.iterrows():
        print(f"Iteration {row['iteration']}: {row['evidence_count']} evidence items, Assessment: {row['final_assessment'][:100]}...")


if __name__ == "__main__":
    asyncio.run(main()) 