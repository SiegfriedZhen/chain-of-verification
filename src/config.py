from typing import Optional
from langchain_core.language_models import BaseLanguageModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

class ModelConfig:
    """Configuration for language models used in different steps of the verification process"""
    
    def __init__(
        self,
        verification_question_model: Optional[BaseLanguageModel] = None,
        react_model: Optional[BaseLanguageModel] = None,
        final_assessment_model: Optional[BaseLanguageModel] = None,
        aggregation_model: Optional[BaseLanguageModel] = None,
    ):
        # Default models if not specified
        self.verification_question_model = verification_question_model or ChatOpenAI(model="gpt-4o-mini")
        #claude-3-haiku-20240307, claude-3-5-haiku-20241022
        # self.react_model = react_model or ChatAnthropic(temperature=0, model="claude-3-haiku-20240307")
        self.react_model = react_model or ChatOpenAI(model="o3-mini")
        self.final_assessment_model = final_assessment_model or ChatOpenAI(model="o3-mini")
        self.aggregation_model = aggregation_model or ChatOpenAI(model="o3-mini") 