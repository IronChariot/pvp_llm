# LLM Provider Implementation Details

This document explains how each provider is implemented and any special handling required.

## Provider-Specific Features

### Google (Gemini)

**API**: Google GenAI (`google.genai`) - newer SDK
**Token Counting**: From `response.usage_metadata.total_token_count`

**Extended Thinking Support**:

Gemini 3.0 Pro, 2.5 Flash, and 2.5 Flash Lite have extended thinking capabilities. However, the Python SDK's `GenerateContentConfig` doesn't yet accept `thinking_config` as a parameter (validation error: "Extra inputs are not permitted").

The models may still use thinking automatically based on the task complexity. Explicit thinking configuration will be added when officially supported in the Python SDK.

**Current Implementation**:
```python
from google import genai
from google.genai import types

client = genai.Client(api_key=api_key)
response = client.models.generate_content(
    model=model_name,
    contents=contents
)
```

**Notes**:
- Uses `google.genai.Client` (newer library, replaces `google.generativeai`)
- Requires `pip install google-genai` (not `google-generativeai`)
- System prompts are prepended to the first user message
- Thinking tokens (when used) are included in total count
- Generally fast and cost-effective
- Models may automatically engage thinking for complex tasks

### OpenAI (GPT)

**API**: OpenAI Chat Completions
**Token Counting**: From `response.usage.total_tokens`

**Special Handling**:

#### Reasoning Models (o1, GPT-5, GPT-5.1)
These models have extended thinking capabilities and require special parameters:

1. **`reasoning_effort='high'`**: Automatically set for models containing "o1" or "gpt-5" in the name
   - Without this parameter, reasoning defaults to 'none'!
   - 'high' maximizes the model's thinking capability

2. **No System Messages**: o1 models don't support system messages
   - System prompts are skipped for models starting with "o1"
   - For GPT-5, system messages are supported

