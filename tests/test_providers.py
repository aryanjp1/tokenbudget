"""Tests for provider wrappers."""

from unittest.mock import MagicMock, Mock

import pytest

from tokenbudget import TokenTracker


def test_openai_wrapper():
    """Test OpenAI wrapper (requires openai package)."""
    pytest.importorskip("openai")

    from tokenbudget.providers.openai import OpenAIWrapper

    # Create mock client
    mock_client = Mock()
    mock_response = Mock()
    mock_response.model = "gpt-4o"
    mock_response.usage = Mock(prompt_tokens=100, completion_tokens=50)

    mock_client.chat.completions.create.return_value = mock_response

    # Wrap client
    tracker = TokenTracker()
    wrapped_client = OpenAIWrapper(mock_client, tracker)

    # Make a call
    response = wrapped_client.chat.completions.create(
        model="gpt-4o", messages=[{"role": "user", "content": "test"}]
    )

    # Verify tracking
    assert tracker.usage.total_tokens == 150
    assert tracker.usage.calls == 1
    assert tracker.usage.total_cost_usd > 0


def test_anthropic_wrapper():
    """Test Anthropic wrapper (requires anthropic package)."""
    pytest.importorskip("anthropic")

    from tokenbudget.providers.anthropic import AnthropicWrapper

    # Create mock client
    mock_client = Mock()
    mock_response = Mock()
    mock_response.model = "claude-sonnet-4-5"
    mock_response.usage = Mock(input_tokens=100, output_tokens=50)

    mock_client.messages.create.return_value = mock_response

    # Wrap client
    tracker = TokenTracker()
    wrapped_client = AnthropicWrapper(mock_client, tracker)

    # Make a call
    response = wrapped_client.messages.create(
        model="claude-sonnet-4-5", messages=[{"role": "user", "content": "test"}]
    )

    # Verify tracking
    assert tracker.usage.total_tokens == 150
    assert tracker.usage.calls == 1
    assert tracker.usage.total_cost_usd > 0


def test_custom_provider():
    """Test custom provider support."""
    from tokenbudget.providers.custom import CustomProvider

    tracker = TokenTracker()

    # Define extraction functions
    def extract_model(response):
        return response["model"]

    def extract_prompt_tokens(response):
        return response["usage"]["input"]

    def extract_completion_tokens(response):
        return response["usage"]["output"]

    # Create custom provider
    custom = CustomProvider(
        tracker=tracker,
        provider_name="my-llm",
        extract_model=extract_model,
        extract_prompt_tokens=extract_prompt_tokens,
        extract_completion_tokens=extract_completion_tokens,
    )

    # Mock response
    response = {"model": "my-model", "usage": {"input": 100, "output": 50}}

    # Register custom model pricing
    from tokenbudget import register_model

    register_model("my-model", input_per_1k=0.001, output_per_1k=0.002, provider="my-llm")

    # Track response
    custom.track(response)

    # Verify tracking
    assert tracker.usage.total_tokens == 150
    assert tracker.usage.calls == 1
    assert "my-llm" in tracker.usage_by_provider
