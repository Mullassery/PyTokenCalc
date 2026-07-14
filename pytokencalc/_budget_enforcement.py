"""
Hard budget enforcement and spending limits.

Prevents runaway costs by enforcing hard stops when budgets are exceeded.
This is a CRITICAL safety feature to prevent agent-driven cost explosions.
"""

from dataclasses import dataclass
from typing import Optional, Callable, List
from enum import Enum
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class BudgetPeriod(Enum):
    """Budget enforcement period."""
    HOURLY = "hourly"
    DAILY = "daily"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    TOTAL = "total"  # Total lifetime budget


class EnforcementAction(Enum):
    """Action to take when budget is exceeded."""
    ALERT = "alert"  # Log warning, continue
    THROTTLE = "throttle"  # Reduce rate, continue
    STOP = "stop"  # Hard stop, raise exception
    WEBHOOK = "webhook"  # Call external webhook


@dataclass
class BudgetLimit:
    """Budget limit definition."""
    limit_usd: float
    period: BudgetPeriod
    action: EnforcementAction
    warning_threshold: float = 0.80  # Alert at 80% of budget
    description: str = ""


@dataclass
class BudgetStatus:
    """Current budget status."""
    period: BudgetPeriod
    limit_usd: float
    spent_usd: float
    remaining_usd: float
    percent_used: float
    is_exceeded: bool
    is_warning: bool
    timestamp: datetime


