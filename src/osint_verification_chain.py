import os
import json
from typing import Any, Dict, List, Optional
from pydantic import Extra, BaseModel, Field

from langchain_core.language_models import BaseLanguageModel
from langchain_core.callbacks import (
    AsyncCallbackManagerForChainRun,
    CallbackManagerForChainRun,
)
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage
)
from langchain.chains.base import Chain
from langchain_core.prompts import BasePromptTemplate, PromptTemplate
from langchain_core.runnables import RunnableSequence, RunnablePassthrough, RunnableConfig
from langchain_experimental.tools import PythonREPLTool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
import time
from anthropic._exceptions import OverloadedError
from .config import ModelConfig


def read_prompt_file(file_path):
    """Read prompt template from file"""
    with open(file_path, 'r') as file:
        return file.read()


class OSINTDataVerificationChain(Chain):
    """
    Implements the logic to verify OSINT information through data analysis using ReAct approach
    """

    llm: BaseLanguageModel
    input_key: str = "verification_questions"
    output_key: str = "verification_answers"
    data_path: str = "data/yt_tsai_secret.xlsx"
    max_retries: int = 3
    retry_delay: float = 2.0
    evidence_id: Optional[str] = None  # Added evidence_id to track which evidence is being processed

    class Config:
        """Configuration for this pydantic object."""
        extra = Extra.forbid
        arbitrary_types_allowed = True

    @property
    def input_keys(self) -> List[str]:
        """Will be whatever keys the prompt expects."""
        return [self.input_key]

    @property
    def output_keys(self) -> List[str]:
        """Will always return text key."""
        return [self.output_key]
    
    def setup_tools(self):
        """Set up tools for the ReAct agent to use for data analysis"""
        
        @tool
        def analyze_data(python_code: str):
            """Execute Python code to analyze data and return the results."""
            # Add matplotlib configuration to use non-interactive backend
            setup_code = """
import matplotlib
matplotlib.use('Agg')
"""
            python_repl = PythonREPLTool()
            # First run the setup code
            python_repl.run(setup_code)
            # Then run the actual analysis code
            return python_repl.run(python_code)
        
        return [analyze_data]
    
    def _invoke_with_retry(self, react_agent, messages, config):
        """Helper method to invoke ReAct agent with retry logic"""
        for attempt in range(self.max_retries):
            try:
                return react_agent.invoke({"messages": messages}, config=config)
            except OverloadedError:
                if attempt == self.max_retries - 1:  # Last attempt
                    raise  # Re-raise the exception if all retries failed
                time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
    
    def invoke(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, str]:
        # Get verification questions from input - strictly require a list
        verification_questions = inputs[self.input_key]
        original_evidence = inputs.get("original_evidence")
        
        # Ensure verification_questions is a list
        if not isinstance(verification_questions, list):
            raise ValueError(f"verification_questions must be a list, got {type(verification_questions)}")
        
        # Format all questions into a single string
        formatted_questions = "\n".join([f"{i}. {q}" for i, q in enumerate(verification_questions, 1)])
        
        # Read React agent prompt template
        react_prompt_template = read_prompt_file("prompts/react_agent.txt")
        
        # Set up ReAct agent with tools
        tools = self.setup_tools()
        react_agent = create_react_agent(self.llm, tools=tools)
        
        # Create config with increased recursion limit
        config = RunnableConfig(
            configurable={
                "recursion_limit": 30
            }
        )
        
        # Format the React prompt with all verification questions and data path
        verification_prompt = react_prompt_template.format(
            verification_question=formatted_questions,
            data_path=self.data_path,
            original_evidence=original_evidence
        )
        
        # Set up messages for ReAct agent
        messages = [
            SystemMessage(content=verification_prompt),
            HumanMessage(content="Please analyze the data to verify these claims.")
        ]
        
        # Run the ReAct agent with retry mechanism
        try:
            response = self._invoke_with_retry(react_agent, messages, config)
            
            # Extract the final response (last AI message)
            final_message = next((m for m in reversed(response["messages"]) if isinstance(m, AIMessage)), None)
            verification_result = final_message.content if final_message else "No analysis was performed"
            
        except Exception as e:
            verification_result = f"Error during verification: {str(e)}"
        
        # Include evidence_id in the verification result if available
        evidence_prefix = f"[Evidence {self.evidence_id}] " if self.evidence_id else ""
        verification_result = f"{evidence_prefix}Analysis for {len(verification_questions)} questions:\n\n{verification_result}"
        
        return {self.output_key: verification_result}

    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, str]:
        return self.invoke(inputs, run_manager)


