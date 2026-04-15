"""
SSE transport for the MCP server, mountable inside a FastAPI/Starlette app.

Usage in FastAPI::

    from app.mcp.sse import create_mcp_sse_app
    app.mount("/mcp", create_mcp_sse_app())
"""
import logging

from starlette.applications import Starlette
from starlette.routing import Mount, Route

from mcp.server.sse import SseServerTransport

from app.mcp.server import create_mcp_server

logger = logging.getLogger(__name__)


def create_mcp_sse_app() -> Starlette:
    """Create a Starlette app that serves the MCP server over SSE."""
    mcp_server = create_mcp_server()
    sse_transport = SseServerTransport("/messages/")

    async def handle_sse(request):
        async with sse_transport.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await mcp_server.run(
                streams[0],
                streams[1],
                mcp_server.create_initialization_options(),
            )

    return Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse_transport.handle_post_message),
        ],
    )
