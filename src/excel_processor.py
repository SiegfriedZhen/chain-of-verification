import os
import argparse
import pandas as pd
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI

# Try both import paths to handle different run locations
try:
    # When running from src directory
    from config import ModelConfig
    from osint_verification_chain import OSINTCOVEChain
except ImportError:
    # When running from project root
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
    def __init__(self, data_path: str, model: str, reasoning_effort: str):
        """
        Initialize CoVe evaluator
        
        Args:
            data_path: Path to Excel file with processed data
            model: Name of model to use (e.g., "o3-mini")
            reasoning_effort: Reasoning effort level ("low", "medium", "high")
        """
        self.data_path = data_path
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.client = OpenAI()
        self.model_config = ModelConfig()
        self.chain = OSINTCOVEChain(model_config=self.model_config, data_path=data_path)()
        
    async def process_evidence(self, evidence: Any) -> List[str]:
        """Convert evidence to list format"""
        # Handle various evidence formats
        if evidence is None or pd.isna(evidence):
            return []
            
        if isinstance(evidence, str):
            try:
                # Try to evaluate as a Python list/dict
                import ast
                evidence_list = ast.literal_eval(evidence)
                if not isinstance(evidence_list, list):
                    evidence_list = [str(evidence_list)]
            except (ValueError, SyntaxError):
                # If evaluation fails, treat as a single string
                evidence_list = [evidence]
        else:
            evidence_list = [str(evidence)]
            
        return evidence_list
        
    async def evaluate_record(self, row: pd.Series) -> Dict[str, Any]:
        """Evaluate a single record using CoVe"""
        iteration = row['iteration']
        print(f"\nProcessing iteration {iteration}")
        
        # Process evidence
        evidence_list = await self.process_evidence(row['found_evidence'])
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

        # Run the language model with specified reasoning effort
        response = self.client.responses.create(
            model=self.model,
            input=formatted_input,
            text={
                "format": {
                    "type": "text"
                }
            },
            reasoning={
                "effort": self.reasoning_effort
            },
            tools=[],
            store=True
        )
        
        # Get verification results using CoVe
        result = self.chain.invoke({
            "collected_evidence": evidence_list
        })

        return {
            'iteration': iteration,
            'evidence_count': len(evidence_list),
            'evidence_list': evidence_list,
            'verification_questions': result.get("all_verification_questions", result.get("verification_questions")),
            'verification_answers': result.get("all_verification_answers", result.get("verification_answers")),
            'final_assessment': result.get("final_verification_result", result.get("credibility_assessment"))
        }
        
    async def evaluate_data(self, limit: int = None) -> pd.DataFrame:
        """
        Evaluate data using CoVe
        
        Args:
            limit: Maximum number of records to evaluate (None for all)
            
        Returns:
            DataFrame with evaluation results
        """
        # Read the processed Excel file
        df = pd.read_excel(self.data_path)
        
        # Limit number of records if specified
        if limit:
            df = df.head(limit)
            
        # Evaluate each record
        tasks = [self.evaluate_record(row) for _, row in df.iterrows()]
        results = await asyncio.gather(*tasks)
        
        # Convert results to DataFrame
        results_df = pd.DataFrame(results)
        
        return results_df


async def main():
    # Parse command line arguments
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
        reasoning_effort=args.reasoning_effort
    )
    
    results_df = await evaluator.evaluate_data(limit=args.limit)
    
    # Save evaluation results
    results_file = os.path.join(args.output_dir, f"cove_results_{timestamp}.xlsx")
    results_df.to_excel(results_file, index=False)
    
    print(f"\nEvaluation results saved to {results_file}")


if __name__ == "__main__":
    asyncio.run(main()) 