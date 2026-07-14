"""
Data persistence layer for PyCostAudit.
Stores cost calculations in SQLite for historical tracking.
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from pytokencalc.cost_calculator import CostCalculator, SessionCost


class CostDatabase:
    """SQLite database for persistent cost storage"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or "~/.pycostaudit/costs.db").expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_costs (
                    id INTEGER PRIMARY KEY,
                    session_id TEXT UNIQUE,
                    timestamp DATETIME,
                    project TEXT,
                    model TEXT,
                    estimated_tokens_in INTEGER,
                    estimated_tokens_out INTEGER,
                    cost_usd REAL,
                    input_cost_usd REAL,
                    output_cost_usd REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_costs (
                    id INTEGER PRIMARY KEY,
                    date TEXT UNIQUE,
                    total_cost_usd REAL,
                    session_count INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS project_costs (
                    id INTEGER PRIMARY KEY,
                    date TEXT,
                    project TEXT,
                    total_cost_usd REAL,
                    session_count INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, project)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_project
                ON session_costs(project)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_timestamp
                ON session_costs(timestamp)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_daily_date
                ON daily_costs(date)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_project_date
                ON project_costs(date)
            """)

            conn.commit()

    def store_session_costs(self, sessions: List[SessionCost]):
        """Store session costs to database"""
        with sqlite3.connect(self.db_path) as conn:
            for session in sessions:
                try:
                    conn.execute("""
                        INSERT INTO session_costs
                        (session_id, timestamp, project, model, estimated_tokens_in,
                         estimated_tokens_out, cost_usd, input_cost_usd, output_cost_usd)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        session.session_id,
                        session.timestamp.isoformat(),
                        session.project,
                        session.model,
                        session.estimated_tokens_in,
                        session.estimated_tokens_out,
                        session.cost_usd,
                        session.breakdown.get("input", 0),
                        session.breakdown.get("output", 0),
                    ))
                except sqlite3.IntegrityError:
                    # Session already exists, skip
                    pass

            conn.commit()

    def aggregate_daily_costs(self):
        """Aggregate costs to daily table"""
        with sqlite3.connect(self.db_path) as conn:
            # Get daily costs from session_costs
            cursor = conn.execute("""
                SELECT
                    DATE(timestamp) as date,
                    SUM(cost_usd) as total_cost,
                    COUNT(*) as session_count
                FROM session_costs
                WHERE DATE(timestamp) NOT IN (
                    SELECT date FROM daily_costs
                )
                GROUP BY DATE(timestamp)
            """)

            for date, total_cost, session_count in cursor.fetchall():
                conn.execute("""
                    INSERT INTO daily_costs (date, total_cost_usd, session_count)
                    VALUES (?, ?, ?)
                """, (date, total_cost, session_count))

            conn.commit()

    def aggregate_project_costs(self):
        """Aggregate costs by project and day"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT
                    DATE(timestamp) as date,
                    project,
                    SUM(cost_usd) as total_cost,
                    COUNT(*) as session_count
                FROM session_costs
                WHERE (DATE(timestamp), project) NOT IN (
                    SELECT date, project FROM project_costs
                )
                GROUP BY DATE(timestamp), project
            """)

            for date, project, total_cost, session_count in cursor.fetchall():
                try:
                    conn.execute("""
                        INSERT INTO project_costs (date, project, total_cost_usd, session_count)
                        VALUES (?, ?, ?, ?)
                    """, (date, project, total_cost, session_count))
                except sqlite3.IntegrityError:
                    pass

            conn.commit()

    def get_daily_costs(self, days: int = 30) -> Dict[str, float]:
        """Get daily costs for last N days"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT date, total_cost_usd
                FROM daily_costs
                WHERE date >= DATE('now', '-{} days')
                ORDER BY date
            """.format(days))

            return {row[0]: row[1] for row in cursor.fetchall()}

    def get_project_costs_history(self, project: str, days: int = 30) -> Dict[str, float]:
        """Get historical costs for a specific project"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT date, total_cost_usd
                FROM project_costs
                WHERE project = ? AND date >= DATE('now', '-{} days')
                ORDER BY date
            """.format(days), (project,))

            return {row[0]: row[1] for row in cursor.fetchall()}

    def get_cost_summary(self) -> Dict:
        """Get comprehensive cost summary"""
        with sqlite3.connect(self.db_path) as conn:
            # Total cost
            total = conn.execute(
                "SELECT SUM(cost_usd) FROM session_costs"
            ).fetchone()[0] or 0

            # Sessions
            sessions = conn.execute(
                "SELECT COUNT(*) FROM session_costs"
            ).fetchone()[0] or 0

            # Projects
            projects = conn.execute(
                "SELECT COUNT(DISTINCT project) FROM session_costs"
            ).fetchone()[0] or 0

            # Date range
            dates = conn.execute(
                "SELECT MIN(timestamp), MAX(timestamp) FROM session_costs"
            ).fetchone()

            return {
                "total_cost_usd": round(total, 2),
                "total_sessions": sessions,
                "unique_projects": projects,
                "first_session": dates[0] if dates[0] else None,
                "last_session": dates[1] if dates[1] else None,
            }

    def get_project_trend(self, project: str, days: int = 30) -> Dict:
        """Get cost trend for a project"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT date, total_cost_usd
                FROM project_costs
                WHERE project = ? AND date >= DATE('now', '-{} days')
                ORDER BY date
            """.format(days), (project,))

            costs = {row[0]: row[1] for row in cursor.fetchall()}

            if len(costs) < 2:
                return {"trend": "insufficient_data"}

            dates = sorted(costs.keys())
            first_half_avg = sum(
                costs[d] for d in dates[:len(dates)//2]
            ) / max(1, len(dates)//2)
            second_half_avg = sum(
                costs[d] for d in dates[len(dates)//2:]
            ) / max(1, len(dates) - len(dates)//2)

            trend = "↑ increasing" if second_half_avg > first_half_avg else "↓ decreasing"
            change_pct = abs((second_half_avg - first_half_avg) / first_half_avg * 100) if first_half_avg > 0 else 0

            return {
                "project": project,
                "trend": trend,
                "change_percentage": round(change_pct, 1),
                "first_half_avg": round(first_half_avg, 2),
                "second_half_avg": round(second_half_avg, 2),
            }

    def compare_periods(self, days1: int, days2: int) -> Dict:
        """
        Compare two time periods.
        E.g., last 7 days vs previous 7 days
        """
        with sqlite3.connect(self.db_path) as conn:
            # Recent period
            recent = conn.execute(f"""
                SELECT SUM(total_cost_usd)
                FROM daily_costs
                WHERE date >= DATE('now', '-{days1} days')
            """).fetchone()[0] or 0

            # Previous period
            previous = conn.execute(f"""
                SELECT SUM(total_cost_usd)
                FROM daily_costs
                WHERE date >= DATE('now', '-{days1 + days2} days')
                  AND date < DATE('now', '-{days1} days')
            """).fetchone()[0] or 0

            change = recent - previous
            change_pct = (change / previous * 100) if previous > 0 else 0

            return {
                "recent_period": round(recent, 2),
                "previous_period": round(previous, 2),
                "change_usd": round(change, 2),
                "change_percentage": round(change_pct, 1),
                "direction": "↑ up" if change > 0 else "↓ down" if change < 0 else "→ stable",
            }
