"""MCP-facing facade for PyTokenCalc.

Historically this module tried to launch an external ``dab`` binary (via an
optional ``statguardian`` package) to serve the MCP tools over HTTP. Neither
is a dependency of this project and the path was never verified to work, so it
has been removed.

What remains is honest and real: :class:`TokenCalculator` exposes the token
counting/cost-estimation tool surface (:mod:`pytokencalc._mcp_tools`) backed by
the library's real :class:`~pytokencalc.tokenizers.TokenCounterRegistry` and
the static :mod:`pytokencalc.pricing` table. The optional FastMCP transport in
:mod:`pytokencalc.mcp_server` serves those same tools over stdio or HTTP when
installed with ``pip install "pytokencalc[mcp]"``; without it, building a
server raises an actionable :class:`~pytokencalc.mcp_server.MCPUnavailable`
instead of reporting a fake endpoint.
"""

from typing import Any, Dict, Optional

from .tokenizers import get_global_registry


class TokenCalculator:
    """Facade over the MCP tool surface, backed by the real token registry.

    Example::

        from pytokencalc import TokenCalculator

        calc = TokenCalculator()
        handler = calc.get_handler()
        tools = calc.get_tools()
    """

    def __init__(self, registry: Optional[Any] = None):
        self.registry = registry if registry is not None else get_global_registry()

    def get_tools(self) -> Dict[str, Any]:
        """Return the MCP tool schemas (``pytokencalc._mcp_tools``)."""
        from pytokencalc._mcp_tools import PyTokenCalcMCPTools

        return PyTokenCalcMCPTools.get_tools()

    def get_handler(self, calc: Optional[Any] = None) -> Any:
        """Return a handler bound to this calculator's registry."""
        from pytokencalc._mcp_tools import PyTokenCalcMCPHandler

        return PyTokenCalcMCPHandler(calc=calc or self, registry=self.registry)

    def create_mcp_server(self):
        """Build a FastMCP server exposing the 12 tools.

        Returns a FastMCP instance; call ``.run(transport="stdio")`` (or
        ``"http"`` with host/port) to serve it. Install the optional transport
        with ``pip install "pytokencalc[mcp]"``.
        """
        from .mcp_server import create_server

        return create_server(self.registry)

    def start_mcp_connector(self, port: int = 8778):
        """Build the MCP server (non-blocking) and return it.

        Kept as a compatibility alias for callers that used the old facade;
        the returned object is a real FastMCP server. The process-level CLI is
        ``pytokencalc-mcp``. Call ``server.run(...)`` to start serving.
        """
        return self.create_mcp_server()

    def serve_mcp(
        self, transport: str = "stdio", host: str = "127.0.0.1", port: int = 8778
    ) -> None:
        """Run the MCP server (blocking)."""
        from .mcp_server import ensure_safe_bind

        ensure_safe_bind(host, transport)
        server = self.create_mcp_server()
        if transport == "stdio":
            server.run(transport="stdio")
        else:
            server.run(transport=transport, host=host, port=port)

    def stop_mcp_connector(self) -> None:
        """No-op: the returned server object owns its own lifecycle."""
