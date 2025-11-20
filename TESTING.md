# Provider Testing Guide

Use `test_providers.py` to validate your API setup and token counting before running expensive game tests.

## Quick Start

```bash
python test_providers.py
```

## What It Tests

For each provider/model combination:

1. ✅ **API Connection**: Can we successfully connect to the API?
2. ✅ **Request/Response**: Does the model respond appropriately?
3. ✅ **Token Counting**: Are tokens being captured from API metadata?
4. ✅ **Token Accuracy**: Are token counts reasonable for the test?

## Test Message

**Non-reasoning models** get:
```
"Return the string 'a' and nothing else in response to this message."
```

**Expected**: Response should be short (ideally just "a"), tokens should be low (~10-50 total including input).

**Reasoning models** (o1-preview, o1-mini) get:
```
"What is 2+2? Think through it step by step, then respond with just the number."
```

**Expected**: Response may include reasoning, tokens will be higher (includes reasoning tokens).

## Running Tests

### Test All Providers

```bash
python test_providers.py
# Select option 5 (All providers)
# Choose whether to test all models or just first one
```

### Test Specific Provider

```bash
python test_providers.py
# Select option 1-4 for specific provider
```

## Expected Output

### Success Case

```
================================================================================
Testing: Google - gemini-2.0-flash-exp
================================================================================
Initializing Google...
Sending test message...

✓ SUCCESS
Response: 'a'
Response length: 1 characters
Tokens reported: 23
Provider total tokens: 23
Provider total time: 0.845s
```

### Failure Case

```
================================================================================
Testing: OpenAI - gpt-4o
================================================================================
Initializing OpenAI...

✗ FAILED: OPENAI_API_KEY environment variable not set
```

## What to Look For

### ✅ Good Signs

- Response is short and follows instructions
- Token count is non-zero
- Token count is reasonable (not suspiciously high/low)
- No errors or warnings

### ⚠️ Warning Signs

- **Token count is 0**: API may not be returning usage data, or we're not parsing it correctly
- **Token count very high**: May indicate context accumulation issue or API returning unexpected format
- **Response is long**: Model not following instructions well (may need prompt engineering)
- **Response structure errors**: Need to update token extraction logic

## Token Count Expectations

### Non-Reasoning Models

| Model Type | Expected Total Tokens |
|------------|----------------------|
| Gemini | 10-40 |
| GPT-4 | 15-50 |
| Claude | 20-60 |
| Grok | 15-50 |

### Reasoning/Thinking Models

| Model | Expected Total Tokens | Configuration |
|-------|----------------------|---------------|
| GPT-5.1 | 50-300+ (includes reasoning) | `reasoning_effort='high'` |
| GPT-5 | 50-300+ (includes reasoning) | `reasoning_effort='high'` |
| o1 | 50-200+ (includes reasoning) | `reasoning_effort='high'` |
| o1-preview | 50-200+ (includes reasoning) | `reasoning_effort='high'` |
| o1-mini | 30-150+ (includes reasoning) | `reasoning_effort='high'` |
| Claude 4.5 Sonnet | 50-300+ (includes thinking) | `thinking enabled, 16000 budget` |
| Claude 4.5 Haiku | 40-250+ (includes thinking) | `thinking enabled, 16000 budget` |
| Claude 4.1 Opus | 60-400+ (includes thinking) | `thinking enabled, 16000 budget, streaming` |
| Gemini 3.0 Pro | 50-300+ | Standard (auto-thinking) |
| Gemini 2.5 Flash | 40-250+ | Standard (auto-thinking) |
| Gemini 2.5 Flash Lite | 30-200+ | Standard (auto-thinking) |

**Note**: All thinking/reasoning tokens are included in the total token count reported by the APIs.

## Troubleshooting

### "Token count is 0"

**Possible causes:**
1. API not returning usage metadata
2. Token extraction code needs updating for new API format
3. Model doesn't support usage reporting

**Fix**: Check the provider's API documentation and update token extraction in `llm/providers.py`.

### "'ThinkingBlock' object has no attribute 'text'"

**Cause**: Claude 4+ models with extended thinking return multiple content block types (TextBlock and ThinkingBlock). ThinkingBlock contains internal reasoning and doesn't have a `.text` attribute.

**Fix**: Already handled - the code now iterates through content blocks and extracts only TextBlock content.

### "Streaming is required for operations..."

**Cause**: Some models (like Claude 4.1 Opus) require streaming for operations that may take longer than 10 minutes.

**Fix**: Already handled - Opus models automatically use streaming mode.

### "Error code: 529 - Overloaded"

**Cause**: Anthropic's API is temporarily over capacity.

**Fix**: Already handled - automatic retry with exponential backoff (2, 4, 8, 16 seconds) up to 5 attempts. You'll see a message like:
```
Anthropic API overloaded (529), retrying in 4s... (attempt 2/5)
```

### "Extra inputs are not permitted" (Google thinking_config)

**Cause**: The `google-genai` library's `GenerateContentConfig` doesn't yet accept `thinking_config` as a parameter.

**Current Status**: Models work without explicit thinking configuration. They may automatically use thinking based on task complexity. We'll add explicit config when the Python SDK supports it.

### API Key Errors

Make sure environment variables are set:

```bash
# Windows CMD
set GOOGLE_API_KEY=your_key_here
set OPENAI_API_KEY=your_key_here
set ANTHROPIC_API_KEY=your_key_here
set XAI_API_KEY=your_key_here

# Windows PowerShell
$env:GOOGLE_API_KEY="your_key_here"
$env:OPENAI_API_KEY="your_key_here"
$env:ANTHROPIC_API_KEY="your_key_here"
$env:XAI_API_KEY="your_key_here"

# Linux/Mac
export GOOGLE_API_KEY=your_key_here
export OPENAI_API_KEY=your_key_here
export ANTHROPIC_API_KEY=your_key_here
export XAI_API_KEY=your_key_here
```

### Model Not Found Errors

The model may not be available in your region or subscription. Try:
1. Checking the provider's documentation for available models
2. Testing with a different model from the same provider
3. Updating `config/models.yml` with correct model names

## Cost Estimate

Each test uses approximately:
- Input: ~20 tokens
- Output: ~5-50 tokens (non-reasoning) or 50-200+ (reasoning)

**Estimated cost per test:**
- Gemini: ~$0.0001-0.0005
- GPT-4o: ~$0.0001-0.0010
- Claude: ~$0.0002-0.0015
- Grok: ~$0.0001-0.0005 (estimated)

**Total for all providers/models** (if testing all):
- ~30 model tests × ~$0.0005 average = **~$0.015-0.05 total**

Very affordable for validation!

