"""Budget enforcement examples."""

from tokenbudget import budget, BudgetExceeded, TokenLimitReached, TokenTracker

# Example 1: Budget as context manager
print("Example 1: Budget Context Manager")
print("=" * 50)

tracker = TokenTracker()

try:
    with budget(max_cost_usd=0.01, tracker=tracker) as ctx:
        # Simulate some API calls
        tracker.track(model="gpt-4o-mini", prompt_tokens=100, completion_tokens=50, provider="openai")
        print(f"After first call:")
        print(f"  Current cost: ${ctx.current_usage.total_cost_usd:.6f}")
        print(f"  Remaining budget: ${ctx.remaining_budget:.6f}")

        tracker.track(model="gpt-4o-mini", prompt_tokens=100, completion_tokens=50, provider="openai")
        print(f"\nAfter second call:")
        print(f"  Current cost: ${ctx.current_usage.total_cost_usd:.6f}")
        print(f"  Remaining budget: ${ctx.remaining_budget:.6f}")

    print("\nBudget not exceeded!")

except BudgetExceeded as e:
    print(f"\nERROR: Budget exceeded!")
    print(f"  Current cost: ${e.current_cost:.6f}")
    print(f"  Max allowed: ${e.max_cost:.6f}")


# Example 2: Budget as decorator
print("\n\nExample 2: Budget Decorator")
print("=" * 50)

tracker = TokenTracker()


@budget(max_cost_usd=0.10, max_tokens=10000, tracker=tracker)
def process_documents(docs):
    """Process documents with LLM calls."""
    results = []
    for doc in docs:
        # Simulate API call
        tracker.track(
            model="gpt-4o-mini",
            prompt_tokens=len(doc) * 10,
            completion_tokens=50,
            provider="openai",
        )
        results.append(f"Processed: {doc}")
    return results


try:
    documents = ["doc1", "doc2", "doc3"]
    results = process_documents(documents)
    print(f"Successfully processed {len(results)} documents")
    print(f"Total cost: ${tracker.usage.total_cost_usd:.6f}")
    print(f"Total tokens: {tracker.usage.total_tokens}")

except BudgetExceeded as e:
    print(f"ERROR: Cost limit exceeded: ${e.current_cost:.6f} > ${e.max_cost:.6f}")
except TokenLimitReached as e:
    print(f"ERROR: Token limit exceeded: {e.current_tokens} > {e.max_tokens}")


# Example 3: Token-only limit
print("\n\nExample 3: Token Limit Only")
print("=" * 50)

tracker = TokenTracker()

try:
    with budget(max_tokens=500, tracker=tracker) as ctx:
        # This will work
        tracker.track(model="gpt-4o-mini", prompt_tokens=200, completion_tokens=100, provider="openai")
        print(f"First call OK. Tokens used: {ctx.current_usage.total_tokens}")
        print(f"Remaining tokens: {ctx.remaining_tokens}")

        # This will exceed the limit
        tracker.track(model="gpt-4o-mini", prompt_tokens=200, completion_tokens=100, provider="openai")

except TokenLimitReached as e:
    print(f"\nERROR: Token limit reached!")
    print(f"  Tokens used: {e.current_tokens}")
    print(f"  Max allowed: {e.max_tokens}")


# Example 4: Real OpenAI example with budget
print("\n\nExample 4: Real OpenAI with Budget")
print("=" * 50)

try:
    import openai

    tracker = TokenTracker()
    client = tracker.wrap_openai(openai.OpenAI())

    # Set a very low budget to demonstrate enforcement
    with budget(max_cost_usd=0.001, tracker=tracker) as ctx:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Write a short poem"}],
        )

        print(f"Response: {response.choices[0].message.content}")
        print(f"Cost: ${ctx.current_usage.total_cost_usd:.6f}")

except BudgetExceeded as e:
    print(f"ERROR: Budget exceeded: ${e.current_cost:.6f} > ${e.max_cost:.6f}")
except ImportError:
    print("OpenAI not installed. Install with: pip install tokenbudget[openai]")
