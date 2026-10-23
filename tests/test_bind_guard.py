"""Safety tests for unauthenticated network binds."""

import pytest

from pytokencalc.mcp_server import ensure_safe_bind


def test_loopback_and_stdio_binds_are_allowed():
    ensure_safe_bind("127.0.0.1", "http")
    ensure_safe_bind("localhost", "http")
    ensure_safe_bind("::1", "http")
    ensure_safe_bind("0.0.0.0", "stdio")


def test_non_loopback_bind_is_refused_by_default(monkeypatch):
    monkeypatch.delenv("PYTOKENCALC_MCP_ALLOW_UNAUTHENTICATED", raising=False)
    with pytest.raises(ValueError, match="Refusing"):
        ensure_safe_bind("0.0.0.0", "http")


def test_non_loopback_bind_requires_explicit_opt_in(monkeypatch):
    monkeypatch.setenv("PYTOKENCALC_MCP_ALLOW_UNAUTHENTICATED", "1")
    ensure_safe_bind("0.0.0.0", "http")
