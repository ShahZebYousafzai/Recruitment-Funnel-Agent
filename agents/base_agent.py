# agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from config.settings import settings

class BaseAgent(ABC):
    """Base class for all agents in the recruitment system"""
    
    def __init__(self, name: str):
        self.name = name
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0.1,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.memory: Dict[str, Any] = {}
    
    @abstractmethod
    def execute(self, input_data: Any) -> Any:
        """Main execution method for the agent"""
        pass
    
    def log(self, message: str):
        """Log agent activity"""
        print(f"[{self.name}] {message}")
    
    def store_memory(self, key: str, value: Any):
        """Store information in agent memory"""
        self.memory[key] = value
    
    def recall_memory(self, key: str) -> Any:
        """Recall information from agent memory"""
        return self.memory.get(key)