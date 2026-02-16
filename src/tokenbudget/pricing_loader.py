"""LiteLLM pricing data loader for tokenbudget.

Fetches and parses the LiteLLM community-maintained pricing JSON to provide
up-to-date pricing for all major LLM models.
"""

import json
import logging
import urllib.request
from typing import Any, Dict, Optional

from .pricing import ModelPrice

logger = logging.getLogger(__name__)

LITELLM_PRICING_URL = (
    "https://raw.githubusercontent.com/BerriAI/litellm/main/"
    "model_prices_and_context_window.json"
)


def parse_litellm_json(raw_data: Dict[str, Any]) -> Dict[str, ModelPrice]:
    """Parse raw LiteLLM JSON into a dictionary of ModelPrice objects.

    Filters to chat models with valid input/output cost per token.
    Converts per-token costs to per-1k-token costs.

    Args:
        raw_data: Raw JSON data from LiteLLM pricing file.

    Returns:
        Dictionary mapping model names to ModelPrice objects.
    """
    models: Dict[str, ModelPrice] = {}

    for model_name, model_data in raw_data.items():
        if not isinstance(model_data, dict):
            continue

        # Skip spec/sample entries
        if model_name == "sample_spec":
            continue

        # Skip entries without valid pricing
        input_cost_per_token = model_data.get("input_cost_per_token")
        output_cost_per_token = model_data.get("output_cost_per_token")
        if input_cost_per_token is None or output_cost_per_token is None:
            continue

        provider = model_data.get("litellm_provider", "")

        # Convert per-token to per-1k-token
        input_per_1k = float(input_cost_per_token) * 1000
        output_per_1k = float(output_cost_per_token) * 1000

        models[model_name] = ModelPrice(
            input_per_1k=input_per_1k,
            output_per_1k=output_per_1k,
            provider=provider,
        )

    return models


def fetch_litellm_pricing(
    url: str = LITELLM_PRICING_URL,
    timeout: int = 10,
) -> Optional[Dict[str, ModelPrice]]:
    """Fetch and parse LiteLLM pricing from the remote URL.

    Args:
        url: URL to fetch pricing JSON from.
        timeout: Request timeout in seconds.

    Returns:
        Dictionary of ModelPrice objects, or None if fetch fails.
    """
    try:
        request = urllib.request.Request(url)
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw_data = json.loads(response.read().decode("utf-8"))
        return parse_litellm_json(raw_data)
    except Exception as e:
        logger.warning("Failed to fetch LiteLLM pricing: %s", e)
        return None
