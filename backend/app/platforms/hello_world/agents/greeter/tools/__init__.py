"""
Greeter Agent tools.

This file is a placeholder for agent tools. The greeter agent doesn't
need any tools, but this demonstrates the pattern for agents that do.

Example tools for other agents might include:
- Web search tool
- Database query tool
- API call tool
- File operations tool
"""
from typing import List

from app.common.base.tool import BaseTool


def get_greeter_tools() -> List[BaseTool]:
    """
    Get the tools available to the greeter agent.

    The greeter agent doesn't need any tools, so this returns an empty list.

    Returns:
        Empty list (greeter doesn't need tools)
    """
    return []


__all__ = ["get_greeter_tools"]
