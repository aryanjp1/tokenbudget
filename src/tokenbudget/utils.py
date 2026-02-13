"""Utility functions for tokenbudget."""

import hashlib
import json
from typing import Any, Dict


def hash_request(data: Dict[str, Any]) -> str:
    """Generate a stable hash for a request.

    Args:
        data: Request data to hash.

    Returns:
        SHA256 hash of the request data.
    """
    # Sort keys for consistent hashing
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()


def format_cost(cost_usd: float) -> str:
    """Format cost in USD with appropriate precision.

    Args:
        cost_usd: Cost in USD.

    Returns:
        Formatted cost string (e.g., "$0.0025" or "$1.50").
    """
    if cost_usd < 0.01:
        return f"${cost_usd:.4f}"
    return f"${cost_usd:.2f}"


def format_number(num: int) -> str:
    """Format large numbers with k/M suffix.

    Args:
        num: Number to format.

    Returns:
        Formatted number string (e.g., "1.2k" or "3.4M").
    """
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    if num >= 1_000:
        return f"{num / 1_000:.1f}k"
    return str(num)
