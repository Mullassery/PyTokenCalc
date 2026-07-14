#!/usr/bin/env python3
"""
PyCostAudit Claude Code Skill
Tracks and displays LLM costs in real-time within Claude Code.

Installation: /install pycostaudit-skill
Usage: /cost-audit track|report|forecast
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from pytokencalc.cost_model import CostTracker
from pytokencalc.alerting import AlertEngine, AlertType, AlertSeverity


class ClaudeCodeSkill:
    """PyCostAudit skill for Claude Code integration"""

    def __init__(self):
        self.tracker = CostTracker()
        self.alert_engine = AlertEngine()
        self.db_path = Path.home() / ".pycostaudit" / "skill_data.json"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.load_session()

    def load_session(self):
        """Load previous session data"""
        if self.db_path.exists():
            with open(self.db_path) as f:
                data = json.load(f)
                self.session_id = data.get("session_id")
                self.costs = data.get("costs", [])
        else:
            self.session_id = f"session-{datetime.now().isoformat()}"
            self.costs = []

    def save_session(self):
        """Save session data"""
        with open(self.db_path, "w") as f:
            json.dump({
                "session_id": self.session_id,
                "costs": self.costs,
                "last_updated": datetime.now().isoformat()
            }, f, indent=2)

    def track_operation(self, operation_type: str, tokens_input: int, tokens_output: int, model: str = "claude-opus-4-8"):
        """Track a Claude Code operation"""
        cost_data = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation_type,
            "model": model,
            "input_tokens": tokens_input,
            "output_tokens": tokens_output,
            "total_tokens": tokens_input + tokens_output,
        }

        # Estimate cost (Claude Pro pricing)
        # Update this based on your plan:
        # Claude Pro: $3.00 input / $15.00 output
        # Claude Opus 4.8: $15.00 input / $75.00 output
        input_cost = (tokens_input / 1_000_000) * 3.00
        output_cost = (tokens_output / 1_000_000) * 15.00
        cost_data["estimated_cost"] = input_cost + output_cost

        self.costs.append(cost_data)
        self.save_session()

        return cost_data

    def get_daily_report(self) -> dict:
        """Get today's cost report"""
        today = datetime.now().date()
        today_costs = [
            c for c in self.costs
            if datetime.fromisoformat(c["timestamp"]).date() == today
        ]

        total_cost = sum(c["estimated_cost"] for c in today_costs)
        total_tokens = sum(c["total_tokens"] for c in today_costs)
        total_operations = len(today_costs)

        # Breakdown by operation
        by_operation = {}
        by_model = {}
        for c in today_costs:
            op = c["operation"]
            by_operation[op] = by_operation.get(op, 0) + c["estimated_cost"]
            model = c["model"]
            by_model[model] = by_model.get(model, 0) + c["estimated_cost"]

        return {
            "date": str(today),
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "total_operations": total_operations,
            "by_operation": by_operation,
            "by_model": by_model,
            "average_cost_per_op": total_cost / total_operations if total_operations > 0 else 0,
        }

    def get_weekly_forecast(self) -> dict:
        """Forecast weekly spending"""
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)

        week_costs = [
            c for c in self.costs
            if datetime.fromisoformat(c["timestamp"]).date() >= week_ago
        ]

        daily_totals = {}
        for c in week_costs:
            date = datetime.fromisoformat(c["timestamp"]).date()
            daily_totals[str(date)] = daily_totals.get(str(date), 0) + c["estimated_cost"]

        if daily_totals:
            avg_daily = sum(daily_totals.values()) / len(daily_totals)
            weekly_forecast = avg_daily * 7
            monthly_forecast = avg_daily * 30
        else:
            avg_daily = weekly_forecast = monthly_forecast = 0

        return {
            "period": "last_7_days",
            "daily_average": avg_daily,
            "weekly_forecast": weekly_forecast,
            "monthly_forecast": monthly_forecast,
            "daily_breakdown": daily_totals,
        }

    def get_alerts(self) -> list:
        """Check for cost alerts"""
        report = self.get_daily_report()
        alerts = []

        # Daily budget alert (assuming $50/day budget)
        daily_budget = 50.0
        if report["total_cost"] > daily_budget * 0.75:
            alerts.append({
                "type": "budget_warning",
                "severity": "high" if report["total_cost"] > daily_budget else "medium",
                "message": f"Daily spend (${report['total_cost']:.2f}) is {(report['total_cost']/daily_budget)*100:.0f}% of daily budget (${daily_budget})",
            })

        # High operation cost alert
        if report["by_operation"]:
            most_expensive = max(report["by_operation"].items(), key=lambda x: x[1])
            if most_expensive[1] > report["total_cost"] * 0.5:
                alerts.append({
                    "type": "high_operation_cost",
                    "severity": "medium",
                    "message": f"Operation '{most_expensive[0]}' uses {(most_expensive[1]/report['total_cost'])*100:.0f}% of daily budget",
                })

        return alerts

    def format_report(self) -> str:
        """Format report for Claude Code display"""
        report = self.get_daily_report()
        forecast = self.get_weekly_forecast()
        alerts = self.get_alerts()

        output = []
        output.append("=" * 70)
        output.append("📊 PyCostAudit - Claude Code Cost Tracking")
        output.append("=" * 70)
        output.append("")

        # Today's summary
        output.append(f"📈 TODAY'S COSTS ({report['date']})")
        output.append(f"  Total Cost:        ${report['total_cost']:.4f}")
        output.append(f"  Operations:        {report['total_operations']}")
        output.append(f"  Tokens:            {report['total_tokens']:,}")
        output.append(f"  Avg Cost/Op:       ${report['average_cost_per_op']:.4f}")
        output.append("")

        # By operation
        if report["by_operation"]:
            output.append("📂 Cost by Operation:")
            for op, cost in sorted(report["by_operation"].items(), key=lambda x: x[1], reverse=True):
                pct = (cost / report["total_cost"] * 100) if report["total_cost"] > 0 else 0
                output.append(f"  • {op:25s} ${cost:8.4f} ({pct:5.1f}%)")
            output.append("")

        # By model
        if report["by_model"]:
            output.append("🤖 Cost by Model:")
            for model, cost in sorted(report["by_model"].items(), key=lambda x: x[1], reverse=True):
                pct = (cost / report["total_cost"] * 100) if report["total_cost"] > 0 else 0
                output.append(f"  • {model:30s} ${cost:8.4f} ({pct:5.1f}%)")
            output.append("")

        # Weekly forecast
        output.append("📅 Weekly Forecast:")
        output.append(f"  Daily Average:     ${forecast['daily_average']:.4f}")
        output.append(f"  Weekly Forecast:   ${forecast['weekly_forecast']:.2f}")
        output.append(f"  Monthly Forecast:  ${forecast['monthly_forecast']:.2f}")
        output.append("")

        # Alerts
        if alerts:
            output.append("⚠️  Alerts:")
            for alert in alerts:
                severity = "🔴" if alert["severity"] == "high" else "🟡"
                output.append(f"  {severity} {alert['message']}")
            output.append("")

        output.append("=" * 70)
        return "\n".join(output)


