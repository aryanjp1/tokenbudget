"""Exception classes for tokenbudget."""


class TokenBudgetError(Exception):
    """Base exception for all tokenbudget errors."""

    pass


class BudgetExceeded(TokenBudgetError):
    """Raised when a budget limit is exceeded."""

    def __init__(self, message: str, current_cost: float, max_cost: float) -> None:
        """Initialize BudgetExceeded exception.

        Args:
            message: Error message.
            current_cost: Current cost in USD.
            max_cost: Maximum allowed cost in USD.
        """
        super().__init__(message)
        self.current_cost = current_cost
        self.max_cost = max_cost


class TokenLimitReached(TokenBudgetError):
    """Raised when a token limit is reached."""

    def __init__(self, message: str, current_tokens: int, max_tokens: int) -> None:
        """Initialize TokenLimitReached exception.

        Args:
            message: Error message.
            current_tokens: Current token count.
            max_tokens: Maximum allowed token count.
        """
        super().__init__(message)
        self.current_tokens = current_tokens
        self.max_tokens = max_tokens


class ProviderNotFoundError(TokenBudgetError):
    """Raised when a provider is not found or not supported."""

    pass


class ModelNotFoundError(TokenBudgetError):
    """Raised when a model is not found in the pricing database."""

    pass


class CacheError(TokenBudgetError):
    """Raised when there's an error with the cache system."""

    pass
