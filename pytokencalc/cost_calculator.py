"""
PyTokenCalc v0.6: Multi-provider token cost calculator.
Calculates real costs from LLM API usage with provider-specific token models.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import json
from collections import defaultdict
from .cost_models import UsageData, CostModelRegistry


@dataclass
class ModelPricing:
    """Pricing for different LLM models (legacy, for backwards compatibility)"""
    name: str
    input_rate: float  # per 1M tokens
    output_rate: float  # per 1M tokens
    context_window: int


class PricingModel:
    """Multi-provider pricing database with legacy Claude support"""

    MODELS = {
        # Anthropic Claude
        "claude-3-5-sonnet": ModelPricing(
            name="Claude 3.5 Sonnet",
            input_rate=3.00,
            output_rate=15.00,
            context_window=200_000
        ),
        "claude-3-5-haiku": ModelPricing(
            name="Claude 3.5 Haiku",
            input_rate=0.80,
            output_rate=4.00,
            context_window=200_000
        ),
        "claude-3-opus": ModelPricing(
            name="Claude 3 Opus",
            input_rate=15.00,
            output_rate=75.00,
            context_window=200_000
        ),
        # OpenAI GPT
        "gpt-4o": ModelPricing(
            name="GPT-4o",
            input_rate=2.50,
            output_rate=10.00,
            context_window=128_000
        ),
        "gpt-4o-mini": ModelPricing(
            name="GPT-4o Mini",
            input_rate=0.15,
            output_rate=0.60,
            context_window=128_000
        ),
        # Google Gemini
        "gemini-2-flash": ModelPricing(
            name="Gemini 2 Flash",
            input_rate=0.000000375,
            output_rate=0.0000015,
            context_window=1_000_000
        ),
        # Open-source APIs
        "llama-70b": ModelPricing(
            name="Llama 70B",
            input_rate=0.23,
            output_rate=0.23,
            context_window=8_000
        ),
    }

    DEFAULT_MODEL = "claude-3-5-sonnet"

    @classmethod
    def get_pricing(cls, model: str = DEFAULT_MODEL) -> ModelPricing:
        """Get pricing for a model"""
        return cls.MODELS.get(model, cls.MODELS[cls.DEFAULT_MODEL])

    @classmethod
    def get_all_models(cls) -> Dict[str, ModelPricing]:
        """Get all available models"""
        return cls.MODELS.copy()


@dataclass
class SessionCost:
    """Cost breakdown for a single session"""
    session_id: str
    timestamp: datetime
    project: str
    model: str
    estimated_tokens_in: int
    estimated_tokens_out: int
    cost_usd: float
    breakdown: Dict[str, float]  # "input": X, "output": Y


class CostCalculatorV6:
    """
    PyTokenCalc v0.6: Multi-provider cost calculator with provider-specific token models.
    Supports 20+ cloud providers and 10+ open-source APIs with accurate cost calculation.
    """

    def __init__(self):
        self.model_registry = CostModelRegistry()
        self.costs_tracked: List[UsageData] = []

    def calculate(self, usage: UsageData) -> float:
        """Calculate cost using provider-specific model"""
        cost = self.model_registry.calculate_cost(usage)
        self.costs_tracked.append(usage)
        return cost

    def calculate_batch(self, usages: List[UsageData]) -> List[float]:
        """Calculate costs for multiple operations"""
        return [self.calculate(usage) for usage in usages]

    def total_cost(self, provider: Optional[str] = None, model: Optional[str] = None) -> float:
        """Get total cost with optional filters"""
        total = 0.0
        for usage in self.costs_tracked:
            if provider and usage.provider != provider:
                continue
            if model and usage.model != model:
                continue
            cost = self.model_registry.calculate_cost(usage)
            total += cost
        return total

    def cost_by_provider(self) -> Dict[str, float]:
        """Breakdown costs by provider"""
        breakdown = defaultdict(float)
        for usage in self.costs_tracked:
            cost = self.model_registry.calculate_cost(usage)
            breakdown[usage.provider] += cost
        return dict(breakdown)

    def cost_by_model(self) -> Dict[str, float]:
        """Breakdown costs by model"""
        breakdown = defaultdict(float)
        for usage in self.costs_tracked:
            cost = self.model_registry.calculate_cost(usage)
            breakdown[usage.model] += cost
        return dict(breakdown)

    def cost_by_task_type(self) -> Dict[str, float]:
        """Breakdown costs by task type"""
        breakdown = defaultdict(float)
        for usage in self.costs_tracked:
            task = usage.task_type or "unspecified"
            cost = self.model_registry.calculate_cost(usage)
            breakdown[task] += cost
        return dict(breakdown)

    def get_tracked_operations(self) -> List[UsageData]:
        """Get all tracked operations"""
        return self.costs_tracked.copy()

    def clear(self):
        """Clear all tracked costs"""
        self.costs_tracked.clear()

    def export(self) -> List[Dict]:
        """Export tracked costs as dictionaries"""
        exported = []
        for usage in self.costs_tracked:
            cost = self.model_registry.calculate_cost(usage)
            exported.append({
                "provider": usage.provider,
                "model": usage.model,
                "timestamp": usage.timestamp.isoformat(),
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "input_characters": usage.input_characters,
                "output_characters": usage.output_characters,
                "speed_tier": usage.speed_tier,
                "cost_usd": cost,
                "task_type": usage.task_type,
            })
        return exported


class CostCalculator:
    """Calculates real costs from Claude Code history"""

    def __init__(self, history_path: Optional[str] = None):
        self.history_path = Path(history_path or "~/.claude/history.jsonl").expanduser()
        self.sessions_costs: List[SessionCost] = []
        self.project_costs: Dict[str, float] = defaultdict(float)
        self.daily_costs: Dict[str, float] = defaultdict(float)
        self.model_used = PricingModel.DEFAULT_MODEL
        self._load_and_calculate()

    def _load_and_calculate(self):
        """Load history and calculate costs"""
        if not self.history_path.exists():
            return

        with open(self.history_path, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    self._calculate_session_cost(entry)
                except (json.JSONDecodeError, KeyError):
                    continue

    def _calculate_session_cost(self, entry: Dict):
        """Calculate cost for a single history entry"""
        session_id = entry.get("sessionId", "unknown")
        timestamp_ms = entry.get("timestamp", 0)
        timestamp = datetime.fromtimestamp(timestamp_ms / 1000) if timestamp_ms else datetime.now()
        project_path = entry.get("project", "unknown")
        display = entry.get("display", "")

        # Extract project name from path
        project = self._extract_project_name(project_path, display)

        # Estimate tokens based on content length
        estimated_input_tokens = self._estimate_input_tokens(display)
        estimated_output_tokens = self._estimate_output_tokens(display)

        # Calculate cost
        pricing = PricingModel.get_pricing(self.model_used)
        input_cost = (estimated_input_tokens * pricing.input_rate) / 1_000_000
        output_cost = (estimated_output_tokens * pricing.output_rate) / 1_000_000
        total_cost = input_cost + output_cost

        # Create session cost record
        session_cost = SessionCost(
            session_id=session_id,
            timestamp=timestamp,
            project=project,  # Use extracted project name
            model=self.model_used,
            estimated_tokens_in=estimated_input_tokens,
            estimated_tokens_out=estimated_output_tokens,
            cost_usd=total_cost,
            breakdown={
                "input": input_cost,
                "output": output_cost,
            }
        )

        self.sessions_costs.append(session_cost)

        # Aggregate by project and day
        self.project_costs[session_cost.project] += total_cost

        date_key = timestamp.strftime("%Y-%m-%d")
        self.daily_costs[date_key] += total_cost

    def _extract_project_name(self, project_path: str, display: str) -> str:
        """
        Extract project name from path and display text.
        Looks for known project directories first, then text patterns.
        """
        path_lower = project_path.lower()
        display_lower = display.lower()

        # Map of project identifiers
        known_projects = {
            "statguard": ["statguard"],
            "clusteraudiencekit": ["clusteraudiencekit", "audience"],
            "prismnote": ["prismnote", "notebook"],
            "pyroboframes": ["pyroboframes", "robot", "mlx"],
            "streamxl": ["streamxl", "excel"],
            "pytokencalc": ["pytokencalc", "cost audit"],
        }

        # Check path first
        for project_name, keywords in known_projects.items():
            for keyword in keywords:
                if keyword in path_lower:
                    return project_name

        # Check display text
        for project_name, keywords in known_projects.items():
            for keyword in keywords:
                if keyword in display_lower:
                    return project_name

        # Default: use last part of path
        path_parts = project_path.split("/")
        for part in reversed(path_parts):
            if part and part not in ["Users", "georgimullassery", "~"]:
                return part.lower()

        return "other"

    def _estimate_input_tokens(self, text: str) -> int:
        """
        Estimate input tokens from text.
        Rough estimate: 1 token ≈ 4 characters
        """
        # Length of display text + assume some context from history
        base_tokens = len(text) // 4
        # Add context overhead for Claude Code (typical: 500-2000 tokens)
        context_tokens = 1000
        return base_tokens + context_tokens

    def _estimate_output_tokens(self, text: str) -> int:
        """
        Estimate output tokens.
        For Claude Code: typical responses are 500-3000 tokens
        """
        # Estimate based on query complexity
        word_count = len(text.split())

        if word_count < 20:
            # Short query, short response
            return 500
        elif word_count < 50:
            # Medium query, medium response
            return 1500
        else:
            # Long query, likely long response
            return 3000

    def get_project_costs(self, project: str = None) -> Dict[str, float]:
        """Get costs by project or specific project"""
        if project:
            return {project: self.project_costs.get(project, 0.0)}
        return dict(self.project_costs)

    def get_daily_costs(self, days: int = 30) -> Dict[str, float]:
        """Get last N days of costs"""
        sorted_days = sorted(self.daily_costs.items())
        if len(sorted_days) > days:
            sorted_days = sorted_days[-days:]
        return dict(sorted_days)

    def get_total_cost(self) -> float:
        """Get total cost across all projects"""
        return sum(self.project_costs.values())

    def get_average_daily_cost(self) -> float:
        """Get average daily cost"""
        if not self.daily_costs:
            return 0.0
        return self.get_total_cost() / len(self.daily_costs)

    def get_cost_breakdown(self) -> Dict:
        """Get comprehensive cost breakdown"""
        total = self.get_total_cost()
        avg_daily = self.get_average_daily_cost()

        # Sort projects by cost
        sorted_projects = sorted(
            self.project_costs.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return {
            "total_cost_usd": round(total, 2),
            "average_daily_cost_usd": round(avg_daily, 2),
            "sessions_count": len(self.sessions_costs),
            "projects": {
                project: {
                    "cost_usd": round(cost, 2),
                    "percentage": round((cost / total * 100) if total > 0 else 0, 1),
                }
                for project, cost in sorted_projects
            },
            "model_used": self.model_used,
            "estimated_total_tokens": sum(
                s.estimated_tokens_in + s.estimated_tokens_out
                for s in self.sessions_costs
            ),
        }

    def detect_anomalies(self, threshold_multiplier: float = 2.0) -> List[Dict]:
        """
        Detect unusually expensive sessions.

        Args:
            threshold_multiplier: Sessions costing >N times average are anomalies

        Returns:
            List of anomalous sessions with details
        """
        if not self.sessions_costs:
            return []

        avg_cost = sum(s.cost_usd for s in self.sessions_costs) / len(self.sessions_costs)
        threshold = avg_cost * threshold_multiplier

        anomalies = []
        for session in self.sessions_costs:
            if session.cost_usd > threshold:
                anomalies.append({
                    "session_id": session.session_id,
                    "timestamp": session.timestamp.isoformat(),
                    "project": session.project,
                    "cost_usd": round(session.cost_usd, 4),
                    "multiplier": round(session.cost_usd / avg_cost, 1),
                    "tokens_in": session.estimated_tokens_in,
                    "tokens_out": session.estimated_tokens_out,
                })

        # Sort by cost (most expensive first)
        return sorted(anomalies, key=lambda x: x["cost_usd"], reverse=True)

    def get_project_trends(self, project: str) -> Dict:
        """
        Get cost trends for a specific project.

        Returns:
            Weekly breakdown, trend direction, etc.
        """
        project_sessions = [s for s in self.sessions_costs if s.project == project]

        if not project_sessions:
            return {"error": f"No sessions found for project: {project}"}

        # Group by week
        weekly_costs = defaultdict(float)
        for session in project_sessions:
            week_key = session.timestamp.strftime("%Y-W%U")
            weekly_costs[week_key] += session.cost_usd

        sorted_weeks = sorted(weekly_costs.items())

        # Calculate trend
        if len(sorted_weeks) > 1:
            first_week_avg = sum(v for _, v in sorted_weeks[:len(sorted_weeks)//2]) / max(1, len(sorted_weeks)//2)
            last_week_avg = sum(v for _, v in sorted_weeks[len(sorted_weeks)//2:]) / max(1, len(sorted_weeks) - len(sorted_weeks)//2)
            trend = "↑ increasing" if last_week_avg > first_week_avg else "↓ decreasing"
        else:
            trend = "→ stable (not enough data)"

        return {
            "project": project,
            "total_cost_usd": round(sum(weekly_costs.values()), 2),
            "sessions": len(project_sessions),
            "weekly_breakdown": {
                week: round(cost, 2)
                for week, cost in sorted_weeks
            },
            "trend": trend,
            "average_per_week": round(sum(weekly_costs.values()) / len(weekly_costs), 2) if weekly_costs else 0,
        }

    def get_top_expensive_sessions(self, count: int = 10) -> List[Dict]:
        """Get the N most expensive sessions"""
        sorted_sessions = sorted(
            self.sessions_costs,
            key=lambda x: x.cost_usd,
            reverse=True
        )

        return [
            {
                "rank": i + 1,
                "session_id": s.session_id,
                "timestamp": s.timestamp.isoformat(),
                "project": s.project,
                "cost_usd": round(s.cost_usd, 4),
                "tokens_in": s.estimated_tokens_in,
                "tokens_out": s.estimated_tokens_out,
            }
            for i, s in enumerate(sorted_sessions[:count])
        ]

    def forecast_monthly_cost(self, months_ahead: int = 3) -> Dict:
        """
        Forecast costs for the next N months based on current trend.

        Returns:
            Projections for 30, 60, 90 days
        """
        avg_daily = self.get_average_daily_cost()

        return {
            "current_daily_average_usd": round(avg_daily, 2),
            "30_day_forecast_usd": round(avg_daily * 30, 2),
            "60_day_forecast_usd": round(avg_daily * 60, 2),
            "90_day_forecast_usd": round(avg_daily * 90, 2),
            "yearly_forecast_usd": round(avg_daily * 365, 2),
            "note": "Based on current usage patterns. Assumes steady usage.",
        }

    def compare_model_costs(self, project: str = None) -> Dict:
        """
        Show cost comparison if using different models.

        What if you switched to Haiku for some tasks?
        """
        # Get sessions for project or all
        sessions = self.sessions_costs
        if project:
            sessions = [s for s in sessions if s.project == project]

        current_cost = sum(s.cost_usd for s in sessions)

        # Simulate switching to different models
        comparisons = {}
        for model_name, pricing in PricingModel.get_all_models().items():
            simulated_cost = 0
            for s in sessions:
                input_cost = (s.estimated_tokens_in * pricing.input_rate) / 1_000_000
                output_cost = (s.estimated_tokens_out * pricing.output_rate) / 1_000_000
                simulated_cost += input_cost + output_cost

            savings = current_cost - simulated_cost
            savings_pct = (savings / current_cost * 100) if current_cost > 0 else 0

            comparisons[model_name] = {
                "name": pricing.name,
                "total_cost_usd": round(simulated_cost, 2),
                "savings_usd": round(savings, 2),
                "savings_percentage": round(savings_pct, 1),
            }

        return {
            "current_model": self.model_used,
            "current_cost_usd": round(current_cost, 2),
            "comparisons": comparisons,
        }
