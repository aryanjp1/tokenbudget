# TokenBudget

**Stop bleeding money on LLM API calls.**

A lightweight Python library for tracking tokens, managing costs, and enforcing budgets across all major LLM providers.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/tokenbudget.svg)](https://badge.fury.io/py/tokenbudget)

---

## The Problem

You're building with LLMs and:
- Costs spiral out of control with no visibility
- No idea which API calls are eating your budget
- Production bills that make you cry
- Clunky observability platforms that require external services

**There's no simple `pip install` library that just works.**

## The Solution

```python
from tokenbudget import TokenTracker, budget

tracker = TokenTracker()
client = tracker.wrap_openai(openai.OpenAI())

# Every call is tracked automatically
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}]
)

print(tracker.usage)
# Usage(total_tokens=25, total_cost_usd=0.000375, calls=1)
```

That's it. No platforms, no external services, no configuration.

---

## Features

**Token Tracking** - Automatic tracking for OpenAI, Anthropic, Google
**Cost Calculation** - Built-in pricing database (always up-to-date)
**Budget Enforcement** - Decorators to prevent overspending
**Response Caching** - Save money with zero-cost cached responses
**Usage Reports** - Beautiful tables + CSV/JSON exports
**Multi-Provider** - One tracker for all your LLM calls
**Thread-Safe** - Works seamlessly in concurrent applications
**Async Support** - Works with async clients out of the box

---

## Installation

```bash
# Basic installation
pip install tokenbudget

# With OpenAI support
pip install tokenbudget[openai]

# With Anthropic support
pip install tokenbudget[anthropic]

# With everything
pip install tokenbudget[all]
```

---

## Quick Examples

### 1. Basic Tracking

```python
from tokenbudget import TokenTracker
import openai

tracker = TokenTracker()
client = tracker.wrap_openai(openai.OpenAI())

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "What is 2+2?"}]
)

print(f"Tokens: {tracker.usage.total_tokens}")
print(f"Cost: ${tracker.usage.total_cost_usd:.6f}")
```

### 2. Budget Enforcement

```python
from tokenbudget import budget, BudgetExceeded

@budget(max_cost_usd=1.00, max_tokens=50000)
def my_llm_pipeline(data):
    # All LLM calls inside are tracked
    # Raises BudgetExceeded if limit is hit
    result = process_with_llm(data)
    return result

# Or as context manager
with budget(max_cost_usd=0.50) as ctx:
    response = client.chat.completions.create(...)
    print(f"Remaining: ${ctx.remaining_budget:.4f}")
```

### 3. Multi-Provider Tracking

```python
import openai
import anthropic
from tokenbudget import TokenTracker

tracker = TokenTracker()

# Track OpenAI
openai_client = tracker.wrap_openai(openai.OpenAI())
openai_client.chat.completions.create(model="gpt-4o", ...)

# Track Anthropic
anthropic_client = tracker.wrap_anthropic(anthropic.Anthropic())
anthropic_client.messages.create(model="claude-sonnet-4-5", ...)

# Combined reporting
print(f"Total cost: ${tracker.total_cost_usd:.4f}")
print(tracker.usage_by_provider)
```

### 4. Response Caching

```python
tracker = TokenTracker(cache="memory")
client = tracker.wrap_openai(openai.OpenAI())

# First call - costs money
response1 = client.chat.completions.create(model="gpt-4o", ...)

# Identical call - FREE (cached)
response2 = client.chat.completions.create(model="gpt-4o", ...)

stats = tracker.cache_stats
print(f"Saved: ${stats.saved_cost_usd:.4f}")
```

### 5. Usage Reports

```python
from tokenbudget import generate_table_report

print(generate_table_report(tracker))

# Output:
# ┌─────────────────────────────────────┐
# │ TokenBudget Usage Report            │
# ├─────────────────────────────────────┤
# │ Provider   │ Calls │ Tokens │ Cost  │
# │ openai     │   15  │ 12.3k  │ $0.24 │
# │ anthropic  │    8  │  8.1k  │ $0.18 │
# ├─────────────────────────────────────┤
# │ Total      │   23  │ 20.4k  │ $0.42 │
# └─────────────────────────────────────┘

# Export to CSV/JSON
tracker.export_csv("usage.csv")
tracker.export_json("usage.json")
```

---

## Supported Models

**OpenAI**
`gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `gpt-4`, `gpt-3.5-turbo`, `o1`, `o1-mini`, `o3-mini`

**Anthropic**
`claude-opus-4-5`, `claude-sonnet-4-5`, `claude-haiku-4-5`, `claude-3-5-sonnet`, `claude-3-opus`

**Google**
`gemini-2.0-flash`, `gemini-2.0-pro`, `gemini-1.5-pro`, `gemini-1.5-flash`

Need a custom model? Easy:

```python
from tokenbudget import register_model

register_model(
    "my-custom-model",
    input_per_1k=0.001,
    output_per_1k=0.002,
    provider="custom"
)
```

---

## API Reference

### TokenTracker

```python
tracker = TokenTracker(cache=None)  # cache: "memory", "disk", or None
```

**Methods:**
- `wrap_openai(client)` - Wrap OpenAI client
- `wrap_anthropic(client)` - Wrap Anthropic client
- `track(model, prompt_tokens, completion_tokens, provider)` - Manual tracking
- `reset()` - Reset all statistics

**Properties:**
- `usage` - Overall usage stats
- `usage_by_provider` - Per-provider breakdown
- `total_cost_usd` - Total cost across all calls
- `cache_stats` - Cache hit/miss statistics

### Budget Enforcement

```python
@budget(max_cost_usd=None, max_tokens=None, tracker=None)
def my_function():
    ...

# Or as context manager
with budget(max_cost_usd=1.0) as ctx:
    ...
    print(ctx.remaining_budget)
    print(ctx.current_usage)
```

**Exceptions:**
- `BudgetExceeded` - Cost limit exceeded
- `TokenLimitReached` - Token limit exceeded

### Pricing

```python
from tokenbudget import get_price, register_model, calculate_cost

# Get model pricing
price = get_price("gpt-4o")
print(price.input_per_1k, price.output_per_1k)

# Calculate cost
cost = calculate_cost("gpt-4o", input_tokens=1000, output_tokens=500)

# Register custom model
register_model("my-model", input_per_1k=0.001, output_per_1k=0.002)
```

### Reports

```python
from tokenbudget import generate_table_report, export_csv, export_json

# Pretty table
print(generate_table_report(tracker))

# Export
export_csv(tracker, "usage.csv")
export_json(tracker, "usage.json")
```

---

## Custom Providers

Support any LLM provider:

```python
from tokenbudget.providers.custom import CustomProvider

custom = CustomProvider(
    tracker=tracker,
    provider_name="my-llm-service",
    extract_model=lambda r: r["model"],
    extract_prompt_tokens=lambda r: r["usage"]["input"],
    extract_completion_tokens=lambda r: r["usage"]["output"],
)

# Track your custom response
custom.track(api_response)
```

---

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Author

Built by a developer tired of surprise LLM bills.

If this saved you money, consider starring the repo.
