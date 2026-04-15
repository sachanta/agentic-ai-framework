"""Tests for the MCP SSE transport app."""
import pytest
from starlette.applications import Starlette

from app.mcp.sse import create_mcp_sse_app


@pytest.mark.mcp
class TestCreateMcpSseApp:
    def test_returns_starlette_app(self):
        app = create_mcp_sse_app()
        assert isinstance(app, Starlette)

    def test_has_sse_route(self):
        app = create_mcp_sse_app()
        paths = [r.path for r in app.routes]
        assert "/sse" in paths

    def test_has_messages_mount(self):
        app = create_mcp_sse_app()
        paths = [r.path for r in app.routes]
        # Mount path may or may not have trailing slash depending on Starlette version
        assert any(p.startswith("/messages") for p in paths)
