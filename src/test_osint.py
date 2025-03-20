import os
from dotenv import load_dotenv

from langchain.chat_models import ChatOpenAI

from osint_verification_chain import OSINTCOVEChain

def test_foundit_evidence():
    # Load environment variables
    load_dotenv()
    
    # Foundit evidence and OSINT info
    osint_info = "According to a report, YouTube accounts in the dataset show suspicious patterns of creation dates, suggesting bot activity."
    evidence = "All accounts in the dataset were created on January 1, 1970, with a date range of just 4 nanoseconds. The top accounts by view count and comment count all have creation dates on January 1, 1970."
    
    # Initialize LLM with o3-mini
    llm = ChatOpenAI(
        model_name="o3-mini",
        temperature=0.0,
        max_tokens=1000
    )
    
    # Create and execute OSINT verification chain
    data_path = "data/yt_tsai_secret.xlsx"
    osint_cove_chain_instance = OSINTCOVEChain(llm=llm, data_path=data_path)
    osint_cove_chain = osint_cove_chain_instance()
    
    # Run the chain
    response = osint_cove_chain({
        "osint_information": osint_info,
        "collected_evidence": evidence
    })
    
    # Display results
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
    test_foundit_evidence() 