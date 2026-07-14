"""
PyCostAudit-Multi v0.5: Multi-API Cost Calculation Core

Unified cost calculation and tracking across 20+ cloud providers and 10+ open-source APIs.
This is the cost calculation core that powers OpenAnchor.

v0.5 Scope (Cost Calculation Only):
- CostCalculator: Calculate cost for any provider/model/tokens
- CostDatabase: Track operations and aggregate costs
- PricingManager: Provider pricing + daily updates
- Budget Enforcement: Hard limits to prevent cost overruns

NOT included in v0.5 (deferred to v0.2+):
- Forecasting/ML predictions
- Dashboards/web UI
- Compliance/audit tracking
- Recommendations (that's OpenAnchor's job)
- Advanced reporting/analytics

Documentation: https://github.com/Mullassery/PyCostAudit
OpenAnchor (uses this): https://github.com/Mullassery/openanchor
"""

__version__ = "0.5.0"
__author__ = "Georgi Mammen Mullassery"

# Core cost calculation classes
from .cost_calculator import CostCalculator
from .cost_model import Cost, ProviderType
from .pricing_manager import PricingManager
from .database import DatabaseManager
from .persistence import CostDatabase

# Safety feature: Hard budget enforcement
from ._budget_enforcement import (
    BudgetEnforcer,
    BudgetLimit,
    BudgetStatus,
    BudgetPeriod,
    EnforcementAction,
    BudgetExceededError,
    get_global_enforcer,
    set_budget_limit,
)

__all__ = [
    # Core v0.5
    "CostCalculator",
    "Cost",
    "ProviderType",
    "PricingManager",
    "DatabaseManager",
    "CostDatabase",
    # Budget enforcement (safety feature)
    "BudgetEnforcer",
    "BudgetLimit",
    "BudgetStatus",
    "BudgetPeriod",
    "EnforcementAction",
    "BudgetExceededError",
    "get_global_enforcer",
    "set_budget_limit",
]