class BudgetEnforcer:
    """
    Enforces hard budget limits on API spending.

    Prevents runaway costs from:
    - Agentic loops (5-30x normal token consumption)
    - Context window bloat (re-sending conversation history)
    - Concurrent requests (multiple agents running simultaneously)
    """

    def __init__(self):
        self.limits: List[BudgetLimit] = []
        self.spent_tracking = {
            BudgetPeriod.HOURLY: 0.0,
            BudgetPeriod.DAILY: 0.0,
            BudgetPeriod.MONTHLY: 0.0,
            BudgetPeriod.YEARLY: 0.0,
            BudgetPeriod.TOTAL: 0.0,
        }
        self.last_reset = {
            BudgetPeriod.HOURLY: datetime.now(),
            BudgetPeriod.DAILY: datetime.now(),
            BudgetPeriod.MONTHLY: datetime.now(),
            BudgetPeriod.YEARLY: datetime.now(),
        }
        self.webhook_callbacks: dict[EnforcementAction, List[Callable]] = {
            action: [] for action in EnforcementAction
        }

    def add_limit(self, limit: BudgetLimit):
        """Add a budget limit."""
        self.limits.append(limit)
        logger.info(f"Added budget limit: {limit.limit_usd} USD per {limit.period.value}")

    def add_webhook(self, action: EnforcementAction, callback: Callable):
        """Add callback for enforcement action."""
        self.webhook_callbacks[action].append(callback)

    def check_budget(self, cost_usd: float) -> BudgetStatus:
        """
        Check if a cost can be incurred within budget.

        Raises BudgetExceededError if cost exceeds hard limit.
        """
        self._reset_periods()

        # Check all applicable limits
        exceeded_limits = []
        for limit in self.limits:
            new_spent = self.spent_tracking[limit.period] + cost_usd
            is_exceeded = new_spent > limit.limit_usd
            is_warning = new_spent > (limit.limit_usd * limit.warning_threshold)

            if is_exceeded or is_warning:
                status = BudgetStatus(
                    period=limit.period,
                    limit_usd=limit.limit_usd,
                    spent_usd=new_spent,
                    remaining_usd=max(0, limit.limit_usd - new_spent),
                    percent_used=(new_spent / limit.limit_usd) * 100,
                    is_exceeded=is_exceeded,
                    is_warning=is_warning and not is_exceeded,
                    timestamp=datetime.now()
                )

                if is_exceeded:
                    exceeded_limits.append((limit, status))
                    self._execute_action(limit.action, status)
                elif is_warning:
                    logger.warning(
                        f"Budget warning: {status.percent_used:.1f}% of {limit.period.value} budget used "
                        f"({status.spent_usd:.2f}$ of {status.limit_usd}$)"
                    )

        # If any limit is exceeded, determine what to do
        if exceeded_limits:
            limit, status = exceeded_limits[0]
            if limit.action == EnforcementAction.STOP:
                raise BudgetExceededError(
                    f"Budget exceeded for {limit.period.value}: "
                    f"{status.spent_usd:.2f}$ spent of {status.limit_usd}$ limit"
                )

        # Record the spend
        for period in BudgetPeriod:
            self.spent_tracking[period] += cost_usd

        return status

    def get_status(self) -> dict[BudgetPeriod, BudgetStatus]:
        """Get current budget status for all periods."""
        self._reset_periods()

        status = {}
        for limit in self.limits:
            spent = self.spent_tracking[limit.period]
            status[limit.period] = BudgetStatus(
                period=limit.period,
                limit_usd=limit.limit_usd,
                spent_usd=spent,
                remaining_usd=max(0, limit.limit_usd - spent),
                percent_used=(spent / limit.limit_usd) * 100,
                is_exceeded=spent > limit.limit_usd,
                is_warning=spent > (limit.limit_usd * limit.warning_threshold),
                timestamp=datetime.now()
            )

        return status

    def reset_period(self, period: BudgetPeriod):
        """Manually reset a budget period."""
        self.spent_tracking[period] = 0.0
        self.last_reset[period] = datetime.now()
        logger.info(f"Reset {period.value} budget")

    def _reset_periods(self):
        """Reset periods that have elapsed."""
        now = datetime.now()

        # Hourly
        if (now - self.last_reset[BudgetPeriod.HOURLY]).total_seconds() >= 3600:
            self.spent_tracking[BudgetPeriod.HOURLY] = 0.0
            self.last_reset[BudgetPeriod.HOURLY] = now

        # Daily (reset at midnight)
        if now.date() != self.last_reset[BudgetPeriod.DAILY].date():
            self.spent_tracking[BudgetPeriod.DAILY] = 0.0
            self.last_reset[BudgetPeriod.DAILY] = now

        # Monthly (reset on 1st of month)
        if now.month != self.last_reset[BudgetPeriod.MONTHLY].month:
            self.spent_tracking[BudgetPeriod.MONTHLY] = 0.0
            self.last_reset[BudgetPeriod.MONTHLY] = now

        # Yearly (reset on Jan 1)
        if now.year != self.last_reset[BudgetPeriod.YEARLY].year:
            self.spent_tracking[BudgetPeriod.YEARLY] = 0.0
            self.last_reset[BudgetPeriod.YEARLY] = now

    def _execute_action(self, action: EnforcementAction, status: BudgetStatus):
        """Execute the enforcement action."""
        if action == EnforcementAction.ALERT:
            logger.warning(f"Budget alert: {status.percent_used:.1f}% used ({status.spent_usd:.2f}$)")

        elif action == EnforcementAction.THROTTLE:
            logger.info(f"Throttling requests - budget at {status.percent_used:.1f}%")

        elif action == EnforcementAction.STOP:
            logger.error(
                f"BUDGET EXCEEDED: {status.spent_usd:.2f}$ spent of {status.limit_usd}$ "
                f"limit for {status.period.value}"
            )

        elif action == EnforcementAction.WEBHOOK:
            for callback in self.webhook_callbacks[action]:
                try:
                    callback(status)
                except Exception as e:
                    logger.error(f"Webhook callback failed: {e}")

    def suggest_budget_allocation(self, monthly_budget: float) -> dict:
        """
        Suggest budget allocation across periods based on typical usage patterns.

        Helps teams avoid accidental overspend.
        """
        return {
            "monthly_total": monthly_budget,
            "daily_suggested": monthly_budget / 30,
            "hourly_suggested": monthly_budget / (30 * 24),
            "warning_threshold_pct": 80,
            "hard_stop_action": "STOP",
            "recommendation": (
                "Set a daily limit at 3-5% of monthly budget (1/30) to catch runaway costs early. "
                "Adjust if your usage is bursty. Set action=STOP for automated enforcement."
            )
        }


class BudgetExceededError(Exception):
    """Raised when budget limit is exceeded with STOP action."""
    pass


# Global budget enforcer instance (optional)
_global_enforcer: Optional[BudgetEnforcer] = None


def get_global_enforcer() -> BudgetEnforcer:
    """Get or create global budget enforcer."""
    global _global_enforcer
    if _global_enforcer is None:
        _global_enforcer = BudgetEnforcer()
    return _global_enforcer


def set_budget_limit(
    limit_usd: float,
    period: BudgetPeriod = BudgetPeriod.DAILY,
    action: EnforcementAction = EnforcementAction.STOP
):
    """Convenience function to set a budget limit."""
    enforcer = get_global_enforcer()
    limit = BudgetLimit(
        limit_usd=limit_usd,
        period=period,
        action=action
    )
    enforcer.add_limit(limit)
