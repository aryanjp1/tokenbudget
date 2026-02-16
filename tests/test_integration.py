"""Integration tests for the full TokenBudget pipeline with live LiteLLM pricing."""

import json
import tempfile
from pathlib import Path

import pytest

from tokenbudget import (
    TokenTracker,
    budget,
    BudgetExceeded,
    TokenLimitReached,
    calculate_cost,
    get_price,
    register_model,
    list_models,
    refresh_pricing,
    generate_table_report,
    export_csv,
    export_json,
    ModelNotFoundError,
)
from tokenbudget.pricing import _CUSTOM_DB, _LITELLM_DB, ModelPrice


@pytest.fixture(autouse=True)
def _clean_state():
    """Ensure custom and LiteLLM dicts are clean between tests."""
    _CUSTOM_DB.clear()
    _LITELLM_DB.clear()
    yield
    _CUSTOM_DB.clear()
    _LITELLM_DB.clear()


# ── Live pricing refresh ────────────────────────────────────────────────────


@pytest.mark.parametrize("model_name", [
    "gemini-3-pro-preview",
    "gpt-4o",
    "claude-sonnet-4-5",
    "gpt-4o-mini",
])
def test_refresh_and_get_price(model_name):
    """Test that refresh_pricing loads real models from LiteLLM."""
    success = refresh_pricing()
    assert success is True

    price = get_price(model_name)
    assert price.input_per_1k >= 0
    assert price.output_per_1k >= 0
    assert price.provider != ""


def test_refresh_loads_many_models():
    """Test that refresh_pricing loads a large number of models."""
    refresh_pricing()
    all_models = list_models()
    assert len(all_models) > 500


# ── End-to-end tracking ─────────────────────────────────────────────────────


def test_track_and_cost_with_live_pricing():
    """Test full tracking pipeline with live LiteLLM pricing."""
    refresh_pricing()

    tracker = TokenTracker()
    tracker.track(model="gemini-3-pro-preview", prompt_tokens=1000, completion_tokens=500, provider="google")

    usage = tracker.usage
    assert usage.total_tokens == 1500
    assert usage.prompt_tokens == 1000
    assert usage.completion_tokens == 500
    assert usage.total_cost_usd > 0
    assert usage.calls == 1


def test_multi_provider_tracking():
    """Test tracking across multiple providers with live pricing."""
    refresh_pricing()

    tracker = TokenTracker()
    tracker.track(model="gemini-3-pro-preview", prompt_tokens=2000, completion_tokens=1000, provider="google")
    tracker.track(model="gpt-4o", prompt_tokens=500, completion_tokens=300, provider="openai")
    tracker.track(model="claude-sonnet-4-5", prompt_tokens=800, completion_tokens=400, provider="anthropic")

    assert tracker.total_cost_usd > 0
    assert len(tracker.usage_by_provider) == 3
    assert "google" in tracker.usage_by_provider
    assert "openai" in tracker.usage_by_provider
    assert "anthropic" in tracker.usage_by_provider


# ── Budget enforcement ───────────────────────────────────────────────────────


def test_budget_decorator_enforces_limit():
    """Test that @budget decorator raises BudgetExceeded."""
    refresh_pricing()

    tracker = TokenTracker()

    @budget(max_cost_usd=0.001, tracker=tracker)
    def expensive_call():
        tracker.track(model="gemini-3-pro-preview", prompt_tokens=5000, completion_tokens=2000, provider="google")
        return "done"

    with pytest.raises(BudgetExceeded):
        expensive_call()


def test_budget_context_manager_tracks_remaining():
    """Test budget context manager with remaining budget tracking."""
    refresh_pricing()

    tracker = TokenTracker()

    with budget(max_cost_usd=1.00, max_tokens=50000, tracker=tracker) as ctx:
        tracker.track(model="gemini-3-pro-preview", prompt_tokens=1000, completion_tokens=500, provider="google")

        assert ctx.remaining_budget < 1.00
        assert ctx.remaining_tokens < 50000
        assert ctx.current_usage.total_tokens == 1500


