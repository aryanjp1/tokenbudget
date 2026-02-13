"""Tests for token tracker."""

import pytest

from tokenbudget import TokenTracker, Usage


def test_tracker_initialization():
    """Test tracker initialization."""
    tracker = TokenTracker()
    assert tracker.usage.total_tokens == 0
    assert tracker.usage.total_cost_usd == 0.0
    assert tracker.usage.calls == 0


def test_track_usage():
    """Test tracking token usage."""
    tracker = TokenTracker()

    tracker.track(
        model="gpt-4o",
        prompt_tokens=100,
        completion_tokens=50,
        provider="openai",
    )

    usage = tracker.usage
    assert usage.total_tokens == 150
    assert usage.prompt_tokens == 100
    assert usage.completion_tokens == 50
    assert usage.calls == 1
    assert usage.total_cost_usd > 0


def test_multiple_providers():
    """Test tracking across multiple providers."""
    tracker = TokenTracker()

    tracker.track(model="gpt-4o", prompt_tokens=100, completion_tokens=50, provider="openai")
    tracker.track(
        model="claude-sonnet-4-5",
        prompt_tokens=200,
        completion_tokens=100,
        provider="anthropic",
    )

    # Check total usage
    assert tracker.usage.total_tokens == 450
    assert tracker.usage.calls == 2

    # Check per-provider usage
    usage_by_provider = tracker.usage_by_provider
    assert "openai" in usage_by_provider
    assert "anthropic" in usage_by_provider
    assert usage_by_provider["openai"].total_tokens == 150
    assert usage_by_provider["anthropic"].total_tokens == 300


def test_cache_stats():
    """Test cache statistics tracking."""
    tracker = TokenTracker()

    tracker.record_cache_miss()
    tracker.record_cache_hit(saved_tokens=100, saved_cost=0.01)

    stats = tracker.cache_stats
    assert stats.hits == 1
    assert stats.misses == 1
    assert stats.saved_tokens == 100
    assert stats.saved_cost_usd == 0.01


def test_reset():
    """Test resetting tracker statistics."""
    tracker = TokenTracker()

    tracker.track(model="gpt-4o", prompt_tokens=100, completion_tokens=50, provider="openai")
    tracker.record_cache_hit(saved_tokens=50, saved_cost=0.005)

    tracker.reset()

    assert tracker.usage.total_tokens == 0
    assert tracker.cache_stats.hits == 0
    assert len(tracker.usage_by_provider) == 0


def test_thread_safety():
    """Test thread safety of tracker."""
    import threading

    tracker = TokenTracker()

    def track_calls():
        for _ in range(100):
            tracker.track(model="gpt-4o", prompt_tokens=10, completion_tokens=5, provider="openai")

    threads = [threading.Thread(target=track_calls) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Should have 1000 total calls (10 threads * 100 calls)
    assert tracker.usage.calls == 1000
    assert tracker.usage.total_tokens == 15000
