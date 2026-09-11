#!/usr/bin/env python3
"""
PyTokenCalc v0.7 Quick Start Examples

Shows how to:
1. Count tokens for different models
2. Use intelligent routing (local vs cached API)
3. Batch count tokens
4. Check cache performance
"""

from pytokencalc.tokenizers import TokenCounterRegistry


def single_count_example():
    """Demonstrate basic token counting"""
    print("\n" + "=" * 60)
    print("SINGLE TOKEN COUNT EXAMPLE")
    print("=" * 60)

    registry = TokenCounterRegistry()

    text = "Write me a Python function that calculates the Fibonacci sequence using dynamic programming."

    # Count tokens for a model
    result = registry.count_tokens("gpt-4o", text)

    print(f"\nText: {text}")
    print(f"Model: gpt-4o")
    print(f"Tokens: {result.input_tokens}")
    print(f"Source: {result.source}")  # 'local' for GPT, 'api' for Claude, etc.
    print(f"Latency: {result.latency_ms:.1f}ms")


def multi_model_example():
    """Count tokens across multiple providers"""
    print("\n" + "=" * 60)
    print("MULTI-MODEL TOKEN COUNTING")
    print("=" * 60)

    registry = TokenCounterRegistry()

    text = "Your prompt here: Analyze this data and provide insights."

    # Count for different models
    models = [
        "gpt-4o",              # OpenAI (local with tiktoken)
        "gpt-4o-mini",         # OpenAI mini (local)
        "llama-70b",           # Open-source (local or API)
        "claude-3-5-sonnet",   # Anthropic (API, cached)
        "gemini-2-flash",      # Google (API, cached)
    ]

    print(f"\nText: {text[:40]}...")
    print(f"\n{'Model':<25} {'Tokens':>8} {'Source':<8} {'Latency':>10}")
    print("-" * 55)

    for model in models:
        try:
            result = registry.count_tokens(model, text)
            print(f"{model:<25} {result.input_tokens:>8} {result.source:<8} {result.latency_ms:>9.1f}ms")
        except Exception as e:
            print(f"{model:<25} {'ERROR':<8} {str(e)[:30]}")


def caching_example():
    """Demonstrate automatic caching behavior"""
    print("\n" + "=" * 60)
    print("CACHING EXAMPLE - 70-80% Fewer API Calls")
    print("=" * 60)

    registry = TokenCounterRegistry()

    text = "Python function for Fibonacci sequence"
    model = "gpt-4o"

    # First call: not cached
    print(f"\nFirst call to count_tokens('{model}', '{text}'):")
    result1 = registry.count_tokens(model, text)
    print(f"  Tokens: {result1.input_tokens}")
    print(f"  Source: {result1.source}")
    print(f"  Latency: {result1.latency_ms:.2f}ms")
    print(f"  Cached: {result1.cached}")

    # Second call: CACHED (instant!)
    print(f"\nSecond call (same model + text):")
    result2 = registry.count_tokens(model, text)
    print(f"  Tokens: {result2.input_tokens}")
    print(f"  Source: {result2.source}")
    print(f"  Latency: {result2.latency_ms:.2f}ms (CACHED!)")
    print(f"  Cached: {result2.cached}")

    # Verify identical results
    assert result1.input_tokens == result2.input_tokens
    print(f"\n✅ Results identical: {result1.input_tokens} == {result2.input_tokens}")


def batch_count_example():
    """Batch count tokens for multiple prompts"""
    print("\n" + "=" * 60)
    print("BATCH TOKEN COUNTING")
    print("=" * 60)

    registry = TokenCounterRegistry()

    # Batch of different models + prompts
    batch = [
        {"model": "gpt-4o", "text": "What is machine learning?"},
        {"model": "claude-3-5-sonnet", "text": "Explain neural networks"},
        {"model": "llama-70b", "text": "Define deep learning"},
    ]

    print(f"\nCounting tokens for {len(batch)} prompts:\n")
    print(f"{'Model':<25} {'Text':<30} {'Tokens':>8}")
    print("-" * 65)

    results = registry.count_batch(batch)

    for item, result in zip(batch, results):
        text_preview = item["text"][:25] + "..." if len(item["text"]) > 25 else item["text"]
        print(f"{item['model']:<25} {text_preview:<30} {result.input_tokens:>8}")


def smart_routing_example():
    """Demonstrate smart routing (local vs API)"""
    print("\n" + "=" * 60)
    print("SMART ROUTING: LOCAL vs API")
    print("=" * 60)

    registry = TokenCounterRegistry()
    text = "Sample text for token counting"

    print(f"\nText: {text}\n")
    print("Smart Routing Strategy:")
    print("  • Local models (GPT, Llama): 5-10ms (instant, no API calls)")
    print("  • API models (Claude, Gemini): 200ms first, 0-1ms cached\n")

    print(f"{'Model':<25} {'Strategy':<20} {'Latency':>10} {'Type':<8}")
    print("-" * 65)

    models = {
        "gpt-4o": ("Local (tiktoken)", "5-10ms"),
        "llama-70b": ("Local (HF transformers)", "8-15ms"),
        "claude-3-5-sonnet": ("Cached API", "200ms→1ms"),
        "gemini-2-flash": ("Cached API", "200ms→1ms"),
    }

    for model, (strategy, latency) in models.items():
        result = registry.count_tokens(model, text)
        print(f"{model:<25} {strategy:<20} {result.latency_ms:>9.1f}ms {result.source:<8}")


def use_case_example():
    """Real-world use case: Monitor token usage"""
    print("\n" + "=" * 60)
    print("USE CASE: Monitor Token Usage Per Request")
    print("=" * 60)

    registry = TokenCounterRegistry()

    def llm_request(model: str, prompt: str) -> dict:
        """Simulate an LLM request and log token usage"""
        # Count tokens BEFORE calling the API
        token_result = registry.count_tokens(model, prompt)

        # (In real usage, you'd call the LLM API here)
        # response = llm_api.call(model, prompt)

        return {
            "model": model,
            "prompt_tokens": token_result.input_tokens,
            "prompt_preview": prompt[:40] + "..." if len(prompt) > 40 else prompt,
        }

    # Simulate multiple requests
    requests = [
        ("gpt-4o", "Explain quantum computing"),
        ("claude-3-5-sonnet", "How does photosynthesis work?"),
        ("llama-70b", "What is recursion in programming?"),
    ]

    print("\nTracking token usage across requests:\n")
    print(f"{'Model':<25} {'Prompt':<45} {'Tokens':>8}")
    print("-" * 80)

    total_tokens = 0
    for model, prompt in requests:
        result = llm_request(model, prompt)
        print(f"{result['model']:<25} {result['prompt_preview']:<45} {result['prompt_tokens']:>8}")
        total_tokens += result['prompt_tokens']

    print("-" * 80)
    print(f"{'TOTAL':<25} {'':<45} {total_tokens:>8}")


if __name__ == "__main__":
    print("\n🧮 PyTokenCalc v0.7 Quick Start Examples")
    print("Unified token counting across 20+ LLM providers\n")

    single_count_example()
    multi_model_example()
    smart_routing_example()
    caching_example()
    batch_count_example()
    use_case_example()

    print("\n" + "=" * 60)
    print("✅ All examples completed!")
    print("=" * 60)
    print("\n📚 Next steps:")
    print("  • Read README.md for API reference")
    print("  • Check docs/archive/ADDING_PROVIDERS_v0.7.md (historical) or CUSTOM_PROVIDERS.md to add new tokenizers")
    print("  • Build custom analytics on top of PyTokenCalc's token data")
