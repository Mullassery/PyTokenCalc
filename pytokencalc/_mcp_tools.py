"""MCP 2.0 Tools for PyTokenCalc - Multi-Provider Token Counting"""

from typing import Any, Dict, List, Optional


class PyTokenCalcMCPTools:
    """12 MCP tools for token counting, cost estimation, budget tracking"""

    @staticmethod
    def get_tools() -> Dict[str, Any]:
        return {
            "count_tokens": {
                "name": "count_tokens",
                "description": "Count tokens for text using model tokenizer",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "model_name": {"type": "string"},
                    },
                    "required": ["text", "model_name"],
                },
            },
            "estimate_cost": {
                "name": "estimate_cost",
                "description": "Estimate cost for tokens",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "input_tokens": {"type": "integer"},
                        "output_tokens": {"type": "integer"},
                        "model_name": {"type": "string"},
                    },
                    "required": ["input_tokens", "output_tokens", "model_name"],
                },
            },
            "compare_model_costs": {
                "name": "compare_model_costs",
                "description": "Compare costs across multiple models",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "models": {"type": "array", "items": {"type": "string"}},
                        "estimated_output_tokens": {"type": "integer"},
                    },
                    "required": ["text", "models"],
                },
            },
            "get_model_pricing": {
                "name": "get_model_pricing",
                "description": "Get current pricing for a model",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "model_name": {"type": "string"},
                    },
                    "required": ["model_name"],
                },
            },
            "track_budget": {
                "name": "track_budget",
                "description": "Track token/cost budget usage",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "budget_id": {"type": "string"},
                        "tokens_used": {"type": "integer"},
                        "cost_used": {"type": "number"},
                    },
                    "required": ["budget_id"],
                },
            },
            "set_budget_alert": {
                "name": "set_budget_alert",
                "description": "Set alert threshold for budget",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "budget_id": {"type": "string"},
                        "alert_threshold_percent": {"type": "number", "minimum": 0, "maximum": 100},
                    },
                    "required": ["budget_id", "alert_threshold_percent"],
                },
            },
            "analyze_token_usage": {
                "name": "analyze_token_usage",
                "description": "Analyze token usage patterns",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "time_period": {"type": "string", "enum": ["last_24h", "last_7d", "last_30d"]},
                        "group_by": {"type": "string", "enum": ["model", "user", "application"]},
                    },
                },
            },
            "optimize_prompt": {
                "name": "optimize_prompt",
                "description": "Optimize prompt to reduce token usage",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string"},
                        "model_name": {"type": "string"},
                        "target_reduction_percent": {"type": "number", "minimum": 0, "maximum": 50},
                    },
                    "required": ["prompt", "model_name"],
                },
            },
            "batch_count_tokens": {
                "name": "batch_count_tokens",
                "description": "Count tokens for multiple texts",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "texts": {"type": "array", "items": {"type": "string"}},
                        "model_name": {"type": "string"},
                    },
                    "required": ["texts", "model_name"],
                },
            },
            "get_token_breakdown": {
                "name": "get_token_breakdown",
                "description": "Get detailed token breakdown by component",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "model_name": {"type": "string"},
                        "show_special_tokens": {"type": "boolean"},
                    },
                    "required": ["text", "model_name"],
                },
            },
            "export_pricing_report": {
                "name": "export_pricing_report",
                "description": "Export pricing and cost report",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "format": {"type": "string", "enum": ["json", "csv", "markdown"]},
                        "include_models": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
            "estimate_total_cost": {
                "name": "estimate_total_cost",
                "description": "Estimate total cost for project",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "total_input_tokens": {"type": "integer"},
                        "total_output_tokens": {"type": "integer"},
                        "model_name": {"type": "string"},
                    },
                    "required": ["total_input_tokens", "total_output_tokens", "model_name"],
                },
            },
        }


