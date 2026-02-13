"""Response caching for tokenbudget."""

import json
import os
import pickle
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

from .utils import hash_request


class Cache(ABC):
    """Abstract base class for cache implementations."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found.
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set a value in the cache.

        Args:
            key: Cache key.
            value: Value to cache.
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all cached values."""
        pass

    def make_key(self, request: Dict[str, Any]) -> str:
        """Generate a cache key from a request.

        Args:
            request: Request dictionary.

        Returns:
            Cache key string.
        """
        return hash_request(request)


class MemoryCache(Cache):
    """In-memory cache implementation."""

    def __init__(self) -> None:
        """Initialize the memory cache."""
        self._cache: Dict[str, Any] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found.
        """
        return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        """Set a value in the cache.

        Args:
            key: Cache key.
            value: Value to cache.
        """
        self._cache[key] = value

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()


class DiskCache(Cache):
    """Disk-based cache implementation."""

    def __init__(self, cache_dir: Optional[str] = None) -> None:
        """Initialize the disk cache.

        Args:
            cache_dir: Directory to store cache files. Default: system temp dir.
        """
        if cache_dir is None:
            cache_dir = os.path.join(tempfile.gettempdir(), "tokenbudget_cache")

        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, key: str) -> Path:
        """Get the file path for a cache key.

        Args:
            key: Cache key.

        Returns:
            Path to cache file.
        """
        return self._cache_dir / f"{key}.pkl"

    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found.
        """
        path = self._get_path(key)
        if not path.exists():
            return None

        try:
            with open(path, "rb") as f:
                return pickle.load(f)
        except Exception:
            return None

    def set(self, key: str, value: Any) -> None:
        """Set a value in the cache.

        Args:
            key: Cache key.
            value: Value to cache.
        """
        path = self._get_path(key)
        try:
            with open(path, "wb") as f:
                pickle.dump(value, f)
        except Exception:
            pass

    def clear(self) -> None:
        """Clear all cached values."""
        for file in self._cache_dir.glob("*.pkl"):
            try:
                file.unlink()
            except Exception:
                pass
