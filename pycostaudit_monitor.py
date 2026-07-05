#!/usr/bin/env python3
"""
Real-time Claude Code Cost Monitor
Shows live cost tracking in terminal with auto-refresh.

Usage: python pycostaudit_monitor.py [--refresh 2] [--watch-file /path/to/log]
"""

import os
import sys
import json
import time
import curses
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import argparse


class CostMonitor:
    """Real-time cost monitoring dashboard"""

    def __init__(self, refresh_interval: int = 2):
        self.refresh_interval = refresh_interval
        self.db_path = Path.home() / ".pycostaudit" / "skill_data.json"
        self.data = {"costs": []}
        self.load_data()

    def load_data(self):
        """Load cost data from disk"""
        if self.db_path.exists():
            try:
                with open(self.db_path) as f:
                    self.data = json.load(f)
            except:
                self.data = {"costs": []}

    def get_today_stats(self) -> dict:
        """Calculate today's statistics"""
        today = datetime.now().date()
        today_costs = [
            c for c in self.data.get("costs", [])
            if datetime.fromisoformat(c.get("timestamp", "")).date() == today
        ]

        total = sum(c.get("estimated_cost", 0) for c in today_costs)
        tokens = sum(c.get("total_tokens", 0) for c in today_costs)

        by_op = defaultdict(float)
        by_model = defaultdict(float)
        for c in today_costs:
            by_op[c.get("operation", "unknown")] += c.get("estimated_cost", 0)
            by_model[c.get("model", "unknown")] += c.get("estimated_cost", 0)

        return {
            "total": total,
            "tokens": tokens,
            "count": len(today_costs),
            "by_op": dict(sorted(by_op.items(), key=lambda x: x[1], reverse=True)),
            "by_model": dict(sorted(by_model.items(), key=lambda x: x[1], reverse=True)),
        }

    def get_weekly_forecast(self) -> dict:
        """Calculate weekly forecast"""
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)

        week_costs = [
            c for c in self.data.get("costs", [])
            if datetime.fromisoformat(c.get("timestamp", "")).date() >= week_ago
        ]

        daily_totals = {}
        for c in week_costs:
            date = datetime.fromisoformat(c.get("timestamp", "")).date()
            daily_totals[str(date)] = daily_totals.get(str(date), 0) + c.get("estimated_cost", 0)

        if daily_totals:
            avg_daily = sum(daily_totals.values()) / len(daily_totals)
            weekly_forecast = avg_daily * 7
            monthly_forecast = avg_daily * 30
        else:
            avg_daily = weekly_forecast = monthly_forecast = 0

        return {
            "daily_average": avg_daily,
            "weekly_forecast": weekly_forecast,
            "monthly_forecast": monthly_forecast,
        }

    def get_sparkline(self, values: list, width: int = 10) -> str:
        """Generate ASCII sparkline"""
        if not values:
            return "▁" * width

        chars = "▁▂▃▄▅▆▇█"
        max_val = max(values) if values else 1
        min_val = min(values) if values else 0

        if max_val == min_val:
            result = chars[0] * width
        else:
            range_val = max_val - min_val
            result = ""
            for val in values[-width:]:
                if range_val > 0:
                    idx = int(((val - min_val) / range_val) * (len(chars) - 1))
                else:
                    idx = 0
                result += chars[min(idx, len(chars) - 1)]

        return result if result else "▁" * width

    def draw_text_ui(self):
        """Draw text-based dashboard (non-interactive)"""
        while True:
            os.system("clear" if os.name != "nt" else "cls")
            self.load_data()
            stats = self.get_today_stats()

            # Title
            print("\n" + "═" * 70)
            print("  💰 PYCOSTAUDIT MONITOR - LIVE COST TRACKING")
            print("═" * 70 + "\n")

            # Main stats
            print(f"📊 TODAY'S OVERVIEW")
            print(f"├─ Total Cost:      ${stats['total']:>10.4f}")
            print(f"├─ Operations:      {stats['count']:>10}")
            print(f"├─ Tokens Used:     {stats['tokens']:>10,}")
            print(f"└─ Avg Cost/Op:     ${stats['total']/max(stats['count'], 1):>10.4f}\n")

            # By operation
            if stats['by_op']:
                print("📂 Cost by Operation:")
                for op, cost in stats['by_op'].items():
                    pct = (cost / stats['total'] * 100) if stats['total'] > 0 else 0
                    bar = "█" * int(pct / 2)
                    print(f"  {op:20s} ${cost:8.4f} {pct:5.1f}% {bar}")
                print()

            # By model
            if stats['by_model']:
                print("🤖 Cost by Model:")
                for model, cost in stats['by_model'].items():
                    pct = (cost / stats['total'] * 100) if stats['total'] > 0 else 0
                    bar = "█" * int(pct / 2)
                    model_short = model[:25]
                    print(f"  {model_short:25s} ${cost:8.4f} {pct:5.1f}% {bar}")
                print()

            # Forecast
            week_ago = datetime.now().date() - timedelta(days=7)
            week_costs = [
                c for c in self.data.get("costs", [])
                if datetime.fromisoformat(c.get("timestamp", "")).date() >= week_ago
            ]
            if week_costs:
                daily_totals = defaultdict(float)
                for c in week_costs:
                    date = datetime.fromisoformat(c.get("timestamp", "")).date()
                    daily_totals[date] += c.get("estimated_cost", 0)

                if daily_totals:
                    avg_daily = sum(daily_totals.values()) / len(daily_totals)
                    weekly = avg_daily * 7
                    monthly = avg_daily * 30

                    daily_values = list(sorted(daily_totals.values()))
                    sparkline = self.get_sparkline(daily_values)

                    print("📈 Forecast:")
                    print(f"  Daily Avg:       ${avg_daily:>10.4f}")
                    print(f"  Weekly Est:      ${weekly:>10.2f} {sparkline}")
                    print(f"  Monthly Est:     ${monthly:>10.2f}")
                    print()

            # Footer
            print("─" * 70)
            print(f"⏱️  Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | " +
                  f"Next refresh: {self.refresh_interval}s | Press Ctrl+C to stop\n")

            time.sleep(self.refresh_interval)

    def draw_curses_ui(self, stdscr):
        """Draw interactive curses-based dashboard"""
        curses.curs_set(0)  # Hide cursor
        stdscr.nodelay(True)

        # Color pairs
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)

        try:
            while True:
                self.load_data()
                stats = self.get_today_stats()
                stdscr.clear()
                height, width = stdscr.getmaxyx()

                # Title
                title = "💰 PYCOSTAUDIT MONITOR - LIVE COST TRACKING"
                stdscr.addstr(0, (width - len(title)) // 2, title, curses.color_pair(4) | curses.A_BOLD)

                # Main stats
                y = 2
                stdscr.addstr(y, 0, f"📊 TODAY'S OVERVIEW", curses.color_pair(1) | curses.A_BOLD)
                y += 1
                stdscr.addstr(y, 2, f"Total Cost:        ${stats['total']:10.4f}", curses.color_pair(1))
                y += 1
                stdscr.addstr(y, 2, f"Operations:        {stats['count']:10}", curses.color_pair(1))
                y += 1
                stdscr.addstr(y, 2, f"Tokens Used:       {stats['tokens']:10,}", curses.color_pair(1))
                y += 2

                # By operation
                if stats['by_op'] and y < height - 10:
                    stdscr.addstr(y, 0, "📂 Cost by Operation:", curses.color_pair(2) | curses.A_BOLD)
                    y += 1
                    for op, cost in list(stats['by_op'].items())[:5]:
                        pct = (cost / stats['total'] * 100) if stats['total'] > 0 else 0
                        if y < height - 3:
                            stdscr.addstr(y, 2, f"{op:20s} ${cost:8.4f} {pct:5.1f}%")
                            y += 1
                    y += 1

                # By model
                if stats['by_model'] and y < height - 5:
                    stdscr.addstr(y, 0, "🤖 Cost by Model:", curses.color_pair(2) | curses.A_BOLD)
                    y += 1
                    for model, cost in list(stats['by_model'].items())[:3]:
                        pct = (cost / stats['total'] * 100) if stats['total'] > 0 else 0
                        if y < height - 3:
                            model_short = model[:25]
                            stdscr.addstr(y, 2, f"{model_short:25s} ${cost:8.4f} {pct:5.1f}%")
                            y += 1

                # Footer
                if height > 3:
                    stdscr.addstr(height - 2, 0, "─" * width)
                    footer = f"Updated: {datetime.now().strftime('%H:%M:%S')} | Press q to quit"
                    stdscr.addstr(height - 1, (width - len(footer)) // 2, footer, curses.color_pair(4))

                stdscr.refresh()

                # Check for quit
                try:
                    key = stdscr.getch()
                    if key == ord('q'):
                        break
                except:
                    pass

                time.sleep(self.refresh_interval)

        finally:
            curses.curs_set(1)  # Show cursor

    def run(self, use_curses: bool = False):
        """Run the monitor"""
        if use_curses:
            try:
                curses.wrapper(self.draw_curses_ui)
            except:
                self.draw_text_ui()
        else:
            self.draw_text_ui()


def main():
    parser = argparse.ArgumentParser(description="Real-time PyCostAudit cost monitor")
    parser.add_argument("--refresh", type=int, default=2, help="Refresh interval in seconds")
    parser.add_argument("--curses", action="store_true", help="Use interactive curses UI (if available)")
    parser.add_argument("--text", action="store_true", help="Use text-based UI (default)")
    args = parser.parse_args()

    monitor = CostMonitor(refresh_interval=args.refresh)
    use_curses = args.curses or (not args.text and sys.platform != "win32")

    try:
        monitor.run(use_curses=use_curses)
    except KeyboardInterrupt:
        print("\n\n✋ Monitor stopped")


if __name__ == "__main__":
    main()
