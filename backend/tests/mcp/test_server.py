"""Tests for the MCP server."""
import json
from unittest.mock import AsyncMock, patch

import pytest
import mcp.types as types
from mcp.server.lowlevel import Server

from app.common.tools.registry import TOOL_REGISTRY
from app.mcp.server import (
    _mcp_name_to_tool_id,
    _tool_id_to_mcp_name,
    create_mcp_server,
)


# ---------------------------------------------------------------------------
# TestNameEncoding
# ---------------------------------------------------------------------------

@pytest.mark.mcp
class TestNameEncoding:
    def test_slash_to_underscore(self):
        assert _tool_id_to_mcp_name("search/tavily_search_topic") == "search__tavily_search_topic"

    def test_underscore_to_slash(self):
        assert _mcp_name_to_tool_id("search__tavily_search_topic") == "search/tavily_search_topic"

    def test_roundtrip_all_tools(self):
        for tool in TOOL_REGISTRY:
            tid = tool["tool_id"]
            encoded = _tool_id_to_mcp_name(tid)
            decoded = _mcp_name_to_tool_id(encoded)
            assert decoded == tid, f"Roundtrip failed for {tid}"

    def test_no_slashes_in_mcp_names(self):
        for tool in TOOL_REGISTRY:
            mcp_name = _tool_id_to_mcp_name(tool["tool_id"])
            assert "/" not in mcp_name, f"MCP name '{mcp_name}' contains slash"


# ---------------------------------------------------------------------------
# TestCreateMcpServer
# ---------------------------------------------------------------------------

@pytest.mark.mcp
class TestCreateMcpServer:
    def test_returns_server_instance(self):
        server = create_mcp_server()
        assert isinstance(server, Server)


# ---------------------------------------------------------------------------
# TestListToolsHandler
# ---------------------------------------------------------------------------

@pytest.mark.mcp
class TestListToolsHandler:
    async def test_returns_all_tools(self):
        server = create_mcp_server()
        handler = server.request_handlers[types.ListToolsRequest]
        result = await handler(types.ListToolsRequest(method="tools/list"))
        tools = result.root.tools
        assert len(tools) == len(TOOL_REGISTRY)

    async def test_names_are_encoded(self):
        server = create_mcp_server()
        handler = server.request_handlers[types.ListToolsRequest]
        result = await handler(types.ListToolsRequest(method="tools/list"))
        names = {t.name for t in result.root.tools}
        for tool_def in TOOL_REGISTRY:
            expected = _tool_id_to_mcp_name(tool_def["tool_id"])
            assert expected in names, f"Missing MCP tool name: {expected}"

    async def test_all_have_input_schema(self):
        server = create_mcp_server()
        handler = server.request_handlers[types.ListToolsRequest]
        result = await handler(types.ListToolsRequest(method="tools/list"))
        for tool in result.root.tools:
            assert tool.inputSchema is not None
            assert tool.inputSchema["type"] == "object"


# ---------------------------------------------------------------------------
# TestCallToolHandler
# ---------------------------------------------------------------------------

@pytest.mark.mcp
class TestCallToolHandler:
    async def test_success_returns_json_result(self):
        server = create_mcp_server()
        handler = server.request_handlers[types.CallToolRequest]

        with patch("app.mcp.server.execute_tool", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {"status": "ok"}
            result = await handler(
                types.CallToolRequest(
                    method="tools/call",
                    params=types.CallToolRequestParams(
                        name="search__tavily_search_topic",
                        arguments={"topic": "AI"},
                    ),
                )
            )
        content = result.root.content
        assert len(content) == 1
        data = json.loads(content[0].text)
        assert data == {"status": "ok"}

    async def test_not_found_returns_error(self):
        server = create_mcp_server()
        handler = server.request_handlers[types.CallToolRequest]

        result = await handler(
            types.CallToolRequest(
                method="tools/call",
                params=types.CallToolRequestParams(
                    name="nonexistent__tool",
                    arguments={},
                ),
            )
        )
        content = result.root.content
        data = json.loads(content[0].text)
        assert "error" in data
        assert "not found" in data["error"]

    async def test_timeout_returns_error(self):
        import asyncio
        server = create_mcp_server()
        handler = server.request_handlers[types.CallToolRequest]

        async def slow_exec(*args, **kwargs):
            await asyncio.sleep(999)

        with patch("app.mcp.server.execute_tool", side_effect=slow_exec):
            with patch("app.mcp.server.asyncio.wait_for", side_effect=asyncio.TimeoutError):
                result = await handler(
                    types.CallToolRequest(
                        method="tools/call",
                        params=types.CallToolRequestParams(
                            name="search__tavily_search_topic",
                            arguments={"topic": "AI"},
                        ),
                    )
                )
        data = json.loads(result.root.content[0].text)
        assert "error" in data
        assert "timed out" in data["error"].lower()

    async def test_exception_returns_error(self):
        server = create_mcp_server()
        handler = server.request_handlers[types.CallToolRequest]

        with patch("app.mcp.server.execute_tool", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = RuntimeError("something broke")
            result = await handler(
                types.CallToolRequest(
                    method="tools/call",
                    params=types.CallToolRequestParams(
                        name="search__tavily_search_topic",
                        arguments={"topic": "AI"},
                    ),
                )
            )
        data = json.loads(result.root.content[0].text)
        assert "error" in data
        assert "something broke" in data["error"]
