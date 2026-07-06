#!/usr/bin/env python3
"""Claude Code cost tracking report - comprehensive insights on first run."""

import sqlite3
from datetime import datetime
from collections import defaultdict

db_path = '/Users/georgimullassery/.pycostaudit/costs.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("\n" + "=" * 80)
print("CLAUDE CODE COST AUDIT REPORT")
print("=" * 80)
print(f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# 1. SESSION COSTS OVERVIEW
print("1️⃣  RECENT SESSION ACTIVITY")
print("-" * 80)
cursor.execute("SELECT * FROM session_costs ORDER BY timestamp DESC LIMIT 10")
sessions = cursor.fetchall()
total_sessions = cursor.execute("SELECT COUNT(*) FROM session_costs").fetchone()[0]
print(f"Total recorded sessions: {total_sessions}\n")
print(f"{'Date':<12} {'Model':<25} {'Input':<8} {'Output':<8} {'Cost':<10}")
print("-" * 80)
total_in = total_out = total_cost = 0
for row in sessions:
    date_str = row['timestamp'][:10] if row['timestamp'] else "N/A"
    model = row['model'][:25] if row['model'] else "N/A"
    print(f"{date_str:<12} {model:<25} {row['estimated_tokens_in']:<8} {row['estimated_tokens_out']:<8} ${row['cost_usd']:<9.4f}")
    total_in += row['estimated_tokens_in']
    total_out += row['estimated_tokens_out']
    total_cost += row['cost_usd']

# 2. DAILY COST TRENDS
print("\n" + "=" * 80)
print("2️⃣  DAILY COST TRENDS & PATTERNS")
print("-" * 80)
cursor.execute("SELECT date, total_cost_usd, session_count FROM daily_costs ORDER BY date DESC LIMIT 10")
daily_costs = cursor.fetchall()
daily_costs_list = [row['total_cost_usd'] for row in reversed(daily_costs)]
print(f"{'Date':<12} {'Cost':<10} {'Sessions':<10}")
print("-" * 80)
for row in reversed(daily_costs):
    print(f"{row['date']:<12} ${row['total_cost_usd']:<9.4f} {row['session_count']:<10}")

if daily_costs_list:
    avg_daily = sum(daily_costs_list) / len(daily_costs_list)
    print(f"\nAverage daily: ${avg_daily:.4f} | Monthly projection: ${avg_daily * 30:.2f}")

# 3. MODEL COST BREAKDOWN
print("\n" + "=" * 80)
print("3️⃣  MODEL COST BREAKDOWN")
print("-" * 80)
cursor.execute("""
    SELECT model, COUNT(*) as count,
           SUM(estimated_tokens_in) as total_input,
           SUM(estimated_tokens_out) as total_output,
           SUM(cost_usd) as total_cost
    FROM session_costs
    GROUP BY model
    ORDER BY total_cost DESC
""")
model_data = cursor.fetchall()
total_all_cost = sum(row['total_cost'] for row in model_data)
print(f"{'Model':<30} {'Sessions':<10} {'Cost':<10} {'% of Total':<12}")
print("-" * 80)
for row in model_data:
    pct = (row['total_cost'] / total_all_cost * 100) if total_all_cost > 0 else 0
    print(f"{row['model']:<30} {row['count']:<10} ${row['total_cost']:<9.4f} {pct:>10.1f}%")

# 4. PROJECT COST DISTRIBUTION
print("\n" + "=" * 80)
print("4️⃣  PROJECT COST DISTRIBUTION")
print("-" * 80)
cursor.execute("""
    SELECT project, SUM(total_cost_usd) as total, COUNT(*) as sessions
    FROM project_costs
    GROUP BY project
    ORDER BY total DESC
""")
project_data = cursor.fetchall()
print(f"{'Project':<25} {'Cost':<12} {'Sessions':<10} {'% Share':<10}")
print("-" * 80)
total_project_cost = sum(row['total'] for row in project_data)
for row in project_data:
    pct = (row['total'] / total_project_cost * 100) if total_project_cost > 0 else 0
    print(f"{row['project']:<25} ${row['total']:<11.4f} {row['sessions']:<10} {pct:>8.1f}%")

# 5. TOKEN EFFICIENCY
print("\n" + "=" * 80)
print("5️⃣  TOKEN EFFICIENCY METRICS")
print("-" * 80)
cursor.execute("""
    SELECT model,
           COUNT(*) as operations,
           AVG(estimated_tokens_in) as avg_input,
           AVG(estimated_tokens_out) as avg_output,
           SUM(estimated_tokens_in + estimated_tokens_out) as total_tokens
    FROM session_costs
    GROUP BY model
""")
efficiency = cursor.fetchall()
print(f"{'Model':<30} {'Ops':<6} {'Avg Input':<12} {'Avg Output':<12} {'Total Tokens':<12}")
print("-" * 80)
for row in efficiency:
    print(f"{row['model']:<30} {row['operations']:<6} {row['avg_input']:<12.0f} {row['avg_output']:<12.0f} {row['total_tokens']:<12,}")

# 6. COST EFFICIENCY
print("\n" + "=" * 80)
print("6️⃣  COST PER 1K TOKENS (Lower is better)")
print("-" * 80)
cursor.execute("""
    SELECT model,
           ROUND(SUM(cost_usd) / (SUM(estimated_tokens_in + estimated_tokens_out) / 1000.0), 4) as cost_per_1k
    FROM session_costs
    GROUP BY model
    ORDER BY cost_per_1k
""")
cost_eff = cursor.fetchall()
print(f"{'Model':<30} {'Cost per 1K tokens':<20}")
print("-" * 80)
for row in cost_eff:
    print(f"{row['model']:<30} ${row['cost_per_1k']:<19.4f}")

# 7. SPENDING VELOCITY
print("\n" + "=" * 80)
print("7️⃣  SPENDING VELOCITY TREND (Last 7 days)")
print("-" * 80)
cursor.execute("""
    SELECT DATE(timestamp) as date, COUNT(*) as ops, SUM(cost_usd) as daily_cost
    FROM session_costs
    GROUP BY DATE(timestamp)
    ORDER BY date DESC
    LIMIT 7
""")
velocity = cursor.fetchall()
print(f"{'Date':<12} {'Operations':<15} {'Daily Cost':<15}")
print("-" * 80)
for row in velocity:
    print(f"{row['date']:<12} {row['ops']:<15} ${row['daily_cost']:<14.4f}")

# Trend analysis
if len(velocity) >= 3:
    recent_avg = sum(row['daily_cost'] for row in velocity[:3]) / 3
    older_avg = sum(row['daily_cost'] for row in velocity[3:]) / len(velocity[3:]) if len(velocity) > 3 else recent_avg
    trend_pct = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
    trend_dir = "📈 INCREASING" if trend_pct > 5 else "📉 DECREASING" if trend_pct < -5 else "➡️  STABLE"
    print(f"\nTrend: {trend_dir} ({trend_pct:+.1f}%)")

# 8. INPUT/OUTPUT RATIO
print("\n" + "=" * 80)
print("8️⃣  INPUT/OUTPUT TOKEN RATIO")
print("-" * 80)
cursor.execute("""
    SELECT model,
           SUM(estimated_tokens_in) as total_input,
           SUM(estimated_tokens_out) as total_output,
           ROUND(CAST(SUM(estimated_tokens_in) AS FLOAT) /
                 CAST(SUM(estimated_tokens_out) AS FLOAT), 2) as ratio
    FROM session_costs
    GROUP BY model
""")
ratios = cursor.fetchall()
print(f"{'Model':<30} {'Input Tokens':<15} {'Output Tokens':<15} {'Ratio':<10}")
print("-" * 80)
for row in ratios:
    print(f"{row['model']:<30} {row['total_input']:<15,} {row['total_output']:<15,} {row['ratio']:.2f}:1")

# 9. OPTIMIZATION OPPORTUNITIES
print("\n" + "=" * 80)
print("9️⃣  OPTIMIZATION OPPORTUNITIES")
print("-" * 80)

# Find most expensive model
cursor.execute("SELECT model, SUM(cost_usd) as total FROM session_costs GROUP BY model ORDER BY total DESC LIMIT 1")
most_expensive = cursor.fetchone()

# Find most efficient model
cursor.execute("""
    SELECT model, ROUND(SUM(cost_usd) / (SUM(estimated_tokens_in + estimated_tokens_out) / 1000.0), 4) as cost_per_1k
    FROM session_costs
    GROUP BY model
    ORDER BY cost_per_1k
    LIMIT 1
""")
most_efficient = cursor.fetchone()

print(f"✗ Highest cost model: {most_expensive['model']} (${most_expensive['total']:.4f})")
print(f"✓ Most efficient model: {most_efficient['model']} (${most_efficient['cost_per_1k']:.4f} per 1K tokens)")

# Estimate savings
savings_potential = total_all_cost * 0.15
print(f"\n💡 Potential Monthly Savings: ${savings_potential:.2f} (15% reduction)")
print(f"   Strategies:")
print(f"   • Route simple tasks to more efficient models")
print(f"   • Batch similar operations to reduce overhead")
print(f"   • Cache frequently requested information")

# 10. COST FORECAST
print("\n" + "=" * 80)
print("🔟 COST FORECAST (Next 30/90 days)")
print("-" * 80)
if daily_costs_list and len(daily_costs_list) > 1:
    avg_daily = sum(daily_costs_list) / len(daily_costs_list)
    next_7_days = avg_daily * 7
    next_30_days = avg_daily * 30
    next_90_days = avg_daily * 90

    print(f"Based on average daily spend: ${avg_daily:.4f}")
    print(f"  • Next 7 days:   ${next_7_days:.2f}")
    print(f"  • Next 30 days:  ${next_30_days:.2f}")
    print(f"  • Next 90 days:  ${next_90_days:.2f}")

# SUMMARY
print("\n" + "=" * 80)
print("📊 SUMMARY")
print("=" * 80)
print(f"Total historical cost: ${total_all_cost:.4f}")
print(f"Sessions analyzed: {total_sessions}")
if daily_costs:
    print(f"Date range: {daily_costs[-1]['date']} to {daily_costs[0]['date']}")
print(f"Models tracked: {len(model_data)}")
print(f"Projects: {len(project_data)}")

conn.close()
print("\n" + "=" * 80 + "\n")
