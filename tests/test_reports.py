"""Tests for reporting functionality."""

import json
import tempfile
from pathlib import Path

import pytest

from tokenbudget import TokenTracker, export_csv, export_json, generate_table_report


def test_table_report():
    """Test table report generation."""
    tracker = TokenTracker()

    tracker.track(model="gpt-4o", prompt_tokens=100, completion_tokens=50, provider="openai")
    tracker.track(
        model="claude-sonnet-4-5",
        prompt_tokens=200,
        completion_tokens=100,
        provider="anthropic",
    )

    report = generate_table_report(tracker)

    assert "TokenBudget Usage Report" in report
    assert "openai" in report
    assert "anthropic" in report
    assert "Total" in report


def test_empty_report():
    """Test report generation with no data."""
    tracker = TokenTracker()
    report = generate_table_report(tracker)

    assert "No usage data" in report


def test_export_csv():
    """Test CSV export."""
    tracker = TokenTracker()

    tracker.track(model="gpt-4o", prompt_tokens=100, completion_tokens=50, provider="openai")
    tracker.track(
        model="claude-sonnet-4-5",
        prompt_tokens=200,
        completion_tokens=100,
        provider="anthropic",
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        export_csv(tracker, f.name)

        # Read and verify
        with open(f.name, "r") as rf:
            content = rf.read()
            assert "provider,calls,total_tokens" in content
            assert "openai" in content
            assert "anthropic" in content

        # Clean up
        Path(f.name).unlink()


def test_export_json():
    """Test JSON export."""
    tracker = TokenTracker()

    tracker.track(model="gpt-4o", prompt_tokens=100, completion_tokens=50, provider="openai")
    tracker.track(
        model="claude-sonnet-4-5",
        prompt_tokens=200,
        completion_tokens=100,
        provider="anthropic",
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        export_json(tracker, f.name)

        # Read and verify
        with open(f.name, "r") as rf:
            data = json.load(rf)
            assert "total" in data
            assert "by_provider" in data
            assert "cache_stats" in data
            assert "openai" in data["by_provider"]
            assert "anthropic" in data["by_provider"]

        # Clean up
        Path(f.name).unlink()


def test_report_with_cache():
    """Test report generation with cache statistics."""
    tracker = TokenTracker()

    tracker.track(model="gpt-4o", prompt_tokens=100, completion_tokens=50, provider="openai")
    tracker.record_cache_hit(saved_tokens=150, saved_cost=0.01)

    report = generate_table_report(tracker)

    assert "Cache Saved" in report