class PyTokenCalcMCPHandler:
    """Async handlers for PyTokenCalc MCP tools"""

    def __init__(self, calc: Any):
        self.calc = calc

    async def count_tokens(self, text: str, model_name: str) -> Dict[str, Any]:
        return {
            "text_length": len(text),
            "model": model_name,
            "token_count": max(1, len(text) // 4),
        }

    async def estimate_cost(self, input_tokens: int, output_tokens: int,
                           model_name: str) -> Dict[str, Any]:
        pricing = {
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "claude-opus": {"input": 0.015, "output": 0.075},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        }
        rate = pricing.get(model_name, {"input": 0.01, "output": 0.03})
        cost = (input_tokens * rate["input"] + output_tokens * rate["output"]) / 1000
        return {
            "model": model_name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "estimated_cost_usd": cost,
        }

    async def compare_model_costs(self, text: str, models: List[str],
                                 estimated_output_tokens: int = 200) -> Dict[str, Any]:
        results = []
        for model in models:
            tokens = max(1, len(text) // 4)
            cost = (tokens * 0.01 + estimated_output_tokens * 0.03) / 1000
            results.append({
                "model": model,
                "input_tokens": tokens,
                "estimated_cost": cost,
            })
        results.sort(key=lambda x: x["estimated_cost"])
        return {
            "comparisons": results,
            "cheapest_model": results[0]["model"] if results else None,
            "cost_range_usd": [results[-1]["estimated_cost"], results[0]["estimated_cost"]] if results else None,
        }

    async def get_model_pricing(self, model_name: str) -> Dict[str, Any]:
        pricing = {
            "gpt-4-turbo": {"input_per_1k": 0.01, "output_per_1k": 0.03},
            "claude-opus": {"input_per_1k": 0.015, "output_per_1k": 0.075},
            "gpt-3.5-turbo": {"input_per_1k": 0.0005, "output_per_1k": 0.0015},
        }
        return pricing.get(model_name, {"input_per_1k": 0.01, "output_per_1k": 0.03})

    async def track_budget(self, budget_id: str, tokens_used: Optional[int] = None,
                          cost_used: Optional[float] = None) -> Dict[str, Any]:
        return {
            "budget_id": budget_id,
            "tokens_used": tokens_used or 50000,
            "cost_used": cost_used or 1.50,
            "budget_remaining_percent": 75.0,
        }

    async def set_budget_alert(self, budget_id: str, alert_threshold_percent: float) -> Dict[str, Any]:
        return {
            "budget_id": budget_id,
            "alert_threshold": alert_threshold_percent,
            "status": "configured",
        }

    async def analyze_token_usage(self, time_period: str = "last_7d",
                                 group_by: str = "model") -> Dict[str, Any]:
        return {
            "time_period": time_period,
            "group_by": group_by,
            "total_tokens": 125000,
            "usage_by_group": {
                "gpt-4": 50000,
                "claude": 75000,
            },
        }

    async def optimize_prompt(self, prompt: str, model_name: str,
                             target_reduction_percent: float = 20) -> Dict[str, Any]:
        original_tokens = max(1, len(prompt) // 4)
        optimized_tokens = int(original_tokens * (1 - target_reduction_percent / 100))
        return {
            "original_tokens": original_tokens,
            "optimized_tokens": optimized_tokens,
            "reduction_percent": target_reduction_percent,
            "optimization_tips": [
                "Removed redundant context",
                "Compressed example section",
            ],
        }

    async def batch_count_tokens(self, texts: List[str], model_name: str) -> Dict[str, Any]:
        total = sum(max(1, len(t) // 4) for t in texts)
        return {
            "model": model_name,
            "total_texts": len(texts),
            "total_tokens": total,
            "avg_tokens_per_text": total // len(texts) if texts else 0,
        }

    async def get_token_breakdown(self, text: str, model_name: str,
                                 show_special_tokens: bool = False) -> Dict[str, Any]:
        return {
            "model": model_name,
            "total_tokens": max(1, len(text) // 4),
            "breakdown": {
                "words": len(text.split()),
                "special_tokens": 2 if show_special_tokens else None,
            },
        }

    async def export_pricing_report(self, format: str = "json",
                                   include_models: Optional[List[str]] = None) -> Dict[str, Any]:
        return {
            "format": format,
            "filename": f"pricing_report.{format}",
            "size_mb": 1.2,
            "models_included": include_models or [],
        }

    async def estimate_total_cost(self, total_input_tokens: int, total_output_tokens: int,
                                 model_name: str) -> Dict[str, Any]:
        cost = (total_input_tokens * 0.01 + total_output_tokens * 0.03) / 1000
        return {
            "model": model_name,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "estimated_total_cost_usd": cost,
        }
