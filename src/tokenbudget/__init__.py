"""TokenBudget - Lightweight token tracking and cost management for LLM APIs.

Stop bleeding money on LLM API calls with simple decorators and wrappers.
"""

from .budget import budget, BudgetContext, get_current_budget
from .exceptions import (
    BudgetExceeded,
    CacheError,
    ModelNotFoundError,
    ProviderNotFoundError,
    TokenBudgetError,
    TokenLimitReached,
)
from .pricing import calculate_cost, get_price, list_models, register_model, ModelPrice
from .reports import export_csv, export_json, generate_table_report
from .tracker import CacheStats, TokenTracker, Usage

__version__ = "0.1.1"

__all__ = [
    # Core
    "TokenTracker",
    "Usage",
    "CacheStats",
    # Budget
    "budget",
    "BudgetContext",
    "get_current_budget",
    # Pricing
    "get_price",
    "register_model",
    "list_models",
    "calculate_cost",
    "ModelPrice",
    # Reports
    "generate_table_report",
    "export_csv",
    "export_json",
    # Exceptions
    "TokenBudgetError",
    "BudgetExceeded",
    "TokenLimitReached",
    "ProviderNotFoundError",
    "ModelNotFoundError",
    "CacheError",
]
