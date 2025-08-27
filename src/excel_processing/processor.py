"""
Excel Processor Module

Contains the core functionality for processing Excel data and performing CoVe evaluation.
"""

import os
import argparse
import pandas as pd
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Set, Optional
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# 簡化環境變數加載
project_root = Path(__file__).parent.parent.parent
env_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=env_path)

# Import from parent package
from src.config import ModelConfig
from src.osint_verification_chain import OSINTCOVEChain

class ExcelProcessor:
    def __init__(self, input_file: str, sheet_name: str, timestamp_column: str):
        """
        Initialize Excel processor
        
        Args:
            input_file: Path to input Excel file
            sheet_name: Name of sheet to process
            timestamp_column: Name of timestamp column to use for iteration ordering
        """
        self.input_file = input_file
        self.sheet_name = sheet_name
        self.timestamp_column = timestamp_column
        self.df = None
        
    def load_data(self) -> pd.DataFrame:
        """Load Excel data and return DataFrame"""
        self.df = pd.read_excel(self.input_file, sheet_name=self.sheet_name)
        return self.df
        
    def add_iteration_column(self) -> pd.DataFrame:
        """Add iteration column based on timestamp, sorted chronologically"""
        if self.df is None:
            self.load_data()
            
        # Make sure timestamp column exists
        if self.timestamp_column not in self.df.columns:
            raise ValueError(f"Timestamp column '{self.timestamp_column}' not found in the Excel file")
            
        # Convert timestamp column to datetime if it's not already
        self.df[self.timestamp_column] = pd.to_datetime(self.df[self.timestamp_column])
        
        # Sort by timestamp
        self.df = self.df.sort_values(by=self.timestamp_column)
        
        # Add iteration column (1-based)
        self.df['iteration'] = range(1, len(self.df) + 1)
        
        return self.df
        
    def save_processed_data(self, output_file: str) -> None:
        """Save processed DataFrame to Excel file"""
        if self.df is None:
            raise ValueError("No data to save. Call add_iteration_column() first.")
            
        self.df.to_excel(output_file, index=False)
        print(f"Processed data saved to {output_file}")


