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


def get_current_budget() -> Optional[BudgetContext]:
    """Get the current budget context.

    Returns:
        Current BudgetContext or None if not in a budget context.
    """
    return _budget_context.get()


def budget(
    max_cost_usd: Optional[float] = None,
    max_tokens: Optional[int] = None,
    tracker: Optional[TokenTracker] = None,
) -> Any:
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
        BudgetContext when used as context manager, or decorated function.

    Raises:
        BudgetExceeded: If cost limit is exceeded.
        TokenLimitReached: If token limit is exceeded.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with BudgetContext(max_cost_usd, max_tokens, tracker) as ctx:
                result = func(*args, **kwargs)
                ctx.check_limits()
                return result

        return cast(F, wrapper)

    # If called without arguments, return context manager
    if max_cost_usd is None and max_tokens is None and tracker is not None:
        # Called as @budget(tracker=...)
        return decorator

    # If used as context manager
    if callable(max_cost_usd):
        # Called as @budget without parentheses
        func = max_cost_usd
        return decorator(func)

    # Return both decorator and context manager
    context = BudgetContext(max_cost_usd, max_tokens, tracker)

    # Add decorator capability to context
    context.__call__ = decorator  # type: ignore

    return context
