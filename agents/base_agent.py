# agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List
import os

# Try to import langchain, fallback to mock if not available
try:
    from langchain_openai import ChatOpenAI
    from config.settings import settings
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("Warning: LangChain not available, using mock LLM")

class MockLLM:
    """Mock LLM for testing when LangChain is not available"""
    def invoke(self, messages):
        class MockResponse:
            def __init__(self):
                # Return a proper JSON response for email generation
                self.content = '''
{
    "subject": "Exciting Opportunity - Let's Connect!",
    "body": "Dear candidate, we have an exciting opportunity that matches your skills perfectly. Would you be interested in a brief call to discuss?",
    "call_to_action": "Please reply with your availability for a brief call"
}'''
        return MockResponse()

class BaseAgent(ABC):
    """Base class for all agents in the recruitment system"""
    
    def __init__(self, name: str):
        self.name = name
        
        if LANGCHAIN_AVAILABLE and hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                model=settings.LLM_MODEL,
                temperature=0.1,
                openai_api_key=settings.OPENAI_API_KEY
            )
        else:
            print(f"Warning: Using mock LLM for {name}")
            self.llm = MockLLM()
            
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