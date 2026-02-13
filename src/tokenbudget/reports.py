"""Usage reports and analytics for tokenbudget."""

import csv
import json
from typing import TYPE_CHECKING, Any, Dict, List

from .utils import format_cost, format_number

if TYPE_CHECKING:
    from .tracker import TokenTracker


def generate_table_report(tracker: "TokenTracker") -> str:
    """Generate a pretty table report of usage.

    Args:
        tracker: TokenTracker instance.

    Returns:
        Formatted table string.
    """
    usage_by_provider = tracker.usage_by_provider
    cache_stats = tracker.cache_stats

    if not usage_by_provider:
        return "No usage data to report."

    # Calculate column widths
    max_provider_len = max(len(p) for p in usage_by_provider.keys())
    provider_width = max(max_provider_len, len("Provider"))

    # Build table
    lines = []
    lines.append("┌" + "─" * (provider_width + 32) + "┐")
    lines.append("│ TokenBudget Usage Report" + " " * (provider_width + 8) + "│")
    lines.append("├" + "─" * (provider_width + 32) + "┤")

    # Header
    header = f"│ {'Provider':<{provider_width}} │ Calls │ Tokens │ Cost   │"
    lines.append(header)
    lines.append("├" + "─" * (provider_width + 32) + "┤")

    # Provider rows
    for provider, usage in sorted(usage_by_provider.items()):
        tokens_str = format_number(usage.total_tokens)
        cost_str = format_cost(usage.total_cost_usd)
        row = f"│ {provider:<{provider_width}} │ {usage.calls:5d} │ {tokens_str:>6} │ {cost_str:>6} │"
        lines.append(row)

    # Total row
    total_usage = tracker.usage
    total_tokens_str = format_number(total_usage.total_tokens)
    total_cost_str = format_cost(total_usage.total_cost_usd)
    lines.append("├" + "─" * (provider_width + 32) + "┤")
    total_row = (
        f"│ {'Total':<{provider_width}} │ {total_usage.calls:5d} │ "
        f"{total_tokens_str:>6} │ {total_cost_str:>6} │"
    )
    lines.append(total_row)

    # Cache stats if applicable
    if cache_stats.hits > 0:
        saved_tokens_str = format_number(cache_stats.saved_tokens)
        saved_cost_str = format_cost(cache_stats.saved_cost_usd)
        cache_row = (
            f"│ {'Cache Saved':<{provider_width}} │ {' ':>5} │ "
            f"{saved_tokens_str:>6} │ {saved_cost_str:>6} │"
        )
        lines.append(cache_row)

    lines.append("└" + "─" * (provider_width + 32) + "┘")

    return "\n".join(lines)


def export_csv(tracker: "TokenTracker", filepath: str) -> None:
    """Export usage data to CSV.

    Args:
        tracker: TokenTracker instance.
        filepath: Path to CSV file.
    """
    usage_by_provider = tracker.usage_by_provider

    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["provider", "calls", "total_tokens", "prompt_tokens", "completion_tokens", "cost_usd"]
        )

        for provider, usage in sorted(usage_by_provider.items()):
            writer.writerow(
                [
                    provider,
                    usage.calls,
                    usage.total_tokens,
                    usage.prompt_tokens,
                    usage.completion_tokens,
                    f"{usage.total_cost_usd:.6f}",
                ]
            )


def export_json(tracker: "TokenTracker", filepath: str) -> None:
    """Export usage data to JSON.

    Args:
        tracker: TokenTracker instance.
        filepath: Path to JSON file.
    """
    usage_by_provider = tracker.usage_by_provider
    cache_stats = tracker.cache_stats

    data: Dict[str, Any] = {
        "total": tracker.usage.model_dump(),
        "by_provider": {p: u.model_dump() for p, u in usage_by_provider.items()},
        "cache_stats": {
            "hits": cache_stats.hits,
            "misses": cache_stats.misses,
            "saved_tokens": cache_stats.saved_tokens,
            "saved_cost_usd": cache_stats.saved_cost_usd,
        },
    }

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
