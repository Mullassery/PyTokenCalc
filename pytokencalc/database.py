"""
Database schema and ORM models for PyCostAudit v0.6+
Extends Phase 3 to support alerts, forecasting, anomaly detection, and auditing.
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, Dict, List, Any
import uuid


class AlertStatus(Enum):
    """Alert delivery status"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    ACKNOWLEDGED = "acknowledged"


class AnomalyType(Enum):
    """Types of cost anomalies detected"""
    SPIKE = "spike"  # Sudden increase
    UNUSUAL_PATTERN = "unusual_pattern"  # Deviation from baseline
    OPERATION_TYPE_SHIFT = "operation_type_shift"  # Composition change
    OUTLIER = "outlier"  # Statistical outlier


@dataclass
class AlertConfiguration:
    """User-configurable alert settings (persistent in DB)"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""

    # Budget thresholds
    daily_budget_usd: Optional[float] = None
    weekly_budget_usd: Optional[float] = None
    monthly_budget_usd: Optional[float] = None

    # Alert triggers
    alert_at_percent: float = 0.75  # Alert at 75% of budget
    critical_at_percent: float = 0.90  # Critical alert at 90%

    # Notification channels
    slack_webhook_url: Optional[str] = None
    email_address: Optional[str] = None
    sms_phone: Optional[str] = None

    # Notification preferences
    notify_on_anomaly: bool = True
    notify_on_spike: bool = True
    notify_on_budget_threshold: bool = True

    # Cooldown to prevent alert spam
    alert_cooldown_minutes: int = 60
    max_alerts_per_day: int = 20

    # Settings
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AlertHistory:
    """Record of all alerts sent (audit trail)"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    alert_config_id: str = ""

    # Alert content
    alert_type: str = ""  # budget_threshold, spike, anomaly, etc.
    severity: str = "medium"  # low, medium, high, critical
    message: str = ""

    # What triggered it
    current_cost: float = 0.0
    budget_limit: float = 0.0
    threshold_percent: float = 0.0

    # Delivery status
    status: str = "pending"
    sent_to_slack: bool = False
    sent_to_email: bool = False
    sent_to_sms: bool = False

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None


@dataclass
class TimeSeriesDataPoint:
    """Individual hourly/daily cost data point for forecasting"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""

    # Time period
    period_start: datetime = field(default_factory=datetime.utcnow)
    period_type: str = "hourly"  # hourly, daily, weekly

    # Cost aggregates
    total_cost: float = 0.0
    num_operations: int = 0

    # Breakdown by dimension
    by_operation_type: Dict[str, float] = field(default_factory=dict)  # {file_read: 10.5, api_call: 5.2, ...}
    by_file_format: Dict[str, float] = field(default_factory=dict)  # {pdf_url: 20.0, csv_pasted: 2.1, ...}
    by_model: Dict[str, float] = field(default_factory=dict)  # {sonnet: 15.0, haiku: 3.0, ...}
    by_provider: Dict[str, float] = field(default_factory=dict)  # {openai: 5.0, bedrock: 15.0, ...}

    # Time-of-day characteristics
    hour_of_day: int = 0  # 0-23
    day_of_week: int = 0  # 0-6 (Monday-Sunday)
    is_weekend: bool = False

    # Anomaly markers
    is_anomaly: bool = False
    anomaly_score: float = 0.0  # 0-1, how abnormal is this point

    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ForecastCache:
    """Pre-computed forecasts to avoid recalculation"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""

    # Forecast parameters
    forecast_type: str = ""  # 7day, 30day, 60day, 90day
    horizon_days: int = 7

    # Forecast data
    predicted_daily_cost: float = 0.0  # Predicted cost per day
    predicted_total_cost: float = 0.0  # Total for the period
    confidence_interval_low: float = 0.0  # 95% CI lower bound
    confidence_interval_high: float = 0.0  # 95% CI upper bound

    # Trend information
    trend_direction: str = "stable"  # up, down, stable
    trend_percent: float = 0.0  # % change expected

    # What-if scenario results (JSON stored)
    scenarios: Dict[str, Any] = field(default_factory=dict)  # {scenario_name: {cost: X, savings: Y}, ...}

    # Model information
    forecast_model: str = ""  # arima, exponential_smoothing, linear, etc.
    model_confidence: float = 0.0  # 0-1, how confident in the model

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=1))


