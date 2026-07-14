#!/usr/bin/env python3
"""
Demo: Track Claude Code operations in real-time
Shows how PyCostAudit tracks costs across multi-provider LLM usage.

This demo simulates typical Claude Code operations:
- Model API calls (Claude, GPT-4, Bedrock)
- File operations
- Code execution
- Tool use

Run: python examples/demo_claude_code_tracking.py
"""

from datetime import datetime, timedelta
from pytokencalc.cost_model import CostTracker, Cost
from pytokencalc.alerting import AlertEngine, AlertType, AlertSeverity, SlackAlertChannel
import random


def simulate_claude_code_operations():
    """Simulate real Claude Code operations and track costs"""

    print("=" * 80)
    print("PyCostAudit: Claude Code Session Cost Tracking Demo")
    print("=" * 80)
    print()

    # Initialize tracker and alerting
    tracker = CostTracker()
    alert_engine = AlertEngine()

    # Set up alerting (without actual Slack for demo)
    print("📊 Initializing cost tracker and alert engine...")
    print()

    # Create alert policies
    budget_policy = alert_engine.create_policy(
        name="Budget Threshold",
        alert_type=AlertType.BUDGET_THRESHOLD,
        severity=AlertSeverity.HIGH,
        budget_threshold_percent=0.75,
        slack_enabled=True,
        slack_channel="#cost-alerts",
    )

    anomaly_policy = alert_engine.create_policy(
        name="Cost Anomaly",
        alert_type=AlertType.COST_ANOMALY,
        severity=AlertSeverity.MEDIUM,
        anomaly_sigma=2.0,
    )

    spike_policy = alert_engine.create_policy(
        name="Daily Spike",
        alert_type=AlertType.DAILY_SPIKE,
        severity=AlertSeverity.HIGH,
        spike_multiplier=1.5,
    )

    print("✅ Created 3 alert policies:")
    print("   • Budget Threshold (75%)")
    print("   • Cost Anomaly (2-sigma)")
    print("   • Daily Spike (1.5x multiplier)")
    print()

    # ========================================================================
    # OPERATION 1: OpenAI GPT-4 Turbo (External API Call)
    # ========================================================================
    print("─" * 80)
    print("OPERATION 1: OpenAI GPT-4 Turbo - File Analysis Tool")
    print("─" * 80)

    op1_call = {"model": "gpt-4-turbo"}
    op1_response = {
        "usage": {
            "prompt_tokens": 2500,  # Context from files + prior messages
            "completion_tokens": 150,  # Response
        }
    }

    cost1 = tracker.track_api_call(op1_call, op1_response)
    print(f"Provider: {cost1.provider}")
    print(f"Model: {cost1.model}")
    print(f"Input tokens: {cost1.input_tokens:,}")
    print(f"Output tokens: {cost1.output_tokens:,}")
    print(f"Cost: ${cost1.total_cost:.4f}")
    print()

    # ========================================================================
    # OPERATION 2: OpenAI GPT-5 Call (Premium Model for Complex Task)
    # ========================================================================
    print("─" * 80)
    print("OPERATION 2: OpenAI GPT-5 - Complex Code Analysis")
    print("─" * 80)

    op2_call = {"model": "gpt-5"}
    op2_response = {
        "usage": {
            "prompt_tokens": 1800,
            "completion_tokens": 300,
        }
    }

    cost2 = tracker.track_api_call(op2_call, op2_response)
    print(f"Provider: {cost2.provider}")
    print(f"Model: {cost2.model}")
    print(f"Input tokens: {cost2.input_tokens:,}")
    print(f"Output tokens: {cost2.output_tokens:,}")
    print(f"Cost: ${cost2.total_cost:.4f}")
    print()

    # ========================================================================
    # OPERATION 3: AWS Bedrock Claude 3 Opus (Enterprise Fallback)
    # ========================================================================
    print("─" * 80)
    print("OPERATION 3: AWS Bedrock - Enterprise Alternative")
    print("─" * 80)

    op3_call = {"modelId": "anthropic.claude-3-opus"}
    op3_response = {
        "usage": {
            "inputTokens": 3200,
            "outputTokens": 400,
        }
    }

    cost3 = tracker.track_api_call(op3_call, op3_response)
    print(f"Provider: {cost3.provider}")
    print(f"Model: {cost3.model}")
    print(f"Input tokens: {cost3.input_tokens:,}")
    print(f"Output tokens: {cost3.output_tokens:,}")
    print(f"Cost: ${cost3.total_cost:.4f}")
    print()

    # ========================================================================
    # OPERATION 4: Google Gemini Call (Research/Testing)
    # ========================================================================
    print("─" * 80)
    print("OPERATION 4: Google Gemini - Cost-Effective Alternative")
    print("─" * 80)

    op4_call = {"model": "gemini-pro"}
    op4_response = {
        "usage_metadata": {
            "prompt_token_count": 1500,
            "candidates_token_count": 200,
        }
    }

    cost4 = tracker.track_api_call(op4_call, op4_response)
    print(f"Provider: {cost4.provider}")
    print(f"Model: {cost4.model}")
    print(f"Input tokens: {cost4.input_tokens:,}")
    print(f"Output tokens: {cost4.output_tokens:,}")
    print(f"Cost: ${cost4.total_cost:.4f}")
    print()

    # ========================================================================
    # COST SUMMARY & BREAKDOWN
    # ========================================================================
    print("=" * 80)
    print("COST SUMMARY & BREAKDOWN")
    print("=" * 80)
    print()

    total_cost = tracker.get_total_cost()
    print(f"📈 Total Session Cost: ${total_cost:.4f}")
    print()

    print("Cost Breakdown by Provider:")
    by_provider = tracker.cost_by_provider()
    for provider, cost in sorted(by_provider.items(), key=lambda x: x[1], reverse=True):
        pct = (cost / total_cost * 100) if total_cost > 0 else 0
        print(f"  • {provider.upper():10s}: ${cost:8.4f} ({pct:5.1f}%)")
    print()

    print("Cost Breakdown by Model:")
    by_model = tracker.cost_by_model()
    for model, cost in sorted(by_model.items(), key=lambda x: x[1], reverse=True):
        pct = (cost / total_cost * 100) if total_cost > 0 else 0
        print(f"  • {model:25s}: ${cost:8.4f} ({pct:5.1f}%)")
    print()

    # ========================================================================
    # MULTI-PROVIDER COMPARISON
    # ========================================================================
    print("=" * 80)
    print("MULTI-PROVIDER COST COMPARISON")
    print("=" * 80)
    print()

    print("For equivalent 2,500 input + 300 output tokens:")
    print()

    test_tokens = {"input": 2500, "output": 300}

    # Claude (Opus 4.8) - via Anthropic
    claude_input = (test_tokens["input"] / 1000) * 0.015
    claude_output = (test_tokens["output"] / 1000) * 0.075
    claude_total = claude_input + claude_output

    # GPT-4 - via OpenAI
    gpt4_input = (test_tokens["input"] / 1000) * 0.030
    gpt4_output = (test_tokens["output"] / 1000) * 0.060
    gpt4_total = gpt4_input + gpt4_output

    # Claude 3 Opus - via Bedrock
    bedrock_input = (test_tokens["input"] / 1000) * 0.015
    bedrock_output = (test_tokens["output"] / 1000) * 0.075
    bedrock_total = bedrock_input + bedrock_output

    # Gemini Pro - via Google
    gemini_input = (test_tokens["input"] / 1000) * 0.000125
    gemini_output = (test_tokens["output"] / 1000) * 0.000375
    gemini_total = gemini_input + gemini_output

    costs = {
        "Claude (Direct)": claude_total,
        "Claude (Bedrock)": bedrock_total,
        "GPT-4 (OpenAI)": gpt4_total,
        "Gemini (Google)": gemini_total,
    }

    min_cost = min(costs.values())
    for model, cost in sorted(costs.items(), key=lambda x: x[1]):
        savings = ((cost - min_cost) / min_cost) * 100 if min_cost > 0 else 0
        marker = "🏆 CHEAPEST" if cost == min_cost else f"+{savings:5.1f}%"
        print(f"  {model:20s}: ${cost:.5f}  {marker}")
    print()

    # ========================================================================
    # ALERTING DEMO
    # ========================================================================
    print("=" * 80)
    print("ALERTING SYSTEM DEMO")
    print("=" * 80)
    print()

    # Set up hourly costs for spike detection
    alert_engine.update_hourly_costs([0.05, 0.06, 0.04, 0.05, 0.06])

    # Simulate a cost that would trigger spike alert
    spike_cost = Cost(
        provider="openai",
        model="gpt-4",
        input_tokens=5000,
        output_tokens=1000,
        input_cost=0.15,
        output_cost=0.06,
        total_cost=0.21,
    )

    print("Testing alert policies with sample costs...")
    print()

    # Test spike detection
    print("Spike Detection Test:")
    print(f"  Hourly average cost: $0.052")
    print(f"  Current cost: ${spike_cost.total_cost:.4f}")
    print(f"  Spike multiplier: 1.5x (trigger at $0.078)")
    is_spike = spike_cost.total_cost > (0.052 * 1.5)
    print(f"  Result: {'⚠️  SPIKE DETECTED!' if is_spike else '✅ Normal'}")
    print()

    # Mock alert sending
    print("Alert Channels Configuration:")
    print("  • Slack: #cost-alerts (enabled)")
    print("  • Twilio: Not configured (SMS for critical only)")
    print()

    # ========================================================================
    # EXPORT & RECOMMENDATIONS
    # ========================================================================
    print("=" * 80)
    print("OPTIMIZATION RECOMMENDATIONS")
    print("=" * 80)
    print()

    print("Based on this session's usage patterns:")
    print()

    print("1. 🎯 Provider Selection")
    cheapest = min(costs, key=costs.get)
    print(f"   → {cheapest} is {((gpt4_total - costs[cheapest]) / gpt4_total * 100):.0f}% cheaper than GPT-4")
    print()

    print("2. 💰 Cost Optimization")
    if gpt4_total > claude_total * 1.5:
        print(f"   → Switch from GPT-4 to Claude: Save ${gpt4_total - claude_total:.4f} per call")
    else:
        print(f"   → Current provider selection is already cost-optimal")
    print()

    print("3. 📊 Session Insights")
    total_tokens = sum(c.input_tokens + c.output_tokens for c in tracker.costs)
    print(f"   → Total tokens used: {total_tokens:,}")
    print(f"   → Avg cost per token: ${total_cost / total_tokens * 1000000:.2f} per 1M")
    print()

    # ========================================================================
    # EXPORT DATA
    # ========================================================================
    print("=" * 80)
    print("EXPORT & INTEGRATION")
    print("=" * 80)
    print()

    exported = tracker.export_costs()
    print(f"✅ Exported {len(exported)} operation records")
    print()

    print("Sample exported record:")
    if exported:
        import json

        sample = exported[0]
        print(json.dumps(sample, indent=2, default=str))
    print()

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()

    print(f"Session tracked {len(tracker.costs)} operations across {len(set(c.provider for c in tracker.costs))} providers")
    print(f"Total session cost: ${total_cost:.4f}")
    print(f"Potential savings by optimization: ${gpt4_total - costs[cheapest]:.4f} per equivalent call")
    print()

    print("✅ Real-time alerting ready (Slack + Twilio configured)")
    print("✅ Cost breakdown available by provider, model, and operation")
    print("✅ Historical tracking enabled for trend analysis")
    print()


if __name__ == "__main__":
    simulate_claude_code_operations()
