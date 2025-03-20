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


def read_prompt_file(file_path):
    """Read prompt template from file"""
    with open(file_path, 'r') as file:
        return file.read()


class OSINTDataVerificationChain(Chain):
    """
    Implements the logic to verify OSINT information through data analysis using ReAct approach
    """

    prompt: BasePromptTemplate
    llm: BaseLanguageModel
    input_key: str = "verification_questions"
    output_key: str = "verification_answers"
    data_path: str = "data/yt_tsai_secret.xlsx"
    max_retries: int = 3
    retry_delay: float = 2.0

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
            python_repl = PythonREPLTool()
            # Add matplotlib configuration to use non-interactive backend
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
        verification_answers_list = [] # Will contain the analysis of each verification question
        
        # Get verification questions from input - strictly require a list
        verification_questions = inputs[self.input_key]
        
        # Ensure verification_questions is a list
        if not isinstance(verification_questions, list):
            raise ValueError(f"verification_questions must be a list, got {type(verification_questions)}")
        
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
        
        # Run ReAct verification for each question
        for i, question in enumerate(verification_questions, 1):
            if isinstance(question, dict) and "text" in question:
                # If question is a dict with text field, extract it
                question = question["text"]
            
            if not isinstance(question, str) or not question.strip():
                continue
            
            # Format the React prompt with this verification question and data path
            verification_prompt = react_prompt_template.format(
                verification_question=question,
                data_path=self.data_path
            )
            
            # Set up messages for ReAct agent
            messages = [
                SystemMessage(content=verification_prompt),
                HumanMessage(content="Please analyze the data to verify this claim.")
            ]
            
            # Run the ReAct agent with retry mechanism
            try:
                response = self._invoke_with_retry(react_agent, messages, config)
                
                # Extract the final response (last AI message)
                final_message = next((m for m in reversed(response["messages"]) if isinstance(m, AIMessage)), None)
                verification_result = final_message.content if final_message else "No analysis was performed"
                
            except Exception as e:
                verification_result = f"Error during verification: {str(e)}"
            
            verification_answers_list.append(f"Question {i}: {question}\nAnalysis: {verification_result}")
        
        # Format the output as question-analysis pairs
        question_analysis_pairs = "\n\n".join(verification_answers_list)
        
        return {self.output_key: question_analysis_pairs}

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
    
    def __init__(self, llm, react_llm=None, data_path="data/yt_tsai_secret.xlsx"):
        self.llm = llm
        self.react_llm = react_llm or llm  # Use the same llm if react_llm is not provided
        self.data_path = data_path
        
    def __call__(self):
        # Load prompt templates from files
        #baseline_prompt = read_prompt_file("prompts/baseline.txt")
        #verification_question_template_prompt_text = read_prompt_file("prompts/verification_question_template.txt")
        verification_question_prompt_text = read_prompt_file("prompts/verification_question.txt")
        execute_plan_prompt_text = read_prompt_file("prompts/execute_plan.txt")
        final_assessment_prompt_text = read_prompt_file("prompts/final_assessment.txt")
        
        # Create verification question template chain with JSON parser
        parser = JsonOutputParser(pydantic_object=VerificationQuestions)
        
        verification_question_prompt = PromptTemplate(
            input_variables=["collected_evidence"],
            template=verification_question_prompt_text
        )
        
        verification_question_chain = (
            verification_question_prompt | 
            self.llm | 
            parser | 
            (lambda x: {"verification_questions": x["verification_questions"] if isinstance(x, dict) else x.verification_questions})
        )
        
        # Create execution verification chain
        execute_verification_prompt = PromptTemplate(
            input_variables=["verification_questions"],
            template=execute_plan_prompt_text
        )
        execute_verification_chain = OSINTDataVerificationChain(
            llm=self.react_llm,  # Use react_llm for the verification chain
            prompt=execute_verification_prompt,
            output_key="verification_answers",
            data_path=self.data_path
        )
        
        # Create final assessment chain
        final_assessment_prompt = PromptTemplate(
            input_variables=["collected_evidence", "verification_answers"],
            template=final_assessment_prompt_text
        )
        final_assessment_chain = (
            final_assessment_prompt | 
            self.llm | 
            (lambda x: {"credibility_assessment": x})
        )
        
        # Create the combined chain
        input_runnable = RunnablePassthrough()
        
        def combine_outputs(inputs):
            outputs = {}
            outputs.update(inputs)
            #outputs.update(verification_question_template_chain.invoke(inputs))
            outputs.update(verification_question_chain.invoke(inputs))
            outputs.update(execute_verification_chain.invoke(outputs))
            outputs.update(final_assessment_chain.invoke(outputs))
            return outputs
        
        osint_verification_cove_chain = input_runnable | combine_outputs
        
        return osint_verification_cove_chain


class VerificationQuestions(BaseModel):
    verification_questions: List[str] = Field(description="The list of verification questions")

