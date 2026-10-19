"""FastMCP server tests using an injected fake registry (no provider calls)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pytest

pytest.importorskip("fastmcp")

from pytokencalc.mcp_server import create_server


@dataclass
class _Result:
    input_tokens: int = 2
    total_tokens: int = 2
    system_tokens: int = 0
    tool_tokens: int = 0
    image_tokens: int = 0
    provider: str = "fake"
    source: str = "fake"
    cached: bool = False
    latency_ms: float = 0.1


class _Registry:
    def count_tokens(self, model, text, provider=None):
        return _Result()


def test_server_exposes_all_tools_and_calls_count():
    server = create_server(_Registry())

    async def run():
        tools = await server.list_tools()
        assert len(tools) == 12
        names = {tool.name for tool in tools}
        assert "count_tokens" in names
        assert "estimate_cost" in names
        result = await server.call_tool("count_tokens", {"text": "a b", "model_name": "gpt-4o"})
        return result

    result = asyncio.run(run())
    # FastMCP returns a ToolResult; content is serialized tool output.
    text = str(result)
    assert "input_tokens" in text


def test_real_fastmcp_client_roundtrip():
    from fastmcp import Client

    server = create_server(_Registry())

    async def run():
        async with Client(server) as client:
            tools = await client.list_tools()
            assert len(tools) == 12
            result = await client.call_tool("count_tokens", {"text": "a b", "model_name": "gpt-4o"})
            return result

    result = asyncio.run(run())
    assert "input_tokens" in str(result)
