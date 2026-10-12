"""MCP-facing facade for PyTokenCalc.

Historically this module tried to launch an external ``dab`` binary (via an
optional ``statguardian`` package) to serve the MCP tools over HTTP. Neither
is a dependency of this project and the path was never verified to work, so it
has been removed.

What remains is honest and real: :class:`TokenCalculator` exposes the token
counting/cost-estimation tool surface (:mod:`pytokencalc._mcp_tools`) backed by
the library's real :class:`~pytokencalc.tokenizers.TokenCounterRegistry` and
the static :mod:`pytokencalc.pricing` table. There is no bundled MCP server or
transport in this package, so :meth:`TokenCalculator.start_mcp_connector`
raises ``NotImplementedError`` rather than reporting a fake endpoint.
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

    def start_mcp_connector(self, port: int = 8778) -> str:
        """Not implemented: this package ships no MCP server/transport.

        The previous implementation shelled out to a ``dab`` binary that is
        not a dependency of PyTokenCalc. Use :meth:`get_handler` and
        :meth:`get_tools` directly (e.g. from your own MCP host), or run the
        REST server in :mod:`pytokencalc.server`.
        """
        raise NotImplementedError(
            "PyTokenCalc does not ship an MCP server/transport. The former "
            "implementation launched an external 'dab' binary that is not a "
            "dependency. Use TokenCalculator.get_tools()/get_handler() from "
            "your own MCP host, or pytokencalc.server for the REST API."
        )

    def stop_mcp_connector(self) -> None:
        """No-op: there is no connector process to stop."""
