"""MCP 2.0 tools and handlers for PyTokenCalc.

These tools count tokens and estimate cost using the same real machinery as
the rest of the library:

- token counts come from :class:`pytokencalc.tokenizers.TokenCounterRegistry`
  (the model's real tokenizer; OpenAI via tiktoken, etc.). An optional
  tokenizer dependency for a given provider must be installed or that count
  raises.
- cost comes from the static :mod:`pytokencalc.pricing` table (USD per
  million tokens), not from a live pricing feed.

Budget tracking and usage analytics are **in-memory** for the lifetime of the
handler instance. PyTokenCalc has no persistence layer by design, so these are
explicitly process-scoped and non-durable rather than pretending otherwise.
Prompt "optimization" applies conservative, lossless whitespace edits and
reports the token reduction it actually achieves -- the
``target_reduction_percent`` argument is a goal, not a promise.

There is no background daemon, no ``dab`` binary, and no external service
involved.
"""

import csv
import io
import json
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .pricing import (
    PRICING_LAST_UPDATED,
    PRICING_TABLE,
    get_model_pricing,
    resolve_model_pricing_key,
)

_TIME_PERIOD_HOURS = {"last_24h": 24, "last_7d": 24 * 7, "last_30d": 24 * 30}


def _resolved_pricing_key(model: str) -> Optional[str]:
    """Return the PRICING_TABLE key a model resolves to, using the same
    safe exact/snapshot-suffix matching as pricing.get_model_pricing."""
    return resolve_model_pricing_key(model)


class PyTokenCalcMCPTools:
    """12 MCP tools for token counting, cost estimation, budget tracking"""

    @staticmethod
    def get_tools() -> Dict[str, Any]:
        return {
            "count_tokens": {
                "name": "count_tokens",
                "description": (
                    "Count input tokens for text using model_name's real "
                    "tokenizer (OpenAI via tiktoken; other providers need "
                    "their optional tokenizer dependency installed)."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "model_name": {"type": "string"},
                        "provider": {"type": "string"},
                    },
                    "required": ["text", "model_name"],
                },
            },
            "estimate_cost": {
                "name": "estimate_cost",
                "description": (
                    "Estimate USD cost for a token count using the static "
                    "pytokencalc.pricing table. Errors if the model has no "
                    "pricing entry."
                ),
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
                "description": (
                    "Count tokens for the same text with each model's real "
                    "tokenizer and estimate costs from the pricing table."
                ),
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
                "description": "Get static USD-per-million pricing for a model.",
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
                "description": (
                    "Record cumulative token/cost usage for a budget id in "
                    "memory (this process only). Pass limit_tokens/limit_cost "
                    "to get remaining amount and used percent."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "budget_id": {"type": "string"},
                        "tokens_used": {"type": "integer"},
                        "cost_used": {"type": "number"},
                        "limit_tokens": {"type": "integer"},
                        "limit_cost": {"type": "number"},
                    },
                    "required": ["budget_id"],
                },
            },
            "set_budget_alert": {
                "name": "set_budget_alert",
                "description": (
                    "Set an in-memory alert threshold (percent of a budget "
                    "limit) for a budget id."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "budget_id": {"type": "string"},
                        "alert_threshold_percent": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 100,
                        },
                    },
                    "required": ["budget_id", "alert_threshold_percent"],
                },
            },
            "analyze_token_usage": {
                "name": "analyze_token_usage",
                "description": (
                    "Summarize token/cost usage recorded in memory by this "
                    "handler instance since it was created."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "time_period": {
                            "type": "string",
                            "enum": ["last_24h", "last_7d", "last_30d"],
                        },
                        "group_by": {
                            "type": "string",
                            "enum": ["model", "user", "application"],
                        },
                    },
                },
            },
            "optimize_prompt": {
                "name": "optimize_prompt",
                "description": (
                    "Apply conservative whitespace/normalization edits and "
                    "report the token reduction actually achieved. The target "
                    "is a goal, not a guarantee."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string"},
                        "model_name": {"type": "string"},
                        "target_reduction_percent": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 50,
                        },
                    },
                    "required": ["prompt", "model_name"],
                },
            },
            "batch_count_tokens": {
                "name": "batch_count_tokens",
                "description": (
                    "Count input tokens for a list of texts with model_name's "
                    "real tokenizer."
                ),
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
                "description": (
                    "Return the tokenizer result's component fields "
                    "(input/system/tool/image) plus text statistics instead of "
                    "a fabricated per-word split."
                ),
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
                "description": (
                    "Build a pricing report (json/csv/markdown) from the static "
                    "pytokencalc.pricing table."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "format": {
                            "type": "string",
                            "enum": ["json", "csv", "markdown"],
                        },
                        "include_models": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                },
            },
            "estimate_total_cost": {
                "name": "estimate_total_cost",
                "description": (
                    "Estimate total USD cost for a project's input/output "
                    "token totals using the static pricing table."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "total_input_tokens": {"type": "integer"},
                        "total_output_tokens": {"type": "integer"},
                        "model_name": {"type": "string"},
                    },
                    "required": [
                        "total_input_tokens",
                        "total_output_tokens",
                        "model_name",
                    ],
                },
            },
        }


