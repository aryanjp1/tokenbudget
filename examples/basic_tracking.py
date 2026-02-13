"""Basic token tracking example."""

from tokenbudget import TokenTracker

# Example 1: Track OpenAI usage
print("Example 1: Basic OpenAI Tracking")
print("=" * 50)

try:
    import openai

    tracker = TokenTracker()
    client = tracker.wrap_openai(openai.OpenAI())

    # Make an API call (tracking happens automatically)
    response = client.chat.completions.create(
        model="gpt-4o-mini", messages=[{"role": "user", "content": "What is 2+2?"}]
    )

    print(f"Response: {response.choices[0].message.content}")
    print(f"\nUsage stats:")
    print(f"  Total tokens: {tracker.usage.total_tokens}")
    print(f"  Prompt tokens: {tracker.usage.prompt_tokens}")
    print(f"  Completion tokens: {tracker.usage.completion_tokens}")
    print(f"  Total cost: ${tracker.usage.total_cost_usd:.6f}")
    print(f"  API calls: {tracker.usage.calls}")

except ImportError:
    print("OpenAI not installed. Install with: pip install tokenbudget[openai]")


# Example 2: Track multiple providers
print("\n\nExample 2: Multi-Provider Tracking")
print("=" * 50)

try:
    import anthropic
    import openai

    tracker = TokenTracker()

    # Wrap both clients
    openai_client = tracker.wrap_openai(openai.OpenAI())
    anthropic_client = tracker.wrap_anthropic(anthropic.Anthropic())

    # Make calls to both
    openai_response = openai_client.chat.completions.create(
        model="gpt-4o-mini", messages=[{"role": "user", "content": "Hello"}]
    )

    anthropic_response = anthropic_client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=100,
        messages=[{"role": "user", "content": "Hello"}],
    )

    # View combined stats
    print(f"Total cost across all providers: ${tracker.total_cost_usd:.6f}")
    print(f"Total tokens: {tracker.usage.total_tokens}")

    print("\nPer-provider breakdown:")
    for provider, usage in tracker.usage_by_provider.items():
        print(f"  {provider}: {usage.total_tokens} tokens, ${usage.total_cost_usd:.6f}")

except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install tokenbudget[all]")


# Example 3: Manual tracking for custom providers
print("\n\nExample 3: Custom Provider Tracking")
print("=" * 50)

from tokenbudget import register_model
from tokenbudget.providers.custom import CustomProvider

# Register your custom model
register_model("my-llm-model", input_per_1k=0.001, output_per_1k=0.002, provider="my-llm")

tracker = TokenTracker()

# Define how to extract usage from your API responses
custom = CustomProvider(
    tracker=tracker,
    provider_name="my-llm",
    extract_model=lambda r: r["model"],
    extract_prompt_tokens=lambda r: r["usage"]["input"],
    extract_completion_tokens=lambda r: r["usage"]["output"],
)

# Simulate your API response
mock_response = {"model": "my-llm-model", "usage": {"input": 150, "output": 75}}

# Track it
custom.track(mock_response)

print(f"Custom provider tracked!")
print(f"  Total tokens: {tracker.usage.total_tokens}")
print(f"  Total cost: ${tracker.usage.total_cost_usd:.6f}")
