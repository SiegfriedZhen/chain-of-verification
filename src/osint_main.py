import argparse
import json
import os
from dotenv import load_dotenv

from langchain.chat_models import ChatOpenAI

from osint_verification_chain import OSINTCOVEChain

def main():
    # Load environment variables
    load_dotenv()
    
    # Configure command line arguments
    parser = argparse.ArgumentParser(description="OSINT Verification using Chain of Verification (CoVe)")
    parser.add_argument("--osint-info", type=str, required=True, help="OSINT information to verify")
    parser.add_argument("--evidence", type=str, required=True, help="Collected evidence for verification")
    parser.add_argument("--data-path", type=str, default="data/yt_tsai_secret.xlsx", help="Path to the data file for verification")
    parser.add_argument("--llm-name", type=str, default="o3-mini", help="LLM model name to use")
    parser.add_argument("--temperature", type=float, default=0.0, help="Temperature for LLM")
    parser.add_argument("--max-tokens", type=int, default=1000, help="Max tokens for LLM")
    parser.add_argument("--show-intermediate-steps", action="store_true", help="Show intermediate steps of verification")
    
    args = parser.parse_args()
    
    # Initialize LLM
    llm = ChatOpenAI(
        model_name=args.llm_name,
        temperature=args.temperature,
        max_tokens=args.max_tokens
    )
    
    # Pass data path to the verification chain constructor
    osint_cove_chain_instance = OSINTCOVEChain(llm=llm, data_path=args.data_path)
    osint_cove_chain = osint_cove_chain_instance()
    
    # Run the chain
    response = osint_cove_chain({
        "osint_information": args.osint_info,
        "collected_evidence": args.evidence
    })
    
    # Display results
    if args.show_intermediate_steps:
        print("\n========== VERIFICATION QUESTION TEMPLATE ==========")
        print(response["verification_question_template"])
        
        print("\n========== VERIFICATION QUESTIONS ==========")
        print(response["verification_questions"])
        
        print("\n========== VERIFICATION ANSWERS ==========")
        print(response["verification_answers"])
        
    print("\n========== CREDIBILITY ASSESSMENT ==========")
    print(response["credibility_assessment"])
    
    return response

if __name__ == "__main__":
    main() 