"""Abstract base class for LLM providers."""
from abc import ABC, abstractmethod
from typing import Dict, List


class LLMBase(ABC):
    """Abstract base class for all LLM providers."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.total_tokens = 0
        self.total_time = 0.0
    
    @abstractmethod
    def send_message(self, messages: List[Dict[str, str]], system_prompt: str = "") -> Dict:
        """
        Send a message to the LLM and get a response.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            system_prompt: System prompt for the LLM
            
        Returns:
            Dict with 'response' (str) and 'tokens' (int) keys
        """
        pass
    
    def get_provider_name(self) -> str:
        """Return the provider name (e.g., 'OpenAI', 'Google', etc.)."""
        return self.__class__.__name__.replace("Provider", "")

