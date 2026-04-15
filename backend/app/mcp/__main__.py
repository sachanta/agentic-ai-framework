"""Entry point for running the MCP server via ``python -m app.mcp``."""
import asyncio

from app.mcp.server import run_stdio

if __name__ == "__main__":
    asyncio.run(run_stdio())
