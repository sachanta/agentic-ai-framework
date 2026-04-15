"""
MCP Server for the Agentic AI Framework.

Exposes all 16 framework tools over the Model Context Protocol using the
low-level Server class. Tools are registered dynamically from the shared
tool registry.

Transports:
  - stdio: run directly with ``python -m app.mcp``
  - SSE:   mount via ``app.mcp.sse`` in the FastAPI application
"""
import asyncio
import json
import logging
from typing import Any, Sequence

from mcp.server.lowlevel import Server
import mcp.types as types

from app.common.tools.registry import (
    TOOL_REGISTRY,
    execute_tool,
    get_tool,
    tool_def_to_input_schema,
)

logger = logging.getLogger(__name__)

# MCP tool names cannot contain '/'. We encode '/' as '__'.
_SEP = "__"


def _tool_id_to_mcp_name(tool_id: str) -> str:
    return tool_id.replace("/", _SEP)


def _mcp_name_to_tool_id(name: str) -> str:
    return name.replace(_SEP, "/")


def create_mcp_server() -> Server:
    """Create and configure the MCP server with all framework tools."""
    server = Server("agentic-ai-framework")

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        tools: list[types.Tool] = []
        for tool_def in TOOL_REGISTRY:
            description_parts = [tool_def["description"]]
            description_parts.append(f"[{tool_def['category']}] {tool_def['service_class']}")
            description_parts.append(f"Returns: {tool_def.get('returns', 'Any')}")
            if tool_def.get("requires"):
                description_parts.append(f"Requires: {', '.join(tool_def['requires'])}")

            tools.append(
                types.Tool(
                    name=_tool_id_to_mcp_name(tool_def["tool_id"]),
                    description="\n".join(description_parts),
                    inputSchema=tool_def_to_input_schema(tool_def),
                )
            )
        return tools

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict[str, Any] | None
    ) -> Sequence[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        tool_id = _mcp_name_to_tool_id(name)

        try:
            tool_def = get_tool(tool_id)
        except KeyError:
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps({"error": f"Tool '{tool_id}' not found"}),
                )
            ]

        params = arguments or {}

        try:
            result = await asyncio.wait_for(
                execute_tool(tool_def, params),
                timeout=60,
            )
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, default=str),
                )
            ]
        except asyncio.TimeoutError:
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps({"error": "Tool execution timed out after 60 seconds"}),
                )
            ]
        except Exception as e:
            logger.warning(f"MCP tool execution failed for {tool_id}: {e}")
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)}),
                )
            ]

    return server


async def run_stdio() -> None:
    """Run the MCP server with stdio transport (for Claude Desktop / Claude Code)."""
    from mcp.server.stdio import stdio_server

    server = create_mcp_server()

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )
