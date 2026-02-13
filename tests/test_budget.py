"""Tests for budget enforcement."""

import pytest

from tokenbudget import budget, BudgetContext, BudgetExceeded, TokenLimitReached, TokenTracker


def test_budget_context_manager():
    """Test budget as context manager."""
    tracker = TokenTracker()

    with budget(max_cost_usd=1.0, tracker=tracker) as ctx:
        tracker.track(model="gpt-4o", prompt_tokens=100, completion_tokens=50, provider="openai")

        assert ctx.current_usage.total_tokens == 150
        assert ctx.remaining_budget is not None
        assert ctx.remaining_budget < 1.0


def test_budget_exceeded():
    """Test BudgetExceeded exception."""
    tracker = TokenTracker()

    with pytest.raises(BudgetExceeded) as exc_info:
        with budget(max_cost_usd=0.001, tracker=tracker):
            # This should exceed the budget
            tracker.track(
                model="gpt-4o", prompt_tokens=1000, completion_tokens=1000, provider="openai"
            )

    assert exc_info.value.current_cost > 0.001
    assert exc_info.value.max_cost == 0.001


def test_token_limit_exceeded():
    """Test TokenLimitReached exception."""
    tracker = TokenTracker()

    with pytest.raises(TokenLimitReached) as exc_info:
        with budget(max_tokens=100, tracker=tracker):
            tracker.track(
                model="gpt-4o", prompt_tokens=100, completion_tokens=50, provider="openai"
            )

    assert exc_info.value.current_tokens == 150
    assert exc_info.value.max_tokens == 100


def test_budget_decorator():
    """Test budget as decorator."""
    tracker = TokenTracker()

    @budget(max_cost_usd=1.0, tracker=tracker)
    def process_with_llm():
        tracker.track(model="gpt-4o", prompt_tokens=100, completion_tokens=50, provider="openai")
        return "success"

    result = process_with_llm()
    assert result == "success"
    assert tracker.usage.total_tokens == 150


def test_budget_decorator_exceeded():
    """Test budget decorator with exceeded limit."""
    tracker = TokenTracker()

    @budget(max_cost_usd=0.001, tracker=tracker)
    def process_with_llm():
        tracker.track(model="gpt-4o", prompt_tokens=1000, completion_tokens=1000, provider="openai")
        return "success"

    with pytest.raises(BudgetExceeded):
        process_with_llm()


def test_remaining_budget():
    """Test remaining budget calculation."""
    tracker = TokenTracker()

    with budget(max_cost_usd=0.1, max_tokens=1000, tracker=tracker) as ctx:
        initial_budget = ctx.remaining_budget
        initial_tokens = ctx.remaining_tokens

        assert initial_budget == 0.1
        assert initial_tokens == 1000

        tracker.track(model="gpt-4o", prompt_tokens=100, completion_tokens=50, provider="openai")

        assert ctx.remaining_budget < initial_budget
        assert ctx.remaining_tokens == 850  # 1000 - 150


def test_no_limits():
    """Test budget with no limits."""
    tracker = TokenTracker()

    with budget(tracker=tracker) as ctx:
        tracker.track(model="gpt-4o", prompt_tokens=10000, completion_tokens=5000, provider="openai")

        assert ctx.remaining_budget is None
        assert ctx.remaining_tokens is None
        assert ctx.current_usage.total_tokens == 15000
