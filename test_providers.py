"""Test script to validate LLM providers and token counting."""
import os
import sys
import yaml
from typing import Dict, List

# Import providers
from llm.providers import (
    GoogleProvider, OpenAIProvider, AnthropicProvider, XAIProvider
)


def load_model_config() -> Dict:
    """Load model configuration from YAML."""
    with open("config/models.yml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_provider(provider_name: str, provider_class, model_name: str) -> Dict:
    """
    Test a single provider/model combination.
    
    Returns:
        Dict with test results including success status, response, tokens, and metadata
    """
    print(f"\n{'='*80}")
    print(f"Testing: {provider_name} - {model_name}")
    print(f"{'='*80}")
    
    result = {
        "provider": provider_name,
        "model": model_name,
        "success": False,
        "error": None,
        "response": None,
        "tokens": None,
        "token_metadata": None,
        "response_structure": None
    }
    
    try:
        # Initialize provider
        print(f"Initializing {provider_name}...")
        provider = provider_class(model_name)
        
        # Send test message
        print("Sending test message...")
        test_message = [
            {"role": "user", "content": "Return the string 'a' and nothing else in response to this message."}
        ]
        
        response_data = provider.send_message(test_message, system_prompt="")
        
        # Extract results
        response_text = response_data.get("response", "")
        tokens = response_data.get("tokens", 0)
        
        result["success"] = True
        result["response"] = response_text
        result["tokens"] = tokens
        result["token_metadata"] = {
            "total_tokens": provider.total_tokens,
            "total_time": provider.total_time
        }
        
        # Print results
        print(f"\n✓ SUCCESS")
        print(f"Response: {repr(response_text[:100])}")  # First 100 chars
        print(f"Response length: {len(response_text)} characters")
        print(f"Tokens reported: {tokens}")
        print(f"Provider total tokens: {provider.total_tokens}")
        print(f"Provider total time: {provider.total_time:.3f}s")
        
        # Validate expectations
        warnings = []
        
        # Check if response is reasonably short
        if len(response_text) > 50:
            warnings.append(f"Response longer than expected ({len(response_text)} chars)")
        
        # Check token count (expecting small number)
        if tokens == 0:
            warnings.append("Token count is 0 - may not be captured correctly")
        elif tokens > 100:
            warnings.append(f"Token count seems high ({tokens}) for such a simple prompt")
        
        if warnings:
            print("\n⚠ WARNINGS:")
            for warning in warnings:
                print(f"  - {warning}")
        
        return result
        
    except Exception as e:
        result["error"] = str(e)
        print(f"\n✗ FAILED: {e}")
        return result


def test_reasoning_model(provider_name: str, provider_class, model_name: str) -> Dict:
    """
    Test a reasoning model (o1, etc.) with a simple reasoning task.
    
    Returns:
        Dict with test results including reasoning token breakdown
    """
    print(f"\n{'='*80}")
    print(f"Testing REASONING MODEL: {provider_name} - {model_name}")
    print(f"{'='*80}")
    
    result = {
        "provider": provider_name,
        "model": model_name,
        "success": False,
        "error": None,
        "response": None,
        "tokens": None,
        "reasoning_tokens": None,
        "token_metadata": None
    }
    
    try:
        # Initialize provider
        print(f"Initializing {provider_name}...")
        provider = provider_class(model_name)
        
        # Send test message with reasoning requirement
        print("Sending test message (reasoning task)...")
        test_message = [
            {"role": "user", "content": "What is 2+2? Think through it step by step, then respond with just the number."}
        ]
        
        response_data = provider.send_message(test_message, system_prompt="")
        
        # Extract results
        response_text = response_data.get("response", "")
        tokens = response_data.get("tokens", 0)
        
        result["success"] = True
        result["response"] = response_text
        result["tokens"] = tokens
        result["token_metadata"] = {
            "total_tokens": provider.total_tokens,
            "total_time": provider.total_time
        }
        
        # Print results
        print(f"\n✓ SUCCESS")
        print(f"Response: {repr(response_text[:200])}")
        print(f"Response length: {len(response_text)} characters")
        print(f"Total tokens: {tokens}")
        print(f"Provider total time: {provider.total_time:.3f}s")
        
        # Note special configurations for thinking/reasoning models
        if provider_name == "OpenAI" and any(x in model_name.lower() for x in ["o1", "gpt-5"]):
            print("\nNote: Using reasoning_effort='high' for optimal performance")
            print("Reasoning tokens are included in total_tokens")
        elif provider_name == "Anthropic" and ("claude-sonnet-4" in model_name.lower() or "claude-opus-4" in model_name.lower() or "claude-haiku-4" in model_name.lower()):
            print("\nNote: Extended thinking enabled with 16000 token budget")
            if "opus" in model_name.lower():
                print("Streaming enabled for long operations")
            print("Thinking tokens are included in total_tokens")
        elif provider_name == "Google" and ("gemini-3" in model_name.lower() or "gemini-2.5" in model_name.lower()):
            print("\nNote: This model supports extended thinking")
            print("(Explicit config not yet supported in Python SDK, may auto-engage thinking)")
            print("Using newer google-genai library")
        
        return result
        
    except Exception as e:
        result["error"] = str(e)
        print(f"\n✗ FAILED: {e}")
        return result


def main():
    """Main test runner."""
    print("="*80)
    print("LLM Provider Test Suite")
    print("="*80)
    print("\nThis script tests each provider's API connection and token counting.")
    print("Make sure you have the following environment variables set:")
    print("  - GOOGLE_API_KEY")
    print("  - OPENAI_API_KEY")
    print("  - ANTHROPIC_API_KEY")
    print("  - XAI_API_KEY")
    print("\nNote: This will make real API calls and consume a small number of tokens.")
    
    proceed = input("\nProceed with tests? (y/n): ").strip().lower()
    if proceed != 'y':
        print("Aborted.")
        return
    
    # Load model config
    print("\nLoading model configuration...")
    try:
        config = load_model_config()
    except Exception as e:
        print(f"Error loading config: {e}")
        return
    
    # Define which providers to test
    providers_to_test = {
        "google": ("Google", GoogleProvider, config.get("google", [])),
        "openai": ("OpenAI", OpenAIProvider, config.get("openai", [])),
        "anthropic": ("Anthropic", AnthropicProvider, config.get("anthropic", [])),
        "xai": ("xAI", XAIProvider, config.get("xai", []))
    }
    
    # Special handling for reasoning/thinking models
    reasoning_models = [
        "o1", "gpt-5",  # OpenAI reasoning models
        "claude-4", "claude-sonnet-4", "claude-opus-4", "claude-haiku-4",  # Claude 4+ thinking models
        "gemini-3", "gemini-2.5"  # Gemini thinking models
    ]
    
    # Let user select which providers to test
    print("\nAvailable providers:")
    print("1. Google (Gemini)")
    print("2. OpenAI (GPT)")
    print("3. Anthropic (Claude)")
    print("4. xAI (Grok)")
    print("5. All providers")
    
    choice = input("\nWhich provider to test? (1-5): ").strip()
    
    selected_providers = []
    if choice == "1":
        selected_providers = ["google"]
    elif choice == "2":
        selected_providers = ["openai"]
    elif choice == "3":
        selected_providers = ["anthropic"]
    elif choice == "4":
        selected_providers = ["xai"]
    elif choice == "5":
        selected_providers = list(providers_to_test.keys())
    else:
        print("Invalid choice.")
        return
    
    # Ask if they want to test all models or just the first one
    test_all = input("\nTest all models for each provider? (y/n, default=n): ").strip().lower()
    test_all_models = test_all == 'y'
    
    # Run tests
    all_results = []
    
    for provider_key in selected_providers:
        if provider_key not in providers_to_test:
            continue
            
        provider_name, provider_class, models = providers_to_test[provider_key]
        
        if not models:
            print(f"\n⚠ No models configured for {provider_name}")
            continue
        
        # Test models
        models_to_test = models if test_all_models else [models[0]]
        
        for model_info in models_to_test:
            model_name = model_info.get("model")
            
            if not model_name:
                continue
            
            # Check if it's a reasoning model
            is_reasoning = any(rm in model_name for rm in reasoning_models)
            
            if is_reasoning:
                result = test_reasoning_model(provider_name, provider_class, model_name)
            else:
                result = test_provider(provider_name, provider_class, model_name)
            
            all_results.append(result)
            
            # Small delay between tests
            import time
            time.sleep(1)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    successful = [r for r in all_results if r["success"]]
    failed = [r for r in all_results if not r["success"]]
    
    print(f"\nTotal tests: {len(all_results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print("\nFailed tests:")
        for result in failed:
            print(f"  ✗ {result['provider']} - {result['model']}: {result['error']}")
    
    if successful:
        print("\nToken statistics:")
        for result in successful:
            tokens = result.get("tokens", 0)
            print(f"  {result['provider']:15} {result['model']:40} {tokens:4} tokens")
    
    print("\n" + "="*80)
    print("Testing complete!")
    print("="*80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