def test_token_limit_enforcement():
    """Test that token limit is enforced."""
    refresh_pricing()

    tracker = TokenTracker()

    with pytest.raises(TokenLimitReached):
        with budget(max_tokens=100, tracker=tracker):
            tracker.track(model="gemini-3-pro-preview", prompt_tokens=500, completion_tokens=200, provider="google")


# ── Cache stats ──────────────────────────────────────────────────────────────


def test_cache_stats_with_tracking():
    """Test cache statistics alongside usage tracking."""
    refresh_pricing()

    tracker = TokenTracker(cache="memory")
    tracker.track(model="gemini-3-pro-preview", prompt_tokens=1000, completion_tokens=500, provider="google")
    tracker.record_cache_miss()

    saved_cost = calculate_cost("gemini-3-pro-preview", input_tokens=1000, output_tokens=500)
    tracker.record_cache_hit(saved_tokens=1500, saved_cost=saved_cost)

    stats = tracker.cache_stats
    assert stats.hits == 1
    assert stats.misses == 1
    assert stats.saved_tokens == 1500
    assert stats.saved_cost_usd == pytest.approx(saved_cost)


# ── Custom model override ───────────────────────────────────────────────────


def test_custom_model_overrides_litellm():
    """Test that user-registered models override LiteLLM pricing."""
    refresh_pricing()

    # LiteLLM has pricing for gpt-4o
    litellm_price = get_price("gpt-4o")

    # Register custom override
    register_model("gpt-4o", input_per_1k=0.999, output_per_1k=0.999, provider="custom")

    custom_price = get_price("gpt-4o")
    assert custom_price.input_per_1k == 0.999
    assert custom_price.provider == "custom"
    assert custom_price.input_per_1k != litellm_price.input_per_1k


# ── Reports ──────────────────────────────────────────────────────────────────


def test_table_report_with_live_pricing():
    """Test report generation with live pricing data."""
    refresh_pricing()

    tracker = TokenTracker()
    tracker.track(model="gemini-3-pro-preview", prompt_tokens=5000, completion_tokens=2000, provider="google")

    report = generate_table_report(tracker)
    assert "TokenBudget Usage Report" in report
    assert "google" in report


def test_export_csv_with_live_pricing():
    """Test CSV export with live pricing data."""
    refresh_pricing()

    tracker = TokenTracker()
    tracker.track(model="gemini-3-pro-preview", prompt_tokens=1000, completion_tokens=500, provider="google")

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        filepath = f.name

    try:
        export_csv(tracker, filepath)
        with open(filepath, "r") as rf:
            content = rf.read()
            assert "google" in content
    finally:
        Path(filepath).unlink(missing_ok=True)


def test_export_json_with_live_pricing():
    """Test JSON export with live pricing data."""
    refresh_pricing()

    tracker = TokenTracker()
    tracker.track(model="gemini-3-pro-preview", prompt_tokens=1000, completion_tokens=500, provider="google")

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        filepath = f.name

    try:
        export_json(tracker, filepath)
        with open(filepath, "r") as rf:
            data = json.load(rf)
            assert "total" in data
            assert "google" in data["by_provider"]
    finally:
        Path(filepath).unlink(missing_ok=True)


# ── Reset ────────────────────────────────────────────────────────────────────


def test_tracker_reset():
    """Test tracker reset clears all usage."""
    refresh_pricing()

    tracker = TokenTracker()
    tracker.track(model="gemini-3-pro-preview", prompt_tokens=1000, completion_tokens=500, provider="google")
    assert tracker.usage.total_tokens > 0

    tracker.reset()
    assert tracker.usage.total_tokens == 0
    assert tracker.usage.total_cost_usd == 0.0
    assert tracker.usage.calls == 0
