"""Core token and cost tracking engine."""

import threading
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from .cache import Cache
from .exceptions import ProviderNotFoundError
from .pricing import calculate_cost


class Usage(BaseModel):
    """Token usage and cost information.

    Attributes:
        total_tokens: Total number of tokens used.
        prompt_tokens: Number of prompt/input tokens.
        completion_tokens: Number of completion/output tokens.
        total_cost_usd: Total cost in USD.
        calls: Number of API calls made.
    """

    total_tokens: int = Field(default=0, ge=0)
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_cost_usd: float = Field(default=0.0, ge=0.0)
    calls: int = Field(default=0, ge=0)

    def add(self, other: "Usage") -> None:
        """Add another Usage object to this one.

        Args:
            other: Usage object to add.
        """
        self.total_tokens += other.total_tokens
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.total_cost_usd += other.total_cost_usd
        self.calls += other.calls


@dataclass
class CacheStats:
    """Cache statistics.

    Attributes:
        hits: Number of cache hits.
        misses: Number of cache misses.
        saved_cost_usd: Total cost saved by cache in USD.
        saved_tokens: Total tokens saved by cache.
    """

    hits: int = 0
    misses: int = 0
    saved_cost_usd: float = 0.0
    saved_tokens: int = 0


class TokenTracker:
    """Core token and cost tracking engine.

    Tracks token usage and costs across all LLM providers. Thread-safe.

    Attributes:
        usage: Overall usage statistics.
        usage_by_provider: Usage statistics by provider.
        cache_stats: Cache statistics (if caching is enabled).
    """

    def __init__(self, cache: Optional[str] = None) -> None:
        """Initialize the token tracker.

        Args:
            cache: Cache backend ("memory", "disk", None). Default: None.
        """
        self._usage = Usage()
        self._usage_by_provider: Dict[str, Usage] = {}
        self._cache_stats = CacheStats()
        self._lock = threading.Lock()
        self._cache: Optional[Cache] = None

        if cache == "memory":
            from .cache import MemoryCache

            self._cache = MemoryCache()
        elif cache == "disk":
            from .cache import DiskCache

            self._cache = DiskCache()
        elif cache is not None:
            raise ValueError(f"Unknown cache backend: {cache}. Use 'memory' or 'disk'.")

    @property
    def usage(self) -> Usage:
        """Get overall usage statistics."""
        with self._lock:
            return self._usage.model_copy()

    @property
    def usage_by_provider(self) -> Dict[str, Usage]:
        """Get usage statistics by provider."""
        with self._lock:
            return {k: v.model_copy() for k, v in self._usage_by_provider.items()}

    @property
    def total_cost_usd(self) -> float:
        """Get total cost in USD."""
        with self._lock:
            return self._usage.total_cost_usd

    @property
    def cache_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self._lock:
            return CacheStats(
                hits=self._cache_stats.hits,
                misses=self._cache_stats.misses,
                saved_cost_usd=self._cache_stats.saved_cost_usd,
                saved_tokens=self._cache_stats.saved_tokens,
            )

    def track(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        provider: str,
    ) -> None:
        """Track a single API call.

        Args:
            model: Model name.
            prompt_tokens: Number of prompt/input tokens.
            completion_tokens: Number of completion/output tokens.
            provider: Provider name.
        """
        total_tokens = prompt_tokens + completion_tokens
        cost = calculate_cost(model, prompt_tokens, completion_tokens)

        usage = Usage(
            total_tokens=total_tokens,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_cost_usd=cost,
            calls=1,
        )

        with self._lock:
            self._usage.add(usage)
            if provider not in self._usage_by_provider:
                self._usage_by_provider[provider] = Usage()
            self._usage_by_provider[provider].add(usage)

    def record_cache_hit(self, saved_tokens: int, saved_cost: float) -> None:
        """Record a cache hit.

        Args:
            saved_tokens: Number of tokens saved.
            saved_cost: Cost saved in USD.
        """
        with self._lock:
            self._cache_stats.hits += 1
            self._cache_stats.saved_tokens += saved_tokens
            self._cache_stats.saved_cost_usd += saved_cost

    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        with self._lock:
            self._cache_stats.misses += 1

    def reset(self) -> None:
        """Reset all tracking statistics."""
        with self._lock:
            self._usage = Usage()
            self._usage_by_provider.clear()
            self._cache_stats = CacheStats()

    def wrap_openai(self, client: Any) -> Any:
        """Wrap an OpenAI client to track token usage.

        Args:
            client: OpenAI client instance.

        Returns:
            Wrapped client that tracks token usage.
        """
        try:
            from .providers.openai import OpenAIWrapper

            return OpenAIWrapper(client, self)
        except ImportError as e:
            raise ProviderNotFoundError(
                "OpenAI support requires: pip install tokenbudget[openai]"
            ) from e

    def wrap_anthropic(self, client: Any) -> Any:
        """Wrap an Anthropic client to track token usage.

        Args:
            client: Anthropic client instance.

        Returns:
            Wrapped client that tracks token usage.
        """
        try:
            from .providers.anthropic import AnthropicWrapper

            return AnthropicWrapper(client, self)
        except ImportError as e:
            raise ProviderNotFoundError(
                "Anthropic support requires: pip install tokenbudget[anthropic]"
            ) from e

    def get_cache(self) -> Optional[Cache]:
        """Get the cache instance if caching is enabled.

        Returns:
            Cache instance or None.
        """
        return self._cache
