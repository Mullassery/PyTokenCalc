"""
CostReporter: Real-time LLM cost tracking and optimization

A MIT OSS tool that tracks:
- File format cost multipliers (36x variance: CSV vs PDF URL)
- Operation type breakdown (55x variance: browser vs file)
- Instruction context costs (10x-50x: .claude/claude.md overhead)
- Data warehouse queries (100x-1000x+: millions of rows)
- S3 operations (100x-1000x+: file listing/download)
- SaaS MCP inefficiency (10x-100x: Stripe, Salesforce, etc)
- Session-based cost grouping (root cause analysis)

Usage:
    from pycost_reporter import CostReporter

    reporter = CostReporter(db_path="~/.cost-reporter/costs.db")

    # Track an operation
    session_id = reporter.start_session("debug-auth")
    cost = reporter.track_operation(
        operation_type="file_read",
        tokens_input=300,
        tokens_output=100,
        model="claude-3-5-haiku",
        session_id=session_id,
        file_source="pdf_url"  # 3.6x multiplier!
    )
    reporter.end_session(session_id)

    # Analyze
    breakdown = reporter.analyze_daily()
    print(f"Today's spend: ${breakdown['total_cost_usd']}")
"""

from ._core import PyCostReporter
import json


class CostReporter:
    """
    Main API for cost tracking and analysis.

    This is a wrapper around the Rust core for convenient Python usage.
    """

    def __init__(self, db_path: str = "~/.cost-reporter/costs.db"):
        """
        Initialize CostReporter.

        Args:
            db_path: Path to SQLite database (auto-created if missing)
        """
        import os
        db_path = os.path.expanduser(db_path)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self._core = PyCostReporter(db_path)
        self._current_session = None

    def start_session(self, name: str = None) -> str:
        """
        Start a new session (groups related operations).

        Args:
            name: Optional session name (e.g., "debug-auth", "feature/search")

        Returns:
            Session ID

        Example:
            session_id = reporter.start_session("feature/auth")
        """
        session_id = self._core.start_session(name)
        self._current_session = session_id
        return session_id

    def end_session(self, session_id: str = None) -> dict:
        """
        End a session and get summary.

        Args:
            session_id: Session ID (uses current if None)

        Returns:
            Session summary with costs
        """
        session_id = session_id or self._current_session
        if not session_id:
            raise ValueError("No session active")

        result = self._core.end_session(session_id)
        self._current_session = None
        return json.loads(result)

    def tag_session(self, key: str, value: str, session_id: str = None):
        """
        Add tags to a session (for filtering/grouping).

        Args:
            key: Tag key (e.g., "branch", "feature", "type")
            value: Tag value
            session_id: Session ID (uses current if None)

        Example:
            reporter.tag_session("branch", "main")
            reporter.tag_session("feature", "auth")
        """
        session_id = session_id or self._current_session
        self._core.tag_session(session_id, key, value)

    def track_operation(
        self,
        operation_type: str,
        tokens_input: int,
        tokens_output: int,
        model: str,
        session_id: str = None,
        user: str = None,
        file_source: str = None,
        mcp_name: str = None,
        user_timezone: str = None,
    ) -> dict:
        """
        Track a single operation (called silently in background).

        Args:
            operation_type: One of:
                - "api_call": LLM API invocation (baseline)
                - "file_read": File read (1x-4.2x multiplier)
                - "browser_op": Browser scrape (55x multiplier!)
                - "mcp_invocation": MCP/Skill call (2.4x multiplier)
                - "git_op": Git operation (0.8x multiplier)
                - "database_query": Database query (2x multiplier)
                - "instruction_context": Markdown context (.claude/claude.md)

            tokens_input: Input tokens
            tokens_output: Output tokens
            model: Model name (e.g., "claude-3-5-haiku", "claude-3-5-sonnet")
            session_id: Session ID (uses current if None)
            user: Username (for team cost attribution)
            file_source: File source type:
                - "csv_pasted": CSV pasted (1.0x)
                - "pdf_local": PDF from disk (1.2x)
                - "pdf_url": PDF via URL (3.6x) ← EXPENSIVE!
                - "image_url": Image via URL (4.2x)
                - "stream": Stream/socket (2.8x)
                - "mcp_stream": MCP stream (2.4x)

            mcp_name: MCP/Skill name (e.g., "web_search", "code_execution")
            user_timezone: User's timezone (IANA format, e.g., "America/New_York", "Europe/London")
                CRITICAL: Used for daily budget resets, session grouping, team reporting

        Returns:
            Cost data with multipliers applied

        Example:
            cost = reporter.track_operation(
                operation_type="file_read",
                tokens_input=450,
                tokens_output=120,
                model="claude-3-5-haiku",
                file_source="pdf_url",  # 3.6x multiplier
                user="alice",
                user_timezone="America/New_York"  # Daily reset at midnight EST
            )
            print(f"Cost: ${cost['cost_usd']}")
        """
        session_id = session_id or self._current_session

        result = self._core.track_operation(
            operation_type=operation_type,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            model=model,
            session_id=session_id,
            user=user,
            file_source=file_source,
            mcp_name=mcp_name,
            user_timezone=user_timezone,
        )
        return json.loads(result)

    def analyze_daily(self) -> dict:
        """
        Get today's cost breakdown.

        Returns:
            Breakdown by:
            - operation_type (api_call, file_read, browser_op, etc)
            - file_format (csv, pdf_local, pdf_url, etc)
            - mcp (web_search, code_execution, etc)

        Example:
            breakdown = reporter.analyze_daily()
            print(f"Total: ${breakdown['total_cost_usd']}")
            print(f"File reads: ${breakdown['by_file_format']['pdf_url']['cost_usd']}")
        """
        result = self._core.analyze_daily()
        return json.loads(result)

    def analyze_session(self, session_id: str = None) -> dict:
        """
        Analyze a session's costs with root cause diagnosis.

        Args:
            session_id: Session ID (uses current if None)

        Returns:
            Session analysis including:
            - total_cost_usd
            - operations count
            - duration_seconds
            - cost by operation type
            - biggest waste (root cause)
            - recommendations

        Example:
            analysis = reporter.analyze_session()
            print(f"Session cost: ${analysis['total_cost_usd']}")
            print(f"Biggest waste: {analysis['biggest_waste']['type']} ({analysis['biggest_waste']['percentage']}%)")
            for rec in analysis['recommendations']:
                print(f"- {rec['suggestion']}: save ${rec['cost_usd']}")
        """
        session_id = session_id or self._current_session
        if not session_id:
            raise ValueError("No session specified")

        result = self._core.analyze_session(session_id)
        return json.loads(result)

    def analyze_mcp_costs(self) -> dict:
        """
        Rank MCPs by cost (which skills drain budget most).

        Returns:
            MCP ranking with:
            - rank, name, calls, cost_usd, avg_cost_per_call
            - anomalies (spikes detected)
            - caching opportunities

        Example:
            mcps = reporter.analyze_mcp_costs()
            for mcp in mcps['mcp_ranking'][:3]:
                print(f"{mcp['rank']}. {mcp['name']}: ${mcp['cost_usd']}")
        """
        result = self._core.analyze_mcp_costs()
        return json.loads(result)

    def get_recommendations(self) -> dict:
        """
        Get cost optimization recommendations.

        Returns:
            List of recommendations ranked by impact:
            - action (what to fix)
            - effort_minutes
            - expected_savings_usd
            - roi_weekly

        Example:
            recs = reporter.get_recommendations()
            for rec in recs['recommendations']:
                print(f"Save ${rec['expected_savings_usd']}/session: {rec['action']}")
        """
        result = self._core.get_recommendations()
        return json.loads(result)

    def detect_anomalies(self) -> dict:
        """
        Detect unusual spending patterns.

        Returns:
            List of anomalies:
            - type (spike, sudden change, etc)
            - cost difference
            - likely cause

        Example:
            anomalies = reporter.detect_anomalies()
            if anomalies['anomalies']:
                for anom in anomalies['anomalies']:
                    print(f"⚠️ {anom['type']}: {anom['likely_cause']}")
        """
        result = self._core.detect_anomalies()
        return json.loads(result)


__all__ = ["CostReporter"]