class PyTokenCalcMCPHandler:
    """Async handlers for PyTokenCalc MCP tools.

    Args:
        calc: Optional :class:`pytokencalc.TokenCalculator` (or any object
            exposing a ``registry``). Used only to obtain a
            ``TokenCounterRegistry``.
        registry: Optional explicit registry. Takes precedence over
            ``calc.registry``. When neither is given, the process-wide
            ``get_global_registry()`` is used lazily.
    """

    def __init__(self, calc: Any = None, registry: Any = None):
        self.calc = calc
        self._registry = registry
        self._budgets: Dict[str, Dict[str, Any]] = {}
        self._usage: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    # ----------------------------------------------------------------- helpers

    def _get_registry(self):
        if self._registry is not None:
            return self._registry
        calc_registry = getattr(self.calc, "registry", None)
        if calc_registry is not None:
            return calc_registry
        from pytokencalc.tokenizers import get_global_registry

        self._registry = get_global_registry()
        return self._registry

    def _count(self, text: str, model_name: str, provider: Optional[str] = None):
        return self._get_registry().count_tokens(model_name, text, provider)

    def _record_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
    ) -> None:
        with self._lock:
            self._usage.append(
                {
                    "timestamp": datetime.utcnow(),
                    "model": model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_usd": cost_usd,
                }
            )

    @staticmethod
    def _budget_state(budgets: Dict[str, Dict[str, Any]], budget_id: str) -> Dict[str, Any]:
        return budgets.setdefault(
            budget_id,
            {
                "tokens_used": 0,
                "cost_used": 0.0,
                "limit_tokens": None,
                "limit_cost": None,
                "alert_threshold_percent": None,
            },
        )

    # -------------------------------------------------------------- token tools

    async def count_tokens(
        self, text: str, model_name: str, provider: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            result = self._count(text, model_name, provider)
        except Exception as e:  # noqa: BLE001 - surface as an MCP error result
            return {"status": "error", "model": model_name, "message": str(e)}

        self._record_usage(model_name, result.input_tokens)
        return {
            "text_length": len(text),
            "model": model_name,
            "provider": result.provider,
            "input_tokens": result.input_tokens,
            "total_tokens": result.total_tokens,
            "source": result.source,
            "cached": result.cached,
            "latency_ms": round(result.latency_ms, 3),
        }

    async def batch_count_tokens(
        self, texts: List[str], model_name: str
    ) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        total = 0
        counted = 0
        for index, text in enumerate(texts):
            try:
                result = self._count(text, model_name)
            except Exception as e:  # noqa: BLE001
                results.append({"index": index, "error": str(e)})
                continue
            total += result.input_tokens
            counted += 1
            self._record_usage(model_name, result.input_tokens)
            results.append(
                {"index": index, "text_length": len(text), "tokens": result.input_tokens}
            )
        return {
            "model": model_name,
            "total_texts": len(texts),
            "counted_texts": counted,
            "total_tokens": total,
            "avg_tokens_per_text": (total / counted) if counted else None,
            "results": results,
        }

    async def get_token_breakdown(
        self,
        text: str,
        model_name: str,
        show_special_tokens: bool = False,
    ) -> Dict[str, Any]:
        try:
            result = self._count(text, model_name)
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "model": model_name, "message": str(e)}
        note = (
            "Component tokens (system/tool/image) are non-zero only for "
            "structured inputs; this tool receives plain text, so they are 0."
        )
        if show_special_tokens:
            note += " Special tokens are not separately exposed by the tokenizer."
        return {
            "model": model_name,
            "provider": result.provider,
            "total_tokens": result.total_tokens,
            "breakdown": {
                "input_tokens": result.input_tokens,
                "system_tokens": result.system_tokens,
                "tool_tokens": result.tool_tokens,
                "image_tokens": result.image_tokens,
            },
            "text_stats": {
                "characters": len(text),
                "words": len(text.split()),
                "lines": text.count("\n") + 1,
            },
            "note": note,
        }

    # --------------------------------------------------------------- cost tools

    async def estimate_cost(
        self, input_tokens: int, output_tokens: int, model_name: str
    ) -> Dict[str, Any]:
        pricing = get_model_pricing(model_name)
        if pricing is None:
            return {
                "status": "error",
                "model": model_name,
                "message": f"No pricing data for model '{model_name}'.",
                "known_models": sorted(PRICING_TABLE),
                "pricing_last_updated": PRICING_LAST_UPDATED,
            }
        input_cost = input_tokens * pricing.input_per_million / 1_000_000
        output_cost = output_tokens * pricing.output_per_million / 1_000_000
        self._record_usage(model_name, input_tokens, output_tokens, input_cost + output_cost)
        return {
            "model": model_name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "input_cost_usd": input_cost,
            "output_cost_usd": output_cost,
            "estimated_cost_usd": input_cost + output_cost,
            "pricing_per_million": {
                "input": pricing.input_per_million,
                "output": pricing.output_per_million,
            },
            "pricing_last_updated": PRICING_LAST_UPDATED,
        }

    async def estimate_total_cost(
        self, total_input_tokens: int, total_output_tokens: int, model_name: str
    ) -> Dict[str, Any]:
        return await self.estimate_cost(
            total_input_tokens, total_output_tokens, model_name
        )

    async def compare_model_costs(
        self,
        text: str,
        models: List[str],
        estimated_output_tokens: int = 200,
    ) -> Dict[str, Any]:
        comparisons: List[Dict[str, Any]] = []
        for model in models:
            pricing = get_model_pricing(model)
            try:
                input_tokens = self._count(text, model).input_tokens
            except Exception as e:  # noqa: BLE001
                comparisons.append({"model": model, "error": str(e)})
                continue
            if pricing is None:
                comparisons.append(
                    {
                        "model": model,
                        "input_tokens": input_tokens,
                        "error": "no pricing data",
                    }
                )
                continue
            input_cost = input_tokens * pricing.input_per_million / 1_000_000
            output_cost = estimated_output_tokens * pricing.output_per_million / 1_000_000
            comparisons.append(
                {
                    "model": model,
                    "input_tokens": input_tokens,
                    "estimated_output_tokens": estimated_output_tokens,
                    "input_cost_usd": input_cost,
                    "output_cost_usd": output_cost,
                    "estimated_cost_usd": input_cost + output_cost,
                }
            )

        priced = [c for c in comparisons if "estimated_cost_usd" in c]
        priced.sort(key=lambda c: c["estimated_cost_usd"])
        comparisons.sort(
            key=lambda c: (
                0 if "estimated_cost_usd" in c else 1,
                c.get("estimated_cost_usd", 0.0),
            )
        )
        return {
            "comparisons": comparisons,
            "priced_models": len(priced),
            "cheapest_model": priced[0]["model"] if priced else None,
            "most_expensive_model": priced[-1]["model"] if priced else None,
            "cost_range_usd": (
                [priced[0]["estimated_cost_usd"], priced[-1]["estimated_cost_usd"]]
                if priced
                else None
            ),
            "pricing_last_updated": PRICING_LAST_UPDATED,
        }

    async def get_model_pricing(self, model_name: str) -> Dict[str, Any]:
        pricing = get_model_pricing(model_name)
        if pricing is None:
            return {
                "status": "error",
                "model": model_name,
                "message": f"No pricing data for model '{model_name}'.",
                "known_models": sorted(PRICING_TABLE),
                "pricing_last_updated": PRICING_LAST_UPDATED,
            }
        return {
            "model": model_name,
            "resolved_model": _resolved_pricing_key(model_name),
            "input_per_million_usd": pricing.input_per_million,
            "output_per_million_usd": pricing.output_per_million,
            "pricing_last_updated": PRICING_LAST_UPDATED,
        }

    async def export_pricing_report(
        self,
        format: str = "json",
        include_models: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        models = include_models or sorted(PRICING_TABLE)
        rows = []
        for model in models:
            pricing = get_model_pricing(model)
            rows.append(
                {
                    "model": model,
                    "input_per_million_usd": (
                        pricing.input_per_million if pricing else None
                    ),
                    "output_per_million_usd": (
                        pricing.output_per_million if pricing else None
                    ),
                }
            )

        if format == "json":
            content = json.dumps(
                {
                    "pricing_last_updated": PRICING_LAST_UPDATED,
                    "models": rows,
                },
                indent=2,
            )
        elif format == "csv":
            buffer = io.StringIO()
            writer = csv.DictWriter(
                buffer,
                fieldnames=[
                    "model",
                    "input_per_million_usd",
                    "output_per_million_usd",
                ],
            )
            writer.writeheader()
            writer.writerows(rows)
            content = buffer.getvalue()
        elif format == "markdown":
            lines = [
                "# PyTokenCalc Pricing Report",
                f"\nPricing last updated: {PRICING_LAST_UPDATED}\n",
                "| Model | Input ($/M) | Output ($/M) |",
                "|---|---|---|",
            ]
            for row in rows:
                lines.append(
                    f"| {row['model']} | {row['input_per_million_usd']} "
                    f"| {row['output_per_million_usd']} |"
                )
            content = "\n".join(lines)
        else:
            return {
                "status": "error",
                "message": f"Unsupported format '{format}'.",
                "supported_formats": ["json", "csv", "markdown"],
            }

        return {
            "format": format,
            "models_included": models,
            "model_count": len(models),
            "pricing_last_updated": PRICING_LAST_UPDATED,
            "content": content,
            "size_bytes": len(content.encode("utf-8")),
        }

    # ------------------------------------------------------------- budget tools

    async def track_budget(
        self,
        budget_id: str,
        tokens_used: Optional[int] = None,
        cost_used: Optional[float] = None,
        limit_tokens: Optional[int] = None,
        limit_cost: Optional[float] = None,
    ) -> Dict[str, Any]:
        with self._lock:
            state = self._budget_state(self._budgets, budget_id)
            if tokens_used:
                state["tokens_used"] += tokens_used
            if cost_used:
                state["cost_used"] += cost_used
            if limit_tokens is not None:
                state["limit_tokens"] = limit_tokens
            if limit_cost is not None:
                state["limit_cost"] = limit_cost

            remaining_tokens = (
                state["limit_tokens"] - state["tokens_used"]
                if state["limit_tokens"] is not None
                else None
            )
            remaining_cost = (
                state["limit_cost"] - state["cost_used"]
                if state["limit_cost"] is not None
                else None
            )
            used_percent = None
            if state["limit_cost"]:
                used_percent = state["cost_used"] / state["limit_cost"] * 100
            elif state["limit_tokens"]:
                used_percent = state["tokens_used"] / state["limit_tokens"] * 100

            threshold = state["alert_threshold_percent"]
            alert_triggered = (
                used_percent is not None
                and threshold is not None
                and used_percent >= threshold
            )
            snapshot = dict(state)

        if cost_used:
            self._record_usage("(budget)", 0, 0, cost_used)

        return {
            "budget_id": budget_id,
            "tokens_used": snapshot["tokens_used"],
            "cost_used_usd": snapshot["cost_used"],
            "limit_tokens": snapshot["limit_tokens"],
            "limit_cost_usd": snapshot["limit_cost"],
            "remaining_tokens": remaining_tokens,
            "remaining_cost_usd": remaining_cost,
            "used_percent": used_percent,
            "alert_threshold_percent": threshold,
            "alert_triggered": alert_triggered,
            "scope": "in-memory (this process only; not persisted)",
        }

    async def set_budget_alert(
        self, budget_id: str, alert_threshold_percent: float
    ) -> Dict[str, Any]:
        with self._lock:
            state = self._budget_state(self._budgets, budget_id)
            state["alert_threshold_percent"] = alert_threshold_percent
        return {
            "budget_id": budget_id,
            "alert_threshold_percent": alert_threshold_percent,
            "status": "configured",
            "scope": "in-memory (this process only; not persisted)",
        }

    async def analyze_token_usage(
        self, time_period: str = "last_7d", group_by: str = "model"
    ) -> Dict[str, Any]:
        hours = _TIME_PERIOD_HOURS.get(time_period)
        if hours is None:
            return {
                "status": "error",
                "message": f"Unsupported time_period '{time_period}'.",
                "supported_periods": sorted(_TIME_PERIOD_HOURS),
            }
        if group_by not in ("model", "user", "application"):
            return {
                "status": "error",
                "message": f"Unsupported group_by '{group_by}'.",
                "supported_groups": ["model", "user", "application"],
            }

        cutoff = datetime.utcnow() - timedelta(hours=hours)
        with self._lock:
            recent = [r for r in self._usage if r["timestamp"] >= cutoff]

        usage_by_group: Dict[str, int] = {}
        total_input = 0
        total_output = 0
        total_cost = 0.0
        for record in recent:
            total_input += record["input_tokens"]
            total_output += record["output_tokens"]
            total_cost += record["cost_usd"]
            # group_by user/application have no data source in this library;
            # usage is only attributable to a model.
            key = record["model"] if group_by == "model" else "unknown"
            usage_by_group[key] = (
                usage_by_group.get(key, 0)
                + record["input_tokens"]
                + record["output_tokens"]
            )

        return {
            "time_period": time_period,
            "window_hours": hours,
            "group_by": group_by,
            "records": len(recent),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "total_cost_usd": total_cost,
            "usage_by_group": usage_by_group,
            "note": (
                "Counts usage recorded in memory by this handler instance; "
                "PyTokenCalc persists nothing. user/application grouping has "
                "no data source and reports 'unknown'."
            ),
        }

    # -------------------------------------------------------------- prompt tools

    @staticmethod
    def _normalize_prompt(prompt: str) -> str:
        """Conservative, lossless-ish whitespace cleanup: strip trailing
        whitespace per line, collapse 3+ blank lines to one, trim ends."""
        lines = [line.rstrip() for line in prompt.split("\n")]
        collapsed: List[str] = []
        blank_run = 0
        for line in lines:
            if line == "":
                blank_run += 1
                if blank_run > 1:
                    continue
            else:
                blank_run = 0
            collapsed.append(line)
        return "\n".join(collapsed).strip()

    async def optimize_prompt(
        self,
        prompt: str,
        model_name: str,
        target_reduction_percent: float = 20,
    ) -> Dict[str, Any]:
        try:
            original_tokens = self._count(prompt, model_name).input_tokens
        except Exception as e:  # noqa: BLE001
            return {"status": "error", "model": model_name, "message": str(e)}

        optimized = self._normalize_prompt(prompt)
        optimized_tokens = self._count(optimized, model_name).input_tokens
        reduction = (
            (original_tokens - optimized_tokens) / original_tokens * 100
            if original_tokens
            else 0.0
        )

        tips = []
        if optimized_tokens < original_tokens:
            tips.append("Stripped trailing whitespace and collapsed blank lines.")
        else:
            tips.append(
                "No safe whitespace savings available; no textual edits applied."
            )
        if target_reduction_percent and reduction < target_reduction_percent:
            tips.append(
                "Target not reached by lossless whitespace edits alone; "
                "reaching it needs semantic rewriting, which this tool does "
                "not attempt."
            )

        return {
            "model": model_name,
            "original_tokens": original_tokens,
            "optimized_tokens": optimized_tokens,
            "actual_reduction_percent": round(reduction, 2),
            "target_reduction_percent": target_reduction_percent,
            "target_met": reduction >= (target_reduction_percent or 0),
            "optimized_prompt": optimized,
            "optimization_tips": tips,
        }
