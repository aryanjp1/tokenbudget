"""Model pricing database for tokenbudget.

Pricing is resolved in three tiers (highest priority first):
1. User-registered models via ``register_model()``
2. LiteLLM community-maintained pricing (fetched via ``refresh_pricing()``)
3. Hardcoded fallback pricing shipped with the package
"""

import logging
from dataclasses import dataclass
from typing import Dict, Optional

from .exceptions import ModelNotFoundError

logger = logging.getLogger(__name__)


@dataclass
class ModelPrice:
    """Pricing information for a specific model.

    Attributes:
        input_per_1k: Cost per 1000 input tokens in USD.
        output_per_1k: Cost per 1000 output tokens in USD.
        provider: Provider name (e.g., "openai", "anthropic").
    """

    input_per_1k: float
    output_per_1k: float
    provider: str


# Pricing database (as of February 2026)
_PRICING_DB: Dict[str, ModelPrice] = {
    # OpenAI models
    "gpt-4o": ModelPrice(input_per_1k=0.0025, output_per_1k=0.010, provider="openai"),
    "gpt-4o-mini": ModelPrice(input_per_1k=0.00015, output_per_1k=0.0006, provider="openai"),
    "gpt-4-turbo": ModelPrice(input_per_1k=0.01, output_per_1k=0.03, provider="openai"),
    "gpt-4": ModelPrice(input_per_1k=0.03, output_per_1k=0.06, provider="openai"),
    "gpt-3.5-turbo": ModelPrice(input_per_1k=0.0005, output_per_1k=0.0015, provider="openai"),
    "o1": ModelPrice(input_per_1k=0.015, output_per_1k=0.060, provider="openai"),
    "o1-mini": ModelPrice(input_per_1k=0.003, output_per_1k=0.012, provider="openai"),
    "o3-mini": ModelPrice(input_per_1k=0.0011, output_per_1k=0.0044, provider="openai"),
    # Anthropic models
    "claude-opus-4-5": ModelPrice(input_per_1k=0.015, output_per_1k=0.075, provider="anthropic"),
    "claude-opus-4-5-20251101": ModelPrice(
        input_per_1k=0.015, output_per_1k=0.075, provider="anthropic"
    ),
    "claude-sonnet-4-5": ModelPrice(
        input_per_1k=0.003, output_per_1k=0.015, provider="anthropic"
    ),
    "claude-sonnet-4-5-20250929": ModelPrice(
        input_per_1k=0.003, output_per_1k=0.015, provider="anthropic"
    ),
    "claude-haiku-4-5": ModelPrice(
        input_per_1k=0.0008, output_per_1k=0.004, provider="anthropic"
    ),
    "claude-haiku-4-5-20251001": ModelPrice(
        input_per_1k=0.0008, output_per_1k=0.004, provider="anthropic"
    ),
    "claude-3-5-sonnet-20241022": ModelPrice(
        input_per_1k=0.003, output_per_1k=0.015, provider="anthropic"
    ),
    "claude-3-opus-20240229": ModelPrice(
        input_per_1k=0.015, output_per_1k=0.075, provider="anthropic"
    ),
    # Google models
    "gemini-2.0-flash": ModelPrice(input_per_1k=0.0, output_per_1k=0.0, provider="google"),
    "gemini-2.0-flash-exp": ModelPrice(input_per_1k=0.0, output_per_1k=0.0, provider="google"),
    "gemini-1.5-pro": ModelPrice(input_per_1k=0.00125, output_per_1k=0.005, provider="google"),
    "gemini-1.5-flash": ModelPrice(
        input_per_1k=0.000075, output_per_1k=0.0003, provider="google"
    ),
}

# User-registered models (highest priority)
_CUSTOM_DB: Dict[str, ModelPrice] = {}

# LiteLLM-fetched models (middle priority)
_LITELLM_DB: Dict[str, ModelPrice] = {}


def get_price(model: str) -> ModelPrice:
    """Get pricing information for a model.

    Resolves pricing in order: user-registered → LiteLLM → hardcoded fallback.

    Args:
        model: Model name (e.g., "gpt-4o", "claude-sonnet-4-5").

    Returns:
        ModelPrice object with pricing information.

    Raises:
        ModelNotFoundError: If the model is not found in any pricing source.
    """
    # 1. User-registered models (highest priority)
    if model in _CUSTOM_DB:
        return _CUSTOM_DB[model]

    # 2. LiteLLM-fetched models
    if model in _LITELLM_DB:
        return _LITELLM_DB[model]

    # 3. Hardcoded fallback
    if model in _PRICING_DB:
        return _PRICING_DB[model]

    raise ModelNotFoundError(
        f"Model '{model}' not found in pricing database. "
        f"Use register_model() to add custom pricing, "
        f"or call refresh_pricing() to fetch latest models."
    )


def register_model(
    model: str,
    input_per_1k: float,
    output_per_1k: float,
    provider: str = "custom",
) -> None:
    """Register a custom model with pricing information.

    Custom models always take the highest priority over LiteLLM and
    hardcoded pricing entries.

    Args:
        model: Model name.
        input_per_1k: Cost per 1000 input tokens in USD.
        output_per_1k: Cost per 1000 output tokens in USD.
        provider: Provider name (default: "custom").
    """
    _CUSTOM_DB[model] = ModelPrice(
        input_per_1k=input_per_1k,
        output_per_1k=output_per_1k,
        provider=provider,
    )


def list_models(provider: Optional[str] = None) -> Dict[str, ModelPrice]:
    """List all available models across all pricing sources.

    Returns a merged view with user-registered models taking priority
    over LiteLLM entries, which take priority over hardcoded entries.

    Args:
        provider: Optional provider name to filter by.

    Returns:
        Dictionary of model names to ModelPrice objects.
    """
    # Merge: hardcoded → litellm → custom (last wins)
    merged: Dict[str, ModelPrice] = {}
    merged.update(_PRICING_DB)
    merged.update(_LITELLM_DB)
    merged.update(_CUSTOM_DB)

    if provider is None:
        return merged
    return {k: v for k, v in merged.items() if v.provider == provider}


def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """Calculate the cost of a request.

    Args:
        model: Model name.
        input_tokens: Number of input tokens.
        output_tokens: Number of output tokens.

    Returns:
        Total cost in USD.

    Raises:
        ModelNotFoundError: If the model is not found in the pricing database.
    """
    price = get_price(model)
    input_cost = (input_tokens / 1000) * price.input_per_1k
    output_cost = (output_tokens / 1000) * price.output_per_1k
    return input_cost + output_cost


def refresh_pricing(
    url: Optional[str] = None,
    timeout: int = 10,
) -> bool:
    """Fetch latest pricing from the LiteLLM community pricing database.

    On success, the fetched models become available in the middle priority
    tier (above hardcoded, below user-registered). On failure, existing
    pricing remains unchanged.

    Args:
        url: Custom URL to fetch pricing from. Default: LiteLLM GitHub URL.
        timeout: Request timeout in seconds. Default: 10.

    Returns:
        True if pricing was successfully fetched and loaded, False otherwise.
    """
    from .pricing_loader import LITELLM_PRICING_URL, fetch_litellm_pricing

    fetch_url = url or LITELLM_PRICING_URL
    result = fetch_litellm_pricing(url=fetch_url, timeout=timeout)

    if result is not None:
        _LITELLM_DB.clear()
        _LITELLM_DB.update(result)
        logger.info("Loaded %d models from LiteLLM pricing.", len(result))
        return True

    logger.warning("Failed to refresh pricing. Using existing pricing data.")
    return False
