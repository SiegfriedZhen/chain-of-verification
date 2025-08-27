from langchain_core.language_models.fake import FakeListLLM
from src.osint_verification_chain import VerificationQuestions
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
import json

# Test input
osint_info = "Analysis suggests potential bot activity in YouTube comments, with multiple accounts created in rapid succession."
evidence_list = [
    "The account creation dates are concentrated within a 4-second window, with the majority (274 out of 573) created at 1970-08-23 06:15:08.",
    "There are several spikes in the account creation dates, with 61 accounts created at 1970-08-23 06:15:05, 60 at 1970-08-23 06:15:06, 93 at 1970-08-23 06:15:07, and 85 at 1970-08-23 06:15:09.",
    "The histogram of account creation dates shows a clear spike in the distribution, with the majority of accounts being created within a very short time frame."
]

# Define expected response
verification_questions_response = """
{
  "verification_questions": [
    "Can data analysis confirm the concentration of account creation dates within a 4-second window?",
    "Can data analysis verify the specific spikes in account creation times at 1970-08-23 06:15:05-09?",
    "Can data analysis validate the histogram distribution showing a clear spike in account creations?"
  ]
}
"""

def test_json_parsing():
    print("Testing JSON parsing functionality...")
    
    # Create parser
    parser = JsonOutputParser(pydantic_object=VerificationQuestions)
    
    # Test direct parsing
    print("\n1. Testing direct JSON parsing:")
    try:
        parsed = parser.parse(verification_questions_response)
        print("✓ Successfully parsed JSON")
        print("Parsed output:", type(parsed))
        print("Questions:")
        if isinstance(parsed, dict):
            for i, q in enumerate(parsed["verification_questions"], 1):
                print(f"{i}. {q}")
        else:
            for i, q in enumerate(parsed.verification_questions, 1):
                print(f"{i}. {q}")
    except Exception as e:
        print(f"✗ Error parsing JSON: {str(e)}")

def test_prompt_format():
    print("\n2. Testing prompt format instructions:")
    parser = JsonOutputParser(pydantic_object=VerificationQuestions)
    format_instructions = parser.get_format_instructions()
    print("Format Instructions:")
    print(format_instructions)

def test_llm_integration():
    print("\n3. Testing LLM integration:")
    
    # Create mock LLM
    llm = FakeListLLM(responses=[verification_questions_response])
    
    # Create parser
    parser = JsonOutputParser(pydantic_object=VerificationQuestions)
    
    # Create prompt template
    template = """
    Generate verification questions based on the following information:
    
    OSINT Information: {osint_information}
    Evidence:
    {evidence}
    
    {format_instructions}
    """
    
    prompt = PromptTemplate(
        template=template,
        input_variables=["osint_information", "evidence"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    # Create chain
    chain = prompt | llm | parser
    
    try:
        # Format evidence as bullet points
        evidence_formatted = "\n".join([f"- {e}" for e in evidence_list])
        
        # Run chain
        result = chain.invoke({
            "osint_information": osint_info,
            "evidence": evidence_formatted
        })
        
        print("✓ Chain execution successful")
        print("\nGenerated Questions:")
        if isinstance(result, dict):
            for i, q in enumerate(result["verification_questions"], 1):
                print(f"{i}. {q}")
        else:
            for i, q in enumerate(result.verification_questions, 1):
                print(f"{i}. {q}")
                
    except Exception as e:
        print(f"✗ Error in chain execution: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== JSON Output Parser Testing ===\n")
    test_json_parsing()
    test_prompt_format()
    test_llm_integration() 