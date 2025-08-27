import os
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
from src.osint_verification_chain import OSINTCOVEChain
from src.config import ModelConfig

# Load environment variables (for API keys)
load_dotenv()

# Initialize language models
model_config = ModelConfig()

# Evidence collected from data analysis
evidence_list = [
    "The account creation dates are concentrated within a 4-second window, with the majority (274 out of 573) created at 1970-08-23 06:15:08.",
    "There are several spikes in the account creation dates, with 61 accounts created at 1970-08-23 06:15:05, 60 at 1970-08-23 06:15:06, 93 at 1970-08-23 06:15:07, and 85 at 1970-08-23 06:15:09.",
    "The histogram of account creation dates shows a clear spike in the distribution, with the majority of accounts being created within a very short time frame."
]

# Create chain
osint_chain_builder = OSINTCOVEChain(model_config=model_config, data_path="data/yt_tsai_secret.xlsx")
osint_chain = osint_chain_builder()

# Run the chain
result = osint_chain.invoke({
    "collected_evidence": evidence_list
})

print("\nVerification Questions:")
print(result["all_verification_questions"])

print("\nVerification Answers:")
print(result["all_verification_answers"])

print("\nFinal Assessment:")
print(result["final_verification_result"])

