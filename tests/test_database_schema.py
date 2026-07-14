"""
Tests for database schema and backend service.
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta

from pytokencalc.database import (
    DatabaseManager, AlertConfiguration, TimeSeriesDataPoint,
    ForecastCache, AnomalyRecord, RecommendationRecord
)
from pytokencalc.backend_service import BackendService


@pytest.fixture
def temp_db():
    """Create temporary database"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        yield db_path


def test_database_init(temp_db):
    """Test database initialization"""
    db = DatabaseManager(temp_db)
    db.connect()
    db.init_schema()

    # Verify tables exist
    cursor = db.cursor
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
    """)

    tables = {row[0] for row in cursor.fetchall()}
    expected_tables = {
        'alert_configurations', 'alert_history', 'time_series_data',
        'forecast_cache', 'anomalies', 'recommendations', 'audit_logs'
    }

    assert expected_tables.issubset(tables), f"Missing tables: {expected_tables - tables}"
    db.disconnect()


def test_alert_config_crud(temp_db):
    """Test alert configuration CRUD operations"""
    db = DatabaseManager(temp_db)
    db.connect()
    db.init_schema()

    # Create
    config = AlertConfiguration(
        user_id="user123",
        daily_budget_usd=100.0,
        weekly_budget_usd=500.0,
        slack_webhook_url="https://hooks.slack.com/test"
    )
    config_id = db.insert_alert_config(config)

    assert config_id == config.id

    # Read
    retrieved = db.get_alert_config("user123")
    assert retrieved is not None
    assert retrieved.daily_budget_usd == 100.0
    assert retrieved.slack_webhook_url == "https://hooks.slack.com/test"

    db.disconnect()


def test_time_series_insert(temp_db):
    """Test time series data insertion"""
    db = DatabaseManager(temp_db)
    db.connect()
    db.init_schema()

    # Insert
    ts = TimeSeriesDataPoint(
        user_id="user123",
        period_start=datetime.utcnow(),
        total_cost=50.0,
        num_operations=10,
        by_operation_type={"api_call": 30.0, "file_read": 20.0}
    )
    ts_id = db.insert_time_series(ts)

    # Query
    results = db.get_time_series("user123", "daily", limit=1)
    assert len(results) == 1
    assert results[0].total_cost == 50.0
    assert results[0].num_operations == 10
    assert "api_call" in results[0].by_operation_type

    db.disconnect()


def test_backend_service_initialize(temp_db):
    """Test backend service initialization"""
    service = BackendService(temp_db)
    service.initialize()

    # Verify database is initialized
    with service.db:
        service.db.cursor.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
        )
        count = service.db.cursor.fetchone()[0]
        assert count > 0


def test_backend_service_set_budget(temp_db):
    """Test setting budget in backend service"""
    service = BackendService(temp_db)
    service.initialize()

    config = service.set_budget(
        user_id="user123",
        daily=100.0,
        slack_webhook="https://hooks.slack.com/test"
    )

    assert config.daily_budget_usd == 100.0
    assert config.slack_webhook_url == "https://hooks.slack.com/test"


def test_backend_service_daily_summary(temp_db):
    """Test getting daily summary"""
    service = BackendService(temp_db)
    service.initialize()

    # Get summary for empty user
    summary = service.get_daily_summary("user123")

    assert summary["total_cost"] == 0.0
    assert summary["num_operations"] == 0


def test_backend_service_trend(temp_db):
    """Test trend calculation"""
    service = BackendService(temp_db)
    service.initialize()

    # Insert multiple days of data
    with service.db:
        for i in range(7):
            date = datetime.utcnow() - timedelta(days=6-i)
            date = date.replace(hour=0, minute=0, second=0, microsecond=0)

            ts = TimeSeriesDataPoint(
                user_id="user123",
                period_start=date,
                period_type="daily",
                total_cost=50.0 + (i * 5)  # Increasing trend
            )
            service.db.insert_time_series(ts)

    # Get trend
    trend = service.get_trend("user123", days=7)

    assert trend["period_days"] == 7
    assert len(trend["daily_costs"]) == 7
    assert "up" in trend["trend"] or "stable" in trend["trend"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
