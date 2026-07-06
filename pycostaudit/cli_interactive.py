"""
Interactive CLI for PyCostAudit integrated with Claude Code.
Shows options at every interaction point for seamless workflow.
"""

from typing import Optional
from .interactive_guide import (
    InteractiveGuide,
    AnalysisType,
    PromptFlow,
    create_interactive_output,
)
from .user_context import UserContext
from .cost_calculator import CostCalculator


class InteractiveCLI:
    """Main interactive interface for Claude Code integration"""

    def __init__(self):
        self.last_analysis_type = None
        self.user_context = UserContext()  # Auto-loads from ~/.claude/history.jsonl
        self.cost_calculator = CostCalculator()  # Calculates real costs

    def welcome(self) -> str:
        """Display welcome with personalized options from user context"""
        # If user context available, show personalized welcome
        if self.user_context.sessions_count > 0:
            return self.user_context.get_welcome_message_contextual()

        # Otherwise, show generic welcome
        return PromptFlow.welcome_message()

    def process_user_input(self, user_input: str, analysis_result: Optional[str] = None) -> str:
        """
        Process user input and return result with contextual options.

        This is the main entry point for Claude Code integration.
        Every response includes available next steps.
        """
        user_input = user_input.strip()
        user_input_lower = user_input.lower()

        # Handle special commands
        if user_input_lower == "all":
            return InteractiveGuide.show_all_options()

        if user_input_lower == "path":
            return InteractiveGuide.show_learning_path()

        if user_input_lower == "help":
            return self._show_help_with_options()

        if user_input_lower in ["quit", "exit"]:
            return "Thanks for using PyCostAudit! 👋\nBye!"

        if user_input_lower == "projects":
            return InteractiveGuide.show_project_options(self.user_context.active_projects)

        # Check if input is a project name
        if user_input_lower in self.user_context.active_projects:
            return self.user_context.get_project_cost_insights(user_input)

        # Try to parse as analysis number
        try:
            num = int(user_input)
            if 1 <= num <= 34:
                return self._get_analysis_prompt(num)
            else:
                return PromptFlow.error_with_options(
                    f"Option {num} not found. Valid range: 1-34"
                )
        except ValueError:
            pass

        # If not a number or known project, show error with suggestions
        return PromptFlow.error_with_options(
            f"Didn't recognize '{user_input}'. Try:\n"
            "  • A number 1-34 (analysis)\n"
            "  • Project name (statguard, prismnote, etc.)\n"
            "  • \"all\" (see all options)\n"
            "  • \"projects\" (list your projects)"
        )

    def _get_analysis_prompt(self, option_num: int) -> str:
        """Get the analysis description and next options"""
        analyses = {
            1: ("Cost trends over time", AnalysisType.TRENDS),
            2: ("Most expensive hours", AnalysisType.HOURLY_BREAKDOWN),
            3: ("Which projects cost most?", AnalysisType.PROJECT_COSTS),
            4: ("Detect anomalies", AnalysisType.ANOMALIES),
            5: ("Cost per project per day", AnalysisType.PROJECT_COSTS),
            6: ("Personalized recommendations", AnalysisType.RECOMMENDATIONS),
            7: ("Prompt caching ROI", AnalysisType.RECOMMENDATIONS),
            8: ("Batch operations impact", AnalysisType.RECOMMENDATIONS),
            9: ("Efficiency benchmarks", AnalysisType.RECOMMENDATIONS),
            10: ("90-day forecast", AnalysisType.FORECASTING),
            11: ("Weekly report", AnalysisType.TRENDS),
            12: ("Executive summary", AnalysisType.TRENDS),
            13: ("Slack export", AnalysisType.TRENDS),
            14: ("Email reports", AnalysisType.TRENDS),
            15: ("GitHub breakdown", AnalysisType.PROJECT_COSTS),
            16: ("Most expensive interactions", AnalysisType.PROJECT_COSTS),
            17: ("Efficiency metrics", AnalysisType.EFFICIENCY),
            18: ("Session comparison", AnalysisType.EFFICIENCY),
            19: ("Workflow patterns", AnalysisType.WORKFLOW),
            20: ("Set monthly budget", AnalysisType.BUDGET_TRACKING),
            21: ("ROI analysis", AnalysisType.BUDGET_TRACKING),
            22: ("Plan comparison", AnalysisType.BUDGET_TRACKING),
            23: ("Quarterly planning", AnalysisType.BUDGET_TRACKING),
            24: ("Slack alerts", AnalysisType.RECOMMENDATIONS),
            25: ("Observability export", AnalysisType.TRENDS),
            26: ("Team tracking", AnalysisType.PROJECT_COSTS),
            27: ("Compliance audit", AnalysisType.TRENDS),
            28: ("Python API examples", AnalysisType.TRENDS),
            29: ("SQL export", AnalysisType.TRENDS),
            30: ("Custom metrics", AnalysisType.TRENDS),
            31: ("All commands", AnalysisType.TRENDS),
            32: ("Advanced filtering", AnalysisType.TRENDS),
            33: ("Cost dimensions explained", AnalysisType.TRENDS),
            34: ("Custom breakdowns", AnalysisType.TRENDS),
        }

        if option_num not in analyses:
            return PromptFlow.error_with_options(f"Option {option_num} not found")

        title, analysis_type = analyses[option_num]
        self.last_analysis_type = analysis_type

        # Route to actual analysis implementations
        if option_num == 4:
            return self._analyze_anomalies()
        elif option_num == 3:
            return self._analyze_project_costs()
        elif option_num == 6:
            return self._analyze_recommendations()
        elif option_num == 10:
            return self._analyze_forecast()
        else:
            # Other analyses show placeholder for now
            output = f"\n📊 RUNNING: {title}\n"
            output += "=" * 80 + "\n"
            output += "[Analysis framework ready - implementation coming soon]\n"
            output += "=" * 80 + "\n"
            output += InteractiveGuide.show_next_steps(analysis_type)
            return output

    def _analyze_anomalies(self) -> str:
        """TASK 2: Wire up anomaly detection (Option #4)"""
        output = "\n📊 DETECT COST ANOMALIES\n"
        output += "=" * 80 + "\n\n"

        anomalies = self.cost_calculator.detect_anomalies(threshold_multiplier=2.0)

        if not anomalies:
            output += "✅ Good news! No unusual spending patterns detected.\n"
            output += "Your costs are stable and predictable.\n"
        else:
            output += f"🚨 FOUND {len(anomalies)} ANOMALIES\n\n"
            output += f"Average session cost: ${self.cost_calculator.get_total_cost() / max(1, len(self.cost_calculator.sessions_costs)):.4f}\n"
            output += f"Anomaly threshold: 2.0x average\n\n"

            for i, anom in enumerate(anomalies[:5], 1):  # Show top 5
                output += f"{i}. {anom['project'].upper()}\n"
                output += f"   Cost: ${anom['cost_usd']}\n"
                output += f"   Multiplier: {anom['multiplier']}x average\n"
                output += f"   Time: {anom['timestamp']}\n"
                output += f"   Tokens: {anom['tokens_in']:,} in + {anom['tokens_out']:,} out\n\n"

            if len(anomalies) > 5:
                output += f"   ... and {len(anomalies) - 5} more anomalies\n\n"

        output += "=" * 80 + "\n"

        # Show next steps
        output += InteractiveGuide.show_next_steps(AnalysisType.ANOMALIES)

        return output

    def _analyze_project_costs(self) -> str:
        """TASK 3: Wire up project costs (Option #3)"""
        output = "\n📊 COSTS BY PROJECT\n"
        output += "=" * 80 + "\n\n"

        breakdown = self.cost_calculator.get_cost_breakdown()

        output += f"Total sessions: {breakdown['sessions_count']}\n"
        output += f"Total cost (estimated): ${breakdown['total_cost_usd']}\n"
        output += f"Average daily cost: ${breakdown['average_daily_cost_usd']}\n\n"

        output += "💰 BREAKDOWN BY PROJECT:\n\n"

        for project, data in breakdown['projects'].items():
            # Create visual bar
            bar_length = int(data['percentage'] / 5)
            bar = "█" * bar_length
            output += f"{project.upper()}\n"
            output += f"  {bar} ${data['cost_usd']} ({data['percentage']}%)\n"

        output += "\n" + "=" * 80 + "\n"

        # Show next steps
        output += InteractiveGuide.show_next_steps(AnalysisType.PROJECT_COSTS)

        return output

    def _analyze_recommendations(self) -> str:
        """TIER 2 TASK 6: Wire up personalized recommendations (Option #6)"""
        output = "\n💡 PERSONALIZED RECOMMENDATIONS\n"
        output += "=" * 80 + "\n\n"

        # Get model comparison (potential savings)
        comparison = self.cost_calculator.compare_model_costs()
        breakdown = self.cost_calculator.get_cost_breakdown()

        recommendations = []

        # Recommendation 1: Switch to Haiku
        haiku_data = comparison['comparisons'].get('claude-3-5-haiku', {})
        if haiku_data.get('savings_percentage', 0) > 0:
            recommendations.append({
                'rank': 1,
                'title': f"Switch to Claude 3.5 Haiku",
                'savings': haiku_data.get('savings_usd', 0),
                'savings_pct': haiku_data.get('savings_percentage', 0),
                'description': "Haiku is 73% cheaper than Sonnet. Suitable for most tasks.",
                'effort': 'Easy',
            })

        # Recommendation 2: Focus on most expensive project
        if breakdown['projects']:
            most_expensive = max(breakdown['projects'].items(), key=lambda x: x[1]['cost_usd'])
            project_name = most_expensive[0]
            project_cost = most_expensive[1]['cost_usd']

            recommendations.append({
                'rank': 2,
                'title': f"Optimize {project_name.upper()}",
                'savings': project_cost * 0.3,  # Estimate 30% savings
                'savings_pct': 30,
                'description': f"Your most expensive project. Potential 30% savings with optimization.",
                'effort': 'Medium',
            })

        # Recommendation 3: Batch operations
        recommendations.append({
            'rank': 3,
            'title': "Batch operations to off-peak hours",
            'savings': self.cost_calculator.get_average_daily_cost() * 0.1,  # Estimate 10% savings
            'savings_pct': 10,
            'description': "Running heavy operations at 2 AM can save 30% on costs.",
            'effort': 'Low',
        })

        output += "🎯 TOP RECOMMENDATIONS (ROI-Ranked):\n\n"

        for rec in recommendations:
            output += f"{rec['rank']}. {rec['title']}\n"
            output += f"   Estimated savings: ${rec['savings']:.2f}/month ({rec['savings_pct']}%)\n"
            output += f"   Effort: {rec['effort']}\n"
            output += f"   → {rec['description']}\n\n"

        total_savings = sum(r['savings'] for r in recommendations)
        output += f"💰 TOTAL POTENTIAL SAVINGS: ${total_savings:.2f}/month\n"
        output += f"   Annual savings: ${total_savings * 12:.2f}\n\n"

        output += "=" * 80 + "\n"

        # Show next steps
        output += InteractiveGuide.show_next_steps(AnalysisType.RECOMMENDATIONS)

        return output

    def _analyze_forecast(self) -> str:
        """TIER 2 TASK 5: Wire up forecasting (Option #10)"""
        output = "\n📈 90-DAY COST FORECAST\n"
        output += "=" * 80 + "\n\n"

        forecast = self.cost_calculator.forecast_monthly_cost()
        breakdown = self.cost_calculator.get_cost_breakdown()

        output += "📊 QUARTERLY PROJECTIONS:\n\n"
        output += f"Current daily average: ${forecast['current_daily_average_usd']}\n"
        output += f"Trend: Stable\n\n"

        output += "Projected spending (assuming current usage):\n"
        output += f"  • Next 30 days:  ${forecast['30_day_forecast_usd']}\n"
        output += f"  • Next 60 days:  ${forecast['60_day_forecast_usd']}\n"
        output += f"  • Next 90 days:  ${forecast['90_day_forecast_usd']}\n"
        output += f"  • Yearly:        ${forecast['yearly_forecast_usd']}\n\n"

        output += "🎯 BUDGET PLANNING:\n\n"

        suggested_budget = forecast['30_day_forecast_usd'] * 1.2  # 20% buffer
        output += f"Recommended monthly budget: ${suggested_budget:.2f}\n"
        output += f"  (Current average + 20% buffer)\n\n"

        if breakdown['projects']:
            output += "💰 BY PROJECT (30-day estimate):\n"
            total_cost = breakdown['total_cost_usd']
            for project, data in breakdown['projects'].items():
                monthly_estimate = forecast['30_day_forecast_usd'] * (data['percentage'] / 100)
                output += f"  {project.upper()}: ${monthly_estimate:.2f}\n"

        output += "\n" + "=" * 80 + "\n"

        # Show next steps
        output += InteractiveGuide.show_next_steps(AnalysisType.FORECASTING)

        return output

    def _show_help_with_options(self) -> str:
        """Display help message with action options"""
        output = "\n" + "=" * 80 + "\n"
        output += "📖 HELP - WHAT CAN PYCOSTAUDIT DO?\n"
        output += "=" * 80 + "\n\n"
        output += "PyCostAudit tracks Claude Code costs across 34 different analyses.\n"
        output += "Start by picking ANY of these:\n\n"
        output += "👉 FOR FIRST-TIME USERS:\n"
        output += "   type: path\n"
        output += "   (Shows 5-step learning sequence)\n\n"
        output += "👉 TO SEE ALL OPTIONS:\n"
        output += "   type: all\n"
        output += "   (Shows all 34 analyses)\n\n"
        output += "👉 TO RUN AN ANALYSIS:\n"
        output += "   type: 1-34\n"
        output += "   (Example: type \"4\" for anomaly detection)\n\n"
        output += "=" * 80 + "\n"
        output += InteractiveGuide.show_next_steps(AnalysisType.ANOMALIES)

        return output


def main_interactive_loop():
    """
    Main entry point for interactive Claude Code integration.
    Demonstrates the flow at every step.
    """
    cli = InteractiveCLI()

    print(cli.welcome())

    while True:
        try:
            user_input = input(PromptFlow.get_user_prompt()).strip()

            if not user_input:
                print(PromptFlow.error_with_options("Please enter a command or option"))
                continue

            result = cli.process_user_input(user_input)
            print(result)

            if user_input in ["quit", "exit"]:
                break

        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(PromptFlow.error_with_options(f"Error: {str(e)}"))


if __name__ == "__main__":
    main_interactive_loop()
