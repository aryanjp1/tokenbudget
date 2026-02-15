"""Budget enforcement decorators and context managers."""

import functools
import threading
from contextvars import ContextVar
from typing import Any, Callable, Optional, TypeVar, cast

from .exceptions import BudgetExceeded, TokenLimitReached
from .tracker import TokenTracker, Usage

# Context variable to store the current budget context
_budget_context: ContextVar[Optional["BudgetContext"]] = ContextVar(
    "_budget_context", default=None
)

F = TypeVar("F", bound=Callable[..., Any])


class BudgetContext:
    """Budget enforcement context.

    Tracks usage within a budget and raises exceptions when limits are exceeded.
    """

    def __init__(
        self,
        max_cost_usd: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tracker: Optional[TokenTracker] = None,
    ) -> None:
        """Initialize budget context.

        Args:
            max_cost_usd: Maximum cost in USD. Default: None (no limit).
            max_tokens: Maximum number of tokens. Default: None (no limit).
            tracker: TokenTracker instance. Default: None (create new tracker).
        """
        self.max_cost_usd = max_cost_usd
        self.max_tokens = max_tokens
        self.tracker = tracker or TokenTracker()
        self._initial_usage = self.tracker.usage
        self._lock = threading.Lock()

    @property
    def current_usage(self) -> Usage:
        """Get current usage within this budget context."""
        with self._lock:
            current = self.tracker.usage
            # Calculate delta from initial usage
            return Usage(
                total_tokens=current.total_tokens - self._initial_usage.total_tokens,
                prompt_tokens=current.prompt_tokens - self._initial_usage.prompt_tokens,
                completion_tokens=current.completion_tokens
                - self._initial_usage.completion_tokens,
                total_cost_usd=current.total_cost_usd - self._initial_usage.total_cost_usd,
                calls=current.calls - self._initial_usage.calls,
            )

    @property
    def remaining_budget(self) -> Optional[float]:
        """Get remaining budget in USD."""
        if self.max_cost_usd is None:
            return None
        return max(0.0, self.max_cost_usd - self.current_usage.total_cost_usd)

    @property
    def remaining_tokens(self) -> Optional[int]:
        """Get remaining token budget."""
        if self.max_tokens is None:
            return None
        return max(0, self.max_tokens - self.current_usage.total_tokens)

    def check_limits(self) -> None:
        """Check if budget limits have been exceeded.

        Raises:
            BudgetExceeded: If cost limit is exceeded.
            TokenLimitReached: If token limit is exceeded.
        """
        usage = self.current_usage

        if self.max_cost_usd is not None and usage.total_cost_usd > self.max_cost_usd:
            raise BudgetExceeded(
                f"Budget exceeded: ${usage.total_cost_usd:.4f} > ${self.max_cost_usd:.4f}",
                current_cost=usage.total_cost_usd,
                max_cost=self.max_cost_usd,
            )

        if self.max_tokens is not None and usage.total_tokens > self.max_tokens:
            raise TokenLimitReached(
                f"Token limit exceeded: {usage.total_tokens} > {self.max_tokens}",
                current_tokens=usage.total_tokens,
                max_tokens=self.max_tokens,
            )

    def __enter__(self) -> "BudgetContext":
        """Enter the budget context."""
        _budget_context.set(self)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the budget context."""
        _budget_context.set(None)
        # Check limits when exiting context (if no exception occurred)
        if exc_type is None:
            self.check_limits()


def get_current_budget() -> Optional[BudgetContext]:
    """Get the current budget context.

    Returns:
        Current BudgetContext or None if not in a budget context.
    """
    return _budget_context.get()


class _BudgetDecorator:
    """Helper class to make budget work as both decorator and context manager."""

    def __init__(
        self,
        max_cost_usd: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tracker: Optional[TokenTracker] = None,
    ) -> None:
        """Initialize decorator/context manager."""
        self.max_cost_usd = max_cost_usd
        self.max_tokens = max_tokens
        self.tracker = tracker
        self._context: Optional[BudgetContext] = None

    def __call__(self, func: F) -> F:
        """Use as decorator."""

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with BudgetContext(self.max_cost_usd, self.max_tokens, self.tracker):
                return func(*args, **kwargs)

        return cast(F, wrapper)

    def __enter__(self) -> BudgetContext:
        """Use as context manager."""
        self._context = BudgetContext(self.max_cost_usd, self.max_tokens, self.tracker)
        return self._context.__enter__()

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager."""
        if self._context:
            self._context.__exit__(exc_type, exc_val, exc_tb)


def budget(
    max_cost_usd: Optional[float] = None,
    max_tokens: Optional[int] = None,
    tracker: Optional[TokenTracker] = None,
) -> _BudgetDecorator:
    """Decorator or context manager for budget enforcement.

    Can be used as a decorator:
        @budget(max_cost_usd=1.00)
        def my_function():
            ...

    Or as a context manager:
        with budget(max_cost_usd=1.00):
            ...

    Args:
        max_cost_usd: Maximum cost in USD. Default: None (no limit).
        max_tokens: Maximum number of tokens. Default: None (no limit).
        tracker: TokenTracker instance. Default: None (create new tracker).

    Returns:
        _BudgetDecorator that can be used as decorator or context manager.

    Raises:
        BudgetExceeded: If cost limit is exceeded.
        TokenLimitReached: If token limit is exceeded.
    """
    return _BudgetDecorator(max_cost_usd, max_tokens, tracker)