class OSINTCOVEChain:
    """
    Implements the Chain of Verification process for OSINT information validation
    using dataset analysis for disinformation detection
    """
    
    def __init__(self, model_config: ModelConfig, data_path="data/yt_tsai_secret.xlsx"):
        self.model_config = model_config
        self.data_path = data_path
        
    def __call__(self):
        # Load prompt templates from files
        verification_question_prompt_text = read_prompt_file("prompts/verification_question.txt")
        final_assessment_prompt_text = read_prompt_file("prompts/final_assessment.txt")
        aggregation_prompt_text = read_prompt_file("prompts/aggregation.txt")
        
        # Create verification question template chain with JSON parser
        parser = JsonOutputParser(pydantic_object=VerificationQuestions)
        
        # Create the combined chain
        input_runnable = RunnablePassthrough()
        
        def process_individual_evidences(inputs):
            """Process each evidence independently"""
            outputs = {}
            outputs.update(inputs)
            
            # Get the list of evidences
            evidences = inputs.get("collected_evidence", [])
            if not isinstance(evidences, list):
                evidences = [evidences]
            
            all_verification_questions = []
            all_verification_answers = []
            all_credibility_assessments = []
            
            # Process each evidence independently
            for i, evidence in enumerate(evidences, 1):
                evidence_id = str(i)
                
                # Get max questions parameter
                max_questions = self.model_config.model_settings["verification_question"].get("max_questions", 3)
                
                # Create verification question chain for this evidence
                verification_question_prompt = PromptTemplate(
                    input_variables=["collected_evidence", "max_questions"],
                    template=verification_question_prompt_text
                )
                
                evidence_input = {
                    "collected_evidence": evidence,
                    "max_questions": max_questions
                }
                
                verification_question_chain_output = verification_question_prompt | self.model_config.verification_question_model | parser
                verification_questions_result = verification_question_chain_output.invoke(evidence_input)
                
                verification_questions = verification_questions_result.verification_questions if hasattr(verification_questions_result, "verification_questions") else verification_questions_result["verification_questions"]
                
                # Limit to max_questions if needed
                if len(verification_questions) > max_questions:
                    verification_questions = verification_questions[:max_questions]
                    print(f"Limited verification questions to maximum of {max_questions}")
                
                # Store questions with evidence ID
                for q in verification_questions:
                    all_verification_questions.append(f"[Evidence {evidence_id}] {q}")
                
                # Create execution verification chain for this evidence
                execute_verification_chain = OSINTDataVerificationChain(
                    llm=self.model_config.react_model,
                    output_key="verification_answers",
                    data_path=self.data_path,
                    evidence_id=evidence_id
                )
                
                verification_answers = execute_verification_chain.invoke({
                    "verification_questions": verification_questions,
                    "original_evidence": evidence
                })["verification_answers"]
                
                all_verification_answers.append(verification_answers)
                
                # Create final assessment chain for this evidence
                final_assessment_prompt = PromptTemplate(
                    input_variables=["collected_evidence", "verification_answers"],
                    template=final_assessment_prompt_text
                )
                
                final_assessment_chain = final_assessment_prompt | self.model_config.final_assessment_model
                
                credibility_assessment = final_assessment_chain.invoke({
                    "collected_evidence": evidence,
                    "verification_answers": verification_answers
                })
                
                all_credibility_assessments.append(f"[Evidence {evidence_id}] {credibility_assessment}")
            
            # Aggregate all results
            outputs["all_verification_questions"] = all_verification_questions
            outputs["all_verification_answers"] = "\n\n".join(all_verification_answers)
            outputs["all_credibility_assessments"] = "\n\n".join(all_credibility_assessments)
            
            # Format all evidences for aggregation
            formatted_evidences = "\n\n".join([f"[Evidence {i+1}] {evidence}" for i, evidence in enumerate(evidences)])
            
            # Run the aggregation step
            aggregation_prompt = PromptTemplate(
                input_variables=["all_credibility_assessments", "all_evidences"],
                template=aggregation_prompt_text
            )
            
            aggregation_chain = aggregation_prompt | self.model_config.aggregation_model
            
            final_result = aggregation_chain.invoke({
                "all_credibility_assessments": outputs["all_credibility_assessments"],
                "all_evidences": formatted_evidences
            })
            
            outputs["final_verification_result"] = final_result
            
            return outputs
        
        osint_verification_cove_chain = input_runnable | process_individual_evidences
        
        return osint_verification_cove_chain


class VerificationQuestions(BaseModel):
    verification_questions: List[str] = Field(description="The list of verification questions")

