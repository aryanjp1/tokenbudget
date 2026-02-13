"""Response caching examples."""

from tokenbudget import TokenTracker

# Example 1: In-memory caching
print("Example 1: In-Memory Caching")
print("=" * 50)

try:
    import openai

    # Enable in-memory cache
    tracker = TokenTracker(cache="memory")
    client = tracker.wrap_openai(openai.OpenAI())

    # First call - cache miss
    print("Making first call...")
    response1 = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "What is the capital of France?"}],
    )

    print(f"Response: {response1.choices[0].message.content}")
    print(f"Cost: ${tracker.usage.total_cost_usd:.6f}")

    # Second identical call - cache hit (zero cost!)
    print("\nMaking identical second call...")
    response2 = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "What is the capital of France?"}],
    )

    print(f"Response: {response2.choices[0].message.content}")
    print(f"Total cost: ${tracker.usage.total_cost_usd:.6f}")

    # Check cache statistics
    stats = tracker.cache_stats
    print(f"\n Cache Statistics:")
    print(f"  Hits: {stats.hits}")
    print(f"  Misses: {stats.misses}")
    print(f"  Tokens saved: {stats.saved_tokens}")
    print(f"  Cost saved: ${stats.saved_cost_usd:.6f}")

except ImportError:
    print("OpenAI not installed. Install with: pip install tokenbudget[openai]")


# Example 2: Disk caching (persistent across runs)
print("\n\nExample 2: Disk Caching")
print("=" * 50)

try:
    import openai

    # Enable disk cache
    tracker = TokenTracker(cache="disk")
    client = tracker.wrap_openai(openai.OpenAI())

    print("Making call with disk cache...")
    response = client.chat.completions.create(
        model="gpt-4o-mini", messages=[{"role": "user", "content": "Hello!"}]
    )

    print(f"Response: {response.choices[0].message.content}")
    print(f"Cost: ${tracker.usage.total_cost_usd:.6f}")

    stats = tracker.cache_stats
    print(f"\n Cache Statistics:")
    print(f"  Hits: {stats.hits}")
    print(f"  Misses: {stats.misses}")
    if stats.saved_cost_usd > 0:
        print(f"  Cost saved: ${stats.saved_cost_usd:.6f}")

except ImportError:
    print("OpenAI not installed. Install with: pip install tokenbudget[openai]")


# Example 3: Compare caching savings
print("\n\nExample 3: Caching Savings Demo")
print("=" * 50)

# Simulate repeated queries
queries = [
    "What is 2+2?",
    "What is the capital of France?",
    "What is 2+2?",  # Duplicate
    "What is the capital of Spain?",
    "What is the capital of France?",  # Duplicate
    "What is 2+2?",  # Duplicate
]

tracker = TokenTracker(cache="memory")

print(f"Processing {len(queries)} queries (some duplicates)...\n")

for i, query in enumerate(queries, 1):
    # Simulate API call
    is_duplicate = queries[:i-1].count(query) > 0

    if is_duplicate:
        # Cache hit - no cost
        tracker.record_cache_hit(saved_tokens=150, saved_cost=0.0001)
        print(f"{i}. '{query}' -> [CACHED] Cache hit!")
    else:
        # Cache miss - incur cost
        tracker.record_cache_miss()
        tracker.track(model="gpt-4o-mini", prompt_tokens=100, completion_tokens=50, provider="openai")
        print(f"{i}. '{query}' -> [API] API call")

stats = tracker.cache_stats
print(f"\n Final Statistics:")
print(f"  Total queries: {len(queries)}")
print(f"  API calls made: {tracker.usage.calls}")
print(f"  Cache hits: {stats.hits}")
print(f"  Actual cost: ${tracker.usage.total_cost_usd:.6f}")
print(f"  Saved cost: ${stats.saved_cost_usd:.6f}")
print(f"  Total saved: {stats.saved_cost_usd / (tracker.usage.total_cost_usd + stats.saved_cost_usd) * 100:.1f}%")
