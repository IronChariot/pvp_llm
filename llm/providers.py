"""LLM provider implementations for various APIs."""
import os
import time
from typing import Dict, List
from llm.base import LLMBase


class GoogleProvider(LLMBase):
    """Google AI Studio (Gemini) provider."""
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        super().__init__(model_name)
        try:
            import google.generativeai as genai
            api_key = os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable not set")
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
        except ImportError:
            raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")
    
    def send_message(self, messages: List[Dict[str, str]], system_prompt: str = "") -> Dict:
        """Send message to Google's Gemini API."""
        import google.generativeai as genai
        
        start_time = time.time()
        
        # Convert messages to Gemini format
        chat_history = []
        for msg in messages[:-1]:  # All but the last message
            role = "user" if msg["role"] == "user" else "model"
            chat_history.append({"role": role, "parts": [msg["content"]]})
        
        # Create chat with history
        chat = self.model.start_chat(history=chat_history)
        
        # Send the last message
        last_message = messages[-1]["content"] if messages else ""
        
        # Add system prompt if provided
        if system_prompt:
            last_message = f"{system_prompt}\n\n{last_message}"
        
        response = chat.send_message(last_message)
        
        elapsed_time = time.time() - start_time
        self.total_time += elapsed_time
        
        # Extract token count
        tokens = 0
        if hasattr(response, 'usage_metadata'):
            tokens = getattr(response.usage_metadata, 'total_token_count', 0)
        
        self.total_tokens += tokens
        
        return {
            "response": response.text,
            "tokens": tokens
        }


class OpenAIProvider(LLMBase):
    """OpenAI provider."""
    
    def __init__(self, model_name: str = "gpt-4o"):
        super().__init__(model_name)
        try:
            from openai import OpenAI
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self.client = OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("openai not installed. Run: pip install openai")
    
    def send_message(self, messages: List[Dict[str, str]], system_prompt: str = "") -> Dict:
        """Send message to OpenAI API."""
        start_time = time.time()
        
        # Add system message if provided
        api_messages = []
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
        api_messages.extend(messages)
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=api_messages
        )
        
        elapsed_time = time.time() - start_time
        self.total_time += elapsed_time
        
        tokens = response.usage.total_tokens if response.usage else 0
        self.total_tokens += tokens
        
        return {
            "response": response.choices[0].message.content,
            "tokens": tokens
        }


class AnthropicProvider(LLMBase):
    """Anthropic (Claude) provider."""
    
    def __init__(self, model_name: str = "claude-3-5-sonnet-20241022"):
        super().__init__(model_name)
        try:
            from anthropic import Anthropic
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            self.client = Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError("anthropic not installed. Run: pip install anthropic")
    
    def send_message(self, messages: List[Dict[str, str]], system_prompt: str = "") -> Dict:
        """Send message to Anthropic API."""
        start_time = time.time()
        
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=8000,
            system=system_prompt if system_prompt else "You are a helpful assistant.",
            messages=messages
        )
        
        elapsed_time = time.time() - start_time
        self.total_time += elapsed_time
        
        tokens = response.usage.input_tokens + response.usage.output_tokens
        self.total_tokens += tokens
        
        return {
            "response": response.content[0].text,
            "tokens": tokens
        }


class XAIProvider(LLMBase):
    """xAI (Grok) provider."""
    
    def __init__(self, model_name: str = "grok-beta"):
        super().__init__(model_name)
        import httpx
        api_key = os.environ.get("XAI_API_KEY")
        if not api_key:
            raise ValueError("XAI_API_KEY environment variable not set")
        self.api_key = api_key
        self.base_url = "https://api.x.ai/v1"
        self.client = httpx.Client()
    
    def send_message(self, messages: List[Dict[str, str]], system_prompt: str = "") -> Dict:
        """Send message to xAI API."""
        import httpx
        
        start_time = time.time()
        
        # Add system message if provided
        api_messages = []
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
        api_messages.extend(messages)
        
        response = self.client.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model_name,
                "messages": api_messages
            }
        )
        
        elapsed_time = time.time() - start_time
        self.total_time += elapsed_time
        
        data = response.json()
        tokens = data.get("usage", {}).get("total_tokens", 0)
        self.total_tokens += tokens
        
        return {
            "response": data["choices"][0]["message"]["content"],
            "tokens": tokens
        }


class OllamaProvider(LLMBase):
    """Ollama (local) provider."""
    
    def __init__(self, model_name: str = "llama3.2"):
        super().__init__(model_name)
        import httpx
        self.base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.client = httpx.Client()
    
    def send_message(self, messages: List[Dict[str, str]], system_prompt: str = "") -> Dict:
        """Send message to Ollama API."""
        import httpx
        
        start_time = time.time()
        
        # Add system message if provided
        api_messages = []
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
        api_messages.extend(messages)
        
        response = self.client.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model_name,
                "messages": api_messages,
                "stream": False
            }
        )
        
        elapsed_time = time.time() - start_time
        self.total_time += elapsed_time
        
        data = response.json()
        
        # Ollama doesn't always provide token counts, estimate if needed
        tokens = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)
        self.total_tokens += tokens
        
        return {
            "response": data["message"]["content"],
            "tokens": tokens
        }


class OpenRouterProvider(LLMBase):
    """OpenRouter provider (unified API for multiple models)."""
    
    def __init__(self, model_name: str = "anthropic/claude-3.5-sonnet"):
        super().__init__(model_name)
        import httpx
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.client = httpx.Client()
    
    def send_message(self, messages: List[Dict[str, str]], system_prompt: str = "") -> Dict:
        """Send message to OpenRouter API."""
        import httpx
        
        start_time = time.time()
        
        # Add system message if provided
        api_messages = []
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
        api_messages.extend(messages)
        
        response = self.client.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model_name,
                "messages": api_messages
            }
        )
        
        elapsed_time = time.time() - start_time
        self.total_time += elapsed_time
        
        data = response.json()
        tokens = data.get("usage", {}).get("total_tokens", 0)
        self.total_tokens += tokens
        
        return {
            "response": data["choices"][0]["message"]["content"],
            "tokens": tokens
        }

