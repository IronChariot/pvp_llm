# Model Configuration Guide

The `config/models.yml` file defines the available models for each provider. This makes it easy to add new models as they are released without modifying the code.

## File Format

```yaml
provider_key:
  - name: "Human-readable model name"
    model: "actual-model-identifier"
  - name: "Another model"
    model: "model-id"
```

## Provider Keys

- `google` - Google AI Studio (Gemini models)
- `openai` - OpenAI API
- `anthropic` - Anthropic API (Claude models)
- `xai` - xAI API (Grok models)
- `ollama` - Ollama (local models)
- `openrouter` - OpenRouter (unified API)

## How It Works

When you select a provider in the CLI:

1. The framework loads `config/models.yml`
2. Shows a numbered list of available models for that provider
3. You select by entering a number
4. You can also choose "Custom" to enter any model name manually

### Example Flow

```
=== Select Model for Team A ===
1. Google (Gemini)
2. OpenAI (GPT)
...
Enter your choice (1-7): 1

Available Google models:
1. Gemini 2.0 Flash (Experimental)
2. Gemini 1.5 Pro
3. Gemini 1.5 Flash
4. Gemini 1.0 Pro
5. Custom (enter model name manually)

Select model (1-5): 1
Selected: Gemini 2.0 Flash (Experimental) (gemini-2.0-flash-exp)
```

## Adding New Models

When a provider releases a new model, simply edit `config/models.yml`:

```yaml
google:
  - name: "Gemini 2.0 Pro (NEW!)"
    model: "gemini-2.0-pro"
  - name: "Gemini 2.0 Flash (Experimental)"
    model: "gemini-2.0-flash-exp"
  # ... existing models
```

No code changes needed!

## Current Models (as of November 2025)

### Google (Gemini)
- Gemini 2.0 Flash (Experimental)
- Gemini 1.5 Pro
- Gemini 1.5 Flash
- Gemini 1.0 Pro

### OpenAI
- GPT-4o
- GPT-4o Mini
- GPT-4 Turbo
- GPT-3.5 Turbo
- o1-preview
- o1-mini

### Anthropic (Claude)
- Claude 3.5 Sonnet (2024-10-22)
- Claude 3.5 Sonnet (2024-06-20)
- Claude 3 Opus
- Claude 3 Sonnet
- Claude 3 Haiku

### xAI (Grok)
- Grok Beta
- Grok 2 (Latest)
- Grok 2

### Ollama (Local)
- Llama 3.3 70B
- Llama 3.2 3B
- Llama 3.2 1B
- Llama 3.1 8B
- Qwen 2.5 7B
- Mistral 7B
- Gemma 2 9B
- DeepSeek R1 7B

### OpenRouter
- Anthropic: Claude 3.5 Sonnet
- OpenAI: GPT-4o
- Google: Gemini 2.0 Flash (Experimental)
- Google: Gemini Flash 1.5
- Meta: Llama 3.3 70B
- Anthropic: Claude 3 Opus
- DeepSeek: R1
- Qwen: QwQ 32B

## Tips

1. **Keep it updated**: When you hear about a new model, add it to `config/models.yml`
2. **Use descriptive names**: The `name` field should be clear and include version info
3. **Verify model IDs**: Make sure the `model` field matches the exact identifier the API expects
4. **Test first**: Use the Dummy option to test new game setups before spending tokens

