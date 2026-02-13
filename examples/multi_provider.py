"""Multi-provider tracking and reporting example."""

from tokenbudget import TokenTracker, generate_table_report, export_csv, export_json

print("Multi-Provider Usage Example")
print("=" * 50)

# Create tracker
tracker = TokenTracker()

# Example 1: Simulate mixed provider usage
print("\nSimulating API calls across multiple providers...\n")

# OpenAI calls
tracker.track(model="gpt-4o", prompt_tokens=500, completion_tokens=300, provider="openai")
tracker.track(model="gpt-4o-mini", prompt_tokens=200, completion_tokens=100, provider="openai")
tracker.track(model="gpt-4o-mini", prompt_tokens=150, completion_tokens=75, provider="openai")

# Anthropic calls
tracker.track(model="claude-sonnet-4-5", prompt_tokens=800, completion_tokens=400, provider="anthropic")
tracker.track(model="claude-haiku-4-5", prompt_tokens=300, completion_tokens=150, provider="anthropic")

# Google calls
tracker.track(model="gemini-2.0-flash", prompt_tokens=1000, completion_tokens=500, provider="google")

print("API calls completed!")

# Example 2: Generate table report
print("\n" + "=" * 50)
print("USAGE REPORT")
print("=" * 50)
print(generate_table_report(tracker))

# Example 3: Per-provider breakdown
print("\n" + "=" * 50)
print("DETAILED BREAKDOWN")
print("=" * 50)

for provider, usage in sorted(tracker.usage_by_provider.items()):
    print(f"\n{provider.upper()}:")
    print(f"  Calls: {usage.calls}")
    print(f"  Total tokens: {usage.total_tokens:,}")
    print(f"  Prompt tokens: {usage.prompt_tokens:,}")
    print(f"  Completion tokens: {usage.completion_tokens:,}")
    print(f"  Cost: ${usage.total_cost_usd:.6f}")

# Example 4: Export data
print("\n" + "=" * 50)
print("EXPORTING DATA")
print("=" * 50)

try:
    export_csv(tracker, "usage_report.csv")
    print("SUCCESS: Exported to: usage_report.csv")

    export_json(tracker, "usage_report.json")
    print("SUCCESS: Exported to: usage_report.json")

    # Show JSON content
    import json
    with open("usage_report.json", "r") as f:
        data = json.load(f)
        print(f"\nJSON structure preview:")
        print(f"  - total: {data['total']['calls']} calls, ${data['total']['total_cost_usd']:.6f}")
        print(f"  - by_provider: {len(data['by_provider'])} providers")
        print(f"  - cache_stats: {data['cache_stats']['hits']} hits")

except Exception as e:
    print(f"ERROR: Export error: {e}")

# Example 5: Real-world scenario
print("\n" + "=" * 50)
print("REAL-WORLD SCENARIO")
print("=" * 50)

try:
    import anthropic
    import openai

    # Create new tracker with caching
    real_tracker = TokenTracker(cache="memory")

    # Wrap multiple clients
    openai_client = real_tracker.wrap_openai(openai.OpenAI())
    anthropic_client = real_tracker.wrap_anthropic(anthropic.Anthropic())

    print("\nMaking real API calls...\n")

    # Use OpenAI for quick tasks
    openai_response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "What is 2+2?"}],
    )
    print(f"OpenAI: {openai_response.choices[0].message.content}")

    # Use Anthropic for complex reasoning
    anthropic_response = anthropic_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=150,
        messages=[{"role": "user", "content": "Explain quantum computing in one sentence."}],
    )
    print(f"Anthropic: {anthropic_response.content[0].text}")

    # Show combined report
    print("\n" + generate_table_report(real_tracker))

except ImportError:
    print("\nWARNING: Install providers to run real API calls:")
    print("  pip install tokenbudget[all]")
