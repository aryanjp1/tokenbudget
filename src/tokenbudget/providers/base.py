"""Abstract base class for provider wrappers."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..tracker import TokenTracker


class BaseProvider(ABC):
    """Abstract base class for provider wrappers.

    All provider wrappers should inherit from this class.
    """

    def __init__(self, client: Any, tracker: "TokenTracker") -> None:
        """Initialize the provider wrapper.

        Args:
            client: Original client instance.
            tracker: TokenTracker instance for tracking usage.
        """
        self._client = client
        self._tracker = tracker

    @abstractmethod
    def _extract_usage(self, response: Any) -> tuple[str, int, int]:
        """Extract usage information from a response.

        Args:
            response: API response object.

        Returns:
            Tuple of (model, prompt_tokens, completion_tokens).
        """
        pass

    @property
    def original_client(self) -> Any:
        """Get the original unwrapped client.

        Returns:
            Original client instance.
        """
        return self._client