@dataclass
class AnomalyRecord:
    """Detected cost anomalies for historical analysis"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""

    # What was anomalous
    anomaly_type: str = ""  # spike, unusual_pattern, operation_type_shift, outlier
    severity: str = "medium"  # low, medium, high

    # The data
    observed_value: float = 0.0  # Actual cost observed
    expected_value: float = 0.0  # What we expected
    deviation_percent: float = 0.0  # How much different
    z_score: float = 0.0  # Statistical z-score

    # Context
    dimension: str = ""  # What dimension (operation_type, file_format, model, etc.)
    dimension_value: str = ""  # Specific value (file_read, pdf_url, sonnet, etc.)

    # Details
    message: str = ""
    recommendation: Optional[str] = None

    # Status
    acknowledged: bool = False
    investigated: bool = False

    created_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None


@dataclass
class RecommendationRecord:
    """Cost optimization recommendations"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""

    # Recommendation details
    recommendation_type: str = ""  # batch_operations, off_peak_scheduling, model_downgrade, file_format_optimization, etc.
    title: str = ""
    description: str = ""

    # ROI calculation
    estimated_savings_usd: float = 0.0  # $ per period
    estimated_savings_percent: float = 0.0  # % of current spend
    implementation_effort_hours: float = 0.0
    roi_score: float = 0.0  # Savings / effort

    # Implementation guidance
    implementation_steps: List[str] = field(default_factory=list)
    estimated_implementation_time: str = ""  # "5 min", "1 hour", "1 day"

    # Tracking
    implemented: bool = False
    implemented_at: Optional[datetime] = None
    actual_savings_usd: Optional[float] = None

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AuditLog:
    """Immutable audit trail for compliance (Phase 3)"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""

    # Action details
    action: str = ""  # cost_operation, alert_sent, config_changed, report_generated, etc.
    resource_type: str = ""  # cost, alert_config, forecast, etc.
    resource_id: str = ""

    # Changes
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None

    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None

    # Integrity
    checksum: Optional[str] = None  # SHA256 of log entry for tamper detection

    created_at: datetime = field(default_factory=datetime.utcnow)


class DatabaseManager:
    """Manages SQLite database connections and schema"""

    def __init__(self, db_path: str = "~/.pycostaudit/pycostaudit.db"):
        self.db_path = db_path.replace("~", os.path.expanduser("~"))
        self.conn = None
        self.cursor = None

    def connect(self):
        """Open database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def init_schema(self):
        """Create all tables if they don't exist"""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_configurations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                daily_budget_usd REAL,
                weekly_budget_usd REAL,
                monthly_budget_usd REAL,
                alert_at_percent REAL DEFAULT 0.75,
                critical_at_percent REAL DEFAULT 0.90,
                slack_webhook_url TEXT,
                email_address TEXT,
                sms_phone TEXT,
                notify_on_anomaly INTEGER DEFAULT 1,
                notify_on_spike INTEGER DEFAULT 1,
                notify_on_budget_threshold INTEGER DEFAULT 1,
                alert_cooldown_minutes INTEGER DEFAULT 60,
                max_alerts_per_day INTEGER DEFAULT 20,
                enabled INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS alert_history (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                alert_config_id TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                severity TEXT DEFAULT 'medium',
                message TEXT NOT NULL,
                current_cost REAL,
                budget_limit REAL,
                threshold_percent REAL,
                status TEXT DEFAULT 'pending',
                sent_to_slack INTEGER DEFAULT 0,
                sent_to_email INTEGER DEFAULT 0,
                sent_to_sms INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                sent_at TEXT,
                acknowledged_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (alert_config_id) REFERENCES alert_configurations(id)
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS time_series_data (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                period_start TEXT NOT NULL,
                period_type TEXT DEFAULT 'hourly',
                total_cost REAL DEFAULT 0.0,
                num_operations INTEGER DEFAULT 0,
                by_operation_type TEXT,
                by_file_format TEXT,
                by_model TEXT,
                by_provider TEXT,
                hour_of_day INTEGER,
                day_of_week INTEGER,
                is_weekend INTEGER DEFAULT 0,
                is_anomaly INTEGER DEFAULT 0,
                anomaly_score REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS forecast_cache (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                forecast_type TEXT NOT NULL,
                horizon_days INTEGER,
                predicted_daily_cost REAL,
                predicted_total_cost REAL,
                confidence_interval_low REAL,
                confidence_interval_high REAL,
                trend_direction TEXT DEFAULT 'stable',
                trend_percent REAL,
                scenarios TEXT,
                forecast_model TEXT,
                model_confidence REAL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS anomalies (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                anomaly_type TEXT NOT NULL,
                severity TEXT DEFAULT 'medium',
                observed_value REAL,
                expected_value REAL,
                deviation_percent REAL,
                z_score REAL,
                dimension TEXT,
                dimension_value TEXT,
                message TEXT,
                recommendation TEXT,
                acknowledged INTEGER DEFAULT 0,
                investigated INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                acknowledged_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                recommendation_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                estimated_savings_usd REAL,
                estimated_savings_percent REAL,
                implementation_effort_hours REAL,
                roi_score REAL,
                implementation_steps TEXT,
                estimated_implementation_time TEXT,
                implemented INTEGER DEFAULT 0,
                implemented_at TEXT,
                actual_savings_usd REAL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                resource_type TEXT,
                resource_id TEXT,
                old_value TEXT,
                new_value TEXT,
                ip_address TEXT,
                user_agent TEXT,
                session_id TEXT,
                checksum TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Create indexes for faster queries
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_alert_config_user
            ON alert_configurations(user_id)
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_alert_history_user
            ON alert_history(user_id, created_at DESC)
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_time_series_user_period
            ON time_series_data(user_id, period_start DESC)
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_forecast_user
            ON forecast_cache(user_id, forecast_type)
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_anomaly_user
            ON anomalies(user_id, created_at DESC)
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_recommendation_user
            ON recommendations(user_id, roi_score DESC)
        """)

        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_log_user
            ON audit_logs(user_id, created_at DESC)
        """)

        self.conn.commit()

    def insert_alert_config(self, config: AlertConfiguration) -> str:
        """Insert alert configuration"""
        self.cursor.execute("""
            INSERT INTO alert_configurations (
                id, user_id, daily_budget_usd, weekly_budget_usd, monthly_budget_usd,
                alert_at_percent, critical_at_percent, slack_webhook_url, email_address,
                sms_phone, notify_on_anomaly, notify_on_spike, notify_on_budget_threshold,
                alert_cooldown_minutes, max_alerts_per_day, enabled, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            config.id, config.user_id, config.daily_budget_usd, config.weekly_budget_usd,
            config.monthly_budget_usd, config.alert_at_percent, config.critical_at_percent,
            config.slack_webhook_url, config.email_address, config.sms_phone,
            int(config.notify_on_anomaly), int(config.notify_on_spike),
            int(config.notify_on_budget_threshold), config.alert_cooldown_minutes,
            config.max_alerts_per_day, int(config.enabled),
            config.created_at.isoformat(), config.updated_at.isoformat()
        ))
        self.conn.commit()
        return config.id

    def get_alert_config(self, user_id: str) -> Optional[AlertConfiguration]:
        """Get alert configuration for user"""
        self.cursor.execute(
            "SELECT * FROM alert_configurations WHERE user_id = ?",
            (user_id,)
        )
        row = self.cursor.fetchone()
        if not row:
            return None

        return AlertConfiguration(
            id=row["id"],
            user_id=row["user_id"],
            daily_budget_usd=row["daily_budget_usd"],
            weekly_budget_usd=row["weekly_budget_usd"],
            monthly_budget_usd=row["monthly_budget_usd"],
            alert_at_percent=row["alert_at_percent"],
            critical_at_percent=row["critical_at_percent"],
            slack_webhook_url=row["slack_webhook_url"],
            email_address=row["email_address"],
            sms_phone=row["sms_phone"],
            notify_on_anomaly=bool(row["notify_on_anomaly"]),
            notify_on_spike=bool(row["notify_on_spike"]),
            notify_on_budget_threshold=bool(row["notify_on_budget_threshold"]),
            alert_cooldown_minutes=row["alert_cooldown_minutes"],
            max_alerts_per_day=row["max_alerts_per_day"],
            enabled=bool(row["enabled"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"])
        )

    def insert_time_series(self, data: TimeSeriesDataPoint) -> str:
        """Insert time series data point"""
        self.cursor.execute("""
            INSERT INTO time_series_data (
                id, user_id, period_start, period_type, total_cost, num_operations,
                by_operation_type, by_file_format, by_model, by_provider,
                hour_of_day, day_of_week, is_weekend, is_anomaly, anomaly_score, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.id, data.user_id, data.period_start.isoformat(), data.period_type,
            data.total_cost, data.num_operations,
            json.dumps(data.by_operation_type), json.dumps(data.by_file_format),
            json.dumps(data.by_model), json.dumps(data.by_provider),
            data.hour_of_day, data.day_of_week, int(data.is_weekend),
            int(data.is_anomaly), data.anomaly_score, data.created_at.isoformat()
        ))
        self.conn.commit()
        return data.id

    def get_time_series(
        self,
        user_id: str,
        period_type: str = "daily",
        limit: int = 30
    ) -> List[TimeSeriesDataPoint]:
        """Get time series data for user"""
        self.cursor.execute("""
            SELECT * FROM time_series_data
            WHERE user_id = ?
            ORDER BY period_start DESC
            LIMIT ?
        """, (user_id, limit))

        results = []
        for row in self.cursor.fetchall():
            results.append(TimeSeriesDataPoint(
                id=row["id"],
                user_id=row["user_id"],
                period_start=datetime.fromisoformat(row["period_start"]),
                period_type=row["period_type"],
                total_cost=row["total_cost"],
                num_operations=row["num_operations"],
                by_operation_type=json.loads(row["by_operation_type"] or "{}"),
                by_file_format=json.loads(row["by_file_format"] or "{}"),
                by_model=json.loads(row["by_model"] or "{}"),
                by_provider=json.loads(row["by_provider"] or "{}"),
                hour_of_day=row["hour_of_day"],
                day_of_week=row["day_of_week"],
                is_weekend=bool(row["is_weekend"]),
                is_anomaly=bool(row["is_anomaly"]),
                anomaly_score=row["anomaly_score"],
                created_at=datetime.fromisoformat(row["created_at"])
            ))

        return results
