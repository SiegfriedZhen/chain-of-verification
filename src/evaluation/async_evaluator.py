import os
import ast
import asyncio
import argparse
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
from openai import OpenAI
from src.osint_verification_chain import OSINTCOVEChain
from src.config import ModelConfig

class AsyncEvaluator:
    def __init__(self, model_config: ModelConfig, data_path: str, model: str, reasoning_effort: str):
        self.model_config = model_config
        self.data_path = data_path
        self.client = OpenAI()
        self.chain = OSINTCOVEChain(model_config=model_config, data_path=data_path)()
        self.model = model
        self.reasoning_effort = reasoning_effort

    async def process_evidence(self, evidence: Any) -> List[str]:
        """Convert evidence to list format."""
        try:
            if isinstance(evidence, str):
                evidence_list = ast.literal_eval(evidence)
                if not isinstance(evidence_list, list):
                    evidence_list = [str(evidence_list)]
            else:
                evidence_list = [str(evidence)]
        except (ValueError, SyntaxError):
            evidence_list = [str(evidence)]
        return evidence_list

    async def evaluate_single_iteration(self, row: pd.Series) -> Dict[str, Any]:
        """Evaluate a single iteration asynchronously."""
        iteration = row['Iterations']
        print(f"\nProcessing iteration {iteration}")
        
        # Process evidence
        evidence_list = await self.process_evidence(row['found_evidence'])
        print(f"Number of evidence items: {len(evidence_list)}")
        print("Evidence content:")
        for i, ev in enumerate(evidence_list, 1):
            print(f"{i}. {ev}")

        # Format input for o3-mini with role information
        formatted_input = [{"role": "user", "content": ev} for ev in evidence_list]

        # Run the chain with specified model and reasoning effort
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

        # Get verification results
        result = self.chain.invoke({
            "collected_evidence": evidence_list
        })

        return {
            'iteration': iteration,
            'evidence_count': len(evidence_list),
            'evidence_list': evidence_list,
            'verification_questions': result["all_verification_questions"],
            'verification_answers': result["all_verification_answers"],
            'final_assessment': result["final_verification_result"]
        }

    async def evaluate_all(self, sheet_name: str) -> pd.DataFrame:
        """Evaluate all iterations asynchronously."""
        # Read the Excel file
        df = pd.read_excel(self.data_path, sheet_name=sheet_name)
        
        # Process all iterations concurrently
        tasks = [self.evaluate_single_iteration(row) for _, row in df.iterrows()]
        results = await asyncio.gather(*tasks)
        
        # Convert results to DataFrame
        return pd.DataFrame(results)

async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Async evaluator for LLM evaluation')
    parser.add_argument('--input', type=str, required=True,
                        help='Path to input Excel file')
    parser.add_argument('--sheet', type=str, required=True,
                        help='Sheet name to evaluate')
    parser.add_argument('--output-dir', type=str, required=True,
                        help='Directory to save output files')
    parser.add_argument('--model', type=str, required=True,
                        help='Model to use for evaluation (e.g., o3-mini)')
    parser.add_argument('--reasoning-effort', type=str, required=True,
                        choices=['low', 'medium', 'high'],
                        help='Reasoning effort level for the model')
    args = parser.parse_args()

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Initialize evaluator
    model_config = ModelConfig()
    evaluator = AsyncEvaluator(
        model_config=model_config,
        data_path=args.input,
        model=args.model,
        reasoning_effort=args.reasoning_effort
    )

    # Run evaluation
    results_df = await evaluator.evaluate_all(sheet_name=args.sheet)
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(args.output_dir, f"evaluation_results_{timestamp}.xlsx")
    
    # Save results
    results_df.to_excel(output_file, index=False)
    print(f"\nResults have been saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(main()) 