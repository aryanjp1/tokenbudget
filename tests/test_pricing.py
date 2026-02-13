"""Tests for pricing functionality."""

import pytest

from tokenbudget import (
    ModelNotFoundError,
    calculate_cost,
    get_price,
    list_models,
    register_model,
)


def test_get_price():
    """Test getting model prices."""
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
