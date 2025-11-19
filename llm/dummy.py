"""Dummy LLM provider for testing without API costs."""
import random
import time
from typing import Dict, List
from llm.base import LLMBase


class DummyProvider(LLMBase):
    """Dummy LLM that returns random/simple responses for testing."""
    
    def __init__(self, model_name: str = "dummy"):
        super().__init__(model_name)
    
    def send_message(self, messages: List[Dict[str, str]], system_prompt: str = "") -> Dict:
        """
        Return a dummy response. This is overridden by game-specific dummy players.
        """
        start_time = time.time()
        
        # Simulate some processing time
        time.sleep(0.1)
        
        response = "This is a dummy response."
        
        elapsed_time = time.time() - start_time
        self.total_time += elapsed_time
        
        # Dummy token count
        tokens = random.randint(10, 50)
        self.total_tokens += tokens
        
        return {
            "response": response,
            "tokens": tokens
        }