class CoVeEvaluator:
    def __init__(self, data_path: str, model_config: ModelConfig, evidence_column: str = 'found_evidence', 
                 print_config: bool = False, output_dir: str = 'results', concurrent_tasks: int = 5):
        """
        Initialize CoVe evaluator
        
        Args:
            data_path: Path to Excel file with processed data
            model_config: Configuration for all LLM models used in different verification steps
            evidence_column: Name of column containing evidence (default: found_evidence)
            print_config: Whether to print the model configuration (default: False)
            output_dir: Directory to save output files (default: results)
            concurrent_tasks: Maximum number of concurrent tasks (default: 5)
        """
        # 直接使用環境變數
        api_key = os.getenv("OPENAI_API_KEY")
        
        # 檢查 API 金鑰是否可用
        if not api_key:
            raise ValueError(
                "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable "
                "or add it to your .env file."
            )
            
        # 保存數據路徑
        self.data_path = data_path
        self.processed_data_path = None  # 將在後續流程中填充
        self.evidence_column = evidence_column
        self.output_dir = output_dir
        self.concurrent_tasks = concurrent_tasks
        os.makedirs(output_dir, exist_ok=True)
        
        # Create timestamp for this evaluation session
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_file = os.path.join(output_dir, f"cove_results_{self.timestamp}.xlsx")
        
        # 創建 OpenAI 客戶端，直接使用環境變數
        self.client = OpenAI(api_key=api_key)
        
        self.model_config = model_config
        
        # 使用原始數據路徑（通常是 yt_tsai_secret.xlsx）
        self.analysis_data_path = "data/yt_tsai_secret.xlsx"
        self.chain = OSINTCOVEChain(model_config=self.model_config, data_path=self.analysis_data_path)()
        
        # Print the configuration if requested
        if print_config:
            self.model_config.print_configuration()
            print(f"Analysis data path: {self.analysis_data_path}")
            
        # Set to track processed iterations to avoid duplication
        self.processed_iterations = set()
        
    async def process_evidence(self, evidence: Any) -> List[str]:
        """Convert evidence to list format"""
        print(f"Processing evidence of type: {type(evidence)}")
        
        # Handle various evidence formats
        if evidence is None:
            print("Evidence is None, returning empty list")
            return []
            
        # Handle NaN values
        try:
            if hasattr(evidence, 'any'):
                # For Series-like objects
                if pd.isna(evidence).any():
                    print("Evidence contains NaN values, returning empty list")
                    return []
            elif pd.isna(evidence):
                print("Evidence is NaN, returning empty list")
                return []
        except Exception as e:
            print(f"Error checking for NaN: {e}, treating as non-NaN")
            
        evidence_list = []
        
        try:
            if isinstance(evidence, str):
                # String case - check if it can be parsed as a list/dict
                print(f"Evidence is string of length {len(evidence)}")
                try:
                    # Try to evaluate as a Python list/dict
                    import ast
                    evidence_parsed = ast.literal_eval(evidence)
                    print(f"Successfully parsed as: {type(evidence_parsed)}")
                    
                    # Handle different evidence formats
                    if isinstance(evidence_parsed, list):
                        # If already a list, use it directly
                        evidence_list = evidence_parsed
                    elif isinstance(evidence_parsed, dict):
                        # If a dictionary, convert to string
                        evidence_list = [str(evidence_parsed)]
                    else:
                        # For other types, convert to string
                        evidence_list = [str(evidence_parsed)]
                except (ValueError, SyntaxError) as e:
                    print(f"Could not parse as Python object: {e}")
                    # If evaluation fails, treat as a single string
                    evidence_list = [evidence]
            elif isinstance(evidence, list):
                # List case
                print(f"Evidence is a list with {len(evidence)} items")
                # Process each list item
                for i, item in enumerate(evidence):
                    if item is None:
                        print(f"  Item {i} is None, skipping")
                        continue
                    if pd.isna(item):
                        print(f"  Item {i} is NaN, skipping")
                        continue
                    if isinstance(item, str):
                        evidence_list.append(item)
                    else:
                        evidence_list.append(str(item))
            elif isinstance(evidence, dict):
                # Dictionary case
                print("Evidence is a dictionary")
                evidence_list = [str(evidence)]
            else:
                # Any other type
                print(f"Evidence is of type {type(evidence)}")
                evidence_list = [str(evidence)]
        except Exception as e:
            print(f"Error in evidence processing: {e}")
            import traceback
            traceback.print_exc()
            # Return an empty list in case of error
            return []
            
        # Filter out empty items and ensure all items are strings
        filtered_list = []
        for i, item in enumerate(evidence_list):
            if not item:
                print(f"  Item {i} is empty, skipping")
                continue
                
            # Check for NaN values
            try:
                if pd.isna(item):
                    print(f"  Item {i} is NaN, skipping")
                    continue
            except:
                pass
                
            # Ensure item is a string
            try:
                item_str = str(item)
                filtered_list.append(item_str)
            except Exception as e:
                print(f"  Could not convert item {i} to string: {e}")
                
        print(f"Returning {len(filtered_list)} processed evidence items")
        return filtered_list
        
    async def evaluate_record(self, row: pd.Series) -> Dict[str, Any]:
        """Evaluate a single record using CoVe"""
        iteration = row['iteration']
        print(f"\nProcessing iteration {iteration}")
        
        try:
            # Process evidence
            evidence_list = await self.process_evidence(row[self.evidence_column])
            print(f"Number of evidence items: {len(evidence_list)}")
            
            if not evidence_list:
                print("No evidence found, skipping evaluation")
                return {
                    'iteration': iteration,
                    'evidence_count': 0,
                    'evidence_list': [],
                    'verification_questions': None,
                    'verification_answers': None,
                    'final_assessment': "No evidence to evaluate"
                }
            
            print("Evidence content:")
            for i, ev in enumerate(evidence_list, 1):
                print(f"{i}. {ev[:100]}..." if len(ev) > 100 else f"{i}. {ev}")

            # Format input with role information
            formatted_input = [{"role": "user", "content": ev} for ev in evidence_list]
            
            # 獲取模型設置
            react_model_name = self.model_config.model_settings["react"]["model_name"]
            react_model_provider = self.model_config.model_settings["react"].get("model_provider", "openai")
            
            # 不同模型可能有不同的參數
            react_params = []
            if react_model_provider == "openai" and "reasoning_effort" in self.model_config.model_settings["react"]:
                react_reasoning_effort = self.model_config.model_settings["react"]["reasoning_effort"]
                if react_reasoning_effort:
                    react_params.append(f"Reasoning effort: {react_reasoning_effort}")
                
            # 輸出模型信息
            print(f"Calling LLM ({react_model_name} - {react_model_provider}) with {len(formatted_input)} evidence items...")
            for param in react_params:
                print(f"  {param}")
            
            try:
                # 運行 CoVe 鏈
                response = await asyncio.to_thread(
                    self.chain.invoke,
                    {"collected_evidence": evidence_list}
                )
                
                print("LLM response received successfully")
                print("Invoking CoVe chain...")
                
                # CoVe chain 正常返回值處理邏輯
                return {
                    'iteration': iteration,
                    'evidence_count': len(evidence_list),
                    'evidence_list': evidence_list,
                    'verification_questions': response.get("all_verification_questions", []),
                    'verification_answers': response.get("all_verification_answers", ""),
                    'final_assessment': response.get("final_verification_result", "")
                }
                
            except Exception as e:
                print(f"Error in CoVe chain: {e}")
                return {
                    'iteration': iteration,
                    'evidence_count': len(evidence_list),
                    'evidence_list': evidence_list,
                    'verification_questions': None,
                    'verification_answers': None,
                    'final_assessment': f"Error in CoVe chain: {e}"
                }
        except Exception as e:
            print(f"Unexpected error in evaluate_record for iteration {iteration}: {e}")
            import traceback
            traceback.print_exc()
            return {
                'iteration': iteration,
                'evidence_count': 0,
                'evidence_list': [],
                'verification_questions': None,
                'verification_answers': None,
                'final_assessment': f"Unexpected error: {str(e)}"
            }
        
    async def evaluate_data(self, limit: int = None, continue_from: str = None) -> pd.DataFrame:
        """
        Evaluate data using CoVe asynchronously
        
        Args:
            limit: Maximum number of records to evaluate (None for all)
            continue_from: Path to existing results file to continue from
            
        Returns:
            DataFrame with evaluation results
        """
        # 保存處理後的 Excel 文件路徑
        self.processed_data_path = self.data_path
        
        # Read the processed Excel file
        df = pd.read_excel(self.processed_data_path)
        
        # Load existing results if continuing from previous run
        if continue_from and os.path.exists(continue_from):
            try:
                existing_results = pd.read_excel(continue_from)
                self.processed_iterations = set(existing_results['iteration'].tolist())
                print(f"Loaded {len(self.processed_iterations)} existing results from {continue_from}")
                # Use the existing results file instead of creating a new one
                self.results_file = continue_from
                # Initialize results with existing data
                results = existing_results.to_dict('records')
            except Exception as e:
                print(f"Error loading existing results: {e}")
                self.processed_iterations = set()
                results = []
        else:
            results = []
        
        # 限制處理的記錄數量
        if limit is not None:
            print(f"Limiting evaluation to first {limit} records out of {len(df)} total records")
            df = df.head(limit)
            
        print(f"Processing {len(df)} records...")
        print(f"Using analysis data path: {self.analysis_data_path}")
        print(f"Results will be saved to {self.results_file}")
        print(f"Maximum concurrent tasks: {self.concurrent_tasks}")
        
        # Create a semaphore to limit concurrent tasks (to avoid API rate limiting)
        # Adjust this value based on your API limits and available resources
        semaphore = asyncio.Semaphore(self.concurrent_tasks)  # Process up to N records simultaneously
        
        # Create tasks for all records
        tasks = []
        for i, (_, row) in enumerate(df.iterrows()):
            iteration = row.get('iteration', i+1)
            
            # Skip already processed iterations
            if iteration in self.processed_iterations:
                print(f"Skipping iteration {iteration} - already processed")
                continue
                
            # Create task for this record
            task = self.process_record_with_semaphore(semaphore, i, row, len(df))
            tasks.append(task)
        
        # Process all tasks in parallel
        for completed_task in asyncio.as_completed(tasks):
            try:
                result = await completed_task
                if result:  # Ensure we have a valid result
                    # Add to our in-memory results
                    results.append(result)
                    # Save immediately to file
                    self.save_intermediate_results(results)
                    # Mark as processed
                    self.processed_iterations.add(result['iteration'])
            except Exception as e:
                print(f"Error processing task: {e}")
                import traceback
                traceback.print_exc()
        
        # Convert results to DataFrame
        results_df = pd.DataFrame(results)
        
        # Final save to ensure everything is written
        self.save_final_results(results_df)
        
        return results_df
    
    async def process_record_with_semaphore(self, semaphore, index, row, total):
        """Process a single record with semaphore to limit concurrency"""
        async with semaphore:
            try:
                print(f"\n===== Processing record {index+1} of {total} (Iteration {row.get('iteration', index+1)}) =====")
                result = await self.evaluate_record(row)
                print(f"===== Completed record {index+1} =====")
                return result
            except Exception as e:
                print(f"Error processing record {index+1}: {e}")
                import traceback
                traceback.print_exc()
                # Return error result
                return {
                    'iteration': row.get('iteration', index+1),
                    'evidence_count': 0,
                    'evidence_list': [],
                    'verification_questions': None,
                    'verification_answers': None,
                    'final_assessment': f"Error processing record: {str(e)}"
                }
    
    def save_intermediate_results(self, results):
        """Save intermediate results to Excel file"""
        try:
            # Convert to DataFrame and save
            temp_df = pd.DataFrame(results)
            temp_df.to_excel(self.results_file, index=False)
            print(f"Saved intermediate results for {len(results)} records to {self.results_file}")
        except Exception as e:
            print(f"Error saving intermediate results: {e}")
    
    def save_final_results(self, results_df):
        """Save final results to Excel file"""
        try:
            results_df.to_excel(self.results_file, index=False)
            print(f"Final results saved to {self.results_file}")
        except Exception as e:
            print(f"Error saving final results: {e}") 