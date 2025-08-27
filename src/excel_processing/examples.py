"""
Example usage of the Excel processor for OSINT verification

This module demonstrates how to:
1. Process knowledge base files
2. Extract collection results as evidence
3. Run CoVe verification on the processed data
"""

import os
import asyncio
import pandas as pd
from datetime import datetime
import ast
from pathlib import Path
from dotenv import load_dotenv

# 確保從專案根目錄載入 .env 檔案
project_root = Path(__file__).parent.parent.parent
env_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=env_path)

from langchain_openai import ChatOpenAI
from .processor import ExcelProcessor, CoVeEvaluator
from src.config import ModelConfig

async def process_knowledge_base(
    input_file="data/knowledge_base_v2.xlsx", 
    sheet_name="Sheet1", 
    output_dir="results",
    limit=3,
    model_config=None,
    continue_from=None,
    concurrent_tasks=5
):
    """
    Process knowledge base file and run CoVe evaluation
    
    Args:
        input_file: Path to knowledge base Excel file
        sheet_name: Name of sheet to process
        output_dir: Directory to save output files
        limit: Maximum number of records to evaluate (None for all records)
        model_config: ModelConfig instance to use for evaluation
        continue_from: Path to existing results file to continue from
        concurrent_tasks: Maximum number of concurrent tasks to run (default: 5)
        
    Returns:
        Path to results file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate timestamp for output files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"Loading knowledge base file: {input_file}")
    
    # Check if we're continuing from a previous run
    if continue_from:
        if os.path.exists(continue_from):
            print(f"Continuing from previous run: {continue_from}")
            # Use the processed file from the previous run if it exists
            processed_file_from_path = continue_from.replace("cove_results_", "processed_data_")
            if os.path.exists(processed_file_from_path):
                processed_file = processed_file_from_path
                print(f"Using existing processed file: {processed_file}")
            else:
                # Use default processing flow to create the processed file
                preprocessed_file = await preprocess_knowledge_base(
                    input_file=input_file,
                    sheet_name=sheet_name,
                    output_dir=output_dir,
                    timestamp=timestamp
                )
                
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
                processed_file = os.path.join(output_dir, f"processed_data_{timestamp}.xlsx")
                processor.save_processed_data(processed_file)
        else:
            print(f"Specified continue_from file does not exist: {continue_from}")
            print("Starting a new run instead")
            continue_from = None
    
    # If not continuing or continuing file doesn't exist, do normal processing
    if not continue_from:
        # Preprocess knowledge base to extract collection results as evidence
        preprocessed_file = await preprocess_knowledge_base(
            input_file=input_file,
            sheet_name=sheet_name,
            output_dir=output_dir,
            timestamp=timestamp
        )
        
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
        processed_file = os.path.join(output_dir, f"processed_data_{timestamp}.xlsx")
        processor.save_processed_data(processed_file)
    
    # 檢查環境變數是否存在，若不存在則嘗試從 .env 檔案手動讀取
    if not os.getenv("OPENAI_API_KEY"):
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith('OPENAI_API_KEY='):
                        os.environ["OPENAI_API_KEY"] = line.strip().split('=', 1)[1].strip()
                        print("Manually loaded OPENAI_API_KEY from .env file")
                        break
        except Exception as e:
            print(f"Error loading API key: {e}")
    
    # Use provided model_config or create a default one
    if model_config is None:
        model_config = ModelConfig.get_default_config()
    
    # Run CoVe evaluation
    print(f"\nRunning CoVe evaluation")
    print(f"Evaluating {limit if limit is not None else 'ALL'} records")
    
    evaluator = CoVeEvaluator(
        data_path=processed_file,
        evidence_column='found_evidence',
        model_config=model_config,
        print_config=False,  # Avoid duplicate printing of model configuration
        output_dir=output_dir,
        concurrent_tasks=concurrent_tasks
    )
    
    # Evaluate data with limit
    results_df = await evaluator.evaluate_data(limit=limit, continue_from=continue_from)
    
    # Print summary of results
    print("\nSummary of evaluation results:")
    for _, row in results_df.iterrows():
        # Handle final_assessment which might be an AIMessage or string
        final_assessment = row['final_assessment']
        if hasattr(final_assessment, 'content'):
            # If it's an AIMessage object, get the content
            final_assessment = final_assessment.content
        elif not isinstance(final_assessment, str):
            # If it's another non-string type, convert to string
            final_assessment = str(final_assessment)
            
        # Now display the summary
        print(f"Iteration {row['iteration']}: {row['evidence_count']} evidence items, Assessment: {final_assessment[:100]}...")
    
    # Return the results file path
    return evaluator.results_file if hasattr(evaluator, "results_file") else os.path.join(output_dir, f"cove_results_{timestamp}.xlsx")

async def preprocess_knowledge_base(input_file, sheet_name, output_dir, timestamp=None):
    """
    Preprocess knowledge base to extract collection results as evidence
    
    Args:
        input_file: Path to knowledge base Excel file
        sheet_name: Name of sheet to process
        output_dir: Directory to save output files
        timestamp: Timestamp for output file name (optional)
        
    Returns:
        Path to preprocessed file
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Load the knowledge base
    df = pd.read_excel(input_file, sheet_name=sheet_name)
    
    # Filter for evaluation_result instead of collection_result
    evaluation_results = df[df['content_type'] == 'evaluation_result'].copy()
    print(f"Found {len(evaluation_results)} evaluation results")
    
    # Process content field to extract found_evidence using ast.literal_eval
    # Create a new DataFrame to store processed results
    processed_results = []
    
    for index, row in evaluation_results.iterrows():
        try:
            # 檢查是否有 content 欄位及其值是否有效
            if 'content' not in row or pd.isna(row['content']):
                print(f"Row {index}: Missing or invalid content field. Skipping.")
                continue
                
            # Parse the content as Python literal
            content_dict = ast.literal_eval(row['content'])
            
            # 檢查 content_dict 是否為字典
            if not isinstance(content_dict, dict):
                print(f"Row {index}: Content is not a dictionary. Got {type(content_dict)}. Skipping.")
                continue
                
            # Create a new row with the same data plus extracted found_evidence
            new_row = row.copy()
            
            # Extract found_evidence from the content
            if 'found_evidence' in content_dict:
                # 直接使用 found_evidence
                new_row['found_evidence'] = content_dict['found_evidence']
            elif 'evidence_found' in content_dict:
                # 處理 evidence_found 欄位
                evidence_found = content_dict['evidence_found']
                if not pd.isna(evidence_found).all() if hasattr(pd.isna(evidence_found), 'all') else not pd.isna(evidence_found):
                    new_row['found_evidence'] = evidence_found
                else:
                    new_row['found_evidence'] = []
            else:
                # 如果沒有找到證據欄位，使用空列表
                new_row['found_evidence'] = []
                
            processed_results.append(new_row)
            
        except Exception as e:
            print(f"Error processing row {index}: {e}")
            # Skip invalid rows
            continue
    
    # Convert to DataFrame
    if not processed_results:
        raise ValueError("No valid evaluation results were processed. Check your data format.")
        
    processed_df = pd.DataFrame(processed_results)
    
    # Save the preprocessed data
    preprocessed_file = os.path.join(output_dir, f"preprocessed_data_{timestamp}.xlsx")
    processed_df.to_excel(preprocessed_file, index=False)
    print(f"Preprocessed data saved to {preprocessed_file}")
    
    return preprocessed_file

def main():
    """Run the example knowledge base processing"""
    asyncio.run(process_knowledge_base())

if __name__ == "__main__":
    main() 