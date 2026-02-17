"""Tests for pricing functionality."""

import pytest

from tokenbudget import (
    ModelNotFoundError,
    calculate_cost,
    get_price,
    list_models,
    refresh_pricing,
    register_model,
)
from tokenbudget.pricing import _CUSTOM_DB, _LITELLM_DB, ModelPrice


@pytest.fixture(autouse=True)
def _clean_pricing_state():
    """Ensure custom and LiteLLM dicts are clean between tests."""
    _CUSTOM_DB.clear()
    _LITELLM_DB.clear()
    yield
    _CUSTOM_DB.clear()
    _LITELLM_DB.clear()


# ── Existing tests (preserved) ──────────────────────────────────────────────


def test_get_price():
    """Test getting model prices from hardcoded fallback."""
    # OpenAI model
    price = get_price("gpt-4o")
    assert price.provider == "openai"
    assert price.input_per_1k > 0
    assert price.output_per_1k > 0

    # Anthropic model
    price = get_price("claude-sonnet-4-5")
    assert price.provider == "anthropic"


def test_get_price_not_found():
    """Test error when model not found."""
    with pytest.raises(ModelNotFoundError):
        get_price("nonexistent-model")


def test_register_model():
    """Test registering custom models."""
    register_model("my-custom-model", input_per_1k=0.001, output_per_1k=0.002, provider="custom")

    price = get_price("my-custom-model")
    assert price.input_per_1k == 0.001
    assert price.output_per_1k == 0.002
    assert price.provider == "custom"


def test_list_models():
    """Test listing models."""
    all_models = list_models()
    assert len(all_models) > 0
    assert "gpt-4o" in all_models
    assert "claude-sonnet-4-5" in all_models

    # Filter by provider
    openai_models = list_models(provider="openai")
    assert all(m.provider == "openai" for m in openai_models.values())


def test_calculate_cost():
    """Test cost calculation."""
    # Test with gpt-4o
    cost = calculate_cost("gpt-4o", input_tokens=1000, output_tokens=500)
    assert cost > 0
    assert isinstance(cost, float)

    # Test with different token counts
    cost1 = calculate_cost("gpt-4o", input_tokens=100, output_tokens=50)
    cost2 = calculate_cost("gpt-4o", input_tokens=200, output_tokens=100)
    assert cost2 > cost1


def test_all_major_models_present():
    """Test that all major models are in the pricing database."""
    major_models = [
        "gpt-4o",
        "gpt-4o-mini",
        "claude-sonnet-4-5",
        "claude-opus-4-5",
        "claude-haiku-4-5",
        "gemini-2.0-flash",
    ]

    for model in major_models:
        price = get_price(model)
        assert price is not None


# ── New tests: Three-tier pricing lookup ─────────────────────────────────────


def test_custom_overrides_litellm():
    """Test that user-registered models take priority over LiteLLM entries."""
    # Simulate LiteLLM data for gpt-4o
    _LITELLM_DB["gpt-4o"] = ModelPrice(
        input_per_1k=0.999, output_per_1k=0.999, provider="openai"
    )

    # Register custom override
    register_model("gpt-4o", input_per_1k=0.123, output_per_1k=0.456, provider="custom")

    price = get_price("gpt-4o")
    assert price.input_per_1k == 0.123
    assert price.output_per_1k == 0.456
    assert price.provider == "custom"


def test_litellm_overrides_hardcoded():
    """Test that LiteLLM entries take priority over hardcoded entries."""
    _LITELLM_DB["gpt-4o"] = ModelPrice(
        input_per_1k=0.555, output_per_1k=0.777, provider="openai"
    )

    price = get_price("gpt-4o")
    assert price.input_per_1k == 0.555
    assert price.output_per_1k == 0.777


def test_fallback_to_hardcoded():
    """Test that hardcoded pricing works when LiteLLM is empty."""
    price = get_price("gpt-4o")
    assert price.provider == "openai"
    assert price.input_per_1k > 0


