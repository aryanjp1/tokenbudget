"""OpenAI provider wrapper."""

from typing import Any, Optional

from ..budget import get_current_budget
from ..pricing import calculate_cost
from .base import BaseProvider


class OpenAIWrapper(BaseProvider):
    """Wrapper for OpenAI client that tracks token usage."""

    def __init__(self, client: Any, tracker: Any) -> None:
        """Initialize OpenAI wrapper.

        Args:
            client: OpenAI client instance.
            tracker: TokenTracker instance.
        """
        super().__init__(client, tracker)

        # Wrap the chat.completions.create method
        self.chat = ChatWrapper(client.chat, self)

    def _extract_usage(self, response: Any) -> tuple[str, int, int]:
        """Extract usage from OpenAI response.

        Args:
            response: OpenAI response object.

        Returns:
            Tuple of (model, prompt_tokens, completion_tokens).
        """
        model = response.model
        usage = response.usage
        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens
        return model, prompt_tokens, completion_tokens

    def _track_response(self, response: Any, from_cache: bool = False) -> Any:
        """Track a response and check budget limits.

        Args:
            response: API response.
            from_cache: Whether this response came from cache.

        Returns:
            The response object.
        """
        model, prompt_tokens, completion_tokens = self._extract_usage(response)

        if from_cache:
            # Record cache hit
            cost = calculate_cost(model, prompt_tokens, completion_tokens)
            self._tracker.record_cache_hit(
                saved_tokens=prompt_tokens + completion_tokens,
                saved_cost=cost,
            )
        else:
            # Track normal usage
            self._tracker.track(
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                provider="openai",
            )

        # Check budget limits if in budget context
        budget_ctx = get_current_budget()
        if budget_ctx is not None:
            budget_ctx.check_limits()

        return response

    def __getattr__(self, name: str) -> Any:
        """Forward attribute access to the original client.

        Args:
            name: Attribute name.

        Returns:
            Attribute from original client.
        """
        return getattr(self._client, name)


class ChatWrapper:
    """Wrapper for OpenAI chat completions."""

    def __init__(self, chat: Any, parent: OpenAIWrapper) -> None:
        """Initialize chat wrapper.

        Args:
            chat: Original chat object.
            parent: Parent OpenAIWrapper instance.
        """
        self._chat = chat
        self._parent = parent
        self.completions = CompletionsWrapper(chat.completions, parent)

    def __getattr__(self, name: str) -> Any:
        """Forward attribute access to the original chat object.

        Args:
            name: Attribute name.

        Returns:
            Attribute from original chat object.
        """
        return getattr(self._chat, name)


class CompletionsWrapper:
    """Wrapper for OpenAI chat completions create method."""

    def __init__(self, completions: Any, parent: OpenAIWrapper) -> None:
        """Initialize completions wrapper.

        Args:
            completions: Original completions object.
            parent: Parent OpenAIWrapper instance.
        """
        self._completions = completions
        self._parent = parent

    def create(self, **kwargs: Any) -> Any:
        """Create a chat completion with tracking.

        Args:
            **kwargs: Arguments for chat completion.

        Returns:
            Chat completion response.
        """
        cache = self._parent._tracker.get_cache()

        # Check cache if enabled
        if cache is not None:
            cache_key = cache.make_key(kwargs)
            cached_response = cache.get(cache_key)

            if cached_response is not None:
                # Cache hit
                return self._parent._track_response(cached_response, from_cache=True)

            # Cache miss
            self._parent._tracker.record_cache_miss()

        # Make API call
        response = self._completions.create(**kwargs)

        # Cache the response if caching is enabled
        if cache is not None:
            cache.set(cache_key, response)

        # Track the response
        return self._parent._track_response(response, from_cache=False)

    def __getattr__(self, name: str) -> Any:
        """Forward attribute access to the original completions object.

        Args:
            name: Attribute name.

        Returns:
            Attribute from original completions object.
        """
        return getattr(self._completions, name)
