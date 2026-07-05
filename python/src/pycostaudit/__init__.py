"""
PyCostAudit: Real-time LLM cost tracking and optimization

A MIT OSS tool that tracks:
- File format cost multipliers (36x variance: CSV vs PDF URL)
- Operation type breakdown (55x variance: browser vs file)
- Instruction context costs (10x-50x: .claude/claude.md overhead)
- Data warehouse queries (100x-1000x+: millions of rows)
- S3 operations (100x-1000x+: file listing/download)
- SaaS MCP inefficiency (10x-100x: Stripe, Salesforce, etc)
- Session-based cost grouping (root cause analysis)

Usage:
    from pycost_audit import PyCostAudit

    reporter = PyCostAudit(db_path="~/.pycostaudit/costs.db")

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

from ._core import PyCostAudit as _PyCostAuditCore
import json


class PyCostAudit:
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

        self._core = _PyCostAuditCore(db_path)
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
        cloud_region: str = None,
        billing_plan: str = None,
        pricing_tier: str = None,
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
            cloud_region: Cloud region if using cloud provider (e.g., "us-east-1", "eu-west-1")
                CRITICAL: Cloud pricing varies by region (10-30% variance)
                Bedrock: us-east-1, us-west-2, eu-west-1, ap-northeast-1
                Azure: eastus, westeurope, southeastasia
                GCP: us-central1, europe-west1, asia-east1
            billing_plan: Billing plan/tier for this operation ("api", "pro", "max", "enterprise")
                CRITICAL: Pricing varies 200%+ between plans
                api: Pay-per-token (highest cost)
                pro: $20/month fixed
                max: $200/month fixed (best for high volume)
                enterprise: Custom negotiated (usually 20-50% discount)
            pricing_tier: Time-of-day pricing tier ("peak", "standard", "off_peak", "weekend")
                CRITICAL: Pricing varies 20-40% by hour
                off_peak: 10 PM - 6 AM (30% discount, 0.7x multiplier)
                standard: 6 AM - 5 PM (baseline, 1.0x multiplier)
                peak: 5 PM - 10 PM weekdays (30% premium, 1.3x multiplier)
                weekend: Weekends (15% discount, 0.85x multiplier)

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
                user_timezone="America/New_York",  # Daily reset at midnight EST
                cloud_region="eu-west-1",  # EU premium: +15% on Bedrock
                billing_plan="max",  # User on Max plan: \$200/month fixed
                pricing_tier="off_peak"  # Run at 2 AM: 30% discount (0.7x)
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
            cloud_region=cloud_region,
            billing_plan=billing_plan,
            pricing_tier=pricing_tier,
        )
        return json.loads(result)

    def analyze_daily(self) -> dict:
        """
        Get today's cost breakdown.

        ⚠️ PRICING SOURCE WARNING:
        Costs are ONLY accurate if pricing was fetched from source APIs.
        If any pricing shows source="fallback", that cost is UNRELIABLE.

        Returns:
            Breakdown by:
            - operation_type (api_call, file_read, browser_op, etc)
            - file_format (csv, pdf_local, pdf_url, etc)
            - mcp (web_search, code_execution, etc)
            - pricing_source: "api" (verified), "cache" (updated hourly), "fallback" (⚠️ unreliable)

        Example:
            breakdown = reporter.analyze_daily()
            print(f"Total: ${breakdown['total_cost_usd']}")
            if breakdown.get('pricing_source') != 'api':
                print(f"⚠️ WARNING: Pricing from {breakdown['pricing_source']} - may be inaccurate")
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

    def compare_models(self, tokens_input: int, tokens_output: int) -> dict:
        """
        Compare costs across Claude models for informed model selection.

        ⚠️ CRITICAL: API pricing changes as new models launch and rates update.
        This comparison uses current cached pricing. Always check Anthropic's pricing page
        for real-time rates before final cost decisions.

        Args:
            tokens_input: Sample input token count
            tokens_output: Sample output token count

        Returns:
            Model comparison with:
            - baseline_model: Reference model (Claude 3.5 Sonnet)
            - baseline_cost_usd: Baseline cost
            - comparisons: Array of model costs with ratios and savings %

        Example:
            comparison = reporter.compare_models(tokens_input=1000, tokens_output=500)
            print(f"Baseline (Sonnet): ${comparison['baseline_cost_usd']:.4f}")
            for model in comparison['comparisons']:
                savings = model['savings_percentage']
                if savings > 0:
                    print(f"  {model['model']}: Save {savings:.1f}% → ${model['cost_usd']:.4f}")
                else:
                    print(f"  {model['model']}: Cost {abs(savings):.1f}% more → ${model['cost_usd']:.4f}")

        ⚠️ DISCLAIMER:
            - Pricing may have changed since last update
            - New models (Fable, Opus) pricing subject to change
            - Enterprise customers have negotiated rates (not shown here)
            - Token counting methodology may differ from actual Claude API
            - Use this for estimation only - verify with billing dashboard
        """
        result = self._core.compare_models(
            tokens_input=tokens_input,
            tokens_output=tokens_output
        )
        return json.loads(result)

    def compare_billing_plans(self) -> dict:
        """
        Compare billing plans to find optimal cost tier.

        Returns cost for each plan based on current usage patterns:
        - API: Pay-per-token (most expensive for high volume)
        - Pro: \$20/month fixed (good for low-moderate volume)
        - Max: \$200/month fixed (best for high volume)
        - Enterprise: Custom pricing (typically 20-50% discount)

        Returns:
            Plan comparison with:
            - current_usage_monthly: Projected monthly tokens
            - plan_comparison: Array of plans with monthly costs
            - recommended_plan: Which plan is cheapest
            - savings_message: "Best plan: Max at \$45/month"

        Example:
            plans = reporter.compare_billing_plans()
            print(f"Monthly usage: {plans['current_usage_monthly']['tokens_input']} tokens")
            print(f"Recommended: {plans['recommended_plan']} at \\${plans['recommended_cost']}/month")

            for plan in plans['plan_comparison']:
                print(f"  {plan['plan']}: \\${plan['monthly_cost']}")

        ⚠️ PLAN SWITCHING IMPACT:

            Current (API): \$2,850/month for 1B tokens/month
            → Switch to Pro: \$20/month (save \$2,830!)
            → Switch to Max: \$200/month (save \$2,650!)
            → Switch to Enterprise: ~\$2,000/month (negotiate 30% discount)

        Breakeven points:
            Pro (\$20) ≈ 6.7M tokens/month of Sonnet
            Max (\$200) ≈ 67M tokens/month of Sonnet
            Enterprise ≈ 1B+ tokens/month (negotiate custom rate)

        ⚠️ LIMITATIONS:
            - Effective cost assumes you use full plan limits
            - Pro/Max have usage caps (not unlimited)
            - Enterprise pricing is unique per contract
            - This comparison uses published rates, not your negotiated rate
            - Team multi-channel costs not included (use compare_models for provider breakdown)
        """
        result = self._core.compare_billing_plans()
        return json.loads(result)

    def forecast_quarterly(self) -> dict:
        """
        Forecast quarterly spending with pricing volatility disclaimer.

        ⚠️ CRITICAL DISCLAIMER: All forecasts assume CURRENT pricing remains unchanged.
        Any of these events INVALIDATE this forecast:
          - Anthropic launches new models (Fable-5, etc)
          - Claude API pricing changes
          - Your access switches from Claude API → Bedrock → Azure Foundry → GCP Model Garden
          - New MCP costs discovered
          - Prompt optimization implemented (should reduce costs)

        Returns:
            Forecast with:
            - projected_cost_usd: Quarterly projection
            - confidence_level: How confident (depends on pricing stability)
            - assumptions: What was assumed
            - disclaimer: Pricing volatility warnings
            - breakeven_payback: When optimizations pay off

        Example:
            forecast = reporter.forecast_quarterly()
            print(f"Q3 Projection: ${forecast['projected_cost_usd']:.2f}")
            print(f"Confidence: {forecast['confidence_level']}")
            print("Warnings:")
            for warning in forecast['disclaimer']['warnings']:
                print(f"  ⚠️ {warning}")

        ⚠️ WARNINGS:
            - Forecast valid only until CURRENT PRICING CHANGES
            - New Claude models typically cost less → forecast overstates cost
            - Bedrock/Foundry/Model Garden have DIFFERENT pricing than Claude API
            - If switching providers, re-run forecast (pricing differs by 20-40%)
            - Enterprise discounts not reflected
            - Refresh forecast weekly or after any API changes
        """
        result = self._core.forecast_quarterly()
        return json.loads(result)


__all__ = ["CostReporter"]
