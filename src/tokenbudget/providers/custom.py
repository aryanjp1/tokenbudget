"""Custom provider support for tokenbudget."""

from typing import Any, Callable

from ..tracker import TokenTracker


class CustomProvider:
    """Support for custom LLM providers.

    Allows users to define their own token extraction and tracking logic.
    """

    def __init__(
        self,
        tracker: TokenTracker,
        provider_name: str,
        extract_model: Callable[[Any], str],
        extract_prompt_tokens: Callable[[Any], int],
        extract_completion_tokens: Callable[[Any], int],
    ) -> None:
        """Initialize custom provider.

        Args:
            tracker: TokenTracker instance.
            provider_name: Name of the provider (for reporting).
            extract_model: Function to extract model name from response.
            extract_prompt_tokens: Function to extract prompt tokens from response.
            extract_completion_tokens: Function to extract completion tokens from response.

        Example:
            def get_model(response):
                return response["model"]

            def get_input_tokens(response):
                return response["usage"]["input_tokens"]

            def get_output_tokens(response):
                return response["usage"]["output_tokens"]

            custom = CustomProvider(
                tracker=tracker,
                provider_name="my-llm-service",
                extract_model=get_model,
                extract_prompt_tokens=get_input_tokens,
                extract_completion_tokens=get_output_tokens,
            )

            # Track a response
            custom.track(api_response)
        """
        self.tracker = tracker
        self.provider_name = provider_name
        self._extract_model = extract_model
        self._extract_prompt_tokens = extract_prompt_tokens
        self._extract_completion_tokens = extract_completion_tokens

    def track(self, response: Any) -> None:
        """Track a custom provider response.

        Args:
            response: API response object.
        """
        model = self._extract_model(response)
        prompt_tokens = self._extract_prompt_tokens(response)
        completion_tokens = self._extract_completion_tokens(response)

        self.tracker.track(
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            provider=self.provider_name,
        )
