"""Real MCP server for PyTokenCalc (FastMCP transport).

This exposes the same 12 tools as ``pytokencalc._mcp_tools`` over stdio or
HTTP. It is an optional integration:

    pip install "pytokencalc[mcp]"

CLI:
    pytokencalc-mcp --transport stdio
    pytokencalc-mcp --transport http --host 127.0.0.1 --port 8778

Python:
    from pytokencalc.mcp_server import create_server
    server = create_server()
    server.run(transport="stdio")
"""

from __future__ import annotations

import argparse
import ipaddress
import logging
import os
from typing import Any, Optional

from pytokencalc._mcp_tools import PyTokenCalcMCPHandler, PyTokenCalcMCPTools

logger = logging.getLogger(__name__)


class MCPUnavailable(RuntimeError):
    """Raised when FastMCP is not installed."""


def _is_loopback(host: str) -> bool:
    if host in {"localhost", "127.0.0.1", "::1"}:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def ensure_safe_bind(host: str, transport: str = "http") -> None:
    """Refuse an unauthenticated non-loopback HTTP/SSE bind by default.

    The MCP server has no authentication layer. Binding it to a public
    interface is a deliberate, explicit choice.
    """
    if transport == "stdio" or _is_loopback(host):
        return
    if os.environ.get("PYTOKENCALC_MCP_ALLOW_UNAUTHENTICATED") == "1":
        return
    raise ValueError(
        f"Refusing to bind unauthenticated MCP transport to non-loopback host "
        f"{host!r}. Set PYTOKENCALC_MCP_ALLOW_UNAUTHENTICATED=1 only if you "
        f"have put authentication/network controls in front of it."
    )


def _require_fastmcp():
    try:
        from fastmcp import FastMCP
    except ImportError as exc:
        raise MCPUnavailable(
            "FastMCP is not installed. Install the optional MCP transport with "
            '`pip install "pytokencalc[mcp]"` (or `pip install fastmcp`).'
        ) from exc
    return FastMCP


def create_server(registry: Any = None) -> Any:
    """Build a FastMCP server exposing PyTokenCalc's tools."""
    FastMCP = _require_fastmcp()
    handler = PyTokenCalcMCPHandler(registry=registry)
    schemas = PyTokenCalcMCPTools.get_tools()
    mcp = FastMCP(
        "PyTokenCalc",
        instructions=(
            "Count LLM tokens and estimate USD costs using real tokenizers and "
            "the static pricing table. Budget/usage tools are process-scoped "
            "and non-durable."
        ),
    )

    def desc(name: str) -> str:
        return schemas.get(name, {}).get("description", name)

    @mcp.tool(name="count_tokens", description=desc("count_tokens"))
    async def count_tokens(
        text: str, model_name: str, provider: Optional[str] = None
    ) -> dict[str, Any]:
        return await handler.count_tokens(text, model_name, provider)

    @mcp.tool(name="batch_count_tokens", description=desc("batch_count_tokens"))
    async def batch_count_tokens(texts: list[str], model_name: str) -> dict[str, Any]:
        return await handler.batch_count_tokens(texts, model_name)

    @mcp.tool(name="get_token_breakdown", description=desc("get_token_breakdown"))
    async def get_token_breakdown(
        text: str, model_name: str, show_special_tokens: bool = False
    ) -> dict[str, Any]:
        return await handler.get_token_breakdown(text, model_name, show_special_tokens)

    @mcp.tool(name="estimate_cost", description=desc("estimate_cost"))
    async def estimate_cost(
        input_tokens: int, output_tokens: int, model_name: str
    ) -> dict[str, Any]:
        return await handler.estimate_cost(input_tokens, output_tokens, model_name)

    @mcp.tool(name="estimate_total_cost", description=desc("estimate_total_cost"))
    async def estimate_total_cost(
        total_input_tokens: int, total_output_tokens: int, model_name: str
    ) -> dict[str, Any]:
        return await handler.estimate_total_cost(
            total_input_tokens, total_output_tokens, model_name
        )

    @mcp.tool(name="compare_model_costs", description=desc("compare_model_costs"))
    async def compare_model_costs(
        text: str, models: list[str], estimated_output_tokens: int = 200
    ) -> dict[str, Any]:
        return await handler.compare_model_costs(text, models, estimated_output_tokens)

    @mcp.tool(name="get_model_pricing", description=desc("get_model_pricing"))
    async def get_model_pricing(model_name: str) -> dict[str, Any]:
        return await handler.get_model_pricing(model_name)

    @mcp.tool(name="export_pricing_report", description=desc("export_pricing_report"))
    async def export_pricing_report(
        format: str = "json", include_models: Optional[list[str]] = None
    ) -> dict[str, Any]:
        return await handler.export_pricing_report(format, include_models)

    @mcp.tool(name="track_budget", description=desc("track_budget"))
    async def track_budget(
        budget_id: str,
        tokens_used: Optional[int] = None,
        cost_used: Optional[float] = None,
        limit_tokens: Optional[int] = None,
        limit_cost: Optional[float] = None,
    ) -> dict[str, Any]:
        return await handler.track_budget(
            budget_id, tokens_used, cost_used, limit_tokens, limit_cost
        )

    @mcp.tool(name="set_budget_alert", description=desc("set_budget_alert"))
    async def set_budget_alert(budget_id: str, alert_threshold_percent: float) -> dict[str, Any]:
        return await handler.set_budget_alert(budget_id, alert_threshold_percent)

    @mcp.tool(name="analyze_token_usage", description=desc("analyze_token_usage"))
    async def analyze_token_usage(
        time_period: str = "last_7d", group_by: str = "model"
    ) -> dict[str, Any]:
        return await handler.analyze_token_usage(time_period, group_by)

    @mcp.tool(name="optimize_prompt", description=desc("optimize_prompt"))
    async def optimize_prompt(
        prompt: str, model_name: str, target_reduction_percent: float = 10.0
    ) -> dict[str, Any]:
        return await handler.optimize_prompt(prompt, model_name, target_reduction_percent)

    return mcp


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="PyTokenCalc MCP server")
    parser.add_argument("--transport", choices=["stdio", "http", "sse"], default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8778)
    args = parser.parse_args(argv)

    try:
        ensure_safe_bind(args.host, args.transport)
    except ValueError as exc:
        parser.error(str(exc))

    server = create_server()
    if args.transport == "stdio":
        server.run(transport="stdio")
    else:
        server.run(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
