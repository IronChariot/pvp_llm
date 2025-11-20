"""LLM provider implementations for various APIs."""
import os
import time
from typing import Dict, List
from llm.base import LLMBase


class GoogleProvider(LLMBase):
    """Google AI Studio (Gemini) provider using google.genai."""
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        super().__init__(model_name)
        try:
            from google import genai
            from google.genai import types
            api_key = os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable not set")
            
            self.client = genai.Client(api_key=api_key)
            self.genai = genai
            self.types = types
            
            # Determine thinking configuration based on model
            self.thinking_config = None
            if "gemini-3" in model_name.lower():
                # Gemini 3.0 Pro uses high thinking level
                self.thinking_config = {"thinking_level": "HIGH"}
            elif "gemini-2.5" in model_name.lower() and "flash" in model_name.lower():
                # Gemini 2.5 Flash/Flash Lite uses unlimited thinking budget
                self.thinking_config = {"thinking_budget": -1}
        except ImportError:
            raise ImportError("google-genai not installed. Run: pip install google-genai")
    
    def send_message(self, messages: List[Dict[str, str]], system_prompt: str = "") -> Dict:
        """Send message to Google's Gemini API using google.genai."""
        start_time = time.time()
        
        # Convert messages to google.genai format
        contents = []
        
        # Add system prompt as first user message if provided
        if system_prompt and messages:
            first_msg = messages[0]["content"]
            combined_first = f"{system_prompt}\n\n{first_msg}"
            contents.append(
                self.types.Content(
                    role="user",
                    parts=[self.types.Part.from_text(combined_first)]
                )
            )
            # Add remaining messages
            for msg in messages[1:]:
                role = "user" if msg["role"] == "user" else "model"
                contents.append(
                    self.types.Content(
                        role=role,
                        parts=[self.types.Part.from_text(msg["content"])]
                    )
                )
        else:
            # No system prompt, convert messages directly
            for msg in messages:
                role = "user" if msg["role"] == "user" else "model"
                contents.append(
                    self.types.Content(
                        role=role,
                        parts=[self.types.Part.from_text(msg["content"])]
                    )
                )
        
        # Note: thinking_config is not yet supported in GenerateContentConfig
        # The models still work and may use thinking automatically
        # We'll add explicit config when it's officially supported
        
        # Make the API call
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents
        )
        
        elapsed_time = time.time() - start_time
        self.total_time += elapsed_time
        
        # Extract token count
        tokens = 0
        if hasattr(response, 'usage_metadata'):
            tokens = getattr(response.usage_metadata, 'total_token_count', 0)
        
        self.total_tokens += tokens
        
        # Extract response text
        response_text = response.text if hasattr(response, 'text') else ""
        
        return {
            "response": response_text,
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
            
            # Determine if this is a reasoning model that needs reasoning_effort
            self.is_reasoning_model = any(x in model_name.lower() for x in ['o1', 'gpt-5'])
        except ImportError:
            raise ImportError("openai not installed. Run: pip install openai")
    
    def send_message(self, messages: List[Dict[str, str]], system_prompt: str = "") -> Dict:
        """Send message to OpenAI API."""
        start_time = time.time()
        
        # Add system message if provided (but not for o1 models which don't support system messages)
        api_messages = []
        if system_prompt and not self.model_name.startswith("o1"):
            api_messages.append({"role": "system", "content": system_prompt})
        api_messages.extend(messages)
        
        # Build API call parameters
        api_params = {
            "model": self.model_name,
            "messages": api_messages
        }
        
        # Add reasoning_effort for reasoning models (o1, GPT-5, etc.)
        if self.is_reasoning_model:
            api_params["reasoning_effort"] = "high"
        
        response = self.client.chat.completions.create(**api_params)
        
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
            
            # Check if this is a Claude 4 or 4.5 model (NOT 3.5!)
            # Must check for "claude-sonnet-4", "claude-opus-4", "claude-haiku-4" specifically
            # to avoid matching "claude-3-5-haiku-20241022" (which has "4" in the date)
            model_lower = model_name.lower()
            self.supports_thinking = (
                "claude-sonnet-4" in model_lower or 
                "claude-opus-4" in model_lower or 
                "claude-haiku-4" in model_lower
            )
            
            # Check if this is Opus which may need streaming
            self.is_opus = "opus" in model_lower
        except ImportError:
            raise ImportError("anthropic not installed. Run: pip install anthropic")
    
    def send_message(self, messages: List[Dict[str, str]], system_prompt: str = "", max_retries: int = 5) -> Dict:
        """Send message to Anthropic API with retry logic for overloaded errors."""
        import time as time_module
        
        # Determine max_tokens based on model
        # Claude 4+ models support higher token counts, Claude 3.x has lower limits
        max_tokens = 20000 if self.supports_thinking else 8000
        
        # Build API parameters
        api_params = {
            "model": self.model_name,
            "max_tokens": max_tokens,
            "system": system_prompt if system_prompt else "You are a helpful assistant.",
            "messages": messages
        }
        
        # Add thinking config for Claude 4+ models
        if self.supports_thinking:
            api_params["thinking"] = {
                "type": "enabled",
                "budget_tokens": 16000
            }
        
        # Retry logic for handling 529 (overloaded) errors
        last_exception = None
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                
                # Enable streaming for Opus models to avoid timeout
                if self.is_opus:
                    # Use streaming for Opus to handle long operations
                    full_response = ""
                    with self.client.messages.stream(**api_params) as stream:
                        for text in stream.text_stream:
                            full_response += text
                    
                    elapsed_time = time.time() - start_time
                    self.total_time += elapsed_time
                    
                    # Get usage from the final message
                    message = stream.get_final_message()
                    tokens = message.usage.input_tokens + message.usage.output_tokens
                    self.total_tokens += tokens
                    
                    return {
                        "response": full_response,
                        "tokens": tokens
                    }
                else:
                    # Non-streaming for other models
                    response = self.client.messages.create(**api_params)
                    
                    elapsed_time = time.time() - start_time
                    self.total_time += elapsed_time
                    
                    tokens = response.usage.input_tokens + response.usage.output_tokens
                    self.total_tokens += tokens
                    
                    # Extract text from content blocks (handle both TextBlock and ThinkingBlock)
                    response_text = ""
                    for block in response.content:
                        if hasattr(block, 'text'):
                            response_text += block.text
                        # ThinkingBlocks don't have .text attribute, skip them
                        # (thinking content is internal and not part of the response)
                    
                    return {
                        "response": response_text,
                        "tokens": tokens
                    }
                    
            except Exception as e:
                last_exception = e
                error_str = str(e)
                
                # Check if it's a 529 overloaded error
                if "529" in error_str or "overloaded" in error_str.lower():
                    if attempt < max_retries - 1:
                        # Wait with exponential backoff: 2, 4, 8, 16 seconds
                        wait_time = 2 ** (attempt + 1)
                        print(f"Anthropic API overloaded (529), retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                        time_module.sleep(wait_time)
                        continue
                    else:
                        # Max retries reached
                        raise Exception(f"Anthropic API overloaded after {max_retries} retries: {e}")
                else:
                    # Not a 529 error, raise immediately
                    raise
        
        # If we get here, all retries failed
        raise last_exception


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
        # Set generous timeout for reasoning models (5 minutes)
        self.client = httpx.Client(timeout=300.0)
    
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
        # Set generous timeout for local models (can be slow on CPU)
        self.client = httpx.Client(timeout=300.0)
    
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
        # Set generous timeout for various models (including reasoning models)
        self.client = httpx.Client(timeout=300.0)
    
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