3. **Token Breakdown**:
   - `response.usage.total_tokens` includes reasoning tokens
   - `response.usage.completion_tokens_details.reasoning_tokens` shows reasoning-only count
   - Currently we track total tokens (which is what you're billed for)

**Implementation**:
```python
# Auto-detection
self.is_reasoning_model = any(x in model_name.lower() for x in ['o1', 'gpt-5'])

# API call
if self.is_reasoning_model:
    api_params["reasoning_effort"] = "high"
```

### Anthropic (Claude)

**API**: Anthropic Messages API
**Token Counting**: From `response.usage.input_tokens + response.usage.output_tokens`

**Special Handling**:

#### Claude 4+ Models (Extended Thinking)
Claude 4.5 Sonnet, Claude 4.5 Haiku, and Claude 4.1 Opus support extended thinking:

```python
api_params = {
    "thinking": {
        "type": "enabled",
        "budget_tokens": 16000
    },
    "max_tokens": 20000
}
```

**Auto-detection**: Models containing "claude-sonnet-4", "claude-opus-4", or "claude-haiku-4"
- ⚠️ Note: Must match exactly to avoid false positives (e.g., "claude-3-5-haiku-20241022" has "4" in the date)

**Response Handling**:
When extended thinking is enabled, responses contain multiple content blocks:
- `TextBlock`: Regular response text (has `.text` attribute)
- `ThinkingBlock`: Internal reasoning (no `.text` attribute, not included in output)

We extract only the TextBlock content for the response.

**Retry Logic for Overloaded Errors**:
Implements automatic retry with exponential backoff for 529 (overloaded) errors:
```python
for attempt in range(max_retries):
    try:
        response = client.messages.create(**api_params)
        break
    except Exception as e:
        if "529" in str(e) or "overloaded" in str(e).lower():
            wait_time = 2 ** (attempt + 1)  # 2, 4, 8, 16 seconds
            time.sleep(wait_time)
            continue
```
- Max 5 retries with exponential backoff
- Prevents game interruption due to temporary capacity issues

**Streaming for Opus**:
Claude 4.1 Opus requires streaming for long operations:
```python
with client.messages.stream(**api_params) as stream:
    for text in stream.text_stream:
        full_response += text
```

**Implementation**:
- `max_tokens`: 20000 for Claude 4+, 8000 for Claude 3.x
- Thinking budget: 16000 tokens for deep reasoning
- Thinking tokens are included in total usage
- Streaming automatically enabled for Opus models

**Notes**:
- Uses separate system parameter (not in messages array)
- Provides detailed token breakdown (input vs output)
- Claude 3.x models don't support extended thinking parameter
- Claude 4+ automatically uses thinking when beneficial within the budget

### xAI (Grok)

**API**: xAI Chat Completions (OpenAI-compatible)
**Token Counting**: From `response["usage"]["total_tokens"]`

**Notes**:
- Similar to OpenAI API format
- Uses HTTPS client (httpx)
- Base URL: https://api.x.ai/v1

### Ollama (Local)

**API**: Ollama Local HTTP API
**Token Counting**: From `response["eval_count"] + response["prompt_eval_count"]`

**Notes**:
- Runs locally (default: http://localhost:11434)
- Token counts may not always be available
- No API key required
- Model must be pulled first: `ollama pull model-name`

### OpenRouter (Unified)

**API**: OpenRouter (multi-provider gateway)
**Token Counting**: From `response["usage"]["total_tokens"]`

**Notes**:
- Provides access to models from multiple providers
- Uses provider-specific model names (e.g., "anthropic/claude-3.5-sonnet")
- Billing is per-provider
- Useful for accessing models not directly available

## Model Detection Logic

### Thinking/Reasoning Models

Models are automatically detected and configured based on their names:

#### OpenAI Reasoning Models
Detected if name contains: `"o1"` or `"gpt-5"`
- **Configuration**: `reasoning_effort='high'`
- **System messages**: Disabled for o1 models only
- **Examples**: o1, o1-preview, o1-mini, gpt-5, gpt-5.1

#### Anthropic Extended Thinking Models
Detected if name contains: `"claude-4"`, `"claude-sonnet-4"`, `"claude-opus-4"`, or `"claude-haiku-4"`
- **Configuration**: `thinking={"type": "enabled", "budget_tokens": 16000}`
- **Max tokens**: Increased to 20000
- **Examples**: Claude 4.5 Sonnet, Claude 4.5 Haiku, Claude 4.1 Opus

#### Google Thinking Models
**Gemini Thinking Models** - Detected if name contains: `"gemini-3"` or `"gemini-2.5"`
- **Configuration**: Standard (extended thinking config pending SDK support)
- **Examples**: gemini-3-pro-preview, gemini-2.5-flash, gemini-2.5-flash-lite
- **Note**: Thinking configuration will be added when officially documented in the Python SDK

When detected, special handling is applied:
- Test suite: Uses reasoning-specific test prompt
- Token counting: Includes thinking/reasoning tokens
- Documentation: Marked with thinking/reasoning capabilities

## Adding a New Provider

To add a new LLM provider:

1. **Create provider class** in `llm/providers.py`:
```python
class NewProvider(LLMBase):
    def __init__(self, model_name: str = "default-model"):
        super().__init__(model_name)
        # Initialize API client
        
    def send_message(self, messages: List[Dict[str, str]], system_prompt: str = "") -> Dict:
        # Implement API call
        # Return {"response": str, "tokens": int}
```

2. **Add to model config** in `config/models.yml`:
```yaml
newprovider:
  - name: "Model Name"
    model: "model-id"
```

3. **Update main.py** to include the provider in the selection menu

4. **Add tests** in `test_providers.py`

5. **Document** any special requirements or features

## Token Counting Best Practices

1. **Always use API metadata**: Never estimate tokens client-side
2. **Include all tokens**: Input + output + reasoning (if applicable)
3. **Handle missing data**: Default to 0 if usage data not available
4. **Log discrepancies**: Warn if token count seems wrong
5. **Test regularly**: Use `test_providers.py` to validate

## API Key Management

All providers use environment variables for API keys:

```bash
GOOGLE_API_KEY      # Google AI Studio
OPENAI_API_KEY      # OpenAI Platform
ANTHROPIC_API_KEY   # Anthropic Console
XAI_API_KEY         # xAI Platform
OPENROUTER_API_KEY  # OpenRouter Dashboard
OLLAMA_BASE_URL     # Optional, defaults to localhost
```

**Security**:
- Never commit API keys to version control
- Use `.env` files locally (added to `.gitignore`)
- Use secure secret management in production

## Common Issues

### "Token count is 0"
**Cause**: API not returning usage data or parsing error
**Fix**: Check API response structure and update token extraction

### "Model not found"
**Cause**: Model name incorrect or not available in region
**Fix**: Verify model name in provider documentation

### "Rate limit exceeded"
**Cause**: Too many requests too quickly
**Fix**: Add delays between requests or upgrade API tier

### "Invalid API key"
**Cause**: Environment variable not set or incorrect
**Fix**: Double-check key is set correctly: `echo %OPENAI_API_KEY%` (Windows) or `echo $OPENAI_API_KEY` (Unix)

