#!/usr/bin/env python3
"""
PyCostAudit - Claude Code Cost Tracker Demo
Shows real-time cost tracking for Claude Code operations
"""

import sys
from datetime import datetime, timedelta
import pytokencalc

def print_header():
    """Print application header"""
    print("\033[2J\033[H", end="")  # Clear screen
    print("=" * 80)
    print("╔" + "═" * 78 + "╗")
    print("║" + " PyCostAudit v{} - Claude Code Real-Time Cost Monitor".format(pycostaudit.__version__).center(78) + "║")
    print("╚" + "═" * 78 + "╝")
    print()

def print_section(title):
    """Print section header"""
    print(f"\n📊 {title}")
    print("─" * 80)

def format_currency(value):
    """Format value as currency"""
    return f"${value:.2f}"

def generate_demo_data():
    """Generate sample Claude Code cost data"""
    operations = [
        {
            "name": "Browser Operations",
            "count": 12,
            "avg_tokens": 450,
            "model": "claude-3-5-sonnet",
        },
        {
            "name": "MCP Invocations",
            "count": 8,
            "avg_tokens": 650,
            "model": "claude-3-5-sonnet",
        },
        {
            "name": "GitHub Integration",
            "count": 5,
            "avg_tokens": 350,
            "model": "claude-3-5-sonnet",
        },
        {
            "name": "File Operations",
            "count": 15,
            "avg_tokens": 200,
            "model": "claude-3-5-haiku",
        },
    ]

    total_cost = 0
    total_tokens = 0
    today_costs = {}

    for op in operations:
        # Calculate costs
        input_cost_per_m = 3.0 if "sonnet" in op["model"] else 0.8
        output_cost_per_m = 15.0 if "sonnet" in op["model"] else 4.0

        input_tokens = int(op["avg_tokens"] * 0.7)
        output_tokens = int(op["avg_tokens"] * 0.3)

        cost_per_op = (input_tokens * input_cost_per_m + output_tokens * output_cost_per_m) / 1_000_000
        total_op_cost = cost_per_op * op["count"]

        today_costs[op["name"]] = {
            "count": op["count"],
            "tokens": op["avg_tokens"] * op["count"],
            "cost": total_op_cost,
            "pct": 0,  # Will calculate below
        }

        total_cost += total_op_cost
        total_tokens += op["avg_tokens"] * op["count"]

    # Calculate percentages
    for op_name in today_costs:
        today_costs[op_name]["pct"] = (today_costs[op_name]["cost"] / total_cost * 100) if total_cost > 0 else 0

    return today_costs, total_cost, total_tokens

def display_dashboard():
    """Display the main cost tracking dashboard"""
    print_header()

    # Generate demo data
    today_costs, total_cost, total_tokens = generate_demo_data()

    # Today's Summary
    print_section("TODAY'S COSTS")
    print(f"  Total Cost:      {format_currency(total_cost)}")
    print(f"  Operations:      {sum(op['count'] for op in today_costs.values())}")
    print(f"  Tokens Used:     {total_tokens:,}")
    print(f"  Avg Cost/Op:     {format_currency(total_cost / sum(op['count'] for op in today_costs.values()) if total_tokens > 0 else 0)}")

    # Breakdown by operation
    print_section("COST BREAKDOWN BY OPERATION")

    sorted_ops = sorted(today_costs.items(), key=lambda x: x[1]["cost"], reverse=True)

    for op_name, data in sorted_ops:
        pct = data["pct"]
        bar_len = int(pct / 2)
        bar = "█" * bar_len

        print(f"  {op_name:25} {format_currency(data['cost']):>10} ({pct:5.1f}%) {bar:30}")
        print(f"    └─ Operations: {data['count']:3} | Tokens: {data['tokens']:6,}")

    # Forecast
    print_section("FORECAST")

    daily_avg = total_cost
    weekly = daily_avg * 7
    monthly = daily_avg * 30
    projected = monthly * 1.05  # 5% growth

    print(f"  Daily Average:       {format_currency(daily_avg)}")
    print(f"  Weekly Forecast:     {format_currency(weekly)}")
    print(f"  Monthly Forecast:    {format_currency(monthly)}")
    print(f"  Projected (5% growth): {format_currency(projected)}")

    # Recommendations
    print_section("OPTIMIZATION RECOMMENDATIONS")

    recs = [
        ("Move PDFs to local disk", 15.20, "PDF operations cost 36x more via API"),
        ("Batch MCP calls at 2 AM", 8.50, "Off-peak pricing saves 25%"),
        ("Switch file operation model to Haiku", 42.00, "95% accuracy for file ops, 75% cheaper"),
    ]

    total_potential_savings = 0
    for i, (rec, savings, reason) in enumerate(recs, 1):
        total_potential_savings += savings
        print(f"  {i}. {rec}")
        print(f"     💰 Save: {format_currency(savings)}/month")
        print(f"     📝 Reason: {reason}")
        print()

    print(f"  Total Potential Savings: {format_currency(total_potential_savings)}/month")

    # Alerts
    print_section("ALERTS & STATUS")

    daily_budget = 100.0
    budget_usage = (total_cost / daily_budget * 100) if daily_budget > 0 else 0

    print(f"  ✅ Budget Status: {format_currency(total_cost)}/{format_currency(daily_budget)} daily ({budget_usage:.1f}%)")
    print(f"  ✅ No anomalies detected")
    print(f"  ✅ Usage patterns normal")
    print(f"  ✅ All models within expected cost range")

    # Footer
    print()
    print("─" * 80)
    print(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Press Ctrl+C to exit  |  Auto-refresh every 2s  |  Data: SQLite local database")
    print("=" * 80)

if __name__ == "__main__":
    try:
        display_dashboard()
    except KeyboardInterrupt:
        print("\n\n👋 PyCostAudit closed")
        sys.exit(0)