def test_litellm_only_model():
    """Test accessing a model only available via LiteLLM."""
    _LITELLM_DB["gpt-5-nano"] = ModelPrice(
        input_per_1k=0.05, output_per_1k=0.15, provider="openai"
    )

    price = get_price("gpt-5-nano")
    assert price.input_per_1k == 0.05
    assert price.provider == "openai"


def test_list_models_merges_all_tiers():
    """Test that list_models returns merged view across all tiers."""
    _LITELLM_DB["litellm-only-model"] = ModelPrice(
        input_per_1k=0.01, output_per_1k=0.02, provider="test"
    )
    register_model("custom-only-model", input_per_1k=0.001, output_per_1k=0.002, provider="test")

    all_models = list_models()
    assert "gpt-4o" in all_models  # hardcoded
    assert "litellm-only-model" in all_models  # litellm
    assert "custom-only-model" in all_models  # custom


# ── New tests: LiteLLM parsing ───────────────────────────────────────────────


def test_parse_litellm_json():
    """Test parsing a sample LiteLLM JSON snippet."""
    from tokenbudget.pricing_loader import parse_litellm_json

    raw_data = {
        "gpt-5-mini": {
            "input_cost_per_token": 2.5e-07,
            "output_cost_per_token": 2e-06,
            "litellm_provider": "openai",
            "mode": "chat",
            "max_tokens": 128000,
        },
        "claude-haiku-4-5": {
            "input_cost_per_token": 1e-06,
            "output_cost_per_token": 5e-06,
            "litellm_provider": "anthropic",
            "mode": "chat",
            "max_tokens": 64000,
        },
        "some-embedding-model": {
            "input_cost_per_token": 1e-07,
            "output_cost_per_token": 0.0,
            "litellm_provider": "openai",
            "mode": "embedding",
        },
        "sample_spec": {
            "input_cost_per_token": 0.0,
            "output_cost_per_token": 0.0,
            "mode": "chat",
        },
    }

    result = parse_litellm_json(raw_data)

    # Models with valid costs should be included
    assert "gpt-5-mini" in result
    assert "claude-haiku-4-5" in result
    assert "some-embedding-model" in result

    # sample_spec should be excluded
    assert "sample_spec" not in result

    # Verify per-token to per-1k conversion
    gpt5 = result["gpt-5-mini"]
    assert gpt5.input_per_1k == pytest.approx(2.5e-07 * 1000)
    assert gpt5.output_per_1k == pytest.approx(2e-06 * 1000)
    assert gpt5.provider == "openai"


def test_parse_litellm_skips_missing_costs():
    """Test that models without valid cost fields are skipped."""
    from tokenbudget.pricing_loader import parse_litellm_json

    raw_data = {
        "no-input-cost": {
            "output_cost_per_token": 1e-06,
            "litellm_provider": "openai",
            "mode": "chat",
        },
        "no-output-cost": {
            "input_cost_per_token": 1e-06,
            "litellm_provider": "openai",
            "mode": "chat",
        },
    }

    result = parse_litellm_json(raw_data)
    assert len(result) == 0


def test_parse_litellm_preserves_provider_as_is():
    """Test that litellm_provider value is used directly without normalization."""
    from tokenbudget.pricing_loader import parse_litellm_json

    raw_data = {
        "model-a": {
            "input_cost_per_token": 1e-06,
            "output_cost_per_token": 2e-06,
            "litellm_provider": "vertex_ai-language-models",
            "mode": "chat",
        },
        "model-b": {
            "input_cost_per_token": 1e-06,
            "output_cost_per_token": 2e-06,
            "litellm_provider": "bedrock_converse",
            "mode": "chat",
        },
    }

    result = parse_litellm_json(raw_data)
    assert result["model-a"].provider == "vertex_ai-language-models"
    assert result["model-b"].provider == "bedrock_converse"


# ── New tests: refresh_pricing ───────────────────────────────────────────────


def test_refresh_pricing_with_bad_url():
    """Test that refresh_pricing returns False on failure and preserves existing data."""
    result = refresh_pricing(
        url="http://invalid-url-that-does-not-exist.example/pricing.json",
        timeout=2,
    )
    assert result is False

    # Hardcoded pricing should still work
    price = get_price("gpt-4o")
    assert price.provider == "openai"
