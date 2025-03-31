import os
import ast
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
from src.osint_verification_chain import OSINTCOVEChain
from src.config import ModelConfig

# Load environment variables (for API keys)
load_dotenv()

# Initialize language models
model_config = ModelConfig()

# Read the Excel file
df = pd.read_excel("data/LLM evaluation.xlsx", sheet_name="工作表2")

# Create chain
osint_chain_builder = OSINTCOVEChain(model_config=model_config, data_path="data/LLM evaluation.xlsx")
osint_chain = osint_chain_builder()

# Process each row
results = []
for index, row in df.iterrows():
    # Store original iteration number
    iteration = row['Iterations']
    print(f"\nProcessing iteration {iteration}/{len(df)}")
    
    # Convert found evidence to list
    evidence = row['found_evidence']
    try:
        if isinstance(evidence, str):
            evidence_list = ast.literal_eval(evidence)
            if not isinstance(evidence_list, list):
                evidence_list = [str(evidence_list)]
        else:
            evidence_list = [str(evidence)]
    except (ValueError, SyntaxError):
        # If parsing fails, treat it as a single piece of evidence
        evidence_list = [str(evidence)]

    # Print evidence details
    print(f"Number of evidence items: {len(evidence_list)}")
    print("Evidence content:")
    for i, ev in enumerate(evidence_list, 1):
        print(f"{i}. {ev}")

    # Run the chain
    result = osint_chain.invoke({
        "collected_evidence": evidence_list
    })

    # Store results
    results.append({
        'iteration': iteration,
        'evidence_count': len(evidence_list),
        'evidence_list': evidence_list,
        'verification_questions': result["all_verification_questions"],
        'verification_answers': result["all_verification_answers"],
        'final_assessment': result["final_verification_result"]
    })

    print(f"Completed iteration {iteration}")

# Convert results to DataFrame and save to Excel
results_df = pd.DataFrame(results)
results_df.to_excel("data/evaluation_sheet2_results.xlsx", index=False)
print("\nResults have been saved to data/evaluation_sheet2_results.xlsx") 