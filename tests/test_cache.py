"""Tests for caching functionality."""

import tempfile
from pathlib import Path

import pytest

from tokenbudget.cache import DiskCache, MemoryCache


def test_memory_cache():
    """Test in-memory cache."""
    cache = MemoryCache()

    # Test set and get
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"

    # Test missing key
    assert cache.get("nonexistent") is None

    # Test clear
    cache.clear()
    assert cache.get("key1") is None


def test_disk_cache():
    """Test disk-based cache."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = DiskCache(cache_dir=tmpdir)

        # Test set and get
        cache.set("key1", {"data": "value1"})
        assert cache.get("key1") == {"data": "value1"}

        # Test missing key
        assert cache.get("nonexistent") is None

        # Test persistence (create new cache instance)
        cache2 = DiskCache(cache_dir=tmpdir)
        assert cache2.get("key1") == {"data": "value1"}

        # Test clear
        cache.clear()
        assert cache.get("key1") is None


def test_cache_key_generation():
    """Test cache key generation."""
    cache = MemoryCache()

    request1 = {"model": "gpt-4o", "messages": [{"role": "user", "content": "hello"}]}
    request2 = {"model": "gpt-4o", "messages": [{"role": "user", "content": "hello"}]}
    request3 = {"model": "gpt-4o", "messages": [{"role": "user", "content": "hi"}]}

    key1 = cache.make_key(request1)
    key2 = cache.make_key(request2)
    key3 = cache.make_key(request3)

    # Identical requests should have same key
    assert key1 == key2

    # Different requests should have different keys
    assert key1 != key3


def test_disk_cache_default_directory():
    """Test disk cache with default directory."""
    cache = DiskCache()

    cache.set("test_key", "test_value")
    assert cache.get("test_key") == "test_value"

    # Clean up
    cache.clear()
