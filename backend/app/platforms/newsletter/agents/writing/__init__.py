"""
Writing Agent for Newsletter Platform.

Exports:
- WritingAgent: Main agent class for newsletter generation
- get_writing_llm: LLM provider factory
- format_all: Multi-format output generator
"""
from app.platforms.newsletter.agents.writing.agent import WritingAgent
from app.platforms.newsletter.agents.writing.llm import (
    get_writing_llm,
    get_writing_config,
    get_creative_config,
)
from app.platforms.newsletter.agents.writing.formatters import (
    format_html,
    format_email_html,
    format_plain_text,
    format_markdown,
    format_all,
)

__all__ = [
    "WritingAgent",
    "get_writing_llm",
    "get_writing_config",
    "get_creative_config",
    "format_html",
    "format_email_html",
    "format_plain_text",
    "format_markdown",
    "format_all",
]
