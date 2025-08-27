import os
from typing import Optional, Dict, Any

from langchain_core.language_models import BaseLanguageModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_xai import ChatXAI



class ModelConfig:
    """Configuration for language models used in different steps of the verification process"""
    
    # Default configuration values - separated for each model type
    DEFAULTS = {
        "verification_question": {
            #"model_name": "gpt-4.1",
            "model_name": "gpt-4.1",
            "model_provider": "openai",  # 默認使用 OpenAI
            "temperature": 0.0,
            "max_questions": 3  # 默認最大問題數量為 3
        },
        "react": {
            "model_name": "claude-3-5-haiku-20241022",
            "model_provider": "anthropic",
            "temperature": 0.0
            #"model_name": "o4-mini",
            #"reasoning_effort": "high"
        },
        "final_assessment": {
            #"model_name": "gpt-4.1-nano",
            "model_provider": "openai",
            #"temperature": 0.0
            "model_name": "o4-mini",
            "reasoning_effort": "high"
        },
        "aggregation": {
            #"model_name": "gpt-4.1-nano",
            "model_provider": "openai",
            #"temperature": 0.0,
            "model_name": "o4-mini",
            "reasoning_effort": "high"
        }
    }
    
    # 支援的模型提供商
    MODEL_PROVIDERS = {
        "openai": {
            "class": ChatOpenAI,
            "api_key_env": "OPENAI_API_KEY",
        },
        "anthropic": {
            "class": ChatAnthropic,
            "api_key_env": "ANTHROPIC_API_KEY",
        },
        "google": {
            "class": ChatGoogleGenerativeAI,
            "api_key_env": "GOOGLE_API_KEY",
        },
        "xai": {
            "class": ChatXAI,
            "api_key_env": "XAI_API_KEY",
        }
    }
    
    def __init__(
        self,
        verification_question_model: BaseLanguageModel = None,
        react_model: BaseLanguageModel = None,
        final_assessment_model: BaseLanguageModel = None,
        aggregation_model: BaseLanguageModel = None,
        model_settings: Dict = None,
    ):
        # Set default model settings if none provided
        if model_settings is None:
            model_settings = {}
        
        # Default settings structure with separate defaults for each model
        self.model_settings = {
            "verification_question": {
                "model_name": model_settings.get("verification_question", {}).get("model_name", 
                                self.DEFAULTS["verification_question"]["model_name"]),
                "model_provider": model_settings.get("verification_question", {}).get("model_provider", 
                                  self.DEFAULTS["verification_question"]["model_provider"]),
                "temperature": model_settings.get("verification_question", {}).get("temperature", 
                               self.DEFAULTS["verification_question"].get("temperature", 0.0)),
                "reasoning_effort": model_settings.get("verification_question", {}).get("reasoning_effort", 
                                   None),
                "max_questions": model_settings.get("verification_question", {}).get("max_questions", 
                                 self.DEFAULTS["verification_question"]["max_questions"]),
            },
            "react": {
                "model_name": model_settings.get("react", {}).get("model_name", 
                            self.DEFAULTS["react"]["model_name"]),
                "model_provider": model_settings.get("react", {}).get("model_provider", 
                                  self.DEFAULTS["react"]["model_provider"]),
                "temperature": model_settings.get("react", {}).get("temperature", 
                               self.DEFAULTS["react"].get("temperature", 0.0)),
                "reasoning_effort": model_settings.get("react", {}).get("reasoning_effort", 
                                   self.DEFAULTS["react"].get("reasoning_effort")),
            },
            "final_assessment": {
                "model_name": model_settings.get("final_assessment", {}).get("model_name", 
                              self.DEFAULTS["final_assessment"]["model_name"]),
                "model_provider": model_settings.get("final_assessment", {}).get("model_provider", 
                                  self.DEFAULTS["final_assessment"]["model_provider"]),
                "temperature": model_settings.get("final_assessment", {}).get("temperature", 
                               self.DEFAULTS["final_assessment"].get("temperature", 0.0)),
                "reasoning_effort": model_settings.get("final_assessment", {}).get("reasoning_effort", 
                                   self.DEFAULTS["final_assessment"].get("reasoning_effort")),
            },
            "aggregation": {
                "model_name": model_settings.get("aggregation", {}).get("model_name", 
                              self.DEFAULTS["aggregation"]["model_name"]),
                "model_provider": model_settings.get("aggregation", {}).get("model_provider", 
                                  self.DEFAULTS["aggregation"]["model_provider"]),
                "temperature": model_settings.get("aggregation", {}).get("temperature", 
                               self.DEFAULTS["aggregation"].get("temperature", 0.0)),
                "reasoning_effort": model_settings.get("aggregation", {}).get("reasoning_effort", 
                                   self.DEFAULTS["aggregation"].get("reasoning_effort")),
            }
        }
        
        # Use provided models or create them from settings
        self.verification_question_model = verification_question_model or self._create_model(
            "verification_question"
        )
        
        self.react_model = react_model or self._create_model(
            "react"
        )
        
        self.final_assessment_model = final_assessment_model or self._create_model(
            "final_assessment"
        )
        
        self.aggregation_model = aggregation_model or self._create_model(
            "aggregation"
        )
    
    def _create_model(self, model_type):
        """
        Create a model instance with the parameters defined in model_settings
        
        Args:
            model_type: Type of model (verification_question, react, etc.)
            
        Returns:
            Instance of the model
        """
        settings = self.model_settings[model_type]
        model_name = settings["model_name"]
        model_provider = settings.get("model_provider", "openai")
        
        # 檢查提供商是否支援
        if model_provider not in self.MODEL_PROVIDERS:
            raise ValueError(f"Unsupported model provider: {model_provider}. Supported providers are: {list(self.MODEL_PROVIDERS.keys())}")
        
        provider_info = self.MODEL_PROVIDERS[model_provider]
        
        # 檢查是否有提供商的 API 密鑰
        api_key_env = provider_info["api_key_env"]
        api_key = os.getenv(api_key_env)
        
        if not api_key:
            raise ValueError(f"No API key found for {model_provider}. Please set the {api_key_env} environment variable.")
        
        # 組合模型參數
        model_params = {
            "model": model_name,
            "api_key": api_key
        }
        
        # 根據不同提供商處理參數
        if model_provider == "openai":
            # o 系列模型不支援 temperature 參數
            if "temperature" in settings and not model_name.startswith("o"):
                model_params["temperature"] = settings["temperature"]
                
            # reasoning_effort 只適用於特定模型
            if "reasoning_effort" in settings and settings["reasoning_effort"]:
                model_params["reasoning_effort"] = settings["reasoning_effort"]
                
            # o 系列模型特殊處理
            if model_name.startswith("o"):
                print(f"Note: Using {model_name} without temperature parameter")
                
            return ChatOpenAI(**model_params)
            
        elif model_provider == "anthropic":
            # Anthropic 支援 temperature
            if "temperature" in settings:
                model_params["temperature"] = settings["temperature"]
                
            # Claude 特殊參數
            if "max_tokens" in settings:
                model_params["max_tokens"] = settings["max_tokens"]
                
            return ChatAnthropic(**model_params)
            
        elif model_provider == "google":
            # Google Gemini 參數
            if "temperature" in settings:
                model_params["temperature"] = settings["temperature"]
                
            # Gemini 特殊參數
            if "top_p" in settings:
                model_params["top_p"] = settings["top_p"]
                
            # Gemini API 使用 google_api_key，不是 api_key
            model_params["google_api_key"] = api_key
            del model_params["api_key"]
                
            return ChatGoogleGenerativeAI(**model_params)
            
        elif model_provider == "xai":
            # XAI 參數
            if "temperature" in settings:
                model_params["temperature"] = settings["temperature"]
                
            return ChatXAI(**model_params)
            
        else:
            raise ValueError(f"Provider {model_provider} is recognized but not implemented")
    
    def print_configuration(self):
        """Print the current model configuration"""
        print("\n=== Model Configuration ===")
        for step, settings in self.model_settings.items():
            model_name = settings['model_name']
            provider = settings.get('model_provider', 'openai')
            print(f"\n{step.replace('_', ' ').title()}:")
            print(f"  - Provider: {provider}")
            print(f"  - Model: {model_name}")
            
            # Show temperature if in settings
            if "temperature" in settings:
                print(f"  - Temperature: {settings['temperature']}")
            
            # Show max_questions if applicable
            if step == "verification_question" and "max_questions" in settings:
                print(f"  - Max Questions: {settings['max_questions']}")
            
            # Show reasoning_effort if in settings and provider is OpenAI
            if "reasoning_effort" in settings and settings["reasoning_effort"] and provider == "openai":
                print(f"  - Reasoning Effort: {settings['reasoning_effort']}")
                
            # Show other provider-specific parameters
            if provider == "anthropic" and "max_tokens" in settings:
                print(f"  - Max Tokens: {settings['max_tokens']}")
                
            if provider == "google" and "top_p" in settings:
                print(f"  - Top P: {settings['top_p']}")
        print("\n===========================")
        
        # 提示用戶檢查環境變數
        used_providers = set(settings.get('model_provider', 'openai') for settings in self.model_settings.values())
        for provider in used_providers:
            api_key_env = self.MODEL_PROVIDERS[provider]["api_key_env"]
            if not os.getenv(api_key_env):
                print(f"\n⚠️  WARNING: {api_key_env} environment variable not found but required for {provider}.")

    @classmethod
    def get_default_config(cls):
        """Get a ModelConfig instance with default settings"""
        return cls(model_settings=cls.DEFAULTS) 