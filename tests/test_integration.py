"""
Integration tests for PyCostAudit MVP.

Tests the complete flow: operation tracking → cost calculation → analysis.
"""

import tempfile
import json
from pathlib import Path
from pycostaudit import PyCostAudit


def test_basic_cost_tracking():
    """Test: Track a simple operation and calculate cost."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "costs.db"
        reporter = PyCostAudit(str(db_path))

        # Track an operation
        cost = reporter.track_operation(
            operation_type="api_call",
            tokens_input=1000,
            tokens_output=500,
            model="claude-3-5-haiku",
        )

        assert cost["cost"] > 0
        assert cost["multiplier"] == 1.0  # No multiplier for API call
        assert cost["tokens_actual"] == 1500


def test_file_format_multipliers():
    """Test: File source multipliers (36x variance)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "costs.db"
        reporter = PyCostAudit(str(db_path))

        # CSV local (baseline)
        csv_cost = reporter.track_operation(
            operation_type="file_read",
            tokens_input=450,
            tokens_output=120,
            model="claude-3-5-haiku",
            file_source="csv_local",
        )

        # PDF via URL (3.6x multiplier!)
        pdf_url_cost = reporter.track_operation(
            operation_type="file_read",
            tokens_input=450,
            tokens_output=120,
            model="claude-3-5-haiku",
            file_source="pdf_url",
        )

        # Verify multiplier
        assert pdf_url_cost["multiplier"] == 3.6
        assert pdf_url_cost["cost_usd"] > csv_cost["cost_usd"]
        assert abs(pdf_url_cost["cost_usd"] / csv_cost["cost_usd"] - 3.6) < 0.1


def test_operation_type_variance():
    """Test: Operation type multipliers (55x for browser ops)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "costs.db"
        reporter = PyCostAudit(str(db_path))

        # File read (baseline)
        file_cost = reporter.track_operation(
            operation_type="file_read",
            tokens_input=300,
            tokens_output=100,
            model="claude-3-5-haiku",
            file_source="csv_local",
        )

        # Browser op (55x multiplier!)
        browser_cost = reporter.track_operation(
            operation_type="browser_op",
            tokens_input=300,
            tokens_output=100,
            model="claude-3-5-haiku",
        )

        # Verify multiplier
        assert browser_cost["multiplier"] == 55.0
        assert browser_cost["cost_usd"] > file_cost["cost_usd"]


def test_session_tracking():
    """Test: Session grouping and tagging."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "costs.db"
        reporter = PyCostAudit(str(db_path))

        # Start session
        session_id = reporter.start_session("feature/auth")
        assert session_id is not None

        # Tag session
        reporter.tag_session("branch", "main", session_id)
        reporter.tag_session("feature", "oauth", session_id)

        # Track operations in session
        reporter.track_operation(
            operation_type="api_call",
            tokens_input=1000,
            tokens_output=500,
            model="claude-3-5-haiku",
            session_id=session_id,
        )

        reporter.track_operation(
            operation_type="file_read",
            tokens_input=450,
            tokens_output=120,
            model="claude-3-5-haiku",
            file_source="pdf_url",
            session_id=session_id,
        )

        # End session
        summary = reporter.end_session(session_id)
        assert summary["session_id"] == session_id


def test_instruction_context():
    """Test: Instruction context adds overhead."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "costs.db"
        reporter = PyCostAudit(str(db_path))

        # Simple operation
        simple = reporter.track_operation(
            operation_type="api_call",
            tokens_input=100,
            tokens_output=50,
            model="claude-3-5-haiku",
        )

        # Operation WITH instruction context overhead
        # (In production, this would be auto-detected)
        with_context = reporter.track_operation(
            operation_type="instruction_context",
            tokens_input=2000,  # claude.md + agent.md
            tokens_output=1500,  # workflow.md
            model="claude-3-5-haiku",
        )

        # Instruction context should be significant
        assert with_context["cost_usd"] > simple["cost_usd"]


def test_mcp_tracking():
    """Test: MCP invocation tracking."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "costs.db"
        reporter = PyCostAudit(str(db_path))

        # Track MCP calls
        reporter.track_operation(
            operation_type="mcp_invocation",
            tokens_input=100,
            tokens_output=500,
            model="claude-3-5-haiku",
            mcp_name="web_search",
        )

        reporter.track_operation(
            operation_type="mcp_invocation",
            tokens_input=150,
            tokens_output=200,
            model="claude-3-5-haiku",
            mcp_name="web_search",
        )

        reporter.track_operation(
            operation_type="mcp_invocation",
            tokens_input=200,
            tokens_output=1000,
            model="claude-3-5-haiku",
            mcp_name="code_execution",
        )

        # Analyze MCPs
        mcps = reporter.analyze_mcp_costs()
        assert "mcp_ranking" in mcps
        assert len(mcps["mcp_ranking"]) > 0


def test_user_attribution():
    """Test: Per-user cost tracking for teams."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "costs.db"
        reporter = PyCostAudit(str(db_path))

        # Alice's operations
        reporter.track_operation(
            operation_type="api_call",
            tokens_input=1000,
            tokens_output=500,
            model="claude-3-5-haiku",
            user="alice",
        )

        # Bob's operations
        reporter.track_operation(
            operation_type="api_call",
            tokens_input=500,
            tokens_output=200,
            model="claude-3-5-haiku",
            user="bob",
        )

        # Carol's operations
        reporter.track_operation(
            operation_type="browser_op",
            tokens_input=300,
            tokens_output=100,
            model="claude-3-5-haiku",
            user="carol",
        )

        # Analyze
        breakdown = reporter.analyze_daily()
        assert breakdown["total_cost_usd"] > 0


def test_analysis_output_format():
    """Test: Analysis outputs are valid JSON with expected structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "costs.db"
        reporter = PyCostAudit(str(db_path))

        # Track some operations
        reporter.track_operation(
            operation_type="api_call",
            tokens_input=1000,
            tokens_output=500,
            model="claude-3-5-haiku",
        )

        # Get analysis
        breakdown = reporter.analyze_daily()

        # Verify structure
        assert "total_cost_usd" in breakdown
        assert "total_tokens" in breakdown
        assert breakdown["total_cost_usd"] > 0


if __name__ == "__main__":
    test_basic_cost_tracking()
    test_file_format_multipliers()
    test_operation_type_variance()
    test_session_tracking()
    test_instruction_context()
    test_mcp_tracking()
    test_user_attribution()
    test_analysis_output_format()
    print("✅ All tests passed!")