def main():
    """CLI interface for the skill"""
    skill = ClaudeCodeSkill()

    if len(sys.argv) < 2:
        print(skill.format_report())
        return

    command = sys.argv[1].lower()

    if command == "track":
        # Simulate tracking an operation
        operation = sys.argv[2] if len(sys.argv) > 2 else "code_generation"
        input_tokens = int(sys.argv[3]) if len(sys.argv) > 3 else 2000
        output_tokens = int(sys.argv[4]) if len(sys.argv) > 4 else 500

        cost = skill.track_operation(operation, input_tokens, output_tokens)
        print(f"✅ Tracked operation: {operation}")
        print(f"   Cost: ${cost['estimated_cost']:.4f}")

    elif command == "report":
        print(skill.format_report())

    elif command == "forecast":
        forecast = skill.get_weekly_forecast()
        print("📅 Weekly Forecast:")
        print(f"  Daily Average:    ${forecast['daily_average']:.4f}")
        print(f"  Weekly Forecast:  ${forecast['weekly_forecast']:.2f}")
        print(f"  Monthly Forecast: ${forecast['monthly_forecast']:.2f}")

    elif command == "alerts":
        alerts = skill.get_alerts()
        if alerts:
            print("⚠️  Active Alerts:")
            for alert in alerts:
                print(f"  [{alert['severity'].upper()}] {alert['message']}")
        else:
            print("✅ No alerts")

    else:
        print(f"Unknown command: {command}")
        print("Usage: pycostaudit-skill [track|report|forecast|alerts]")


if __name__ == "__main__":
    main()
